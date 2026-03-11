import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { Gasto, TipoGasto, Moneda, Importacion, OrdenCompra } from "@/lib/types";
import { GASTO_ESTADOS } from "@/lib/constants";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface GastoForm {
  importacion_id: string;
  oc_id: string;
  tipo_gasto_codigo: string;
  descripcion: string;
  proveedor_ruc: string;
  proveedor_nombre: string;
  moneda_id: string;
  monto: string;
  tipo_cambio: string;
  numero_comprobante: string;
  fecha_gasto: string;
  estado: string;
  notas: string;
}

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

interface OrdenesListResponse {
  items: OrdenCompra[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function GastoFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const preselectedImportacionId = searchParams.get("importacion_id") || "";

  const [form, setForm] = useState<GastoForm>({
    importacion_id: preselectedImportacionId,
    oc_id: "",
    tipo_gasto_codigo: "",
    descripcion: "",
    proveedor_ruc: "",
    proveedor_nombre: "",
    moneda_id: "",
    monto: "",
    tipo_cambio: "1",
    numero_comprobante: "",
    fecha_gasto: "",
    estado: "pendiente",
    notas: "",
  });
  const [error, setError] = useState("");

  // Load catalogs
  const { data: tiposGasto } = useQuery({
    queryKey: ["tipos-gasto"],
    queryFn: () =>
      api.get<TipoGasto[]>("/api/catalogos/tipos-gasto").then((r) => r.data),
  });

  const { data: monedas } = useQuery({
    queryKey: ["monedas"],
    queryFn: () =>
      api.get<Moneda[]>("/api/catalogos/monedas").then((r) => r.data),
  });

  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-for-gasto"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const { data: ordenes } = useQuery({
    queryKey: ["ordenes-for-gasto"],
    queryFn: () =>
      api
        .get<OrdenesListResponse>("/api/ordenes", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  // Load existing gasto if editing
  const { data: existing } = useQuery({
    queryKey: ["gasto", id],
    queryFn: () => api.get<Gasto>(`/api/gastos/${id}`).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        importacion_id: existing.importacion_id ? String(existing.importacion_id) : "",
        oc_id: existing.oc_id ? String(existing.oc_id) : "",
        tipo_gasto_codigo: existing.tipo_gasto_codigo,
        descripcion: existing.descripcion || "",
        proveedor_ruc: existing.proveedor_ruc || "",
        proveedor_nombre: existing.proveedor_nombre || "",
        moneda_id: String(existing.moneda_id),
        monto: String(existing.monto),
        tipo_cambio: String(existing.tipo_cambio),
        numero_comprobante: existing.numero_comprobante || "",
        fecha_gasto: existing.fecha_gasto || "",
        estado: existing.estado,
        notas: existing.notas || "",
      });
    }
  }, [existing]);

  // Check if selected tipo_gasto requires proveedor
  const selectedTipo = tiposGasto?.find((t) => t.codigo === form.tipo_gasto_codigo);
  const showProveedor = selectedTipo?.requiere_proveedor ?? false;

  const mutation = useMutation({
    mutationFn: (data: GastoForm) => {
      const payload: Record<string, unknown> = {
        importacion_id: data.importacion_id ? Number(data.importacion_id) : null,
        oc_id: data.oc_id ? Number(data.oc_id) : null,
        tipo_gasto_codigo: data.tipo_gasto_codigo,
        descripcion: data.descripcion || null,
        proveedor_ruc: data.proveedor_ruc || null,
        proveedor_nombre: data.proveedor_nombre || null,
        moneda_id: Number(data.moneda_id),
        monto: Number(data.monto),
        tipo_cambio: Number(data.tipo_cambio),
        numero_comprobante: data.numero_comprobante || null,
        fecha_gasto: data.fecha_gasto || null,
        notas: data.notas || null,
      };

      if (isEdit) {
        payload.estado = data.estado;
        return api.put(`/api/gastos/${id}`, payload);
      }
      return api.post("/api/gastos", payload);
    },
    onSuccess: () => {
      // If we came from an importacion detail, go back there
      if (preselectedImportacionId) {
        navigate(`/importaciones/${preselectedImportacionId}`);
      } else {
        navigate("/gastos");
      }
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al guardar");
      } else {
        setError("Error de conexión");
      }
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate(form);
  };

  const updateField = <K extends keyof GastoForm>(
    key: K,
    value: GastoForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Gasto" : "Nuevo Gasto"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Gasto</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="importacion_id">Importación</Label>
                <Select
                  value={form.importacion_id}
                  onValueChange={(val) =>
                    updateField("importacion_id", val === "__none__" ? "" : val ?? "")
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar importación (opcional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Sin importación</SelectItem>
                    {importaciones?.items.map((imp) => (
                      <SelectItem key={imp.id} value={String(imp.id)}>
                        {imp.numero_importacion} - {imp.descripcion}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="oc_id">Orden de Compra</Label>
                <Select
                  value={form.oc_id}
                  onValueChange={(val) =>
                    updateField("oc_id", val === "__none__" ? "" : val ?? "")
                  }
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar OC (opcional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__none__">Sin OC</SelectItem>
                    {ordenes?.items.map((oc) => (
                      <SelectItem key={oc.id} value={String(oc.id)}>
                        {oc.numero_oc || oc.numero} -{" "}
                        {oc.proveedor_nombre || oc.proveedor?.razon_social || "Sin proveedor"}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tipo_gasto_codigo">Tipo de Gasto</Label>
                <Select
                  value={form.tipo_gasto_codigo}
                  onValueChange={(val) => updateField("tipo_gasto_codigo", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar tipo de gasto" />
                  </SelectTrigger>
                  <SelectContent>
                    {tiposGasto?.map((t) => (
                      <SelectItem key={t.codigo} value={t.codigo}>
                        {t.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="descripcion">Descripción</Label>
                <Input
                  id="descripcion"
                  value={form.descripcion}
                  onChange={(e) => updateField("descripcion", e.target.value)}
                  placeholder="Descripción del gasto"
                />
              </div>

              {showProveedor && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="proveedor_ruc">RUC del Proveedor</Label>
                    <Input
                      id="proveedor_ruc"
                      value={form.proveedor_ruc}
                      onChange={(e) => updateField("proveedor_ruc", e.target.value)}
                      placeholder="20123456789"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="proveedor_nombre">Nombre del Proveedor</Label>
                    <Input
                      id="proveedor_nombre"
                      value={form.proveedor_nombre}
                      onChange={(e) => updateField("proveedor_nombre", e.target.value)}
                      placeholder="Nombre del proveedor"
                    />
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="moneda_id">Moneda</Label>
                <Select
                  value={form.moneda_id}
                  onValueChange={(val) => updateField("moneda_id", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar moneda" />
                  </SelectTrigger>
                  <SelectContent>
                    {monedas?.map((m) => (
                      <SelectItem key={m.id} value={String(m.id)}>
                        {m.codigo} - {m.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="monto">Monto</Label>
                <Input
                  id="monto"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.monto}
                  onChange={(e) => updateField("monto", e.target.value)}
                  required
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tipo_cambio">Tipo de Cambio</Label>
                <Input
                  id="tipo_cambio"
                  type="number"
                  step="0.0001"
                  min="0"
                  value={form.tipo_cambio}
                  onChange={(e) => updateField("tipo_cambio", e.target.value)}
                  required
                  placeholder="1.0000"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_comprobante">Número de Comprobante</Label>
                <Input
                  id="numero_comprobante"
                  value={form.numero_comprobante}
                  onChange={(e) => updateField("numero_comprobante", e.target.value)}
                  placeholder="F001-12345"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_gasto">Fecha del Gasto</Label>
                <Input
                  id="fecha_gasto"
                  type="date"
                  value={form.fecha_gasto}
                  onChange={(e) => updateField("fecha_gasto", e.target.value)}
                />
              </div>

              {isEdit && (
                <div className="space-y-2">
                  <Label htmlFor="estado">Estado</Label>
                  <Select
                    value={form.estado}
                    onValueChange={(val) => updateField("estado", val ?? "")}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Seleccionar estado" />
                    </SelectTrigger>
                    <SelectContent>
                      {GASTO_ESTADOS.map((e) => (
                        <SelectItem key={e.value} value={e.value}>
                          {e.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="notas">Notas</Label>
              <Textarea
                id="notas"
                value={form.notas}
                onChange={(e) => updateField("notas", e.target.value)}
                placeholder="Notas adicionales..."
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (preselectedImportacionId) {
                    navigate(`/importaciones/${preselectedImportacionId}`);
                  } else {
                    navigate("/gastos");
                  }
                }}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  "Guardar"
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
