import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import type { Gasto, TipoGasto, Importacion } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { GASTO_STATUS_COLORS, GASTO_STATUS_LABELS, GASTO_ESTADOS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
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

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

export default function GastosPage() {
  const queryClient = useQueryClient();
  const [importacionId, setImportacionId] = useState("");
  const [tipoGasto, setTipoGasto] = useState("");
  const [estado, setEstado] = useState("");
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data: gastos, isLoading } = useQuery({
    queryKey: ["gastos", importacionId, tipoGasto, estado],
    queryFn: () =>
      api
        .get<Gasto[]>("/api/gastos", {
          params: {
            importacion_id: importacionId || undefined,
            tipo_gasto: tipoGasto || undefined,
            estado: estado || undefined,
          },
        })
        .then((r) => r.data),
  });

  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-list-filter"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const { data: tiposGasto } = useQuery({
    queryKey: ["tipos-gasto"],
    queryFn: () =>
      api.get<TipoGasto[]>("/api/catalogos/tipos-gasto").then((r) => r.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/gastos/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gastos"] });
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
        <h1 className="text-2xl font-bold">Gastos de Importación</h1>
        <Button render={<Link to="/gastos/nuevo" />}>
          <Plus className="h-4 w-4" />
          Nuevo Gasto
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <Select
          value={importacionId}
          onValueChange={(val) => setImportacionId(val === "__all__" ? "" : val ?? "")}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Todas las importaciones" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todas las importaciones</SelectItem>
            {importaciones?.items.map((imp) => (
              <SelectItem key={imp.id} value={String(imp.id)}>
                {imp.numero_importacion}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={tipoGasto}
          onValueChange={(val) => setTipoGasto(val === "__all__" ? "" : val ?? "")}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Todos los tipos" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los tipos</SelectItem>
            {tiposGasto?.map((t) => (
              <SelectItem key={t.codigo} value={t.codigo}>
                {t.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={estado}
          onValueChange={(val) => setEstado(val === "__all__" ? "" : val ?? "")}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los estados</SelectItem>
            {GASTO_ESTADOS.map((e) => (
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
              <TableHead>Tipo Gasto</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Importación</TableHead>
              <TableHead>Proveedor</TableHead>
              <TableHead className="text-right">Monto</TableHead>
              <TableHead>Moneda</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Fecha</TableHead>
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
            ) : !gastos || gastos.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="py-8 text-center text-muted-foreground">
                  No se encontraron gastos
                </TableCell>
              </TableRow>
            ) : (
              gastos.map((gasto) => (
                <TableRow key={gasto.id}>
                  <TableCell className="text-xs font-medium">
                    {gasto.tipo_gasto_nombre || gasto.tipo_gasto_codigo}
                  </TableCell>
                  <TableCell className="max-w-[180px] truncate text-xs">
                    {gasto.descripcion || "-"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {gasto.importacion_id || "-"}
                  </TableCell>
                  <TableCell className="text-xs">
                    {gasto.proveedor_nombre || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs">
                    {formatCurrency(gasto.monto)}
                  </TableCell>
                  <TableCell className="text-xs">
                    {gasto.moneda_codigo || "-"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={GASTO_STATUS_COLORS[gasto.estado] || ""}
                    >
                      {GASTO_STATUS_LABELS[gasto.estado] || gasto.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">
                    {gasto.fecha_gasto ? formatDate(gasto.fecha_gasto) : "-"}
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
                            <Link to={`/gastos/${gasto.id}/editar`} />
                          }
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          variant="destructive"
                          onClick={() => setDeleteId(gasto.id)}
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

      {/* Delete confirmation dialog */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar eliminación</DialogTitle>
            <DialogDescription>
              ¿Está seguro de que desea eliminar este gasto? Esta acción no se
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
