import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Search,
  Calendar,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import type {
  ReporteMensual,
  ReporteProveedor,
  ReporteProducto,
  Producto,
} from "@/lib/types";
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

interface ProductosResponse {
  items: Producto[];
  total: number;
}

const MESES_NOMBRES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

// --- Tab 1: Resumen Mensual ---
function ResumenMensualTab() {
  const currentYear = new Date().getFullYear();
  const [anio, setAnio] = useState(String(currentYear));

  const years = Array.from({ length: 5 }, (_, i) =>
    String(currentYear - i)
  );

  const { data: reporte, isLoading } = useQuery({
    queryKey: ["reporte-mensual", anio],
    queryFn: () =>
      api
        .get<ReporteMensual[]>("/api/dashboard/reporte-mensual", {
          params: { anio },
        })
        .then((r) => r.data),
  });

  const totals = reporte?.reduce(
    (acc, r) => ({
      importaciones: acc.importaciones + r.importaciones,
      total_fob: acc.total_fob + r.total_fob,
      total_gastos: acc.total_gastos + r.total_gastos,
      total_costo: acc.total_costo + r.total_costo,
    }),
    { importaciones: 0, total_fob: 0, total_gastos: 0, total_costo: 0 }
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Anio
          </label>
          <Select value={anio} onValueChange={(val) => setAnio(val ?? "")}>
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {years.map((y) => (
                <SelectItem key={y} value={y}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary cards */}
      {totals && (
        <div className="grid grid-cols-4 gap-4">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Importaciones
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{totals.importaciones}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Total FOB
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {formatCurrency(totals.total_fob)}
              </p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Total Gastos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {formatCurrency(totals.total_gastos)}
              </p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Costo Total
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {formatCurrency(totals.total_costo)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Mes</TableHead>
              <TableHead className="text-center">Importaciones</TableHead>
              <TableHead className="text-right">FOB Total</TableHead>
              <TableHead className="text-right">Gastos Total</TableHead>
              <TableHead className="text-right">Costo Total</TableHead>
              <TableHead className="text-right">Incremento %</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !reporte || reporte.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="py-8 text-center text-muted-foreground"
                >
                  No hay datos para el anio seleccionado
                </TableCell>
              </TableRow>
            ) : (
              reporte.map((r) => {
                const mesNombre =
                  r.mes_nombre || MESES_NOMBRES[r.mes - 1] || `Mes ${r.mes}`;
                const hasActivity = r.importaciones > 0;
                return (
                  <TableRow
                    key={r.mes}
                    className={hasActivity ? "" : "opacity-50"}
                  >
                    <TableCell className="font-medium">{mesNombre}</TableCell>
                    <TableCell className="text-center">
                      {r.importaciones > 0 ? (
                        <Badge variant="secondary">{r.importaciones}</Badge>
                      ) : (
                        <span className="text-xs text-muted-foreground">0</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {r.total_fob > 0 ? formatCurrency(r.total_fob) : "-"}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {r.total_gastos > 0
                        ? formatCurrency(r.total_gastos)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {r.total_costo > 0
                        ? formatCurrency(r.total_costo)
                        : "-"}
                    </TableCell>
                    <TableCell className="text-right">
                      {r.incremento_pct !== 0 ? (
                        <span
                          className={`inline-flex items-center gap-1 text-xs font-medium ${
                            r.incremento_pct > 0
                              ? "text-red-600"
                              : "text-green-600"
                          }`}
                        >
                          {r.incremento_pct > 0 ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {r.incremento_pct.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">-</span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
          {totals && reporte && reporte.length > 0 && (
            <TableFooter>
              <TableRow className="font-bold">
                <TableCell>TOTAL</TableCell>
                <TableCell className="text-center">
                  {totals.importaciones}
                </TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {formatCurrency(totals.total_fob)}
                </TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {formatCurrency(totals.total_gastos)}
                </TableCell>
                <TableCell className="text-right font-mono text-xs">
                  {formatCurrency(totals.total_costo)}
                </TableCell>
                <TableCell />
              </TableRow>
            </TableFooter>
          )}
        </Table>
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

  const { data: reporte, isLoading } = useQuery({
    queryKey: ["reporte-proveedores", queryDates],
    queryFn: () =>
      api
        .get<ReporteProveedor[]>("/api/dashboard/reporte-proveedores", {
          params: {
            fecha_desde: queryDates!.fecha_desde || undefined,
            fecha_hasta: queryDates!.fecha_hasta || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!queryDates,
  });

  const handleGenerar = () => {
    setQueryDates({
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
    });
  };

  const maxPorcentaje = reporte
    ? Math.max(...reporte.map((r) => r.porcentaje_total), 1)
    : 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Desde
          </label>
          <Input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Hasta
          </label>
          <Input
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
          />
        </div>
        <Button onClick={handleGenerar}>
          <Search className="h-4 w-4" />
          Generar
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
                <TableHead>RUC</TableHead>
                <TableHead className="text-center">OCs</TableHead>
                <TableHead className="text-right">Total FOB</TableHead>
                <TableHead className="text-right">Total Gastos</TableHead>
                <TableHead className="text-right">Costo Promedio</TableHead>
                <TableHead className="text-right w-[180px]">
                  % del Total
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !reporte || reporte.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={7}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No se encontraron datos para el periodo seleccionado
                  </TableCell>
                </TableRow>
              ) : (
                reporte.map((r) => (
                  <TableRow key={r.proveedor_id}>
                    <TableCell className="font-medium text-xs">
                      {r.proveedor_nombre}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {r.proveedor_ruc}
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge variant="secondary">{r.total_ocs}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(r.total_fob)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(r.total_gastos)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(r.costo_promedio)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-2 w-24 rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-blue-500 transition-all"
                            style={{
                              width: `${(r.porcentaje_total / maxPorcentaje) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="min-w-[40px] text-right font-mono text-xs">
                          {r.porcentaje_total.toFixed(1)}%
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

// --- Tab 3: Por Producto ---
function PorProductoTab() {
  const [productoId, setProductoId] = useState("");
  const [queryProductoId, setQueryProductoId] = useState("");

  const { data: productos } = useQuery({
    queryKey: ["productos-reporte"],
    queryFn: () =>
      api
        .get<ProductosResponse>("/api/productos", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const { data: reporte, isLoading } = useQuery({
    queryKey: ["reporte-producto", queryProductoId],
    queryFn: () =>
      api
        .get<ReporteProducto[]>("/api/dashboard/reporte-producto", {
          params: { producto_id: queryProductoId },
        })
        .then((r) => r.data),
    enabled: !!queryProductoId,
  });

  const handleConsultar = () => {
    if (!productoId) return;
    setQueryProductoId(productoId);
  };

  // Compute averages
  const averages = reporte?.length
    ? {
        cantidad:
          reporte.reduce((sum, r) => sum + r.cantidad, 0) / reporte.length,
        fob_unitario:
          reporte.reduce((sum, r) => sum + r.fob_unitario, 0) / reporte.length,
        landed_unitario:
          reporte.reduce((sum, r) => sum + r.landed_unitario, 0) /
          reporte.length,
        incremento_pct:
          reporte.reduce((sum, r) => sum + r.incremento_pct, 0) /
          reporte.length,
      }
    : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-[280px]">
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Producto
          </label>
          <Select value={productoId} onValueChange={(val) => setProductoId(val ?? "")}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Seleccionar producto" />
            </SelectTrigger>
            <SelectContent>
              {productos?.items.map((p) => (
                <SelectItem key={p.id} value={String(p.id)}>
                  {p.sku} - {p.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={handleConsultar} disabled={!productoId}>
          <Search className="h-4 w-4" />
          Consultar
        </Button>
      </div>

      {!queryProductoId && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20 p-12">
          <BarChart3 className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-muted-foreground">
            Seleccione un producto para ver su historial de costos
          </p>
        </div>
      )}

      {queryProductoId && (
        <>
          {/* Average costs summary */}
          {averages && reporte && reporte.length > 0 && (
            <div className="grid grid-cols-4 gap-4">
              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-xs text-muted-foreground">
                    Cant. Promedio
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xl font-bold">
                    {averages.cantidad.toFixed(0)}
                  </p>
                </CardContent>
              </Card>
              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-xs text-muted-foreground">
                    FOB Unit. Promedio
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xl font-bold">
                    {formatCurrency(averages.fob_unitario)}
                  </p>
                </CardContent>
              </Card>
              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-xs text-muted-foreground">
                    Landed Unit. Promedio
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xl font-bold">
                    {formatCurrency(averages.landed_unitario)}
                  </p>
                </CardContent>
              </Card>
              <Card size="sm">
                <CardHeader>
                  <CardTitle className="text-xs text-muted-foreground">
                    Incremento Promedio
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p
                    className={`text-xl font-bold ${
                      averages.incremento_pct > 0
                        ? "text-red-600"
                        : "text-green-600"
                    }`}
                  >
                    {averages.incremento_pct.toFixed(1)}%
                  </p>
                </CardContent>
              </Card>
            </div>
          )}

          <div className="rounded-lg border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>OC</TableHead>
                  <TableHead>Importacion</TableHead>
                  <TableHead className="text-right">Cantidad</TableHead>
                  <TableHead className="text-right">FOB Unit.</TableHead>
                  <TableHead className="text-right">Landed Unit.</TableHead>
                  <TableHead className="text-right">Incremento %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 7 }).map((_, j) => (
                        <TableCell key={j}>
                          <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !reporte || reporte.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No se encontraron datos para este producto
                    </TableCell>
                  </TableRow>
                ) : (
                  reporte.map((r, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="text-xs">
                        {formatDate(r.fecha)}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-medium">
                        {r.oc_numero}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {r.importacion_numero || "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {r.cantidad.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {formatCurrency(r.fob_unitario)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-semibold">
                        {formatCurrency(r.landed_unitario)}
                      </TableCell>
                      <TableCell className="text-right">
                        {r.incremento_pct !== 0 ? (
                          <span
                            className={`inline-flex items-center gap-1 text-xs font-medium ${
                              r.incremento_pct > 0
                                ? "text-red-600"
                                : "text-green-600"
                            }`}
                          >
                            {r.incremento_pct > 0 ? (
                              <TrendingUp className="h-3 w-3" />
                            ) : (
                              <TrendingDown className="h-3 w-3" />
                            )}
                            {r.incremento_pct.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            -
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}

// --- Main ReportesPage ---
export default function ReportesPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <BarChart3 className="h-7 w-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Reportes</h1>
          <p className="text-sm text-muted-foreground">
            Analisis y reportes de importaciones
          </p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="mensual">
        <TabsList>
          <TabsTrigger value="mensual">Resumen Mensual</TabsTrigger>
          <TabsTrigger value="proveedor">Por Proveedor</TabsTrigger>
          <TabsTrigger value="producto">Por Producto</TabsTrigger>
        </TabsList>

        <TabsContent value="mensual">
          <ResumenMensualTab />
        </TabsContent>

        <TabsContent value="proveedor">
          <PorProveedorTab />
        </TabsContent>

        <TabsContent value="producto">
          <PorProductoTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
