import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  Code2,
  Pin,
  Play,
  Copy,
  Check,
  Sparkles,
  User,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { GlowButton } from '@/design-system';

const SECTION_LABELS = {
  concept: { icon: Sparkles, label: 'Concept', className: 'text-primary border-primary/30 bg-primary/5' },
  code: { icon: Code2, label: 'Code', className: 'text-primary border-primary/30 bg-primary/5' },
  warning: { icon: null, label: 'Warning', className: 'text-amber-400/90 border-amber-400/30 bg-amber-400/5' },
  tip: { icon: null, label: 'Pro Tip', className: 'text-emerald-400/90 border-emerald-400/30 bg-emerald-400/5' },
};

function parseContentSections(content) {
  if (!content) return [{ type: 'text', body: '(Empty response)' }];
  const sections = [];
  const lines = content.split('\n');
  let current = { type: 'text', body: '' };
  let inCodeBlock = false;
  let codeLang = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const codeStart = line.match(/^```(\w*)/);
    const sectionMatch = line.match(/^(Concept|Code|Warning|Pro Tip|Pro tip):\s*/i);

    if (codeStart) {
      if (inCodeBlock) {
        current.body += line + '\n';
        sections.push({ ...current, body: current.body.trim() });
        current = { type: 'text', body: '' };
      } else {
        if (current.body.trim()) sections.push({ ...current, body: current.body.trim() });
        current = { type: 'code', body: line + '\n', lang: codeStart[1] || 'python' };
      }
      inCodeBlock = !inCodeBlock;
      continue;
    }

    if (inCodeBlock) {
      current.body += line + '\n';
      continue;
    }

    if (sectionMatch) {
      if (current.body.trim()) sections.push({ ...current, body: current.body.trim() });
      const type = sectionMatch[1].toLowerCase().replace(' ', '');
      const mapped = type === 'protip' ? 'tip' : type === 'warning' ? 'warning' : type === 'concept' ? 'concept' : 'code';
      current = { type: mapped, body: line.slice(sectionMatch[0].length) };
      continue;
    }

    if (current.type !== 'text') {
      sections.push({ ...current, body: current.body.trim() });
      current = { type: 'text', body: line };
    } else {
      current.body += (current.body ? '\n' : '') + line;
    }
  }
  if (current.body.trim() || current.type === 'code') sections.push({ ...current, body: current.body.trim() });
  return sections;
}

export function UserMessage({ message, className }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn('flex justify-end', className)}
    >
      <div
        className={cn(
          'max-w-[85%] lg:max-w-[75%] p-4 rounded-xl',
          'border border-white/10 bg-black/40 backdrop-blur-xl',
          'shadow-[0_0_0_1px_rgba(225,6,0,0.08)]',
          'border-l-2 border-l-primary'
        )}
      >
        <div className="flex items-center gap-2 mb-2">
          <User className="w-4 h-4 text-primary" />
          <span className="text-xs font-medium text-muted-foreground">You</span>
        </div>
        <div className="text-sm text-foreground whitespace-pre-wrap">{message.content}</div>
        {message.created_at && (
          <div className="text-[10px] text-muted-foreground/70 mt-2">
            {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function AIMessage({
  message,
  onViewCode,
  onPin,
  onRun,
  isCommandMode = false,
  className,
}) {
  const [expandedSections, setExpandedSections] = useState({});
  const [codeModal, setCodeModal] = useState(null);
  const [copied, setCopied] = useState(false);

  const sections = parseContentSections(message.content);

  const toggleSection = (i) => {
    setExpandedSections((prev) => ({ ...prev, [i]: !prev[i] }));
  };

  const handleCopy = async (code) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn('flex justify-start', isCommandMode && 'opacity-90', className)}
      >
        <div
          className={cn(
            'max-w-[90%] lg:max-w-[85%] w-full',
            'rounded-xl overflow-hidden',
            'border border-white/10 bg-black/40 backdrop-blur-xl',
            'shadow-[0_0_0_1px_rgba(225,6,0,0.1)]',
            isCommandMode && 'border-primary/40 font-mono text-sm'
          )}
        >
          {/* AI Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-primary/20 flex items-center justify-center">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
              </div>
              <span className="text-xs font-semibold text-primary">
                {isCommandMode ? 'Terminal' : 'ML Mentor'}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => onPin?.(message)}
                className="p-1.5 rounded hover:bg-white/5 text-muted-foreground hover:text-foreground"
                title="Pin to workspace"
              >
                <Pin className="w-3.5 h-3.5" />
              </button>
              {onRun && (
                <button
                  type="button"
                  onClick={() => onRun?.(message)}
                  className="p-1.5 rounded hover:bg-primary/10 text-muted-foreground hover:text-primary"
                  title="Run in playground"
                >
                  <Play className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Content sections */}
          <div className="p-4 space-y-3">
            {sections.map((sec, i) => {
              const meta = SECTION_LABELS[sec.type] || { icon: null, label: null, className: '' };
              const isCode = sec.type === 'code';
              const isLong = sec.body.length > 200;
              const expanded = expandedSections[i] ?? !isLong;

              return (
                <div key={i} className="space-y-1.5">
                  {meta.label && (
                    <div
                      className={cn(
                        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border',
                        meta.className
                      )}
                    >
                      {sec.type === 'concept' && <Sparkles className="w-3 h-3" />}
                      {sec.type === 'code' && <Code2 className="w-3 h-3" />}
                      {meta.label}
                    </div>
                  )}
                  {isCode ? (
                    <div className="relative group">
                      <pre
                        className={cn(
                          'p-3 rounded-lg bg-black/50 border border-white/5 font-mono text-xs overflow-x-auto',
                          !expanded && 'max-h-24 overflow-hidden'
                        )}
                      >
                        <code>{sec.body}</code>
                      </pre>
                      <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          type="button"
                          onClick={() => handleCopy(sec.body)}
                          className="p-1.5 rounded bg-white/10 hover:bg-primary/20 text-muted-foreground hover:text-primary"
                        >
                          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                        </button>
                        <button
                          type="button"
                          onClick={() => setCodeModal(sec.body)}
                          className="p-1.5 rounded bg-white/10 hover:bg-primary/20 text-muted-foreground hover:text-primary"
                        >
                          <Code2 className="w-3 h-3" />
                        </button>
                      </div>
                      {isLong && (
                        <button
                          type="button"
                          onClick={() => toggleSection(i)}
                          className="flex items-center gap-1 mt-1 text-xs text-muted-foreground hover:text-primary"
                        >
                          {expanded ? (
                            <><ChevronUp className="w-3 h-3" /> Collapse</>
                          ) : (
                            <><ChevronDown className="w-3 h-3" /> Expand</>
                          )}
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="text-sm text-foreground whitespace-pre-wrap">
                      {expanded ? sec.body : `${sec.body.slice(0, 200)}...`}
                      {isLong && (
                        <button
                          type="button"
                          onClick={() => toggleSection(i)}
                          className="ml-1 text-primary text-xs"
                        >
                          {expanded ? ' less' : ' more'}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {message.created_at && (
            <div className="px-4 pb-2 text-[10px] text-muted-foreground/70">
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
        </div>
      </motion.div>

      {/* Code modal */}
      <AnimatePresence>
        {codeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
            onClick={() => setCodeModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="relative max-w-2xl w-full rounded-xl border border-primary/30 bg-background p-4 shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-3">
                <span className="text-sm font-medium text-primary">Code</span>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => handleCopy(codeModal)}
                    className="p-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary text-xs"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => setCodeModal(null)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <pre className="p-4 rounded-lg bg-black/50 overflow-auto max-h-[60vh] font-mono text-xs">
                <code>{codeModal}</code>
              </pre>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default function ChatMessage({ message, onPin, onRun, isCommandMode }) {
  const isAssistant = message.role === 'assistant';
  if (isAssistant) {
    return (
      <AIMessage
        message={message}
        onPin={onPin}
        onRun={onRun}
        isCommandMode={isCommandMode}
      />
    );
  }
  return <UserMessage message={message} />;
}
