import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

const slideVariants = {
  enter: (direction) => ({
    x: direction > 0 ? 24 : -24,
    opacity: 0,
    filter: 'blur(8px)',
  }),
  center: {
    x: 0,
    opacity: 1,
    filter: 'blur(0px)',
  },
  exit: (direction) => ({
    x: direction < 0 ? 24 : -24,
    opacity: 0,
    filter: 'blur(8px)',
  }),
};

export default function LabContentPanel({
  children,
  className,
  direction = 0,
  key,
}) {
  return (
    <motion.div
      key={key}
      className={cn(
        'relative rounded-xl border border-white/10 bg-black/40 backdrop-blur-xl',
        'shadow-[0_0_0_1px_rgba(255,255,255,0.04),0_0_40px_rgba(0,0,0,0.4)]',
        'ring-1 ring-primary/20',
        className
      )}
    >
      {/* Red edge glow */}
      <div
        className="absolute inset-0 rounded-xl pointer-events-none opacity-50"
        style={{
          boxShadow: 'inset 0 0 0 1px rgba(225,6,0,0.15)',
        }}
      />
      <div className="relative p-6 md:p-8">
        {children}
      </div>
    </motion.div>
  );
}

export function LabContentTransition({ children, stepKey, direction = 0 }) {
  return (
    <AnimatePresence mode="wait" custom={direction}>
      <motion.div
        key={stepKey}
        custom={direction}
        variants={slideVariants}
        initial="enter"
        animate="center"
        exit="exit"
        transition={{
          duration: 0.32,
          ease: [0.22, 0.61, 0.36, 1],
        }}
        className="w-full"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}
