import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  AlertCircle,
  ShieldAlert,
  TrendingDown,
  DollarSign,
} from "lucide-react";
import type { AlertaStock, AlertasResumen, Almacen } from "@/lib/types";
import {
  ALERTA_NIVEL_COLORS,
  ALERTA_NIVEL_LABELS,
} from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function AlertasStockPage() {
  const [almacenId, setAlmacenId] = useState("");
  const [nivel, setNivel] = useState("");
  const [search, setSearch] = useState("");

  const { data: resumen } = useQuery({
    queryKey: ["alertas-resumen", almacenId],
    queryFn: () =>
      api
        .get<AlertasResumen>("/api/inventario/alertas/resumen", {
          params: { almacen_id: almacenId || undefined },
        })
        .then((r) => r.data),
  });

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data: alertas, isLoading } = useQuery({
    queryKey: ["alertas-stock", almacenId, nivel, search],
    queryFn: () =>
      api
        .get<AlertaStock[]>("/api/inventario/alertas", {
          params: {
            almacen_id: almacenId || undefined,
            nivel: nivel || undefined,
            search: search || undefined,
            page: 1,
            per_page: 200,
          },
        })
        .then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-6 w-6 text-amber-500" />
        <h1 className="text-2xl font-bold">Alertas de Stock</h1>
      </div>

      {/* Dashboard Cards */}
      {resumen && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <AlertTriangle className="h-8 w-8 text-amber-500" />
              <div>
                <p className="text-xs text-muted-foreground">Total Alertas</p>
                <p className="text-2xl font-bold">{resumen.total_alertas}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-red-200 bg-red-50">
            <CardContent className="flex items-center gap-3 p-4">
              <ShieldAlert className="h-8 w-8 text-red-600" />
              <div>
                <p className="text-xs text-red-600">Criticos</p>
                <p className="text-2xl font-bold text-red-700">
                  {resumen.alertas_criticas}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-amber-200 bg-amber-50">
            <CardContent className="flex items-center gap-3 p-4">
              <AlertCircle className="h-8 w-8 text-amber-600" />
              <div>
                <p className="text-xs text-amber-600">Stock Bajo</p>
                <p className="text-2xl font-bold text-amber-700">
                  {resumen.alertas_bajas}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-blue-200 bg-blue-50">
            <CardContent className="flex items-center gap-3 p-4">
              <DollarSign className="h-8 w-8 text-blue-600" />
              <div>
                <p className="text-xs text-blue-600">Valor Reposicion</p>
                <p className="text-lg font-bold text-blue-700">
                  {formatCurrency(resumen.valor_reposicion_estimado)}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={almacenId}
          onValueChange={(val) => setAlmacenId(val === "all" ? "" : val ?? "")}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Todos los almacenes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los almacenes</SelectItem>
            {almacenes?.map((alm) => (
              <SelectItem key={alm.id} value={String(alm.id)}>
                {alm.codigo} - {alm.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={nivel}
          onValueChange={(val) => setNivel(val === "all" ? "" : val ?? "")}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Todos los niveles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los niveles</SelectItem>
            <SelectItem value="critico">Critico</SelectItem>
            <SelectItem value="bajo">Bajo</SelectItem>
          </SelectContent>
        </Select>

        <Input
          placeholder="Buscar por SKU o nombre..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64"
        />
      </div>

      {/* Alerts Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-20">Nivel</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Producto</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead className="text-right">Stock Actual</TableHead>
              <TableHead className="text-right">Stock Min.</TableHead>
              <TableHead className="text-right">Pto. Reposicion</TableHead>
              <TableHead className="text-right">Reponer</TableHead>
              <TableHead className="text-right">Valor Stock</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !alertas || alertas.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={9}
                  className="py-12 text-center text-muted-foreground"
                >
                  <div className="flex flex-col items-center gap-2">
                    <AlertTriangle className="h-8 w-8 text-green-500" />
                    <p className="text-lg font-medium">Sin alertas</p>
                    <p className="text-sm">
                      Todos los productos tienen stock adecuado
                    </p>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              alertas.map((alerta) => (
                <TableRow
                  key={alerta.producto_id}
                  className={
                    alerta.nivel_alerta === "critico"
                      ? "bg-red-50/50"
                      : alerta.nivel_alerta === "bajo"
                        ? "bg-amber-50/50"
                        : ""
                  }
                >
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        ALERTA_NIVEL_COLORS[alerta.nivel_alerta] ||
                        "bg-gray-100 text-gray-700"
                      }
                    >
                      {alerta.nivel_alerta === "critico" && (
                        <ShieldAlert className="mr-1 h-3 w-3" />
                      )}
                      {ALERTA_NIVEL_LABELS[alerta.nivel_alerta] ||
                        alerta.nivel_alerta}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {alerta.sku}
                  </TableCell>
                  <TableCell className="font-medium">
                    {alerta.producto_nombre}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {alerta.categoria_nombre || "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <span
                      className={`font-mono font-semibold ${
                        alerta.nivel_alerta === "critico"
                          ? "text-red-700"
                          : alerta.nivel_alerta === "bajo"
                            ? "text-amber-700"
                            : ""
                      }`}
                    >
                      {Number(alerta.stock_actual).toLocaleString()}
                    </span>
                    {alerta.unidad_medida && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        {alerta.unidad_medida}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {Number(alerta.stock_minimo).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {Number(alerta.punto_reposicion).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="flex items-center justify-end gap-1 font-mono font-semibold text-blue-700">
                      <TrendingDown className="h-3 w-3" />
                      {Number(alerta.cantidad_reponer).toLocaleString()}
                    </span>
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(alerta.valor_stock)}
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
