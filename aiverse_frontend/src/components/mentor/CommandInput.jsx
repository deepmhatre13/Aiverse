import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Mic, Paperclip, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';
import { GlowButton } from '@/design-system';

const DEFAULT_SUGGESTIONS = [
  'explain overfitting',
  'suggest model for iris',
  'optimize hyperparameters',
  'what is gradient descent?',
  'compare logistic vs neural',
];

export default function CommandInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  suggestions = DEFAULT_SUGGESTIONS,
  showExplainDeeply = true,
  placeholder = 'Ask or type a command...',
  className,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [explainDeeply, setExplainDeeply] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [value]);

  const handleSubmit = (e) => {
    e?.preventDefault?.();
    if (value?.trim() && !disabled) onSubmit?.(value.trim(), { explainDeeply });
  };

  const handleSuggestionClick = (s) => {
    onChange?.(s);
    textareaRef.current?.focus();
  };

  const isCommand = (v) => {
    const t = (v || '').trim().toLowerCase();
    return (
      t.startsWith('explain ') ||
      t.startsWith('suggest ') ||
      t.startsWith('optimize ') ||
      t.startsWith('compare ') ||
      t.startsWith('what is ') ||
      t.startsWith('how does ')
    );
  };

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {/* Suggestion chips */}
      {suggestions && suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s, i) => (
            <motion.button
              key={i}
              type="button"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              onClick={() => handleSuggestionClick(s)}
              disabled={disabled}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium',
                'border border-white/10 bg-white/[0.03]',
                'hover:border-primary/40 hover:bg-primary/5 hover:text-primary',
                'transition-colors'
              )}
            >
              {s}
            </motion.button>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="relative">
        {/* Expandable container with red glow on focus */}
        <div
          className={cn(
            'rounded-xl border-2 transition-all duration-200',
            'bg-black/40 backdrop-blur-xl',
            isFocused
              ? 'border-primary/50 shadow-[0_0_20px_rgba(225,6,0,0.12)]'
              : 'border-white/10 hover:border-primary/30'
          )}
        >
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange?.(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder={placeholder}
            disabled={disabled}
            rows={2}
            className={cn(
              'w-full px-4 py-3 pr-24 bg-transparent resize-none outline-none',
              'text-sm text-foreground placeholder:text-muted-foreground/60',
              'min-h-[52px] max-h-[200px]'
            )}
          />

          {/* Actions row */}
          <div className="absolute right-3 bottom-3 flex items-center gap-1">
            {showExplainDeeply && (
              <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 rounded text-muted-foreground hover:text-primary hover:bg-primary/10"
                title="More options"
              >
                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
            )}
            <button
              type="button"
              className="p-1.5 rounded text-muted-foreground hover:text-primary hover:bg-primary/10"
              title="Attach dataset (coming soon)"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button
              type="button"
              className="p-1.5 rounded text-muted-foreground hover:text-primary hover:bg-primary/10"
              title="Voice input (coming soon)"
            >
              <Mic className="w-4 h-4" />
            </button>
            <GlowButton
              type="submit"
              size="sm"
              disabled={disabled || !value?.trim()}
              className="h-9 px-3"
            >
              <Send className="w-4 h-4" />
            </GlowButton>
          </div>
        </div>

        {/* Expanded options */}
        <AnimatePresence>
          {isExpanded && showExplainDeeply && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-2 overflow-hidden"
            >
              <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                <input
                  type="checkbox"
                  checked={explainDeeply}
                  onChange={(e) => setExplainDeeply(e.target.checked)}
                  className="rounded border-white/20 bg-black/50 text-primary focus:ring-primary"
                />
                Explain deeply
              </label>
            </motion.div>
          )}
        </AnimatePresence>
      </form>

      <p className="text-[10px] text-muted-foreground">
        Ctrl+Enter to send • Commands: explain, suggest, optimize
      </p>
    </div>
  );
}
