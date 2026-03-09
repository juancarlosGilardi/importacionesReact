import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Warehouse,
  ArrowLeftRight,
  BarChart3,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import type {
  ReporteAlmacenOcupacion,
  ReporteAlmacenMesMov,
  ReporteAlmacenTopProducto,
  ReporteAlmacenComparativo,
  Almacen,
} from "@/lib/types";
import { MESES_NOMBRES } from "@/lib/constants";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
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

// --- Tab 1: Ocupacion ---
function OcupacionTab() {
  const { data: items, isLoading } = useQuery({
    queryKey: ["reporte-almacen-ocupacion"],
    queryFn: () =>
      api.get<ReporteAlmacenOcupacion[]>("/api/reportes/almacen/ocupacion").then((r) => r.data),
  });

  const totalValor = items?.reduce((s, a) => s + Number(a.valor_total), 0) || 0;
  const totalUnidades = items?.reduce((s, a) => s + Number(a.total_unidades), 0) || 0;
  const totalProductos = items?.reduce((s, a) => s + Number(a.total_productos), 0) || 0;
  const maxValor = items?.length ? Math.max(...items.map((a) => Number(a.valor_total)), 1) : 1;

  return (
    <div className="space-y-4">
      {items && items.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Almacenes Activos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{items.length}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total Productos</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{totalProductos}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Total Unidades</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">{totalUnidades.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card size="sm">
            <CardHeader>
              <CardTitle className="text-xs text-muted-foreground">Valor Total</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-bold">{formatCurrency(totalValor)}</p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Almacen</TableHead>
              <TableHead>Responsable</TableHead>
              <TableHead className="text-right">Productos</TableHead>
              <TableHead className="text-right">Unidades</TableHead>
              <TableHead className="text-right">Valor</TableHead>
              <TableHead className="text-right w-[160px]">% del Total</TableHead>
              <TableHead className="text-right">Mov. 30d</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !items || items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                  No hay almacenes
                </TableCell>
              </TableRow>
            ) : (
              items.map((a) => (
                <TableRow key={a.almacen_id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">{a.almacen_codigo}</Badge>
                      <span className="text-sm font-medium">{a.almacen_nombre}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {a.responsable || "-"}
                  </TableCell>
                  <TableCell className="text-right text-xs">{a.total_productos}</TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Number(a.total_unidades).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs font-semibold">
                    {formatCurrency(a.valor_total)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="h-2 w-20 rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{
                            width: `${(Number(a.valor_total) / maxValor) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="min-w-[36px] text-right font-mono text-xs">
                        {(a.porcentaje_valor || 0).toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant="secondary" className="text-xs">
                      {a.movimientos_30d}
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

// --- Tab 2: Movimientos por Almacen ---
function MovimientosAlmacenTab() {
  const [almacenId, setAlmacenId] = useState("");
  const [meses, setMeses] = useState("6");

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes-rep-mov"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes", { params: { status: "activo" } }).then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["reporte-almacen-movimientos", almacenId, meses],
    queryFn: () =>
      api
        .get<{
          resumen_mensual: ReporteAlmacenMesMov[];
          top_productos: ReporteAlmacenTopProducto[];
        }>("/api/reportes/almacen/movimientos", {
          params: {
            almacen_id: almacenId && almacenId !== "all" ? almacenId : undefined,
            meses,
          },
        })
        .then((r) => r.data),
  });

  const resumenMensual = data?.resumen_mensual || [];
  const topProductos = data?.top_productos || [];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-4">
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
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Periodo</label>
          <Select value={meses} onValueChange={setMeses}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3">Ultimos 3 meses</SelectItem>
              <SelectItem value="6">Ultimos 6 meses</SelectItem>
              <SelectItem value="12">Ultimo anio</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Resumen mensual */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Resumen Mensual</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Mes</TableHead>
                <TableHead className="text-right">Ingresos</TableHead>
                <TableHead className="text-right">Salidas</TableHead>
                <TableHead className="text-right">Val. Ingresos</TableHead>
                <TableHead className="text-right">Val. Salidas</TableHead>
                <TableHead className="text-right">Balance</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : resumenMensual.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-6 text-center text-muted-foreground">
                    Sin movimientos
                  </TableCell>
                </TableRow>
              ) : (
                resumenMensual.map((r) => (
                  <TableRow key={`${r.anio}-${r.mes}`}>
                    <TableCell className="text-xs font-medium">
                      {MESES_NOMBRES[r.mes - 1]} {r.anio}
                    </TableCell>
                    <TableCell className="text-right text-xs text-green-600">
                      {r.ingresos_count}
                    </TableCell>
                    <TableCell className="text-right text-xs text-red-600">
                      {r.salidas_count}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(r.valor_ingresos)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(r.valor_salidas)}
                    </TableCell>
                    <TableCell className="text-right">
                      <span
                        className={`inline-flex items-center gap-1 font-mono text-xs font-semibold ${
                          r.balance >= 0 ? "text-green-600" : "text-red-600"
                        }`}
                      >
                        {r.balance >= 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {formatCurrency(Math.abs(r.balance))}
                      </span>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Top productos movidos */}
        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold">Top Productos Mas Movidos</h3>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Producto</TableHead>
                <TableHead className="text-right">Ingresos</TableHead>
                <TableHead className="text-right">Salidas</TableHead>
                <TableHead className="text-right">Mov.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : topProductos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="py-6 text-center text-muted-foreground">
                    Sin datos
                  </TableCell>
                </TableRow>
              ) : (
                topProductos.map((p) => (
                  <TableRow key={p.producto_id}>
                    <TableCell>
                      <p className="text-xs font-medium">{p.sku}</p>
                      <p className="text-xs text-muted-foreground truncate max-w-[180px]">
                        {p.producto_nombre}
                      </p>
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-green-600">
                      {Number(p.cantidad_ingresada).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-red-600">
                      {Number(p.cantidad_salida).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="secondary" className="text-xs">
                        {p.total_movimientos}
                      </Badge>
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

// --- Tab 3: Comparativo ---
function ComparativoTab() {
  const { data: items, isLoading } = useQuery({
    queryKey: ["reporte-almacen-comparativo"],
    queryFn: () =>
      api.get<ReporteAlmacenComparativo[]>("/api/reportes/almacen/comparativo").then((r) => r.data),
  });

  const maxValor = items?.length
    ? Math.max(...items.map((a) => Number(a.valor_inventario)), 1)
    : 1;

  return (
    <div className="space-y-4">
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Almacen</TableHead>
              <TableHead className="text-right">Productos</TableHead>
              <TableHead className="text-right">Unidades</TableHead>
              <TableHead className="text-right w-[200px]">Valor Inventario</TableHead>
              <TableHead className="text-right">Ingresos 30d</TableHead>
              <TableHead className="text-right">Salidas 30d</TableHead>
              <TableHead className="text-right">Alertas</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !items || items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                  No hay almacenes
                </TableCell>
              </TableRow>
            ) : (
              items.map((a) => (
                <TableRow key={a.almacen_id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">{a.almacen_codigo}</Badge>
                      <span className="text-sm font-medium">{a.almacen_nombre}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-xs">{a.productos_distintos}</TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {Number(a.total_unidades).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="h-2 w-24 rounded-full bg-muted">
                        <div
                          className="h-2 rounded-full bg-blue-500"
                          style={{
                            width: `${(Number(a.valor_inventario) / maxValor) * 100}%`,
                          }}
                        />
                      </div>
                      <span className="min-w-[80px] text-right font-mono text-xs font-semibold">
                        {formatCurrency(a.valor_inventario)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-green-600">
                    {formatCurrency(a.ingresos_30d)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-red-600">
                    {formatCurrency(a.salidas_30d)}
                  </TableCell>
                  <TableCell className="text-right">
                    {(a.alertas_stock || 0) > 0 ? (
                      <Badge variant="secondary" className="bg-amber-100 text-amber-700">
                        {a.alertas_stock}
                      </Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">0</span>
                    )}
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
export default function ReportesAlmacenPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Warehouse className="h-7 w-7 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold">Reportes de Almacen</h1>
          <p className="text-sm text-muted-foreground">
            Ocupacion, movimientos y comparativo entre almacenes
          </p>
        </div>
      </div>

      <Tabs defaultValue="ocupacion">
        <TabsList>
          <TabsTrigger value="ocupacion">Ocupacion</TabsTrigger>
          <TabsTrigger value="movimientos">Movimientos</TabsTrigger>
          <TabsTrigger value="comparativo">Comparativo</TabsTrigger>
        </TabsList>

        <TabsContent value="ocupacion">
          <OcupacionTab />
        </TabsContent>
        <TabsContent value="movimientos">
          <MovimientosAlmacenTab />
        </TabsContent>
        <TabsContent value="comparativo">
          <ComparativoTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
