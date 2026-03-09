import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, ChevronDown, Eye } from "lucide-react";
import type { Almacen, MovimientoAlmacen, PaginatedResponse } from "@/lib/types";
import {
  TIPO_MOVIMIENTO_COLORS,
  TIPO_MOVIMIENTO_LABELS,
  MOVIMIENTO_ESTADOS,
  MOVIMIENTO_STATUS_COLORS,
} from "@/lib/constants";
import { formatCurrency, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function MovimientosPage() {
  const [tipo, setTipo] = useState("");
  const [almacenId, setAlmacenId] = useState("");
  const [estado, setEstado] = useState("");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [page, setPage] = useState(1);

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes", { params: { status: "activo" } }).then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["movimientos", tipo, almacenId, estado, fechaDesde, fechaHasta, page],
    queryFn: () =>
      api
        .get<PaginatedResponse<MovimientoAlmacen>>("/api/inventario/movimientos", {
          params: {
            tipo: tipo || undefined,
            almacen_id: almacenId || undefined,
            estado: estado || undefined,
            fecha_desde: fechaDesde || undefined,
            fecha_hasta: fechaHasta || undefined,
            page,
            per_page: 20,
          },
        })
        .then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Movimientos de Almacen</h1>
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button />}>
            <Plus className="h-4 w-4" />
            Nuevo Movimiento
            <ChevronDown className="h-4 w-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem render={<Link to="/movimientos/nuevo?tipo=ingreso" />}>
              Ingreso
            </DropdownMenuItem>
            <DropdownMenuItem render={<Link to="/movimientos/nuevo?tipo=transferencia" />}>
              Transferencia
            </DropdownMenuItem>
            <DropdownMenuItem render={<Link to="/movimientos/nuevo?tipo=salida" />}>
              Salida
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="w-44">
          <Select
            value={tipo}
            onValueChange={(val) => { setTipo(val === "all" ? "" : val); setPage(1); }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los tipos</SelectItem>
              <SelectItem value="ingreso">Ingreso</SelectItem>
              <SelectItem value="transferencia">Transferencia</SelectItem>
              <SelectItem value="ajuste">Ajuste</SelectItem>
              <SelectItem value="salida">Salida</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="w-48">
          <Select
            value={almacenId}
            onValueChange={(val) => { setAlmacenId(val === "all" ? "" : val); setPage(1); }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Almacen" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los almacenes</SelectItem>
              {almacenes?.map((alm) => (
                <SelectItem key={alm.id} value={String(alm.id)}>
                  {alm.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="w-44">
          <Select
            value={estado}
            onValueChange={(val) => { setEstado(val === "all" ? "" : val); setPage(1); }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los estados</SelectItem>
              {MOVIMIENTO_ESTADOS.map((e) => (
                <SelectItem key={e.value} value={e.value}>
                  {e.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Input
            type="date"
            value={fechaDesde}
            onChange={(e) => { setFechaDesde(e.target.value); setPage(1); }}
            placeholder="Desde"
            className="w-40"
          />
        </div>

        <div>
          <Input
            type="date"
            value={fechaHasta}
            onChange={(e) => { setFechaHasta(e.target.value); setPage(1); }}
            placeholder="Hasta"
            className="w-40"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Numero</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Almacen</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead className="text-right">Total Productos</TableHead>
              <TableHead className="text-right">Valor Total</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-16">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !data || data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                  No se encontraron movimientos
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((mov) => (
                <TableRow key={mov.id}>
                  <TableCell className="font-mono text-xs">
                    {mov.numero_movimiento}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={TIPO_MOVIMIENTO_COLORS[mov.tipo_movimiento] || "bg-gray-100 text-gray-700"}
                    >
                      {TIPO_MOVIMIENTO_LABELS[mov.tipo_movimiento] || mov.tipo_movimiento}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {mov.almacen_nombre || "-"}
                    {mov.tipo_movimiento === "transferencia" && mov.almacen_destino_nombre && (
                      <span className="text-muted-foreground">
                        {" → "}{mov.almacen_destino_nombre}
                      </span>
                    )}
                  </TableCell>
                  <TableCell>{formatDate(mov.fecha_movimiento)}</TableCell>
                  <TableCell className="text-right font-mono">
                    {mov.total_productos}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(mov.valor_total)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={MOVIMIENTO_STATUS_COLORS[mov.estado] || "bg-gray-100 text-gray-700"}
                    >
                      {MOVIMIENTO_ESTADOS.find((e) => e.value === mov.estado)?.label || mov.estado}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      render={<Link to={`/movimientos/${mov.id}`} />}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Mostrando {data.items.length} de {data.total} movimientos
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= data.pages}
              onClick={() => setPage(page + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
