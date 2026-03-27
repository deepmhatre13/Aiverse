import { useState, useEffect, useRef, useCallback, forwardRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send, Plus, MessageSquare, XCircle, RefreshCw,
  Copy, Check, User, Sparkles, ArrowDown, Brain, Menu, X,
} from 'lucide-react';
import Layout from '../components/Layout';
import { Button } from '../components/ui/button';
import { mentorAPI } from '../api/mentor';
import { toast } from 'sonner';

// ─── Constants ───────────────────────────────────────────────────────────────

const MAX_POLLS = 300;
const POLL_INTERVAL_MS = 1000;

const SUGGESTION_PROMPTS = [
  'Explain gradient descent intuitively',
  'What is overfitting and how to prevent it?',
  'Compare Random Forest vs XGBoost',
  'Explain backpropagation step by step',
  'What is cross-validation?',
  'How does dropout regularization work?',
];

// ─── AI Thinking Loader ─────────────────────────────────────────────────────

function AIThinkingLoader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3 }}
      className="flex items-start gap-3"
    >
      <div className="relative shrink-0">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-red-500/20 to-red-600/20 border border-red-500/30 flex items-center justify-center">
          <Brain className="w-4 h-4 text-red-400" />
        </div>
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-red-500/40"
          animate={{ scale: [1, 1.4, 1], opacity: [0.6, 0, 0.6] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        />
      </div>
      <div className="relative">
        <div className="px-5 py-3.5 rounded-2xl rounded-tl-md bg-card dark:bg-zinc-900/80 border border-border dark:border-border/50 backdrop-blur-sm">
          <div className="flex items-center gap-1.5">
            {[0, 1, 2].map((i) => (
              <motion.span
                key={i}
                className="w-2 h-2 rounded-full bg-red-400/70"
                animate={{ y: [0, -6, 0], opacity: [0.4, 1, 0.4], scale: [0.8, 1.1, 0.8] }}
                transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2, ease: 'easeInOut' }}
              />
            ))}
            <motion.span
              className="ml-2 text-xs text-muted-foreground font-mono"
              animate={{ opacity: [0.4, 0.8, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              thinking…
            </motion.span>
          </div>
        </div>
        <motion.div
          className="absolute bottom-0 left-0 right-0 h-[1px] rounded-full overflow-hidden"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(225,6,0,0.4), transparent)' }}
          animate={{ x: ['-100%', '100%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
        />
      </div>
    </motion.div>
  );
}

// ─── Copy Button ─────────────────────────────────────────────────────────────

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard unavailable */ }
  };
  return (
    <button onClick={handleCopy} className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground hover:text-foreground/80" title="Copy">
      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
    </button>
  );
}

// ─── Markdown Renderer ───────────────────────────────────────────────────────

function renderMarkdown(content) {
  if (!content) return <span className="text-muted-foreground">(empty)</span>;

  const lines = content.split('\n');
  const elements = [];
  let codeBlock = null;
  let listItems = [];

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`ul-${elements.length}`} className="space-y-1.5 my-2.5 ml-1">
          {listItems.map((li, i) => (
            <li key={i} className="flex gap-2 text-[13.5px] leading-relaxed text-foreground/80">
              <span className="text-muted-foreground/70 mt-0.5 shrink-0">•</span>
              <span>{renderInline(li)}</span>
            </li>
          ))}
        </ul>
      );
      listItems = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.trimStart().startsWith('```')) {
      if (codeBlock === null) {
        flushList();
        codeBlock = { lang: line.trim().slice(3).trim(), lines: [] };
      } else {
        elements.push(
          <div key={`code-${elements.length}`} className="my-3 rounded-lg overflow-hidden border border-border/50 bg-card dark:bg-[#0c0c0c]">
            <div className="flex items-center justify-between px-3 py-1.5 bg-muted/70 dark:bg-zinc-800/70 border-b border-border/30">
              <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">{codeBlock.lang || 'code'}</span>
              <CopyButton text={codeBlock.lines.join('\n')} />
            </div>
            <pre className="p-3 overflow-x-auto text-[13px] leading-relaxed font-mono text-foreground/80">
              <code>{codeBlock.lines.join('\n')}</code>
            </pre>
          </div>
        );
        codeBlock = null;
      }
      continue;
    }
    if (codeBlock !== null) { codeBlock.lines.push(line); continue; }

    if (line.startsWith('#### ')) { flushList(); elements.push(<h5 key={`h4-${i}`} className="text-[13.5px] font-semibold text-foreground/90 mt-4 mb-1.5">{renderInline(line.slice(5))}</h5>); continue; }
    if (line.startsWith('### '))  { flushList(); elements.push(<h4 key={`h3-${i}`} className="text-sm font-bold text-foreground mt-5 mb-2">{renderInline(line.slice(4))}</h4>); continue; }
    if (line.startsWith('## '))   { flushList(); elements.push(<h3 key={`h2-${i}`} className="text-[15px] font-bold text-foreground mt-5 mb-2">{renderInline(line.slice(3))}</h3>); continue; }
    if (line.startsWith('# '))    { flushList(); elements.push(<h2 key={`h1-${i}`} className="text-base font-bold text-foreground mt-4 mb-2">{renderInline(line.slice(2))}</h2>); continue; }

    const numMatch = line.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) { listItems.push(numMatch[2]); continue; }
    if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) { listItems.push(line.slice(2)); continue; }

    flushList();
    if (line.trim() === '') { elements.push(<div key={`br-${i}`} className="h-2" />); continue; }
    elements.push(<p key={`p-${i}`} className="text-[13.5px] leading-[1.7] text-foreground/80 my-0.5">{renderInline(line)}</p>);
  }
  flushList();
  if (codeBlock !== null) {
    elements.push(<pre key="code-unclosed" className="p-3 my-3 rounded-lg bg-card dark:bg-[#0c0c0c] border border-border/50 overflow-x-auto text-[13px] font-mono text-foreground/80"><code>{codeBlock.lines.join('\n')}</code></pre>);
  }
  return elements;
}

