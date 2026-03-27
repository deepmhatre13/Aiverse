import { motion } from 'framer-motion';

const STEPS = [
  { key: 'dataset', label: 'Dataset', short: '1' },
  { key: 'model', label: 'Model', short: '2' },
  { key: 'hyperparams', label: 'Hyperparameters', short: '3' },
  { key: 'train', label: 'Train', short: '4' },
];

export default function LabStepper({ currentStep, onStepClick, stepsOrder = STEPS }) {
  const currentIndex = stepsOrder.findIndex((s) => s.key === currentStep);

  return (
    <nav className="flex flex-col gap-0">
      {stepsOrder.map((step, i) => {
        const isActive = step.key === currentStep;
        const isPast = i < currentIndex;
        const isLast = i === stepsOrder.length - 1;

        return (
          <motion.button
            key={step.key}
            type="button"
            onClick={() => onStepClick?.(step.key)}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.06, duration: 0.28, ease: [0.22, 0.61, 0.36, 1] }}
            className={`
              relative flex items-center gap-3 py-3 px-4 rounded-lg w-full text-left
              transition-colors duration-200
              ${isActive ? 'bg-primary/10' : 'hover:bg-white/[0.04]'}
            `}
          >
            {/* Vertical line to next step */}
            {!isLast && (
              <div
                className="absolute left-[19px] top-full w-px min-h-[16px] mt-1 -mb-1
                  bg-gradient-to-b from-border/60 to-transparent"
                aria-hidden
              />
            )}

            {/* Progress pulse line when active */}
            {isActive && !isLast && (
              <motion.div
                className="absolute left-[19px] top-full w-0.5 min-h-[20px] mt-1
                  bg-primary shadow-[0_0_12px_rgba(225,6,0,0.5)]"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 20, opacity: 1 }}
                transition={{ duration: 0.32, ease: [0.22, 0.61, 0.36, 1] }}
                aria-hidden
              />
            )}

            {/* Step circle */}
            <div
              className={`
                relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full
                border-2 font-mono text-xs font-semibold
                transition-all duration-220
                ${isActive
                  ? 'border-primary bg-primary/15 text-primary shadow-[0_0_20px_rgba(225,6,0,0.25)]'
                  : isPast
                    ? 'border-primary/40 bg-primary/5 text-primary/80'
                    : 'border-border/50 bg-white/[0.02] text-muted-foreground'
                }
              `}
            >
              {step.short}
              {isActive && (
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-primary"
                  animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
                  aria-hidden
                />
              )}
            </div>

            <span
              className={`
                text-sm font-medium
                ${isActive ? 'text-foreground' : isPast ? 'text-muted-foreground' : 'text-muted-foreground/80'}
              `}
            >
              {step.label}
            </span>
          </motion.button>
        );
      })}
    </nav>
  );
}
