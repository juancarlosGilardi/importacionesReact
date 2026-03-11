import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, MoreHorizontal, Pencil, Trash2, Eye } from "lucide-react";
import type { OrdenCompra, Proveedor, PaginatedResponse } from "@/lib/types";
import { STATUS_COLORS, STATUS_LABELS } from "@/lib/constants";
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface OrdenesResponse {
  items: OrdenCompra[];
  total: number;
  page: number;
  per_page: number;
}

const ESTADO_OPTIONS = [
  { value: "borrador", label: "Borrador" },
  { value: "confirmada", label: "Confirmada" },
  { value: "en_transito", label: "En Tránsito" },
  { value: "en_aduana", label: "En Aduana" },
  { value: "completada", label: "Completada" },
  { value: "cancelada", label: "Cancelada" },
];

export default function OrdenesPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [estado, setEstado] = useState("");
  const [proveedorId, setProveedorId] = useState("");
  const [page, setPage] = useState(1);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const perPage = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["ordenes", page, search, estado, proveedorId],
    queryFn: () =>
      api
        .get<OrdenesResponse>("/api/ordenes", {
          params: {
            page,
            per_page: perPage,
            search: search || undefined,
            estado: estado || undefined,
            proveedor_id: proveedorId || undefined,
          },
        })
        .then((r) => r.data),
  });

  const { data: proveedores } = useQuery({
    queryKey: ["proveedores-list"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Proveedor>>("/api/proveedores", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/ordenes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ordenes"] });
      setDeleteId(null);
    },
  });

  const handleDelete = () => {
    if (deleteId) {
      deleteMutation.mutate(deleteId);
    }
  };

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Ordenes de Compra</h1>
        <Button render={<Link to="/ordenes/nueva" />}>
          <Plus className="h-4 w-4" />
          Nueva OC
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por numero o proveedor..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <Select
          value={estado}
          onValueChange={(val) => {
            setEstado(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los estados</SelectItem>
            {ESTADO_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={proveedorId}
          onValueChange={(val) => {
            setProveedorId(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Todos los proveedores" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los proveedores</SelectItem>
            {proveedores?.items.map((prov) => (
              <SelectItem key={prov.id} value={String(prov.id)}>
                {prov.razon_social}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Numero</TableHead>
              <TableHead>Proveedor</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>Moneda</TableHead>
              <TableHead className="text-right">Total FOB</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={7}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron ordenes de compra
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((oc) => (
                <TableRow
                  key={oc.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`/ordenes/${oc.id}`)}
                >
                  <TableCell className="font-mono text-sm font-medium">
                    {oc.numero || oc.numero_oc}
                  </TableCell>
                  <TableCell>{oc.proveedor_nombre || oc.proveedor?.razon_social || "-"}</TableCell>
                  <TableCell>{formatDate(oc.fecha_orden)}</TableCell>
                  <TableCell>{oc.moneda}</TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(oc.total_fob)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={STATUS_COLORS[oc.estado] || "bg-gray-100 text-gray-700"}
                    >
                      {STATUS_LABELS[oc.estado] || oc.estado}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button variant="ghost" size="icon-sm" />
                        }
                        onClick={(e) => e.stopPropagation()}
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          render={
                            <Link to={`/ordenes/${oc.id}`} />
                          }
                        >
                          <Eye className="h-4 w-4" />
                          Ver
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          render={
                            <Link to={`/ordenes/${oc.id}/editar`} />
                          }
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteId(oc.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                          Eliminar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Mostrando {data.items.length} de {data.total} ordenes
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
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={deleteId !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteId(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar eliminacion</DialogTitle>
            <DialogDescription>
              Esta seguro de que desea eliminar esta orden de compra? Esta accion
              no se puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? "Eliminando..." : "Eliminar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
