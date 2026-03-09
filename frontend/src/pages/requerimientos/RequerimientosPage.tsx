import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, Eye, Search, FileCheck } from "lucide-react";
import type {
  Requerimiento,
  Almacen,
  Proveedor,
  PaginatedResponse,
} from "@/lib/types";
import {
  REQ_ESTADOS,
  REQ_STATUS_COLORS,
  REQ_PRIORIDADES,
  REQ_PRIORIDAD_COLORS,
} from "@/lib/constants";
import { formatCurrency, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  solicitante: string;
  almacen_id: string;
  centro_costo: string;
  prioridad: string;
  proveedor_sugerido_id: string;
  fecha: string;
  notas: string;
}

const emptyForm: CreateForm = {
  solicitante: "",
  almacen_id: "",
  centro_costo: "",
  prioridad: "media",
  proveedor_sugerido_id: "",
  fecha: new Date().toISOString().split("T")[0],
  notas: "",
};

export default function RequerimientosPage() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("");
  const [prioridad, setPrioridad] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState<CreateForm>(emptyForm);
  const [createError, setCreateError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["requerimientos", estado, prioridad, search, page],
    queryFn: () =>
      api
        .get<PaginatedResponse<Requerimiento>>("/api/requerimientos", {
          params: {
            estado: estado || undefined,
            prioridad: prioridad || undefined,
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

  const { data: proveedores } = useQuery({
    queryKey: ["proveedores-list"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Proveedor>>("/api/proveedores", {
          params: { page: 1, size: 999, activo: 1 },
        })
        .then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post("/api/requerimientos", payload),
    onSuccess: (res) => {
      const created = res.data;
      setShowCreate(false);
      setForm(emptyForm);
      setCreateError("");
      navigate(`/requerimientos/${created.id}`);
    },
    onError: (err: any) => {
      setCreateError(
        err.response?.data?.detail || "Error al crear requerimiento"
      );
    },
  });

  const handleCreate = () => {
    if (!form.solicitante.trim()) {
      setCreateError("El solicitante es requerido");
      return;
    }
    setCreateError("");
    const payload: Record<string, unknown> = {
      solicitante: form.solicitante,
      fecha: form.fecha,
      prioridad: form.prioridad,
    };
    if (form.almacen_id) payload.almacen_id = Number(form.almacen_id);
    if (form.centro_costo) payload.centro_costo = form.centro_costo;
    if (form.proveedor_sugerido_id)
      payload.proveedor_sugerido_id = Number(form.proveedor_sugerido_id);
    if (form.notas) payload.notas = form.notas;
    createMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileCheck className="h-6 w-6 text-muted-foreground" />
          <h1 className="text-2xl font-bold">Requerimientos Internos</h1>
        </div>
        <Button
          onClick={() => {
            setShowCreate(true);
            setForm(emptyForm);
            setCreateError("");
          }}
        >
          <Plus className="h-4 w-4" />
          Nuevo Requerimiento
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={estado}
          onValueChange={(val) => {
            setEstado(val === "all" ? "" : val);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los estados</SelectItem>
            {REQ_ESTADOS.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={prioridad}
          onValueChange={(val) => {
            setPrioridad(val === "all" ? "" : val);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Todas las prioridades" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las prioridades</SelectItem>
            {REQ_PRIORIDADES.map((p) => (
              <SelectItem key={p.value} value={p.value}>
                {p.label}
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
              <TableHead>Fecha</TableHead>
              <TableHead>Solicitante</TableHead>
              <TableHead>Prioridad</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Almacen</TableHead>
              <TableHead className="text-right">Items</TableHead>
              <TableHead className="text-right">Valor</TableHead>
              <TableHead className="w-16" />
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
            ) : !data?.items || data.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={9}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron requerimientos
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((req) => (
                <TableRow key={req.id}>
                  <TableCell>
                    <Link
                      to={`/requerimientos/${req.id}`}
                      className="font-mono text-sm font-medium text-primary hover:underline"
                    >
                      {req.numero}
                    </Link>
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDate(req.fecha)}
                  </TableCell>
                  <TableCell className="font-medium">
                    {req.solicitante}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        REQ_PRIORIDAD_COLORS[req.prioridad] ||
                        "bg-gray-100 text-gray-700"
                      }
                    >
                      {REQ_PRIORIDADES.find((p) => p.value === req.prioridad)
                        ?.label || req.prioridad}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        REQ_STATUS_COLORS[req.estado] ||
                        "bg-gray-100 text-gray-700"
                      }
                    >
                      {REQ_ESTADOS.find((e) => e.value === req.estado)?.label ||
                        req.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {req.almacen_codigo || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {req.total_items || 0}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(req.valor_total || 0)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      render={<Link to={`/requerimientos/${req.id}`} />}
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
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Nuevo Requerimiento</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Solicitante *</Label>
                <Input
                  value={form.solicitante}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, solicitante: e.target.value }))
                  }
                  placeholder="Nombre del solicitante"
                />
              </div>
              <div>
                <Label>Fecha</Label>
                <Input
                  type="date"
                  value={form.fecha}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, fecha: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Prioridad</Label>
                <Select
                  value={form.prioridad}
                  onValueChange={(val) =>
                    setForm((f) => ({ ...f, prioridad: val }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {REQ_PRIORIDADES.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Centro de Costo</Label>
                <Input
                  value={form.centro_costo}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, centro_costo: e.target.value }))
                  }
                  placeholder="Ej: CC-001"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Almacen</Label>
                <Select
                  value={form.almacen_id}
                  onValueChange={(val) =>
                    setForm((f) => ({
                      ...f,
                      almacen_id: val === "none" ? "" : val,
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Opcional" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin almacen</SelectItem>
                    {almacenes?.map((alm) => (
                      <SelectItem key={alm.id} value={String(alm.id)}>
                        {alm.codigo} - {alm.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Proveedor Sugerido</Label>
                <Select
                  value={form.proveedor_sugerido_id}
                  onValueChange={(val) =>
                    setForm((f) => ({
                      ...f,
                      proveedor_sugerido_id: val === "none" ? "" : val,
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Opcional" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Sin proveedor</SelectItem>
                    {proveedores?.items?.map((prov) => (
                      <SelectItem key={prov.id} value={String(prov.id)}>
                        {prov.razon_social}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
              {createMutation.isPending ? "Creando..." : "Crear Requerimiento"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
