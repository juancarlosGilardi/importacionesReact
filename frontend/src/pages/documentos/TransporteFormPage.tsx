import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { DocumentoTransporte, Importacion } from "@/lib/types";
import { TIPO_DOCUMENTO_TRANSPORTE } from "@/lib/constants";
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

interface TransporteForm {
  importacion_id: string;
  tipo_documento: string;
  numero_documento: string;
  transportista: string;
  nombre_nave: string;
  numero_viaje: string;
  fecha_etd: string;
  fecha_eta: string;
  fecha_arribo_real: string;
  total_bultos: string;
  peso_bruto_kg: string;
  volumen_m3: string;
  tracking_url: string;
  notas: string;
}

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

export default function TransporteFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const preselectedImportacionId = searchParams.get("importacion_id") || "";

  const [form, setForm] = useState<TransporteForm>({
    importacion_id: preselectedImportacionId,
    tipo_documento: "",
    numero_documento: "",
    transportista: "",
    nombre_nave: "",
    numero_viaje: "",
    fecha_etd: "",
    fecha_eta: "",
    fecha_arribo_real: "",
    total_bultos: "",
    peso_bruto_kg: "",
    volumen_m3: "",
    tracking_url: "",
    notas: "",
  });
  const [error, setError] = useState("");

  // Load importaciones catalog
  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-for-transporte"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  // Load existing document if editing
  const { data: existing } = useQuery({
    queryKey: ["transporte", id],
    queryFn: () =>
      api
        .get<DocumentoTransporte>(`/api/documentos/transporte/${id}`)
        .then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        importacion_id: String(existing.importacion_id),
        tipo_documento: existing.tipo_documento,
        numero_documento: existing.numero_documento,
        transportista: existing.transportista || "",
        nombre_nave: existing.nombre_nave || "",
        numero_viaje: existing.numero_viaje || "",
        fecha_etd: existing.fecha_etd || "",
        fecha_eta: existing.fecha_eta || "",
        fecha_arribo_real: existing.fecha_arribo_real || "",
        total_bultos: existing.total_bultos != null ? String(existing.total_bultos) : "",
        peso_bruto_kg: existing.peso_bruto_kg != null ? String(existing.peso_bruto_kg) : "",
        volumen_m3: existing.volumen_m3 != null ? String(existing.volumen_m3) : "",
        tracking_url: existing.tracking_url || "",
        notas: existing.notas || "",
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (data: TransporteForm) => {
      const payload: Record<string, unknown> = {
        importacion_id: Number(data.importacion_id),
        tipo_documento: data.tipo_documento,
        numero_documento: data.numero_documento,
        transportista: data.transportista || null,
        nombre_nave: data.nombre_nave || null,
        numero_viaje: data.numero_viaje || null,
        fecha_etd: data.fecha_etd || null,
        fecha_eta: data.fecha_eta || null,
        total_bultos: data.total_bultos ? Number(data.total_bultos) : null,
        peso_bruto_kg: data.peso_bruto_kg ? Number(data.peso_bruto_kg) : null,
        volumen_m3: data.volumen_m3 ? Number(data.volumen_m3) : null,
        tracking_url: data.tracking_url || null,
        notas: data.notas || null,
      };

      if (isEdit) {
        payload.fecha_arribo_real = data.fecha_arribo_real || null;
        return api.put(`/api/documentos/transporte/${id}`, payload);
      }
      return api.post("/api/documentos/transporte", payload);
    },
    onSuccess: () => {
      if (preselectedImportacionId) {
        navigate(`/importaciones/${preselectedImportacionId}`);
      } else {
        navigate("/importaciones");
      }
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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");
    mutation.mutate(form);
  };

  const updateField = <K extends keyof TransporteForm>(
    key: K,
    value: TransporteForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Documento de Transporte" : "Nuevo Documento de Transporte"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Documento</CardTitle>
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
                <Label htmlFor="importacion_id">Importacion</Label>
                <Select
                  value={form.importacion_id}
                  onValueChange={(val) => updateField("importacion_id", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar importacion" />
                  </SelectTrigger>
                  <SelectContent>
                    {importaciones?.items.map((imp) => (
                      <SelectItem key={imp.id} value={String(imp.id)}>
                        {imp.numero_importacion} - {imp.descripcion}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="tipo_documento">Tipo de Documento</Label>
                <Select
                  value={form.tipo_documento}
                  onValueChange={(val) => updateField("tipo_documento", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPO_DOCUMENTO_TRANSPORTE.map((t) => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_documento">Numero de Documento</Label>
                <Input
                  id="numero_documento"
                  value={form.numero_documento}
                  onChange={(e) => updateField("numero_documento", e.target.value)}
                  required
                  placeholder="BL-123456789"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="transportista">Transportista</Label>
                <Input
                  id="transportista"
                  value={form.transportista}
                  onChange={(e) => updateField("transportista", e.target.value)}
                  placeholder="Nombre de la naviera / aerolinea"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="nombre_nave">Nombre de Nave</Label>
                <Input
                  id="nombre_nave"
                  value={form.nombre_nave}
                  onChange={(e) => updateField("nombre_nave", e.target.value)}
                  placeholder="Nombre del buque o vuelo"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_viaje">Numero de Viaje</Label>
                <Input
                  id="numero_viaje"
                  value={form.numero_viaje}
                  onChange={(e) => updateField("numero_viaje", e.target.value)}
                  placeholder="Ej: V-2024-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_etd">Fecha ETD (Salida Estimada)</Label>
                <Input
                  id="fecha_etd"
                  type="date"
                  value={form.fecha_etd}
                  onChange={(e) => updateField("fecha_etd", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_eta">Fecha ETA (Llegada Estimada)</Label>
                <Input
                  id="fecha_eta"
                  type="date"
                  value={form.fecha_eta}
                  onChange={(e) => updateField("fecha_eta", e.target.value)}
                />
              </div>

              {isEdit && (
                <div className="space-y-2">
                  <Label htmlFor="fecha_arribo_real">Fecha Arribo Real</Label>
                  <Input
                    id="fecha_arribo_real"
                    type="date"
                    value={form.fecha_arribo_real}
                    onChange={(e) => updateField("fecha_arribo_real", e.target.value)}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="total_bultos">Total Bultos</Label>
                <Input
                  id="total_bultos"
                  type="number"
                  min="0"
                  value={form.total_bultos}
                  onChange={(e) => updateField("total_bultos", e.target.value)}
                  placeholder="0"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="peso_bruto_kg">Peso Bruto (kg)</Label>
                <Input
                  id="peso_bruto_kg"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.peso_bruto_kg}
                  onChange={(e) => updateField("peso_bruto_kg", e.target.value)}
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="volumen_m3">Volumen (m3)</Label>
                <Input
                  id="volumen_m3"
                  type="number"
                  step="0.001"
                  min="0"
                  value={form.volumen_m3}
                  onChange={(e) => updateField("volumen_m3", e.target.value)}
                  placeholder="0.000"
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="tracking_url">URL de Tracking</Label>
                <Input
                  id="tracking_url"
                  value={form.tracking_url}
                  onChange={(e) => updateField("tracking_url", e.target.value)}
                  placeholder="https://..."
                />
              </div>
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
                    navigate("/importaciones");
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
