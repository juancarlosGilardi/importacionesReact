import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, Eye, Search } from "lucide-react";
import type {
  Almacen,
  ConceptoAlmacen,
  ValeSalida,
  PaginatedResponse,
} from "@/lib/types";
import { VALE_ESTADOS, VALE_STATUS_COLORS } from "@/lib/constants";
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
  concepto_id: string;
  centro_costo: string;
  solicitante: string;
  documento_referencia: string;
  fecha: string;
  notas: string;
}

const emptyForm: CreateForm = {
  almacen_id: "",
  concepto_id: "",
  centro_costo: "",
  solicitante: "",
  documento_referencia: "",
  fecha: new Date().toISOString().split("T")[0],
  notas: "",
};

export default function ValeSalidaPage() {
  const navigate = useNavigate();
  const [almacenId, setAlmacenId] = useState("");
  const [estado, setEstado] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [form, setForm] = useState<CreateForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data: conceptos } = useQuery({
    queryKey: ["conceptos-salida", form.almacen_id],
    queryFn: () =>
      api
        .get<ConceptoAlmacen[]>(`/api/vales/conceptos/${form.almacen_id}`, {
          params: { tipo: "salida" },
        })
        .then((r) => r.data),
    enabled: !!form.almacen_id,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["vales-salida", almacenId, estado, search, page],
    queryFn: () =>
      api
        .get<PaginatedResponse<ValeSalida>>("/api/vales/salida", {
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

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post("/api/vales/salida", payload),
    onSuccess: (res) => {
      const newId = res.data?.id || res.data?.cabecera?.id;
      setShowCreateDialog(false);
      setForm(emptyForm);
      setError("");
      if (newId) navigate(`/vales/salida/${newId}`);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || "Error al crear vale");
    },
  });

  const handleCreate = () => {
    if (!form.almacen_id || !form.concepto_id) {
      setError("Almacen y Concepto son obligatorios");
      return;
    }
    const payload: Record<string, unknown> = {
      almacen_id: Number(form.almacen_id),
      concepto_id: Number(form.concepto_id),
      fecha: form.fecha,
    };
    if (form.centro_costo) payload.centro_costo = form.centro_costo;
    if (form.solicitante) payload.solicitante = form.solicitante;
    if (form.documento_referencia)
      payload.documento_referencia = form.documento_referencia;
    if (form.notas) payload.notas = form.notas;
    createMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Vales de Salida</h1>
        <Button
          onClick={() => {
            setForm(emptyForm);
            setError("");
            setShowCreateDialog(true);
          }}
        >
          <Plus className="h-4 w-4" />
          Nuevo Vale de Salida
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4">
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

        <div className="w-44">
          <Select
            value={estado}
            onValueChange={(val) => {
              setEstado(val === "all" ? "" : val);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Estado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los estados</SelectItem>
              {VALE_ESTADOS.map((e) => (
                <SelectItem key={e.value} value={e.value}>
                  {e.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por numero..."
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
              <TableHead>Almacen</TableHead>
              <TableHead>Concepto</TableHead>
              <TableHead>Solicitante</TableHead>
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
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !data || data.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron vales de salida
                </TableCell>
              </TableRow>
            ) : (
              data.items.map((vale) => (
                <TableRow key={vale.id}>
                  <TableCell className="font-mono text-xs">
                    {vale.numero_movimiento}
                  </TableCell>
                  <TableCell>{vale.almacen_nombre || "-"}</TableCell>
                  <TableCell>{vale.concepto_nombre || "-"}</TableCell>
                  <TableCell>{vale.solicitante || "-"}</TableCell>
                  <TableCell>{formatDate(vale.fecha_movimiento)}</TableCell>
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
                      render={<Link to={`/vales/salida/${vale.id}`} />}
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

      {/* Create Dialog */}
      <Dialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          if (!open) setShowCreateDialog(false);
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Nuevo Vale de Salida</DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Almacen *</Label>
                <Select
                  value={form.almacen_id}
                  onValueChange={(val) =>
                    setForm((prev) => ({
                      ...prev,
                      almacen_id: val,
                      concepto_id: "",
                    }))
                  }
                >
                  <SelectTrigger className="mt-1.5 w-full">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {almacenes?.map((alm) => (
                      <SelectItem key={alm.id} value={String(alm.id)}>
                        {alm.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Concepto *</Label>
                <Select
                  value={form.concepto_id}
                  onValueChange={(val) =>
                    setForm((prev) => ({ ...prev, concepto_id: val }))
                  }
                  disabled={!form.almacen_id}
                >
                  <SelectTrigger className="mt-1.5 w-full">
                    <SelectValue placeholder="Seleccionar" />
                  </SelectTrigger>
                  <SelectContent>
                    {conceptos
                      ?.filter((c) => c.habilitado !== false)
                      .map((c) => (
                        <SelectItem key={c.id} value={String(c.id)}>
                          {c.codigo} - {c.nombre}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Centro de Costo</Label>
                <Input
                  value={form.centro_costo}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      centro_costo: e.target.value,
                    }))
                  }
                  placeholder="Departamento, area, etc."
                  className="mt-1.5"
                />
              </div>

              <div>
                <Label>Solicitante</Label>
                <Input
                  value={form.solicitante}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      solicitante: e.target.value,
                    }))
                  }
                  placeholder="Nombre del solicitante"
                  className="mt-1.5"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Fecha *</Label>
                <Input
                  type="date"
                  value={form.fecha}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, fecha: e.target.value }))
                  }
                  className="mt-1.5"
                />
              </div>

              <div>
                <Label>Documento Referencia</Label>
                <Input
                  value={form.documento_referencia}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      documento_referencia: e.target.value,
                    }))
                  }
                  placeholder="Referencia"
                  className="mt-1.5"
                />
              </div>
            </div>

            <div>
              <Label>Notas</Label>
              <Textarea
                value={form.notas}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, notas: e.target.value }))
                }
                placeholder="Observaciones..."
                rows={2}
                className="mt-1.5"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Creando..." : "Crear Vale"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
