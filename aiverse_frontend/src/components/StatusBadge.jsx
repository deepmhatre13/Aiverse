import { forwardRef } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';

const STATUS_MAP = {
  success: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500',
    border: 'border-emerald-500/30',
    icon: CheckCircle,
    label: 'Success',
  },
  accepted: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500',
    border: 'border-emerald-500/30',
    icon: CheckCircle,
    label: 'Accepted',
  },
  completed: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    border: 'border-emerald-500/30',
    icon: CheckCircle,
    label: 'Completed',
  },
  passed: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500',
    border: 'border-emerald-500/30',
    icon: CheckCircle,
    label: 'Passed',
  },
  error: {
    bg: 'bg-red-500/10',
    text: 'text-red-500',
    border: 'border-red-500/30',
    icon: XCircle,
    label: 'Error',
  },
  failed: {
    bg: 'bg-red-500/10',
    text: 'text-red-500',
    border: 'border-red-500/30',
    icon: XCircle,
    label: 'Failed',
  },
  rejected: {
    bg: 'bg-orange-500/10',
    text: 'text-orange-500',
    border: 'border-orange-500/30',
    icon: XCircle,
    label: 'Rejected',
  },
  warning: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    border: 'border-amber-500/30',
    icon: AlertTriangle,
    label: 'Warning',
  },
  pending: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    border: 'border-amber-500/30',
    icon: AlertTriangle,
    label: 'Pending',
  },
  info: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-500',
    border: 'border-blue-500/30',
    icon: Info,
    label: 'Info',
  },
  training: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    icon: Info,
    label: 'Training',
  },
};

const StatusBadge = forwardRef(function StatusBadge(
  { status, label, showIcon = true, size = 'sm', className = '' },
  ref
) {
  const config = STATUS_MAP[status?.toLowerCase()] || STATUS_MAP.info;
  const Icon = config.icon;
  const displayLabel = label || config.label;

  const sizeClasses = size === 'xs'
    ? 'px-2 py-0.5 text-[10px] gap-1'
    : size === 'sm'
    ? 'px-2.5 py-1 text-xs gap-1.5'
    : 'px-3 py-1.5 text-sm gap-2';

  const iconSize = size === 'xs' ? 'w-3 h-3' : size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';

  return (
    <span
      ref={ref}
      className={`inline-flex items-center font-medium rounded-md border ${config.bg} ${config.text} ${config.border} ${sizeClasses} ${className}`}
    >
      {showIcon && <Icon className={iconSize} />}
      {displayLabel}
    </span>
  );
});

export default StatusBadge;
export { STATUS_MAP };
