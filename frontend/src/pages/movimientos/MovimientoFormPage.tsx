import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2, ArrowLeft } from "lucide-react";
import type { Almacen, OrdenCompra, PaginatedResponse } from "@/lib/types";
import { TIPO_MOVIMIENTO_COLORS, TIPO_MOVIMIENTO_LABELS } from "@/lib/constants";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface MovimientoForm {
  almacen_id: string;
  almacen_origen_id: string;
  almacen_destino_id: string;
  oc_id: string;
  documento_referencia: string;
  fecha: string;
  notas: string;
}

const emptyForm: MovimientoForm = {
  almacen_id: "",
  almacen_origen_id: "",
  almacen_destino_id: "",
  oc_id: "",
  documento_referencia: "",
  fecha: new Date().toISOString().slice(0, 10),
  notas: "",
};

export default function MovimientoFormPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tipo = searchParams.get("tipo") || "ingreso";
  const [form, setForm] = useState<MovimientoForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes", { params: { status: "activo" } }).then((r) => r.data),
  });

  const { data: ordenes } = useQuery({
    queryKey: ["ordenes-list"],
    queryFn: () =>
      api
        .get<PaginatedResponse<OrdenCompra>>("/api/ordenes", {
          params: { page: 1, size: 999 },
        })
        .then((r) => r.data),
    enabled: tipo === "ingreso",
  });

  const mutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => {
      const endpoints: Record<string, string> = {
        ingreso: "/api/inventario/movimientos/ingreso",
        transferencia: "/api/inventario/movimientos/transferencia",
        salida: "/api/inventario/movimientos/salida",
      };
      return api.post(endpoints[tipo] || endpoints.ingreso, payload);
    },
    onSuccess: (response) => {
      const id = response.data?.id;
      if (id) {
        navigate(`/movimientos/${id}`);
      } else {
        navigate("/movimientos");
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

    const payload: Record<string, unknown> = {
      documento_referencia: form.documento_referencia || undefined,
      fecha: form.fecha,
      notas: form.notas || undefined,
    };

    if (tipo === "ingreso") {
      payload.almacen_id = Number(form.almacen_id);
      if (form.oc_id) payload.oc_id = Number(form.oc_id);
    } else if (tipo === "transferencia") {
      payload.almacen_origen_id = Number(form.almacen_origen_id);
      payload.almacen_destino_id = Number(form.almacen_destino_id);
    } else if (tipo === "salida") {
      payload.almacen_id = Number(form.almacen_id);
    }

    mutation.mutate(payload);
  };

  const updateField = <K extends keyof MovimientoForm>(
    key: K,
    value: MovimientoForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/movimientos")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold">Nuevo Movimiento</h1>
        <Badge
          variant="secondary"
          className={TIPO_MOVIMIENTO_COLORS[tipo] || "bg-gray-100 text-gray-700"}
        >
          {TIPO_MOVIMIENTO_LABELS[tipo] || tipo}
        </Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Movimiento</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {/* Almacen for ingreso/salida */}
              {(tipo === "ingreso" || tipo === "salida") && (
                <div className="space-y-2">
                  <Label htmlFor="almacen_id">Almacen</Label>
                  <Select
                    value={form.almacen_id}
                    onValueChange={(val) => updateField("almacen_id", val)}
                    required
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Seleccionar almacen" />
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
              )}

              {/* Almacen origen/destino for transferencia */}
              {tipo === "transferencia" && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="almacen_origen_id">Almacen Origen</Label>
                    <Select
                      value={form.almacen_origen_id}
                      onValueChange={(val) => updateField("almacen_origen_id", val)}
                      required
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Seleccionar origen" />
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
                  <div className="space-y-2">
                    <Label htmlFor="almacen_destino_id">Almacen Destino</Label>
                    <Select
                      value={form.almacen_destino_id}
                      onValueChange={(val) => updateField("almacen_destino_id", val)}
                      required
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Seleccionar destino" />
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
                </>
              )}

              {/* OC for ingreso only */}
              {tipo === "ingreso" && (
                <div className="space-y-2">
                  <Label htmlFor="oc_id">Orden de Compra (opcional)</Label>
                  <Select
                    value={form.oc_id}
                    onValueChange={(val) => updateField("oc_id", val === "none" ? "" : val)}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Sin OC asociada" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Sin OC asociada</SelectItem>
                      {ordenes?.items.map((oc) => (
                        <SelectItem key={oc.id} value={String(oc.id)}>
                          {oc.numero_oc || oc.numero} - {oc.proveedor_nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="documento_referencia">Documento de Referencia</Label>
                <Input
                  id="documento_referencia"
                  value={form.documento_referencia}
                  onChange={(e) => updateField("documento_referencia", e.target.value)}
                  placeholder="Factura, guia, etc."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fecha">Fecha</Label>
                <Input
                  id="fecha"
                  type="date"
                  value={form.fecha}
                  onChange={(e) => updateField("fecha", e.target.value)}
                  required
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
                rows={3}
              />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/movimientos")}
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
