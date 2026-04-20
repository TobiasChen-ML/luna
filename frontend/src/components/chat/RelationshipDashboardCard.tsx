import type { FC } from 'react';

interface RelationshipDashboardCardProps {
  stage: string;
  intimacy: number;
  trust: number;
  desire: number;
  dependency: number;
  gmNode: string;
}

function MetricRow({ label, value, color }: { label: string; value: number; color: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-zinc-300">
        <span>{label}</span>
        <span className="font-semibold text-white">{clamped}</span>
      </div>
      <div className="h-2 w-full rounded-full bg-zinc-800 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-300`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}

export const RelationshipDashboardCard: FC<RelationshipDashboardCardProps> = ({
  stage,
  intimacy,
  trust,
  desire,
  dependency,
  gmNode,
}) => {
  return (
    <div className="rounded-xl border border-white/10 bg-zinc-900/70 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-white">Relationship Dashboard</h4>
        <span className="text-[11px] uppercase tracking-wide text-zinc-400">{stage}</span>
      </div>
      <MetricRow label="Intimacy" value={intimacy} color="bg-pink-500" />
      <MetricRow label="Trust" value={trust} color="bg-emerald-500" />
      <MetricRow label="Desire" value={desire} color="bg-rose-500" />
      <MetricRow label="Dependency" value={dependency} color="bg-amber-500" />
      <div className="pt-1 text-[11px] text-zinc-400">
        GM Node: <span className="text-zinc-200">{gmNode}</span>
      </div>
    </div>
  );
};

