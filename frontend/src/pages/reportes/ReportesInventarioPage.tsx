import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  PieChart,
  Search,
  Calendar,
  TrendingDown,
  TrendingUp,
  Package,
  Boxes,
  DollarSign,
  Warehouse,
} from "lucide-react";
import type {
  ReporteInventarioResumen,
  ReporteTopProducto,
  ReporteFamilia,
  ReporteMovimientosResumen,
  ReporteMovimientoDetalle,
  ReporteRotacion,
  Almacen,
} from "@/lib/types";
import { ROTACION_COLORS, ROTACION_LABELS, MESES_NOMBRES } from "@/lib/constants";
import { TIPO_MOVIMIENTO_COLORS, TIPO_MOVIMIENTO_LABELS } from "@/lib/constants";
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
function ResumenTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["reporte-inventario-resumen"],
    queryFn: () =>
      api
        .get<{
          resumen: ReporteInventarioResumen;
          top_productos: ReporteTopProducto[];
          por_familia: ReporteFamilia[];
        }>("/api/reportes/inventario/resumen")
        .then((r) => r.data),
  });

  const resumen = data?.resumen;
  const topProductos = data?.top_productos || [];
  const porFamilia = data?.por_familia || [];
  const maxValorFamilia = porFamilia.length
    ? Math.max(...porFamilia.map((f) => f.valor_total), 1)
    : 1;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      {resumen && (
        <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Productos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.total_productos}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Con Stock
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">
                {resumen.productos_con_stock}
              </p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Sin Stock
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-red-600">
                {resumen.productos_sin_stock}
              </p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Almacenes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.almacenes_con_stock}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Total Unidades
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {Number(resumen.total_unidades).toLocaleString()}
              </p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">
                Valor Inventario
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">
                {formatCurrency(resumen.valor_total_inventario)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Top 10 productos por valor */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Top 10 Productos por Valor</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead className="text-right">Stock</TableHead>
                <TableHead className="text-right">Valor</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 3 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : topProductos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="py-6 text-center text-muted-foreground">
                    Sin datos
                  </TableCell>
                </TableRow>
              ) : (
                topProductos.map((p, idx) => (
                  <TableRow key={p.producto_id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                          {idx + 1}
                        </span>
                        <div>
                          <p className="text-xs font-medium">{p.sku}</p>
                          <p className="text-xs text-muted-foreground truncate max-w-[180px]">
                            {p.producto_nombre}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {Number(p.stock_total).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(p.valor_total)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Distribucion por familia */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Distribucion por Categoria</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Categoria</TableHead>
                <TableHead className="text-right">Productos</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead className="text-right w-[140px]">%</TableHead>
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
              ) : porFamilia.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-6 text-center text-muted-foreground">
                    Sin datos
                  </TableCell>
                </TableRow>
              ) : (
                porFamilia.map((f) => (
                  <TableRow key={f.categoria_id}>
                    <TableCell className="text-xs font-medium">
                      {f.categoria_nombre}
                    </TableCell>
                    <TableCell className="text-right text-xs">
                      {f.total_productos}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(f.valor_total)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-2 w-16 rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-blue-500"
                            style={{
                              width: `${(f.valor_total / maxValorFamilia) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="min-w-[36px] text-right font-mono text-xs">
                          {(f.porcentaje || 0).toFixed(1)}%
                        </span>
                      </div>
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

// --- Tab 2: Movimientos ---
function MovimientosTab() {
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [almacenId, setAlmacenId] = useState("");
  const [queryParams, setQueryParams] = useState<Record<string, string> | null>(null);

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes-rep"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes", { params: { status: "activo" } }).then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["reporte-inventario-movimientos", queryParams],
    queryFn: () =>
      api
        .get<{
          resumen: ReporteMovimientosResumen;
          movimientos: ReporteMovimientoDetalle[];
        }>("/api/reportes/inventario/movimientos", {
          params: {
            fecha_desde: queryParams!.fecha_desde || undefined,
            fecha_hasta: queryParams!.fecha_hasta || undefined,
            almacen_id: queryParams!.almacen_id || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!queryParams,
  });

  const handleGenerar = () => {
    setQueryParams({
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
      almacen_id: almacenId === "all" ? "" : almacenId,
    });
  };

  const resumen = data?.resumen;
  const movimientos = data?.movimientos || [];

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
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Almacen</label>
          <Select value={almacenId} onValueChange={setAlmacenId}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Todos" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {almacenes?.map((a) => (
                <SelectItem key={a.id} value={String(a.id)}>
                  {a.codigo} - {a.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <Button onClick={handleGenerar}>
          <Search className="h-4 w-4" /> Generar
        </Button>
      </div>

      {!queryParams && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20 p-12">
          <Calendar className="mb-3 h-10 w-10 text-muted-foreground/40" />
          <p className="text-muted-foreground">
            Seleccione un rango de fechas y presione "Generar"
          </p>
        </div>
      )}

      {queryParams && resumen && (
        <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total Mov.</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.total_movimientos}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Ingresos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">{resumen.total_ingresos}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Salidas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-red-600">{resumen.total_salidas}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Valor Ingresos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold">{formatCurrency(resumen.valor_ingresos)}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Valor Salidas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg font-bold">{formatCurrency(resumen.valor_salidas)}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Balance Neto</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-lg font-bold ${resumen.balance_neto >= 0 ? "text-green-600" : "text-red-600"}`}>
                {formatCurrency(resumen.balance_neto)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {queryParams && (
        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Numero</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Fecha</TableHead>
                <TableHead>Almacen</TableHead>
                <TableHead>Concepto</TableHead>
                <TableHead className="text-right">Items</TableHead>
                <TableHead className="text-right">Valor</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 7 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : movimientos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                    No se encontraron movimientos
                  </TableCell>
                </TableRow>
              ) : (
                movimientos.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-mono text-xs font-medium">
                      {m.numero_movimiento}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={TIPO_MOVIMIENTO_COLORS[m.tipo_movimiento] || ""}
                      >
                        {TIPO_MOVIMIENTO_LABELS[m.tipo_movimiento] || m.tipo_movimiento}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs">{formatDate(m.fecha_movimiento)}</TableCell>
                    <TableCell className="text-xs">
                      {m.almacen_codigo && (
                        <Badge variant="secondary" className="text-xs">
                          {m.almacen_codigo}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs">{m.concepto || "-"}</TableCell>
                    <TableCell className="text-right text-xs">{m.total_productos}</TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(m.valor_total)}
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

// --- Tab 3: Rotacion ---
function RotacionTab() {
  const [meses, setMeses] = useState("12");

  const { data: items, isLoading } = useQuery({
    queryKey: ["reporte-inventario-rotacion", meses],
    queryFn: () =>
      api
        .get<ReporteRotacion[]>("/api/reportes/inventario/rotacion", {
          params: { meses },
        })
        .then((r) => r.data),
  });

  const resumen = items
    ? {
        total: items.length,
        alta: items.filter((i) => i.clasificacion === "alta").length,
        media: items.filter((i) => i.clasificacion === "media").length,
        lenta: items.filter((i) => i.clasificacion === "lenta").length,
        sin_movimiento: items.filter((i) => i.clasificacion === "sin_movimiento").length,
        sin_stock: items.filter((i) => i.clasificacion === "sin_stock").length,
      }
    : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Periodo</label>
          <Select value={meses} onValueChange={setMeses}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">Ultimos 3 meses</SelectItem>
              <SelectItem value="6">Ultimos 6 meses</SelectItem>
              <SelectItem value="12">Ultimo anio</SelectItem>
              <SelectItem value="24">Ultimos 2 anios</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {resumen && (
        <div className="grid grid-cols-3 gap-4 md:grid-cols-6">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{resumen.total}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-green-600">Alta</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-green-600">{resumen.alta}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-blue-600">Media</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-blue-600">{resumen.media}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-amber-600">Lenta</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-amber-600">{resumen.lenta}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-red-600">Sin Mov.</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-red-600">{resumen.sin_movimiento}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-gray-500">Sin Stock</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-gray-500">{resumen.sin_stock}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Producto</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead className="text-right">Stock</TableHead>
              <TableHead className="text-right">Salidas</TableHead>
              <TableHead className="text-right">Ingresos</TableHead>
              <TableHead className="text-right">Indice</TableHead>
              <TableHead>Clasificacion</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
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
                  Sin datos
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.producto_id}>
                  <TableCell className="font-mono text-xs font-medium">{item.sku}</TableCell>
                  <TableCell className="text-xs max-w-[200px] truncate">
                    {item.producto_nombre}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {item.categoria_nombre}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Number(item.stock_actual).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Number(item.total_salidas).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Number(item.total_ingresos).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs font-semibold">
                    {item.indice_rotacion.toFixed(2)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={ROTACION_COLORS[item.clasificacion] || ""}
                    >
                      {ROTACION_LABELS[item.clasificacion] || item.clasificacion}
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
export default function ReportesInventarioPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <PieChart className="h-7 w-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Reportes de Inventario</h1>
          <p className="text-sm text-muted-foreground">
            Analisis de stock, movimientos y rotacion
          </p>
        </div>
      </div>

      <Tabs defaultValue="resumen">
        <TabsList>
          <TabsTrigger value="resumen">Resumen</TabsTrigger>
          <TabsTrigger value="movimientos">Movimientos</TabsTrigger>
          <TabsTrigger value="rotacion">Rotacion</TabsTrigger>
        </TabsList>

        <TabsContent value="resumen">
          <ResumenTab />
        </TabsContent>
        <TabsContent value="movimientos">
          <MovimientosTab />
        </TabsContent>
        <TabsContent value="rotacion">
          <RotacionTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
