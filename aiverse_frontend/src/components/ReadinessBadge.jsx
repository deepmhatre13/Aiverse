const READINESS_STYLES = {
  ready: {
    bg: 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400',
    dot: 'bg-emerald-400',
    label: 'Ready for you',
  },
  stretch: {
    bg: 'bg-amber-500/15 border-amber-500/40 text-amber-400',
    dot: 'bg-amber-400',
    label: 'Stretch goal',
  },
  prerequisite: {
    bg: 'bg-red-500/15 border-red-500/40 text-red-400',
    dot: 'bg-red-400',
    label: 'Build prerequisites first',
  },
};

export default function ReadinessBadge({ readiness, label, reason, compact = false }) {
  if (!readiness) return null;

  const style = READINESS_STYLES[readiness] || READINESS_STYLES.prerequisite;
  const displayLabel = label || style.label;

  return (
    <span
      className={`inline-flex items-center gap-1.5 border rounded-full font-medium ${style.bg} ${
        compact ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'
      }`}
      title={reason || displayLabel}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
      {displayLabel}
    </span>
  );
}
