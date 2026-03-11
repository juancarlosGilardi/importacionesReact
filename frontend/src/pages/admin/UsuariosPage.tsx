import { useState } from "react";
import type { FormEvent } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Pencil,
  Search,
  UserCog,
  KeyRound,
  UserCheck,
  UserX,
  Shield,
  Eye,
  User,
} from "lucide-react";
import type { UsuarioAdmin, Almacen } from "@/lib/types";
import api from "@/lib/api";
import {
  USER_ROLES,
  USER_ROL_COLORS,
  USER_STATUS,
  USER_STATUS_COLORS,
} from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

// ---------- Types ----------
interface UsuarioForm {
  email: string;
  password: string;
  nombre: string;
  apellido: string;
  rol: string;
  almacen_default_id: string;
}

const emptyForm: UsuarioForm = {
  email: "",
  password: "",
  nombre: "",
  apellido: "",
  rol: "usuario",
  almacen_default_id: "",
};

const rolIcons: Record<string, typeof Shield> = {
  admin: Shield,
  usuario: User,
  readonly: Eye,
};

// ---------- Component ----------
export default function UsuariosPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [filterRol, setFilterRol] = useState("todos");
  const [filterStatus, setFilterStatus] = useState("todos");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<UsuarioForm>(emptyForm);
  const [error, setError] = useState("");
  const [resetDialogOpen, setResetDialogOpen] = useState(false);
  const [resetUserId, setResetUserId] = useState<number | null>(null);
  const [resetUserName, setResetUserName] = useState("");
  const [newPassword, setNewPassword] = useState("");

  // ---------- Queries ----------
  const { data: usuarios, isLoading } = useQuery({
    queryKey: ["usuarios", search, filterRol, filterStatus],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (filterRol !== "todos") params.rol = filterRol;
      if (filterStatus !== "todos") params.status = filterStatus;
      return api
        .get<UsuarioAdmin[]>("/api/usuarios", { params })
        .then((r) => r.data);
    },
  });

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () => api.get<Almacen[]>("/api/almacenes").then((r) => r.data),
  });

  // ---------- Mutations ----------
  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => {
      if (editingId) {
        return api.put(`/api/usuarios/${editingId}`, payload);
      }
      return api.post("/api/usuarios", payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
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

  const resetPasswordMutation = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      api.post(`/api/usuarios/${id}/reset-password`, {
        new_password: password,
      }),
    onSuccess: () => {
      setResetDialogOpen(false);
      setResetUserId(null);
      setNewPassword("");
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al resetear");
      }
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "activar" | "desactivar";
    }) => api.post(`/api/usuarios/${id}/${action}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["usuarios"] });
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al cambiar estado");
      }
    },
  });

  // ---------- Handlers ----------
  const handleOpenCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setDialogOpen(true);
  };

  const handleOpenEdit = (u: UsuarioAdmin) => {
    setEditingId(u.id);
    setForm({
      email: u.email,
      password: "",
      nombre: u.nombre,
      apellido: u.apellido,
      rol: u.rol,
      almacen_default_id: u.almacen_default_id
        ? String(u.almacen_default_id)
        : "",
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
      nombre: form.nombre,
      apellido: form.apellido,
      rol: form.rol,
      almacen_default_id: form.almacen_default_id
        ? Number(form.almacen_default_id)
        : null,
    };

    if (!editingId) {
      payload.email = form.email;
      payload.password = form.password;
    }

    saveMutation.mutate(payload);
  };

  const handleOpenResetPassword = (u: UsuarioAdmin) => {
    setResetUserId(u.id);
    setResetUserName(`${u.nombre} ${u.apellido}`);
    setNewPassword("");
    setError("");
    setResetDialogOpen(true);
  };

  const handleResetPassword = (e: FormEvent) => {
    e.preventDefault();
    if (resetUserId && newPassword.length >= 6) {
      resetPasswordMutation.mutate({ id: resetUserId, password: newPassword });
    }
  };

  const updateField = <K extends keyof UsuarioForm>(
    key: K,
    value: UsuarioForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const formatDate = (d?: string) => {
    if (!d) return "-";
    return new Date(d).toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const formatDateTime = (d?: string) => {
    if (!d) return "Nunca";
    return new Date(d).toLocaleDateString("es-PE", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // ---------- Stats ----------
  const totalUsers = usuarios?.length ?? 0;
  const activeUsers = usuarios?.filter((u) => u.status === "active").length ?? 0;
  const adminUsers = usuarios?.filter((u) => u.rol === "admin").length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Gestión de Usuarios</h1>
          <p className="text-sm text-muted-foreground">
            Administre los usuarios del sistema
          </p>
        </div>
        <Button onClick={handleOpenCreate}>
          <Plus className="h-4 w-4" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
              <UserCog className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{totalUsers}</p>
              <p className="text-xs text-muted-foreground">Total Usuarios</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100">
              <UserCheck className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{activeUsers}</p>
              <p className="text-xs text-muted-foreground">Activos</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100">
              <Shield className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold">{adminUsers}</p>
              <p className="text-xs text-muted-foreground">Administradores</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre o email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={filterRol} onValueChange={(val) => setFilterRol(val ?? "")}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Rol" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos los roles</SelectItem>
            {USER_ROLES.map((r) => (
              <SelectItem key={r.value} value={r.value}>
                {r.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterStatus} onValueChange={(val) => setFilterStatus(val ?? "")}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Estado" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos</SelectItem>
            {USER_STATUS.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Error banner */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button
            className="ml-2 underline"
            onClick={() => setError("")}
          >
            Cerrar
          </button>
        </div>
      )}

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Usuario</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Almacén</TableHead>
              <TableHead>Último Login</TableHead>
              <TableHead>Creado</TableHead>
              <TableHead className="w-32">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !usuarios || usuarios.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron usuarios
                </TableCell>
              </TableRow>
            ) : (
              usuarios.map((u) => {
                const RolIcon = rolIcons[u.rol] || User;
                return (
                  <TableRow key={u.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm font-semibold text-blue-700">
                          {u.nombre?.charAt(0)?.toUpperCase() || "U"}
                        </div>
                        <div>
                          <p className="font-medium">
                            {u.nombre} {u.apellido}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {u.email}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={USER_ROL_COLORS[u.rol] || ""}
                      >
                        <RolIcon className="mr-1 h-3 w-3" />
                        {USER_ROLES.find((r) => r.value === u.rol)?.label ||
                          u.rol}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className={USER_STATUS_COLORS[u.status] || ""}
                      >
                        {USER_STATUS.find((s) => s.value === u.status)?.label ||
                          u.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {u.almacen_nombre ? (
                        <span>
                          <span className="font-mono text-xs text-muted-foreground">
                            {u.almacen_codigo}
                          </span>{" "}
                          {u.almacen_nombre}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDateTime(u.ultimo_login)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(u.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title="Editar"
                          onClick={() => handleOpenEdit(u)}
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title="Reset Password"
                          onClick={() => handleOpenResetPassword(u)}
                        >
                          <KeyRound className="h-3.5 w-3.5" />
                        </Button>
                        {u.status === "active" ? (
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            title="Desactivar"
                            onClick={() =>
                              toggleStatusMutation.mutate({
                                id: u.id,
                                action: "desactivar",
                              })
                            }
                          >
                            <UserX className="h-3.5 w-3.5 text-red-500" />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            title="Activar"
                            onClick={() =>
                              toggleStatusMutation.mutate({
                                id: u.id,
                                action: "activar",
                              })
                            }
                          >
                            <UserCheck className="h-3.5 w-3.5 text-green-500" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          if (!open) handleCloseDialog();
        }}
      >
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingId ? "Editar Usuario" : "Nuevo Usuario"}
            </DialogTitle>
            <DialogDescription>
              {editingId
                ? "Modifique los datos del usuario."
                : "Complete los datos del nuevo usuario."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre</Label>
                <Input
                  id="nombre"
                  value={form.nombre}
                  onChange={(e) => updateField("nombre", e.target.value)}
                  required
                  placeholder="Juan"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apellido">Apellido</Label>
                <Input
                  id="apellido"
                  value={form.apellido}
                  onChange={(e) => updateField("apellido", e.target.value)}
                  required
                  placeholder="Perez"
                />
              </div>
            </div>

            {!editingId && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={form.email}
                    onChange={(e) => updateField("email", e.target.value)}
                    required
                    placeholder="juan@empresa.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña</Label>
                  <Input
                    id="password"
                    type="password"
                    value={form.password}
                    onChange={(e) => updateField("password", e.target.value)}
                    required
                    minLength={6}
                    placeholder="Minimo 6 caracteres"
                  />
                </div>
              </>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rol">Rol</Label>
                <Select
                  value={form.rol}
                  onValueChange={(v) => updateField("rol", v ?? "")}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar rol" />
                  </SelectTrigger>
                  <SelectContent>
                    {USER_ROLES.map((r) => (
                      <SelectItem key={r.value} value={r.value}>
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="almacen">Almacén por defecto</Label>
                <Select
                  value={form.almacen_default_id}
                  onValueChange={(v) => updateField("almacen_default_id", v ?? "")}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sin asignar" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Sin asignar</SelectItem>
                    {almacenes
                      ?.filter((a) => a.status === "activo")
                      .map((a) => (
                        <SelectItem key={a.id} value={String(a.id)}>
                          {a.codigo} - {a.nombre}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
              </div>
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

      {/* Reset Password Dialog */}
      <Dialog
        open={resetDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setResetDialogOpen(false);
            setResetUserId(null);
            setNewPassword("");
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Resetear Contraseña</DialogTitle>
            <DialogDescription>
              Ingrese la nueva contraseña para{" "}
              <span className="font-semibold">{resetUserName}</span>
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleResetPassword} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new_password">Nueva Contraseña</Label>
              <Input
                id="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                placeholder="Minimo 6 caracteres"
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setResetDialogOpen(false);
                  setResetUserId(null);
                  setNewPassword("");
                }}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={
                  resetPasswordMutation.isPending || newPassword.length < 6
                }
              >
                {resetPasswordMutation.isPending
                  ? "Guardando..."
                  : "Resetear Contraseña"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