function renderInline(text) {
  if (!text) return text;
  const parts = [];
  const regex = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)/g;
  let lastIdx = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) parts.push(text.slice(lastIdx, match.index));
    if (match[1]) parts.push(<code key={match.index} className="px-1.5 py-0.5 rounded bg-muted dark:bg-zinc-800 text-primary text-xs font-mono border border-border/30">{match[1].slice(1, -1)}</code>);
    else if (match[2]) parts.push(<strong key={match.index} className="font-semibold text-foreground">{match[2].slice(2, -2)}</strong>);
    else if (match[3]) parts.push(<em key={match.index} className="italic text-muted-foreground">{match[3].slice(1, -1)}</em>);
    lastIdx = match.index + match[0].length;
  }
  if (lastIdx < text.length) parts.push(text.slice(lastIdx));
  return parts.length > 0 ? parts : text;
}

// ─── Message Bubble ──────────────────────────────────────────────────────────

const MessageBubble = forwardRef(function MessageBubble({ message }, ref) {
  const isUser = message.role === 'user';
  const isError = message.role === 'error';

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.25, ease: [0.22, 0.61, 0.36, 1] }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* Assistant / Error avatar — left side */}
      {!isUser && (
        <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5 ${
          isError
            ? 'bg-red-900/30 border border-red-500/30'
            : 'bg-gradient-to-br from-red-500/20 to-red-600/15 border border-red-500/25'
        }`}>
          {isError ? <XCircle className="w-4 h-4 text-red-400" /> : <Brain className="w-4 h-4 text-red-400" />}
        </div>
      )}

      {/* Bubble */}
      <div className={`min-w-0 ${isUser ? 'max-w-[65%]' : isError ? 'max-w-[75%]' : 'max-w-[75%]'}`}>
        <div className={`px-4 py-3 rounded-2xl ${
          isUser
            ? 'rounded-br-md bg-primary/5 dark:bg-zinc-800 border border-primary/10 dark:border-border/50 text-foreground'
            : isError
            ? 'rounded-bl-md bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-300'
            : 'rounded-bl-md bg-card dark:bg-zinc-900/80 border border-border dark:border-border/40 backdrop-blur-sm'
        }`}>
          {isUser ? (
            <p className="text-[13.5px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="min-w-0 overflow-hidden">{renderMarkdown(message.content)}</div>
          )}
        </div>

        <div className={`flex items-center gap-2 mt-1 px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {message.created_at && (
            <span className="text-[10px] text-muted-foreground/70 font-mono">
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          {isError && message.onRetry && (
            <button onClick={message.onRetry} className="flex items-center gap-1 text-[10px] text-red-400 hover:text-red-300 transition-colors">
              <RefreshCw className="w-3 h-3" /> Retry
            </button>
          )}
        </div>
      </div>

      {/* User avatar — right side */}
      {isUser && (
        <div className="shrink-0 w-8 h-8 rounded-full bg-muted dark:bg-zinc-800 border border-border dark:border-border/50 flex items-center justify-center mt-0.5">
          <User className="w-4 h-4 text-muted-foreground" />
        </div>
      )}
    </motion.div>
  );
});

// ─── Empty State ─────────────────────────────────────────────────────────────

function EmptyChat({ onSuggestionClick }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="flex flex-col items-center justify-center h-full px-6"
    >
      <div className="relative mb-8">
        <motion.div
          className="w-20 h-20 rounded-full bg-gradient-to-br from-red-500/15 via-red-600/10 to-transparent border border-red-500/15 flex items-center justify-center"
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
        >
          <Brain className="w-9 h-9 text-red-400/80" />
        </motion.div>
        <motion.div
          className="absolute inset-0 rounded-full border border-red-500/10"
          animate={{ scale: [1, 1.5], opacity: [0.4, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeOut' }}
        />
        <motion.div
          className="absolute inset-0 rounded-full border border-red-600/10"
          animate={{ scale: [1, 1.8], opacity: [0.3, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeOut', delay: 0.5 }}
        />
      </div>

      <h2 className="text-xl font-semibold text-foreground mb-2 tracking-tight">ML Mentor</h2>
      <p className="text-sm text-muted-foreground text-center max-w-sm mb-8 leading-relaxed">
        Ask anything about machine learning, deep learning, data science, or your learning journey.
      </p>

      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {SUGGESTION_PROMPTS.map((prompt, i) => (
          <motion.button
            key={prompt}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.06 }}
            onClick={() => onSuggestionClick(prompt)}
            className="px-3 py-1.5 text-xs text-muted-foreground bg-secondary dark:bg-zinc-900/60 hover:bg-muted dark:hover:bg-zinc-800/80 border border-border dark:border-border hover:border-primary/30 rounded-lg transition-all hover:text-foreground/90"
          >
            {prompt}
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// ─── Sidebar Session Item ────────────────────────────────────────────────────

function SessionItem({ session, isActive, onClick }) {
  const msgCount = session.messages?.length || 0;
  const firstUserMsg = session.messages?.find(m => m.role === 'user');
  const preview = firstUserMsg?.content?.slice(0, 50) || '';
  const dateStr = new Date(session.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' });

  return (
    <button
      onClick={onClick}
      className={`group w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 ${
        isActive
          ? 'bg-red-500/10 border border-red-500/20'
          : 'hover:bg-muted/60 dark:hover:bg-zinc-800/60 border border-transparent hover:border-border/40'
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-red-400' : 'text-muted-foreground/70 group-hover:text-muted-foreground'}`} />
        <span className={`text-xs font-medium truncate flex-1 ${isActive ? 'text-red-300' : 'text-muted-foreground group-hover:text-foreground/90'}`}>
          {preview || dateStr}
        </span>
        {msgCount > 0 && (
          <span className="text-[10px] text-muted-foreground/70 font-mono shrink-0">{msgCount}</span>
        )}
      </div>
      {preview && (
        <p className="text-[10px] text-muted-foreground/70 truncate mt-0.5 pl-[1.375rem]">{dateStr}</p>
      )}
    </button>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function Mentor() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const pollingIntervalRef = useRef(null);
  const pollCountRef = useRef(0);
  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // ── Auto-scroll ──

  const scrollToBottom = useCallback((behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);

  useEffect(() => {
    if (messages.length > 0) scrollToBottom();
  }, [messages, isPolling, scrollToBottom]);

  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    setShowScrollBtn(el.scrollHeight - el.scrollTop - el.clientHeight > 120);
  }, []);

  // ── Auto-resize textarea ──

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) { ta.style.height = 'auto'; ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`; }
  }, [inputValue]);

  // ── Focus textarea on session change ──

  useEffect(() => {
    if (!loadingMessages && !isPolling) textareaRef.current?.focus();
  }, [activeSessionId, loadingMessages, isPolling]);

  // ── Load sessions ──

  useEffect(() => {
    (async () => {
      try {
        setLoadingSessions(true);
        const res = await mentorAPI.listSessions();
        setSessions(res.data || []);
        if (res.data?.length > 0) setActiveSessionId(res.data[0].id);
      } catch (err) {
        console.error('[Mentor] Failed to load sessions:', err);
        toast.error('Failed to load chat sessions');
      } finally {
        setLoadingSessions(false);
      }
    })();
  }, []);

  // ── Load messages on session change ──

  useEffect(() => {
    if (pollingIntervalRef.current) { clearInterval(pollingIntervalRef.current); pollingIntervalRef.current = null; }
    setIsPolling(false);
    pollCountRef.current = 0;
    if (!activeSessionId) { setMessages([]); return; }

    (async () => {
      try {
        setLoadingMessages(true);
        const res = await mentorAPI.getMessages(activeSessionId);
        setMessages(res.data || []);
      } catch (err) {
        console.error('[Mentor] Failed to load messages:', err);
        toast.error('Failed to load conversation');
      } finally {
        setLoadingMessages(false);
      }
    })();
  }, [activeSessionId]);

  // ── Cleanup on unmount ──

  useEffect(() => () => {
    if (pollingIntervalRef.current) { clearInterval(pollingIntervalRef.current); pollingIntervalRef.current = null; }
  }, []);

  // ── Create session ──

  const createNewSession = async () => {
    try {
      const res = await mentorAPI.createSession();
      setSessions(prev => [res.data, ...prev]);
      setActiveSessionId(res.data.id);
      setMessages([]);
      setSidebarOpen(false);
      toast.success('New chat started');
    } catch {
      toast.error('Failed to create new chat');
    }
  };

  // ── Polling ──

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) { clearInterval(pollingIntervalRef.current); pollingIntervalRef.current = null; }
    setIsPolling(false);
    pollCountRef.current = 0;
  }, []);

  const startPollingTask = useCallback((taskId) => {
    pollCountRef.current = 0;
    setIsPolling(true);

    const poll = async () => {
      try {
        const res = await mentorAPI.checkTaskStatus(taskId);
        if (res.data.status === 'completed') {
          stopPolling();
          try {
            const msgRes = await mentorAPI.getMessages(activeSessionId);
            setMessages(msgRes.data || []);
          } catch { toast.error('Got response but failed to load it'); }
        } else if (res.data.status === 'error') {
          stopPolling();
          setMessages(prev => [...prev, { id: `err-${Date.now()}`, role: 'error', content: 'The AI service encountered an error. Please try again.', created_at: new Date().toISOString() }]);
        } else {
          pollCountRef.current += 1;
          if (pollCountRef.current > MAX_POLLS) { stopPolling(); toast.error('Request timed out'); }
        }
      } catch {
        stopPolling();
        setMessages(prev => [...prev, { id: `err-${Date.now()}`, role: 'error', content: 'Lost connection while waiting for response.', created_at: new Date().toISOString() }]);
      }
    };

    poll();
    pollingIntervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
  }, [activeSessionId, stopPolling]);

  // ── Send message ──

  const handleSendMessage = useCallback(async (overrideText) => {
    const question = (overrideText || inputValue).trim();
    if (!question || isPolling) return;

    if (!activeSessionId) {
      try {
        const res = await mentorAPI.createSession();
        setSessions(prev => [res.data, ...prev]);
        setActiveSessionId(res.data.id);
        setTimeout(() => handleSendMessage(question), 100);
        return;
      } catch { toast.error('Failed to create chat session'); return; }
    }

    const optimisticId = `tmp-${Date.now()}`;
    setMessages(prev => [...prev, { id: optimisticId, role: 'user', content: question, created_at: new Date().toISOString() }]);
    setInputValue('');

    try {
      const res = await mentorAPI.askQuestion(activeSessionId, question);
      const taskId = res.data?.task_id;
      if (!taskId) throw new Error('No task_id');
      startPollingTask(taskId);
    } catch (err) {
      console.error('[Mentor] Send failed:', err);
      setMessages(prev => prev.filter(m => m.id !== optimisticId));
      const status = err.response?.status;
      const errContent = status === 429
        ? 'Rate limited — please wait a moment before sending.'
        : status === 503
        ? 'AI service unavailable. Ensure Redis and Celery are running.'
        : err.response?.data?.error || 'Failed to send message. Please try again.';

      if (status === 429) { toast.error(errContent); return; }

      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`, role: 'error', content: errContent,
        created_at: new Date().toISOString(),
        onRetry: () => handleSendMessage(question),
      }]);
    }
  }, [inputValue, isPolling, activeSessionId, startPollingTask]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); }
  }, [handleSendMessage]);

  // ── Loading state ──

  if (loadingSessions) {
    return (
      <Layout showFooter={false}>
        <div className="h-[calc(100vh-4rem)] flex items-center justify-center bg-background">
          <motion.div className="flex flex-col items-center gap-4" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <motion.div
              className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center"
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Brain className="w-6 h-6 text-red-400" />
            </motion.div>
            <span className="text-sm text-muted-foreground font-mono">Loading mentor…</span>
          </motion.div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout showFooter={false}>
      <div className="h-[calc(100vh-4rem)] flex bg-background relative">

        {/* ── Mobile sidebar toggle ── */}
        <button
          onClick={() => setSidebarOpen(v => !v)}
          className="lg:hidden fixed top-[4.5rem] left-3 z-30 p-2 rounded-lg bg-card dark:bg-zinc-900 border border-border text-muted-foreground hover:text-foreground"
        >
          {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>

        {/* ── Sidebar ── */}
        <aside className={`
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
          fixed lg:relative z-20 inset-y-0 left-0 top-16 lg:top-0
          w-[280px] lg:w-[280px] border-r border-border/50 bg-card
          flex flex-col shrink-0 transition-transform duration-200
        `}>
          <div className="p-3 border-b border-border/50">
            <Button
              onClick={createNewSession}
              className="w-full gap-2 bg-secondary hover:bg-muted text-foreground border border-border hover:border-border h-9 text-xs font-medium"
              variant="ghost"
            >
              <Plus className="w-3.5 h-3.5" />
              New Chat
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {sessions.length === 0 ? (
              <div className="p-6 text-center">
                <MessageSquare className="w-5 h-5 text-muted-foreground/50 mx-auto mb-2" />
                <p className="text-[11px] text-muted-foreground/70">No conversations yet</p>
              </div>
            ) : sessions.map((s) => (
              <SessionItem key={s.id} session={s} isActive={activeSessionId === s.id} onClick={() => { setActiveSessionId(s.id); setSidebarOpen(false); }} />
            ))}
          </div>
        </aside>

        {/* ── Mobile sidebar backdrop ── */}
        {sidebarOpen && <div className="fixed inset-0 z-10 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />}

        {/* ── Main Chat Area ── */}
        <main className="flex-1 flex flex-col min-w-0 relative">

          {/* Messages scroll area */}
          <div ref={scrollContainerRef} onScroll={handleScroll} className="flex-1 overflow-y-auto">
            {loadingMessages ? (
              <div className="flex items-center justify-center h-full">
                <motion.div className="flex items-center gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <motion.div
                    className="w-8 h-8 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                  >
                    <Sparkles className="w-4 h-4 text-red-400" />
                  </motion.div>
                  <span className="text-sm text-muted-foreground font-mono">Loading…</span>
                </motion.div>
              </div>
            ) : messages.length === 0 && !isPolling ? (
              <EmptyChat onSuggestionClick={(prompt) => handleSendMessage(prompt)} />
            ) : (
              <div className="w-full max-w-[900px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
                <AnimatePresence initial={false}>
                  {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                  ))}
                </AnimatePresence>

                <AnimatePresence>
                  {isPolling && <AIThinkingLoader />}
                </AnimatePresence>

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Scroll-to-bottom FAB */}
          <AnimatePresence>
            {showScrollBtn && (
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                onClick={() => scrollToBottom()}
                className="absolute bottom-28 left-1/2 -translate-x-1/2 p-2 rounded-full bg-card dark:bg-zinc-800 border border-border shadow-lg hover:bg-muted transition-colors z-10"
              >
                <ArrowDown className="w-4 h-4 text-muted-foreground" />
              </motion.button>
            )}
          </AnimatePresence>

          {/* ── Input Area ── */}
          <div className="border-t border-border/50 bg-card/95 backdrop-blur-sm">
            <div className="w-full max-w-[900px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className={`relative rounded-xl border transition-all duration-200 ${
                isPolling
                  ? 'border-border bg-secondary/50 dark:bg-zinc-900/50'
                  : 'border-border dark:border-border/40 bg-secondary dark:bg-zinc-900/70 focus-within:border-primary/30 focus-within:shadow-[0_0_24px_rgba(225,6,0,0.06)]'
              }`}>
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isPolling ? 'Waiting for response…' : 'Ask anything about ML…'}
                  disabled={isPolling}
                  rows={1}
                  className="w-full px-4 py-3 pr-14 bg-transparent resize-none outline-none text-sm text-foreground placeholder:text-muted-foreground min-h-[44px] max-h-[160px] disabled:opacity-50"
                />
                <button
                  onClick={() => handleSendMessage()}
                  disabled={isPolling || !inputValue.trim()}
                  className="absolute right-2 bottom-2 p-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[10px] text-muted-foreground/50 mt-1.5 text-center font-mono">
                Enter to send · Shift+Enter for new line
              </p>
            </div>
          </div>
        </main>
      </div>
    </Layout>
  );
}
