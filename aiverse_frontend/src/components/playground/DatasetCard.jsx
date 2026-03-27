import { motion, useMotionValue, useTransform } from 'framer-motion';
import { Database } from 'lucide-react';
import { cn } from '@/lib/utils';

function MiniFeatureBars({ count = 4, max = 10 }) {
  const normalized = Math.min(Math.max(count, 1), max);
  const barCount = Math.min(6, Math.max(max, 4));
  const bars = Array.from({ length: barCount }, (_, i) => {
    const pct = i < normalized ? 60 + (i / barCount) * 40 : 15 + (i / barCount) * 15;
    return { id: i, height: pct, active: i < normalized };
  });

  return (
    <div className="flex items-end gap-1 h-8">
      {bars.map((b) => (
        <motion.div
          key={b.id}
          className={cn(
            'w-1.5 rounded-t min-h-[4px]',
            b.active ? 'bg-primary/70' : 'bg-white/10'
          )}
          initial={{ height: 0 }}
          animate={{ height: `${b.height}%` }}
          transition={{ duration: 0.35, delay: b.id * 0.05, ease: [0.22, 0.61, 0.36, 1] }}
        />
      ))}
    </div>
  );
}

export default function DatasetCard({
  option,
  isSelected,
  onClick,
  taskType = 'classification',
  numFeatures,
  numSamples,
  difficulty,
  className,
}) {
  const x = useMotionValue(0);
  const rotateYDeg = useTransform(x, [-80, 80], [4, -4]);
  const rotateY = useTransform(rotateYDeg, (v) => `${v}deg`);

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    x.set(e.clientX - centerX);
  };

  const handleMouseLeave = () => {
    x.set(0);
  };

  return (
    <motion.button
      type="button"
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.98 }}
      style={{ rotateY }}
      className={cn(
        'relative w-full p-5 rounded-xl text-left overflow-hidden',
        'border-2 backdrop-blur-xl transition-shadow duration-300',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B0B0F]',
        isSelected
          ? 'border-primary bg-primary/10 shadow-[0_0_30px_rgba(225,6,0,0.2)]'
          : 'border-white/10 bg-white/[0.03] hover:border-primary/40 hover:shadow-[0_0_24px_rgba(225,6,0,0.12)]',
        className
      )}
    >
      {/* Subtle gradient sweep on selection */}
      {isSelected && (
        <div
          className="absolute inset-0 pointer-events-none opacity-30"
          style={{
            background: 'linear-gradient(105deg, transparent 40%, rgba(225,6,0,0.08) 50%, transparent 60%)',
          }}
        />
      )}

      <div className="relative flex flex-col gap-3">
        <div className="flex items-start justify-between gap-2">
          <div className="p-2 rounded-lg bg-primary/10">
            <Database className="w-5 h-5 text-primary" />
          </div>
          <span
            className={cn(
              'text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded',
              taskType === 'regression'
                ? 'bg-primary/20 text-primary/90'
                : 'bg-primary/15 text-primary'
            )}
          >
            {taskType || 'Classification'}
          </span>
        </div>

        <div>
          <div className="font-semibold text-foreground mb-0.5">
            {option?.label ?? option?.name ?? 'Dataset'}
          </div>
          {option?.description && (
            <div className="text-xs text-muted-foreground line-clamp-2">
              {option.description}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-4">
          <MiniFeatureBars count={numFeatures || 4} max={20} />
          <div className="text-xs text-muted-foreground font-mono">
            {numSamples ?? option?.num_samples ?? '—'} samples
          </div>
        </div>

        {difficulty && (
          <div className="text-[10px] text-muted-foreground/80 uppercase tracking-wider">
            {difficulty}
          </div>
        )}
      </div>

      {/* Selection glow ring */}
      {isSelected && (
        <motion.div
          className="absolute inset-0 rounded-xl pointer-events-none border-2 border-primary/50"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1, boxShadow: 'inset 0 0 20px rgba(225,6,0,0.08)' }}
          transition={{ duration: 0.25 }}
        />
      )}
    </motion.button>
  );
}
