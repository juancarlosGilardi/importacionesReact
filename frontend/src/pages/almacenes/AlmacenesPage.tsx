import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Pencil, Trash2 } from "lucide-react";
import type { Almacen } from "@/lib/types";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
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
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface AlmacenForm {
  codigo: string;
  nombre: string;
  responsable: string;
  direccion: string;
  notas: string;
  status: string;
}

const emptyForm: AlmacenForm = {
  codigo: "",
  nombre: "",
  responsable: "",
  direccion: "",
  notas: "",
  status: "activo",
};

export default function AlmacenesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<AlmacenForm>(emptyForm);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [error, setError] = useState("");

  const { data: almacenes, isLoading } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes")
        .then((r) => r.data),
  });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => {
      if (editingId) {
        return api.put(`/api/almacenes/${editingId}`, payload);
      }
      return api.post("/api/almacenes", payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["almacenes"] });
      handleCloseDialog();
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al guardar");
      } else {
        setError("Error de conexion");
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/almacenes/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["almacenes"] });
      setDeleteId(null);
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: (almacen: Almacen) =>
      api.put(`/api/almacenes/${almacen.id}`, {
        codigo: almacen.codigo,
        nombre: almacen.nombre,
        responsable: almacen.responsable || "",
        direccion: almacen.direccion || "",
        notas: almacen.notas || "",
        status: almacen.status === "activo" ? "inactivo" : "activo",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["almacenes"] });
    },
  });

  const handleOpenCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setDialogOpen(true);
  };

  const handleOpenEdit = (almacen: Almacen) => {
    setEditingId(almacen.id);
    setForm({
      codigo: almacen.codigo,
      nombre: almacen.nombre,
      responsable: almacen.responsable || "",
      direccion: almacen.direccion || "",
      notas: almacen.notas || "",
      status: almacen.status,
    });
    setError("");
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingId(null);
    setForm(emptyForm);
    setError("");
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");

    const payload: Record<string, unknown> = {
      codigo: form.codigo,
      nombre: form.nombre,
    };
    if (form.responsable) payload.responsable = form.responsable;
    if (form.direccion) payload.direccion = form.direccion;
    if (form.notas) payload.notas = form.notas;
    if (editingId) payload.status = form.status;

    saveMutation.mutate(payload);
  };

  const updateField = <K extends keyof AlmacenForm>(
    key: K,
    value: AlmacenForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Almacenes</h1>
        <Button onClick={handleOpenCreate}>
          <Plus className="h-4 w-4" />
          Nuevo Almacen
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Codigo</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Responsable</TableHead>
              <TableHead>Direccion</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-24">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 6 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !almacenes || almacenes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="py-8 text-center text-muted-foreground">
                  No se encontraron almacenes
                </TableCell>
              </TableRow>
            ) : (
              almacenes.map((almacen) => (
                <TableRow key={almacen.id}>
                  <TableCell className="font-mono text-xs">{almacen.codigo}</TableCell>
                  <TableCell className="font-medium">{almacen.nombre}</TableCell>
                  <TableCell>{almacen.responsable || "-"}</TableCell>
                  <TableCell>{almacen.direccion || "-"}</TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        almacen.status === "activo"
                          ? "bg-green-100 text-green-700 cursor-pointer"
                          : "bg-gray-100 text-gray-500 cursor-pointer"
                      }
                      onClick={() => toggleStatusMutation.mutate(almacen)}
                    >
                      {almacen.status === "activo" ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => handleOpenEdit(almacen)}
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setDeleteId(almacen.id)}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={(open) => { if (!open) handleCloseDialog(); }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingId ? "Editar Almacen" : "Nuevo Almacen"}
            </DialogTitle>
            <DialogDescription>
              {editingId
                ? "Modifique los datos del almacen."
                : "Complete los datos del nuevo almacen."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="codigo">Codigo</Label>
              <Input
                id="codigo"
                value={form.codigo}
                onChange={(e) => updateField("codigo", e.target.value)}
                required
                placeholder="ALM-001"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="nombre">Nombre</Label>
              <Input
                id="nombre"
                value={form.nombre}
                onChange={(e) => updateField("nombre", e.target.value)}
                required
                placeholder="Almacen Principal"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="responsable">Responsable</Label>
              <Input
                id="responsable"
                value={form.responsable}
                onChange={(e) => updateField("responsable", e.target.value)}
                placeholder="Nombre del responsable"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="direccion">Direccion</Label>
              <Input
                id="direccion"
                value={form.direccion}
                onChange={(e) => updateField("direccion", e.target.value)}
                placeholder="Direccion del almacen"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notas">Notas</Label>
              <Textarea
                id="notas"
                value={form.notas}
                onChange={(e) => updateField("notas", e.target.value)}
                placeholder="Notas adicionales..."
                rows={2}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleCloseDialog}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? "Guardando..." : "Guardar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={deleteId !== null} onOpenChange={(open) => { if (!open) setDeleteId(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar eliminacion</DialogTitle>
            <DialogDescription>
              Esta seguro de que desea eliminar este almacen? Esta accion no se
              puede deshacer.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => { if (deleteId) deleteMutation.mutate(deleteId); }}
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
