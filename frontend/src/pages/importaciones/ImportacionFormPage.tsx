import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { Importacion } from "@/lib/types";
import { VIA_TRANSPORTE, IMPORTACION_ESTADOS } from "@/lib/constants";
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

interface ImportacionForm {
  numero_importacion: string;
  descripcion: string;
  via_transporte: string;
  bl_number: string;
  container_number: string;
  nombre_nave: string;
  numero_viaje: string;
  fecha_embarque: string;
  fecha_arribo_estimada: string;
  fecha_arribo_real: string;
  fecha_desaduanaje: string;
  agente_aduanero: string;
  agente_carga: string;
  estado: string;
  notas: string;
}

const emptyForm: ImportacionForm = {
  numero_importacion: "",
  descripcion: "",
  via_transporte: "maritimo",
  bl_number: "",
  container_number: "",
  nombre_nave: "",
  numero_viaje: "",
  fecha_embarque: "",
  fecha_arribo_estimada: "",
  fecha_arribo_real: "",
  fecha_desaduanaje: "",
  agente_aduanero: "",
  agente_carga: "",
  estado: "planificada",
  notas: "",
};

export default function ImportacionFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form, setForm] = useState<ImportacionForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: existing } = useQuery({
    queryKey: ["importacion", id],
    queryFn: () =>
      api.get<Importacion>(`/api/importaciones/${id}`).then((r) => {
        // The detail endpoint returns { cabecera, ordenes, duas, gastos }
        // but when editing we may get just the flat object too
        const data = r.data;
        if ("cabecera" in data) {
          return (data as unknown as { cabecera: Importacion }).cabecera;
        }
        return data;
      }),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        numero_importacion: existing.numero_importacion,
        descripcion: existing.descripcion,
        via_transporte: existing.via_transporte,
        bl_number: existing.bl_number || "",
        container_number: existing.container_number || "",
        nombre_nave: existing.nombre_nave || "",
        numero_viaje: existing.numero_viaje || "",
        fecha_embarque: existing.fecha_embarque || "",
        fecha_arribo_estimada: existing.fecha_arribo_estimada || "",
        fecha_arribo_real: existing.fecha_arribo_real || "",
        fecha_desaduanaje: existing.fecha_desaduanaje || "",
        agente_aduanero: existing.agente_aduanero || "",
        agente_carga: existing.agente_carga || "",
        estado: existing.estado,
        notas: existing.notas || "",
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (data: ImportacionForm) => {
      // Build the payload - only include edit-specific fields on edit
      const payload: Record<string, unknown> = {
        numero_importacion: data.numero_importacion,
        descripcion: data.descripcion,
        via_transporte: data.via_transporte,
        bl_number: data.bl_number || null,
        container_number: data.container_number || null,
        nombre_nave: data.nombre_nave || null,
        numero_viaje: data.numero_viaje || null,
        fecha_embarque: data.fecha_embarque || null,
        fecha_arribo_estimada: data.fecha_arribo_estimada || null,
        agente_aduanero: data.agente_aduanero || null,
        agente_carga: data.agente_carga || null,
        notas: data.notas || null,
      };

      if (isEdit) {
        payload.fecha_arribo_real = data.fecha_arribo_real || null;
        payload.fecha_desaduanaje = data.fecha_desaduanaje || null;
        payload.estado = data.estado;
        return api.put(`/api/importaciones/${id}`, payload);
      }
      return api.post("/api/importaciones", payload);
    },
    onSuccess: () => {
      navigate("/importaciones");
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

  const updateField = <K extends keyof ImportacionForm>(
    key: K,
    value: ImportacionForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Importación" : "Nueva Importación"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos de la Importación</CardTitle>
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
                <Label htmlFor="numero_importacion">Número de Importación</Label>
                <Input
                  id="numero_importacion"
                  value={form.numero_importacion}
                  onChange={(e) => updateField("numero_importacion", e.target.value)}
                  required
                  placeholder="IMP-2024-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="descripcion">Descripción</Label>
                <Input
                  id="descripcion"
                  value={form.descripcion}
                  onChange={(e) => updateField("descripcion", e.target.value)}
                  required
                  placeholder="Descripción de la importación"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="via_transporte">Vía de Transporte</Label>
                <Select
                  value={form.via_transporte}
                  onValueChange={(val) => updateField("via_transporte", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar vía" />
                  </SelectTrigger>
                  <SelectContent>
                    {VIA_TRANSPORTE.map((v) => (
                      <SelectItem key={v.value} value={v.value}>
                        {v.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="bl_number">Número B/L</Label>
                <Input
                  id="bl_number"
                  value={form.bl_number}
                  onChange={(e) => updateField("bl_number", e.target.value)}
                  placeholder="Bill of Lading"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="container_number">Número de Contenedor</Label>
                <Input
                  id="container_number"
                  value={form.container_number}
                  onChange={(e) => updateField("container_number", e.target.value)}
                  placeholder="CONT-12345"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="nombre_nave">Nombre de Nave</Label>
                <Input
                  id="nombre_nave"
                  value={form.nombre_nave}
                  onChange={(e) => updateField("nombre_nave", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="numero_viaje">Número de Viaje</Label>
                <Input
                  id="numero_viaje"
                  value={form.numero_viaje}
                  onChange={(e) => updateField("numero_viaje", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_embarque">Fecha de Embarque</Label>
                <Input
                  id="fecha_embarque"
                  type="date"
                  value={form.fecha_embarque}
                  onChange={(e) => updateField("fecha_embarque", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_arribo_estimada">Fecha Arribo Estimada</Label>
                <Input
                  id="fecha_arribo_estimada"
                  type="date"
                  value={form.fecha_arribo_estimada}
                  onChange={(e) => updateField("fecha_arribo_estimada", e.target.value)}
                />
              </div>

              {isEdit && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fecha_arribo_real">Fecha Arribo Real</Label>
                    <Input
                      id="fecha_arribo_real"
                      type="date"
                      value={form.fecha_arribo_real}
                      onChange={(e) => updateField("fecha_arribo_real", e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_desaduanaje">Fecha Desaduanaje</Label>
                    <Input
                      id="fecha_desaduanaje"
                      type="date"
                      value={form.fecha_desaduanaje}
                      onChange={(e) => updateField("fecha_desaduanaje", e.target.value)}
                    />
                  </div>

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
                        {IMPORTACION_ESTADOS.map((e) => (
                          <SelectItem key={e.value} value={e.value}>
                            {e.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              <div className="space-y-2">
                <Label htmlFor="agente_aduanero">Agente Aduanero</Label>
                <Input
                  id="agente_aduanero"
                  value={form.agente_aduanero}
                  onChange={(e) => updateField("agente_aduanero", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="agente_carga">Agente de Carga</Label>
                <Input
                  id="agente_carga"
                  value={form.agente_carga}
                  onChange={(e) => updateField("agente_carga", e.target.value)}
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
                onClick={() => navigate("/importaciones")}
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
