import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, Eye, Search, ClipboardCheck } from "lucide-react";
import type { TomaInventario, Almacen, PaginatedResponse } from "@/lib/types";
import { TOMA_ESTADOS, TOMA_STATUS_COLORS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
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
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface CreateForm {
  almacen_id: string;
  responsable: string;
  fecha_inicio: string;
  notas: string;
}

const emptyForm: CreateForm = {
  almacen_id: "",
  responsable: "",
  fecha_inicio: new Date().toISOString().split("T")[0],
  notas: "",
};

export default function TomaInventarioPage() {
  const navigate = useNavigate();
  const [almacenId, setAlmacenId] = useState("");
  const [estado, setEstado] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>(emptyForm);
  const [createError, setCreateError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["tomas-inventario", almacenId, estado, search, page],
    queryFn: () =>
      api
        .get<PaginatedResponse<TomaInventario>>("/api/toma-inventario", {
          params: {
            almacen_id: almacenId || undefined,
            estado: estado || undefined,
            search: search || undefined,
            page,
            per_page: 20,
          },
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

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post("/api/toma-inventario", payload),
    onSuccess: (res) => {
      const created = res.data;
      setShowCreate(false);
      setForm(emptyForm);
      setCreateError("");
      navigate(`/inventario/toma/${created.id}`);
    },
    onError: (err: any) => {
      setCreateError(err.response?.data?.detail || "Error al crear toma");
    },
  });

  const handleCreate = () => {
    if (!form.almacen_id) {
      setCreateError("Seleccione un almacen");
      return;
    }
    if (!form.responsable.trim()) {
      setCreateError("El responsable es requerido");
      return;
    }
    setCreateError("");
    createMutation.mutate({
      almacen_id: Number(form.almacen_id),
      responsable: form.responsable,
      fecha_inicio: form.fecha_inicio,
      notas: form.notas || undefined,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClipboardCheck className="h-6 w-6 text-muted-foreground" />
          <h1 className="text-2xl font-bold">Toma de Inventario</h1>
        </div>
        <Button
          onClick={() => {
            setShowCreate(true);
            setForm(emptyForm);
            setCreateError("");
          }}
        >
          <Plus className="h-4 w-4" />
          Nueva Toma
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={almacenId}
          onValueChange={(val) => {
            setAlmacenId(val === "all" ? "" : val ?? "");
            setPage(1);
          }}
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
          value={estado}
          onValueChange={(val) => {
            setEstado(val === "all" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los estados</SelectItem>
            {TOMA_ESTADOS.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-64 pl-9"
          />
        </div>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Numero</TableHead>
              <TableHead>Almacen</TableHead>
              <TableHead>Fecha Inicio</TableHead>
              <TableHead>Responsable</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Progreso</TableHead>
              <TableHead className="text-right">Diferencias</TableHead>
              <TableHead className="w-16" />
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
            ) : !data?.items || data.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron tomas de inventario
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((toma) => {
                const progreso =
                  toma.total_items && toma.total_items > 0
                    ? Math.round(
                        ((toma.items_contados || 0) / toma.total_items) * 100
                      )
                    : 0;
                return (
                  <TableRow key={toma.id}>
                    <TableCell>
                      <Link
                        to={`/inventario/toma/${toma.id}`}
                        className="font-mono text-sm font-medium text-primary hover:underline"
                      >
                        {toma.numero}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="text-xs">
                        {toma.almacen_codigo}
                      </Badge>
                      <span className="ml-2 text-sm">{toma.almacen_nombre}</span>
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(toma.fecha_inicio)}
                    </TableCell>
                    <TableCell className="font-medium">
                      {toma.responsable}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={
                          TOMA_STATUS_COLORS[toma.estado] ||
                          "bg-gray-100 text-gray-700"
                        }
                      >
                        {TOMA_ESTADOS.find((e) => e.value === toma.estado)
                          ?.label || toma.estado}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-2 w-16 rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-primary"
                            style={{ width: `${progreso}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {toma.items_contados || 0}/{toma.total_items || 0}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {(toma.items_con_diferencia || 0) > 0 ? (
                        <Badge
                          variant="secondary"
                          className="bg-amber-100 text-amber-700"
                        >
                          {toma.items_con_diferencia}
                        </Badge>
                      ) : (
                        <span className="text-sm text-muted-foreground">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        render={<Link to={`/inventario/toma/${toma.id}`} />}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Pagina {data.page} de {data.pages} ({data.total} registros)
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

      {/* Create Dialog */}
      <Dialog
        open={showCreate}
        onOpenChange={(open) => {
          if (!open) setShowCreate(false);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Nueva Toma de Inventario</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Almacen *</Label>
              <Select
                value={form.almacen_id}
                onValueChange={(val) =>
                  setForm((f) => ({ ...f, almacen_id: val }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Seleccione almacen" />
                </SelectTrigger>
                <SelectContent>
                  {almacenes?.map((alm) => (
                    <SelectItem key={alm.id} value={String(alm.id)}>
                      {alm.codigo} - {alm.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Responsable *</Label>
                <Input
                  value={form.responsable}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, responsable: e.target.value }))
                  }
                  placeholder="Nombre del responsable"
                />
              </div>
              <div>
                <Label>Fecha Inicio</Label>
                <Input
                  type="date"
                  value={form.fecha_inicio}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, fecha_inicio: e.target.value }))
                  }
                />
              </div>
            </div>

            <div>
              <Label>Notas</Label>
              <Textarea
                value={form.notas}
                onChange={(e) =>
                  setForm((f) => ({ ...f, notas: e.target.value }))
                }
                placeholder="Observaciones (opcional)"
                rows={2}
              />
            </div>

            {createError && (
              <p className="text-sm text-red-600">{createError}</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreate(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending
                ? "Creando..."
                : "Crear Toma de Inventario"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
