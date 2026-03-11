import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  Search,
  Calendar,
  Clock,
  AlertCircle,
  ShoppingCart,
} from "lucide-react";
import type {
  ReporteComprasResumen,
  ReporteComprasEstado,
  ReporteComprasMes,
  ReporteComprasProveedor,
  ReporteComprasPendiente,
} from "@/lib/types";
import {
  STATUS_COLORS,
  STATUS_LABELS,
  URGENCIA_COLORS,
  URGENCIA_LABELS,
  MESES_NOMBRES,
} from "@/lib/constants";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

// --- Tab 1: Resumen ---
function ResumenComprasTab() {
  const currentYear = new Date().getFullYear();
  const [anio, setAnio] = useState(String(currentYear));
  const years = Array.from({ length: 5 }, (_, i) => String(currentYear - i));

  const { data, isLoading } = useQuery({
    queryKey: ["reporte-compras-resumen", anio],
    queryFn: () =>
      api
        .get<{
          resumen: ReporteComprasResumen;
          por_estado: ReporteComprasEstado[];
          por_mes: ReporteComprasMes[];
        }>("/api/reportes/compras/resumen", { params: { anio } })
        .then((r) => r.data),
  });

  const resumen = data?.resumen;
  const porEstado = data?.por_estado || [];
  const porMes = data?.por_mes || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Anio</label>
          <Select value={anio} onValueChange={(val) => setAnio(val ?? "")}>
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={y}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {resumen && (
        <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total OCs</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.total_ordenes}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total FOB</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">{formatCurrency(resumen.total_fob)}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total Costo</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">{formatCurrency(resumen.total_costo)}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Prom. FOB/OC</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">{formatCurrency(resumen.promedio_fob)}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Proveedores</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.proveedores_distintos}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Dias Entrega Prom.</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {Math.round(resumen.dias_entrega_promedio)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Por estado */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Por Estado</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">FOB Total</TableHead>
                <TableHead className="text-right">Costo Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : porEstado.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-6 text-center text-muted-foreground">
                    Sin datos
                  </TableCell>
                </TableRow>
              ) : (
                porEstado.map((e) => (
                  <TableRow key={e.estado}>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={STATUS_COLORS[e.estado] || "bg-gray-100 text-gray-700"}
                      >
                        {STATUS_LABELS[e.estado] || e.estado}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary">{e.cantidad}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(e.total_fob)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(e.total_costo)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Por mes */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Por Mes</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mes</TableHead>
                <TableHead className="text-right">OCs</TableHead>
                <TableHead className="text-right">FOB Total</TableHead>
                <TableHead className="text-right">Costo Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : porMes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-6 text-center text-muted-foreground">
                    Sin datos
                  </TableCell>
                </TableRow>
              ) : (
                porMes.map((m) => (
                  <TableRow key={m.mes}>
                    <TableCell className="text-xs font-medium">
                      {MESES_NOMBRES[m.mes - 1] || `Mes ${m.mes}`}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary">{m.total_ordenes}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(m.total_fob)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(m.total_costo)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

// --- Tab 2: Por Proveedor ---
function PorProveedorTab() {
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [queryDates, setQueryDates] = useState<{
    fecha_desde: string;
    fecha_hasta: string;
  } | null>(null);

  const { data: items, isLoading } = useQuery({
    queryKey: ["reporte-compras-proveedor", queryDates],
    queryFn: () =>
      api
        .get<ReporteComprasProveedor[]>("/api/reportes/compras/por-proveedor", {
          params: {
            fecha_desde: queryDates!.fecha_desde || undefined,
            fecha_hasta: queryDates!.fecha_hasta || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!queryDates,
  });

  const handleGenerar = () => {
    setQueryDates({ fecha_desde: fechaDesde, fecha_hasta: fechaHasta });
  };

  const maxPorcentaje = items?.length
    ? Math.max(...items.map((r) => r.porcentaje_total || 0), 1)
    : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Desde</label>
          <Input type="date" value={fechaDesde} onChange={(e) => setFechaDesde(e.target.value)} />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Hasta</label>
          <Input type="date" value={fechaHasta} onChange={(e) => setFechaHasta(e.target.value)} />
        </div>
        <Button onClick={handleGenerar}>
          <Search className="h-4 w-4" /> Generar
        </Button>
      </div>

      {!queryDates && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20 p-12">
          <Calendar className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-muted-foreground">
            Seleccione un rango de fechas y presione "Generar"
          </p>
        </div>
      )}

      {queryDates && (
        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Proveedor</TableHead>
                <TableHead>Pais</TableHead>
                <TableHead className="text-right">OCs</TableHead>
                <TableHead className="text-right">Total FOB</TableHead>
                <TableHead className="text-right">Prom. FOB</TableHead>
                <TableHead className="text-right">Dias Entrega</TableHead>
                <TableHead className="text-right">Ultima OC</TableHead>
                <TableHead className="text-right w-[160px]">% Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 8 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !items || items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                    No se encontraron datos
                  </TableCell>
                </TableRow>
              ) : (
                items.map((p) => (
                  <TableRow key={p.proveedor_id}>
                    <TableCell>
                      <p className="text-xs font-medium">{p.proveedor_nombre}</p>
                      <p className="font-mono text-xs text-muted-foreground">{p.proveedor_ruc}</p>
                    </TableCell>
                    <TableCell className="text-xs">{p.pais}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary">{p.total_ordenes}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(p.total_fob)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(p.promedio_fob_orden)}
                    </TableCell>
                    <TableCell className="text-right text-xs">
                      {Math.round(p.dias_entrega_promedio)} dias
                    </TableCell>
                    <TableCell className="text-right text-xs">
                      {formatDate(p.ultima_orden)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-2 w-20 rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-blue-500"
                            style={{
                              width: `${((p.porcentaje_total || 0) / maxPorcentaje) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="min-w-[36px] text-right font-mono text-xs">
                          {(p.porcentaje_total || 0).toFixed(1)}%
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// --- Tab 3: Pendientes ---
function PendientesTab() {
  const { data: items, isLoading } = useQuery({
    queryKey: ["reporte-compras-pendientes"],
    queryFn: () =>
      api.get<ReporteComprasPendiente[]>("/api/reportes/compras/pendientes").then((r) => r.data),
  });

  const resumen = items
    ? {
        total: items.length,
        atrasadas: items.filter((i) => i.urgencia === "atrasada").length,
        proximas: items.filter((i) => i.urgencia === "proxima").length,
        en_plazo: items.filter((i) => i.urgencia === "en_plazo").length,
        valor_total: items.reduce((s, i) => s + Number(i.total_fob), 0),
      }
    : null;

  return (
    <div className="space-y-4">
      {resumen && (
        <div className="grid grid-cols-5 gap-4">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total Pendientes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.total}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-red-600">Atrasadas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-red-600">{resumen.atrasadas}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-amber-600">Proximas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-amber-600">{resumen.proximas}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-green-600">En Plazo</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">{resumen.en_plazo}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Valor FOB Total</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">{formatCurrency(resumen.valor_total)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>OC</TableHead>
              <TableHead>Proveedor</TableHead>
              <TableHead>Fecha Orden</TableHead>
              <TableHead>Llegada Est.</TableHead>
              <TableHead className="text-right">FOB</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Dias</TableHead>
              <TableHead>Urgencia</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !items || items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                  No hay ordenes pendientes
                </TableCell>
              </TableRow>
            ) : (
              items.map((oc) => (
                <TableRow
                  key={oc.id}
                  className={oc.urgencia === "atrasada" ? "bg-red-50/50" : ""}
                >
                  <TableCell className="font-mono text-xs font-medium">{oc.numero_oc}</TableCell>
                  <TableCell>
                    <p className="text-xs font-medium">{oc.proveedor_nombre}</p>
                  </TableCell>
                  <TableCell className="text-xs">{formatDate(oc.fecha_orden)}</TableCell>
                  <TableCell className="text-xs">
                    {oc.fecha_llegada_est ? formatDate(oc.fecha_llegada_est) : "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs font-semibold">
                    {oc.moneda} {formatCurrency(oc.total_fob)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={STATUS_COLORS[oc.estado] || "bg-gray-100 text-gray-700"}
                    >
                      {STATUS_LABELS[oc.estado] || oc.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="text-xs">
                      <span className="font-mono">{oc.dias_desde_orden}d</span>
                      {oc.dias_atraso > 0 && (
                        <span className="ml-1 text-red-600 font-medium">
                          (+{oc.dias_atraso})
                        </span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={URGENCIA_COLORS[oc.urgencia] || ""}
                    >
                      {URGENCIA_LABELS[oc.urgencia] || oc.urgencia}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// --- Main Page ---
export default function ReportesComprasPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <TrendingUp className="h-7 w-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Reportes de Compras</h1>
          <p className="text-sm text-muted-foreground">
            Resumen de ordenes, analisis por proveedor y pendientes
          </p>
        </div>
      </div>

      <Tabs defaultValue="resumen">
        <TabsList>
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
          <TabsTrigger value="proveedor">Por Proveedor</TabsTrigger>
          <TabsTrigger value="pendientes">Pendientes</TabsTrigger>
        </TabsList>

        <TabsContent value="resumen">
          <ResumenComprasTab />
        </TabsContent>
        <TabsContent value="proveedor">
          <PorProveedorTab />
        </TabsContent>
        <TabsContent value="pendientes">
          <PendientesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
