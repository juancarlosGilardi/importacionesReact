import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Eye, Search } from "lucide-react";
import type { Almacen, ValeUnificado, PaginatedResponse } from "@/lib/types";
import {
  VALE_ESTADOS,
  VALE_STATUS_COLORS,
  VALE_TIPO_COLORS,
  VALE_TIPO_LABELS,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function ListaValesPage() {
  const [tipo, setTipo] = useState("");
  const [almacenId, setAlmacenId] = useState("");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data, isLoading } = useQuery({
    queryKey: [
      "vales-unificado",
      tipo,
      almacenId,
      fechaDesde,
      fechaHasta,
      search,
      page,
    ],
    queryFn: () =>
      api
        .get<PaginatedResponse<ValeUnificado>>("/api/vales/unificado", {
          params: {
            tipo: tipo || undefined,
            almacen_id: almacenId || undefined,
            fecha_desde: fechaDesde || undefined,
            fecha_hasta: fechaHasta || undefined,
            search: search || undefined,
            page,
            per_page: 20,
          },
        })
        .then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Lista de Vales</h1>
        <div className="flex gap-2">
          <Button variant="outline" render={<Link to="/vales/ingreso" />}>
            Ver Ingresos
          </Button>
          <Button variant="outline" render={<Link to="/vales/salida" />}>
            Ver Salidas
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="w-44">
          <Select
            value={tipo}
            onValueChange={(val) => {
              setTipo(val === "all" ? "" : val);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Tipo" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los tipos</SelectItem>
              <SelectItem value="ingreso">Ingreso</SelectItem>
              <SelectItem value="salida">Salida</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="w-48">
          <Select
            value={almacenId}
            onValueChange={(val) => {
              setAlmacenId(val === "all" ? "" : val);
              setPage(1);
            }}
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

        <div>
          <Input
            type="date"
            value={fechaDesde}
            onChange={(e) => {
              setFechaDesde(e.target.value);
              setPage(1);
            }}
            className="w-40"
          />
        </div>

        <div>
          <Input
            type="date"
            value={fechaHasta}
            onChange={(e) => {
              setFechaHasta(e.target.value);
              setPage(1);
            }}
            className="w-40"
          />
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-56 pl-9"
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
              <TableHead>Concepto</TableHead>
              <TableHead>Prov. / Solicitante</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !data || data.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={9}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron vales
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((vale) => (
                <TableRow key={`${vale.tipo_movimiento}-${vale.id}`}>
                  <TableCell className="font-mono text-xs">
                    {vale.numero_movimiento}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        VALE_TIPO_COLORS[vale.tipo_movimiento] ||
                        "bg-gray-100 text-gray-700"
                      }
                    >
                      {VALE_TIPO_LABELS[vale.tipo_movimiento] ||
                        vale.tipo_movimiento}
                    </Badge>
                  </TableCell>
                  <TableCell>{vale.almacen_nombre || "-"}</TableCell>
                  <TableCell>{vale.concepto_nombre || "-"}</TableCell>
                  <TableCell>
                    {vale.proveedor_o_solicitante || "-"}
                  </TableCell>
                  <TableCell>
                    {formatDate(vale.fecha_movimiento)}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(vale.total)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        VALE_STATUS_COLORS[vale.estado] ||
                        "bg-gray-100 text-gray-700"
                      }
                    >
                      {VALE_ESTADOS.find((e) => e.value === vale.estado)
                        ?.label || vale.estado}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      render={
                        <Link
                          to={`/vales/${vale.tipo_movimiento}/${vale.id}`}
                        />
                      }
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
            Mostrando {data.items.length} de {data.total} vales
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
