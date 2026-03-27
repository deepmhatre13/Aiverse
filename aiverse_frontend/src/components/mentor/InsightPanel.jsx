import { motion } from 'framer-motion';
import { Cpu, Code2, Lightbulb, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

const placeholderModels = [
  { id: 'lr', name: 'Logistic Regression', fit: 'classification' },
  { id: 'nn', name: 'Neural Network', fit: 'flexible' },
];

export default function InsightPanel({
  suggestedModels = placeholderModels,
  codePreview = null,
  concepts = [],
  graphPlaceholder = true,
  datasetContext = null,
  className,
}) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className={cn(
        'w-80 lg:w-96 shrink-0 flex flex-col gap-4 overflow-y-auto',
        'border-l border-white/10',
        'bg-black/30 backdrop-blur-xl',
        className
      )}
    >
      <div className="p-4 border-b border-white/5">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-primary" />
          AI Insight
        </h3>
        <p className="text-xs text-muted-foreground mt-1">
          Suggestions and context from the conversation
        </p>
      </div>

      <div className="flex-1 space-y-4 px-4 pb-6">
        {/* Suggested models */}
        {suggestedModels && suggestedModels.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Cpu className="w-4 h-4 text-primary" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Suggested Models
              </span>
            </div>
            <div className="space-y-2">
              {suggestedModels.map((m, i) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="p-3 rounded-lg border border-white/10 bg-white/[0.02] hover:border-primary/30 transition-colors"
                >
                  <div className="font-medium text-sm text-foreground">{m.name}</div>
                  {m.fit && (
                    <div className="text-[10px] text-muted-foreground mt-0.5">{m.fit}</div>
                  )}
                </motion.div>
              ))}
            </div>
          </section>
        )}

        {/* Code preview */}
        {codePreview && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Code2 className="w-4 h-4 text-primary" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Code Preview
              </span>
            </div>
            <pre className="p-3 rounded-lg bg-black/50 border border-white/5 font-mono text-[11px] overflow-x-auto max-h-32">
              <code>{codePreview}</code>
            </pre>
          </section>
        )}

        {/* Key concepts */}
        {concepts && concepts.length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-primary" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Key Concepts
              </span>
            </div>
            <ul className="space-y-1.5">
              {concepts.map((c, i) => (
                <li key={i} className="text-xs text-foreground flex items-start gap-2">
                  <span className="text-primary mt-0.5">•</span>
                  <span>{typeof c === 'string' ? c : c.label || c}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Dataset context */}
        {datasetContext && (
          <section>
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Dataset Context
            </div>
            <div className="p-3 rounded-lg border border-white/10 bg-white/[0.02] text-xs text-foreground">
              {datasetContext}
            </div>
          </section>
        )}

        {/* Graph placeholder */}
        {graphPlaceholder && (
          <section>
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Loss Curve
            </div>
            <div
              className="h-24 rounded-lg border border-dashed border-white/10 flex items-center justify-center"
              aria-hidden
            >
              <span className="text-[10px] text-muted-foreground/60">Chart placeholder</span>
            </div>
          </section>
        )}
      </div>
    </motion.aside>
  );
}
