import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { OrdenCompraDetalle, Proveedor, Moneda, PaginatedResponse } from "@/lib/types";
import { INCOTERMS } from "@/lib/constants";
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

interface OrdenForm {
  numero_oc: string;
  proveedor_id: string;
  fecha_orden: string;
  fecha_llegada_est: string;
  incoterm: string;
  moneda_id: string;
  tipo_cambio: string;
  puerto_embarque: string;
  puerto_destino: string;
  agente_aduanero: string;
  agente_carga: string;
  notas: string;
}

const emptyForm: OrdenForm = {
  numero_oc: "",
  proveedor_id: "",
  fecha_orden: "",
  fecha_llegada_est: "",
  incoterm: "FOB",
  moneda_id: "",
  tipo_cambio: "",
  puerto_embarque: "",
  puerto_destino: "",
  agente_aduanero: "",
  agente_carga: "",
  notas: "",
};

export default function OrdenFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form, setForm] = useState<OrdenForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: proveedores } = useQuery({
    queryKey: ["proveedores-list"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Proveedor>>("/api/proveedores", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const { data: monedas } = useQuery({
    queryKey: ["monedas"],
    queryFn: () =>
      api.get<Moneda[]>("/api/catalogos/monedas").then((r) => r.data),
  });

  const { data: existing } = useQuery({
    queryKey: ["orden", id],
    queryFn: () =>
      api.get<OrdenCompraDetalle>(`/api/ordenes/${id}`).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      const cab = existing.cabecera;
      setForm({
        numero_oc: cab.numero_oc || cab.numero || "",
        proveedor_id: String(cab.proveedor_id),
        fecha_orden: cab.fecha_orden ? cab.fecha_orden.slice(0, 10) : "",
        fecha_llegada_est: cab.fecha_llegada_est
          ? cab.fecha_llegada_est.slice(0, 10)
          : "",
        incoterm: cab.incoterm || "FOB",
        moneda_id: cab.moneda_id ? String(cab.moneda_id) : "",
        tipo_cambio: cab.tipo_cambio ? String(cab.tipo_cambio) : "",
        puerto_embarque: cab.puerto_embarque || "",
        puerto_destino: cab.puerto_destino || "",
        agente_aduanero: cab.agente_aduanero || "",
        agente_carga: cab.agente_carga || "",
        notas: cab.notas || "",
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => {
      if (isEdit) {
        return api.put(`/api/ordenes/${id}`, data);
      }
      return api.post("/api/ordenes", data);
    },
    onSuccess: () => {
      navigate("/ordenes");
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

    const payload: Record<string, unknown> = {
      numero_oc: form.numero_oc,
      proveedor_id: Number(form.proveedor_id),
      fecha_orden: form.fecha_orden,
      incoterm: form.incoterm,
    };

    if (form.fecha_llegada_est) payload.fecha_llegada_est = form.fecha_llegada_est;
    if (form.moneda_id) payload.moneda_id = Number(form.moneda_id);
    if (form.tipo_cambio) payload.tipo_cambio = Number(form.tipo_cambio);
    if (form.puerto_embarque) payload.puerto_embarque = form.puerto_embarque;
    if (form.puerto_destino) payload.puerto_destino = form.puerto_destino;
    if (form.agente_aduanero) payload.agente_aduanero = form.agente_aduanero;
    if (form.agente_carga) payload.agente_carga = form.agente_carga;
    if (form.notas) payload.notas = form.notas;

    mutation.mutate(payload);
  };

  const updateField = <K extends keyof OrdenForm>(
    key: K,
    value: OrdenForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Orden de Compra" : "Nueva Orden de Compra"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos de la Orden</CardTitle>
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
                <Label htmlFor="numero_oc">Numero OC</Label>
                <Input
                  id="numero_oc"
                  value={form.numero_oc}
                  onChange={(e) => updateField("numero_oc", e.target.value)}
                  required
                  placeholder="OC-2024-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="proveedor_id">Proveedor</Label>
                <Select
                  value={form.proveedor_id}
                  onValueChange={(val) => updateField("proveedor_id", val)}
                  required
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar proveedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {proveedores?.items.map((prov) => (
                      <SelectItem key={prov.id} value={String(prov.id)}>
                        {prov.razon_social}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_orden">Fecha de Orden</Label>
                <Input
                  id="fecha_orden"
                  type="date"
                  value={form.fecha_orden}
                  onChange={(e) => updateField("fecha_orden", e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha_llegada_est">Fecha Llegada Estimada</Label>
                <Input
                  id="fecha_llegada_est"
                  type="date"
                  value={form.fecha_llegada_est}
                  onChange={(e) =>
                    updateField("fecha_llegada_est", e.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="incoterm">Incoterm</Label>
                <Select
                  value={form.incoterm}
                  onValueChange={(val) => updateField("incoterm", val)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar incoterm" />
                  </SelectTrigger>
                  <SelectContent>
                    {INCOTERMS.map((inc) => (
                      <SelectItem key={inc} value={inc}>
                        {inc}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="moneda_id">Moneda</Label>
                <Select
                  value={form.moneda_id}
                  onValueChange={(val) => updateField("moneda_id", val)}
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
                <Label htmlFor="tipo_cambio">Tipo de Cambio</Label>
                <Input
                  id="tipo_cambio"
                  type="number"
                  step="0.0001"
                  value={form.tipo_cambio}
                  onChange={(e) => updateField("tipo_cambio", e.target.value)}
                  placeholder="3.7500"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="puerto_embarque">Puerto de Embarque</Label>
                <Input
                  id="puerto_embarque"
                  value={form.puerto_embarque}
                  onChange={(e) =>
                    updateField("puerto_embarque", e.target.value)
                  }
                  placeholder="Shanghai, China"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="puerto_destino">Puerto de Destino</Label>
                <Input
                  id="puerto_destino"
                  value={form.puerto_destino}
                  onChange={(e) =>
                    updateField("puerto_destino", e.target.value)
                  }
                  placeholder="Callao, Peru"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="agente_aduanero">Agente Aduanero</Label>
                <Input
                  id="agente_aduanero"
                  value={form.agente_aduanero}
                  onChange={(e) =>
                    updateField("agente_aduanero", e.target.value)
                  }
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
                placeholder="Notas adicionales sobre la orden..."
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/ordenes")}
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
