interface StatusBadgeProps {
  label: string;
  color: string;
}

export default function StatusBadge({ label, color }: StatusBadgeProps) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium text-white"
      style={{ backgroundColor: color }}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-white/40" />
      {label}
    </span>
  );
}
