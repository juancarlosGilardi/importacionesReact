import { useQuery } from "@tanstack/react-query";
import {
  Ship,
  DollarSign,
  TrendingUp,
  Package,
  Clock,
} from "lucide-react";
import type { DashboardMetrics, PipelineItem } from "@/lib/types";
import { STATUS_LABELS, STATUS_BORDER_COLORS, PIPELINE_STATUSES } from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

function MetricCard({
  title,
  value,
  icon: Icon,
  isCurrency = false,
}: {
  title: string;
  value: number | undefined;
  icon: typeof Ship;
  isCurrency?: boolean;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <Icon className="h-4 w-4" />
        </div>
      </CardHeader>
      <CardContent>
        {value !== undefined ? (
          <p className="text-2xl font-bold">
            {isCurrency ? formatCurrency(value) : value.toLocaleString()}
          </p>
        ) : (
          <div className="h-8 w-32 animate-pulse rounded bg-muted" />
        )}
      </CardContent>
    </Card>
  );
}

function PipelineCard({ item }: { item: PipelineItem }) {
  return (
    <div className="rounded-lg border bg-white p-3 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-foreground">{item.numero}</p>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          {item.dias_transcurridos}d
        </div>
      </div>
      <p className="mt-1 truncate text-xs text-muted-foreground">
        {item.proveedor_nombre}
      </p>
      <p className="mt-2 text-sm font-medium text-foreground">
        {formatCurrency(item.total_fob)}
      </p>
    </div>
  );
}

function PipelineColumn({
  status,
  items,
}: {
  status: string;
  items: PipelineItem[];
}) {
  const borderColor = STATUS_BORDER_COLORS[status] || "border-t-gray-400";

  return (
    <div className="flex w-72 shrink-0 flex-col">
      <div
        className={`rounded-t-lg border-t-4 bg-muted/50 px-3 py-2 ${borderColor}`}
      >
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">
            {STATUS_LABELS[status] || status}
          </span>
          <Badge variant="secondary">{items.length}</Badge>
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2 rounded-b-lg border border-t-0 bg-muted/20 p-2">
        {items.length === 0 ? (
          <p className="py-4 text-center text-xs text-muted-foreground">
            Sin operaciones
          </p>
        ) : (
          items.map((item) => <PipelineCard key={item.id} item={item} />)
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: metrics } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () =>
      api.get<DashboardMetrics>("/api/dashboard/metricas").then((r) => r.data),
  });

  const { data: pipeline } = useQuery({
    queryKey: ["dashboard-pipeline"],
    queryFn: () =>
      api.get<PipelineItem[]>("/api/dashboard/pipeline").then((r) => r.data),
  });

  const groupedPipeline = PIPELINE_STATUSES.reduce(
    (acc, status) => {
      acc[status] = pipeline?.filter((item) => item.estado === status) || [];
      return acc;
    },
    {} as Record<string, PipelineItem[]>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Importaciones Activas"
          value={metrics?.importaciones_activas}
          icon={Ship}
        />
        <MetricCard
          title="FOB Mes Actual"
          value={metrics?.fob_mes_actual}
          icon={DollarSign}
          isCurrency
        />
        <MetricCard
          title="Costo Total Mes"
          value={metrics?.costo_total_mes}
          icon={TrendingUp}
          isCurrency
        />
        <MetricCard
          title="Total Productos"
          value={metrics?.total_productos}
          icon={Package}
        />
      </div>

      {/* Pipeline Kanban */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Pipeline de Operaciones</h2>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {PIPELINE_STATUSES.map((status) => (
            <PipelineColumn
              key={status}
              status={status}
              items={groupedPipeline[status] || []}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
