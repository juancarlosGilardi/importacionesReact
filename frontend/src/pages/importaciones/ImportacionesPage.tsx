import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, MoreHorizontal, Pencil, Trash2, Eye } from "lucide-react";
import type { Importacion } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { STATUS_COLORS, STATUS_LABELS, VIA_TRANSPORTE_COLORS, IMPORTACION_ESTADOS } from "@/lib/constants";
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

interface ImportacionesResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

const VIA_LABELS: Record<string, string> = {
  maritimo: "Marítimo",
  aereo: "Aéreo",
  terrestre: "Terrestre",
  multimodal: "Multimodal",
};

export default function ImportacionesPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [estado, setEstado] = useState("");
  const [page, setPage] = useState(1);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const perPage = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["importaciones", page, search, estado],
    queryFn: () =>
      api
        .get<ImportacionesResponse>("/api/importaciones", {
          params: {
            page,
            per_page: perPage,
            search: search || undefined,
            estado: estado || undefined,
          },
        })
        .then((r) => r.data),
  });

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 0;

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/importaciones/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["importaciones"] });
      setDeleteId(null);
    },
  });

  const handleDelete = () => {
    if (deleteId) {
      deleteMutation.mutate(deleteId);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Importaciones</h1>
        <Button render={<Link to="/importaciones/nueva" />}>
          <Plus className="h-4 w-4" />
          Nueva Importación
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por número o descripción..."
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
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los estados</SelectItem>
            {IMPORTACION_ESTADOS.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
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
              <TableHead>Número</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Vía</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">FOB Total</TableHead>
              <TableHead className="text-right">Gastos Total</TableHead>
              <TableHead className="text-right">Costo Total</TableHead>
              <TableHead>Fecha Embarque</TableHead>
              <TableHead className="w-12" />
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
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                  No se encontraron importaciones
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((imp) => (
                <TableRow key={imp.id}>
                  <TableCell className="font-mono text-xs font-medium">
                    {imp.numero_importacion}
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate">
                    {imp.descripcion}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={VIA_TRANSPORTE_COLORS[imp.via_transporte] || ""}
                    >
                      {VIA_LABELS[imp.via_transporte] || imp.via_transporte}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={STATUS_COLORS[imp.estado] || ""}
                    >
                      {STATUS_LABELS[imp.estado] || imp.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {formatCurrency(imp.total_fob_importacion)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {formatCurrency(imp.total_gastos_importacion)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {formatCurrency(imp.total_costo_importacion)}
                  </TableCell>
                  <TableCell className="text-xs">
                    {imp.fecha_embarque ? formatDate(imp.fecha_embarque) : "-"}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button variant="ghost" size="icon-sm" />
                        }
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          render={
                            <Link to={`/importaciones/${imp.id}`} />
                          }
                        >
                          <Eye className="h-4 w-4" />
                          Ver Detalle
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          render={
                            <Link to={`/importaciones/${imp.id}/editar`} />
                          }
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setDeleteId(imp.id)}
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
            Mostrando {data.items.length} de {data.total} importaciones
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
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar eliminación</DialogTitle>
            <DialogDescription>
              ¿Está seguro de que desea eliminar esta importación? Esta acción no se
              puede deshacer.
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
