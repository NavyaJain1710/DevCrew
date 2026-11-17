import clsx from 'clsx';

const STATUS_CONFIG: Record<string, { label: string; className: string; dot?: string }> = {
  CREATED:             { label: 'Created',          className: 'badge-gray' },
  ANALYZING:           { label: 'Analyzing',         className: 'badge-blue',   dot: 'bg-accent-blue animate-pulse' },
  ARCHITECTING:        { label: 'Architecting',      className: 'badge-blue',   dot: 'bg-accent-blue animate-pulse' },
  IMPLEMENTING:        { label: 'Implementing',      className: 'badge-blue',   dot: 'bg-accent-blue animate-pulse' },
  TESTING:             { label: 'Testing',           className: 'badge-yellow', dot: 'bg-accent-yellow animate-pulse' },
  FIXING:              { label: 'Fixing',            className: 'badge-yellow', dot: 'bg-accent-yellow animate-pulse' },
  SECURITY_SCANNING:   { label: 'Security Scan',     className: 'badge-purple', dot: 'bg-accent-purple animate-pulse' },
  REVIEWING:           { label: 'Reviewing',         className: 'badge-blue',   dot: 'bg-accent-blue animate-pulse' },
  DOCUMENTING:         { label: 'Documenting',       className: 'badge-blue',   dot: 'bg-accent-blue animate-pulse' },
  COMPLETED:           { label: 'Completed',         className: 'badge-green' },
  FAILED:              { label: 'Failed',            className: 'badge-red' },
  PAUSED:              { label: 'Paused',            className: 'badge-gray' },
  WAITING_FOR_APPROVAL:{ label: 'Needs Approval',    className: 'badge-yellow', dot: 'bg-accent-yellow animate-pulse' },
};

export function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] ?? { label: status, className: 'badge-gray' };
  return (
    <span className={clsx(cfg.className)}>
      {cfg.dot && <span className={clsx('w-1.5 h-1.5 rounded-full', cfg.dot)} />}
      {cfg.label}
    </span>
  );
}
