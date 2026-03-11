import { useState, useEffect, useMemo } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { FacturaProveedor, Proveedor, OrdenCompra, Moneda } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
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

interface FacturaForm {
  numero_factura: string;
  oc_id: string;
  proveedor_id: string;
  fecha_factura: string;
  moneda_id: string;
  tipo_cambio: string;
  subtotal: string;
  impuesto: string;
  total: string;
  notas: string;
}

interface OrdenesListResponse {
  items: OrdenCompra[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

interface FacturaDetailResponse {
  cabecera: FacturaProveedor;
  items: unknown[];
}

export default function FacturaFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const preselectedOcId = searchParams.get("oc_id") || "";

  const [form, setForm] = useState<FacturaForm>({
    numero_factura: "",
    oc_id: preselectedOcId,
    proveedor_id: "",
    fecha_factura: "",
    moneda_id: "",
    tipo_cambio: "1",
    subtotal: "",
    impuesto: "0",
    total: "",
    notas: "",
  });
  const [error, setError] = useState("");

  // Load proveedores
  const { data: proveedores } = useQuery({
    queryKey: ["proveedores-for-factura"],
    queryFn: () =>
      api
        .get<{ items: Proveedor[]; total: number }>("/api/proveedores", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data.items),
  });

  // Load ordenes
  const { data: ordenes } = useQuery({
    queryKey: ["ordenes-for-factura"],
    queryFn: () =>
      api
        .get<OrdenesListResponse>("/api/ordenes", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  // Load monedas
  const { data: monedas } = useQuery({
    queryKey: ["monedas"],
    queryFn: () =>
      api.get<Moneda[]>("/api/catalogos/monedas").then((r) => r.data),
  });

  // Load existing factura if editing
  const { data: existing } = useQuery({
    queryKey: ["factura", id],
    queryFn: () =>
      api
        .get<FacturaDetailResponse>(`/api/documentos/facturas/${id}`)
        .then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      const f = existing.cabecera;
      setForm({
        numero_factura: f.numero_factura,
        oc_id: f.oc_id ? String(f.oc_id) : "",
        proveedor_id: String(f.proveedor_id),
        fecha_factura: f.fecha_factura,
        moneda_id: String(f.moneda_id),
        tipo_cambio: String(f.tipo_cambio),
        subtotal: String(f.subtotal),
        impuesto: String(f.impuesto),
        total: String(f.total),
        notas: f.notas || "",
      });
    }
  }, [existing]);

  // Auto-calculate total
  const totalCalculado = useMemo(() => {
    const subtotal = Number(form.subtotal) || 0;
    const impuesto = Number(form.impuesto) || 0;
    return subtotal + impuesto;
  }, [form.subtotal, form.impuesto]);

  // Auto-update total when subtotal or impuesto changes
  useEffect(() => {
    setForm((prev) => ({ ...prev, total: String(totalCalculado) }));
  }, [totalCalculado]);

  const mutation = useMutation({
    mutationFn: (data: FacturaForm) => {
      const payload: Record<string, unknown> = {
        numero_factura: data.numero_factura,
        oc_id: data.oc_id ? Number(data.oc_id) : null,
        proveedor_id: Number(data.proveedor_id),
        fecha_factura: data.fecha_factura,
        moneda_id: Number(data.moneda_id),
        tipo_cambio: Number(data.tipo_cambio) || 1,
        subtotal: Number(data.subtotal) || 0,
        impuesto: Number(data.impuesto) || 0,
        total: Number(data.total) || 0,
        notas: data.notas || null,
      };

      if (isEdit) {
        return api.put(`/api/documentos/facturas/${id}`, payload);
      }
      return api.post("/api/documentos/facturas", payload);
    },
    onSuccess: () => {
      navigate("/documentos/facturas");
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al guardar la factura");
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

  const updateField = <K extends keyof FacturaForm>(
    key: K,
    value: FacturaForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Factura" : "Nueva Factura de Proveedor"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos de la Factura</CardTitle>
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
                <Label htmlFor="numero_factura">Numero de Factura</Label>
                <Input
                  id="numero_factura"
                  value={form.numero_factura}
                  onChange={(e) => updateField("numero_factura", e.target.value)}
                  required
                  placeholder="INV-2024-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="proveedor_id">Proveedor</Label>
                <Select
                  value={form.proveedor_id}
                  onValueChange={(val) => updateField("proveedor_id", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar proveedor" />
                  </SelectTrigger>
                  <SelectContent>
                    {proveedores?.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        {p.razon_social} ({p.ruc})
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
                <Label htmlFor="fecha_factura">Fecha de Factura</Label>
                <Input
                  id="fecha_factura"
                  type="date"
                  value={form.fecha_factura}
                  onChange={(e) => updateField("fecha_factura", e.target.value)}
                  required
                />
              </div>

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
                <Label htmlFor="subtotal">Subtotal</Label>
                <Input
                  id="subtotal"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.subtotal}
                  onChange={(e) => updateField("subtotal", e.target.value)}
                  required
                  placeholder="0.00"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="impuesto">Impuesto</Label>
                <Input
                  id="impuesto"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.impuesto}
                  onChange={(e) => updateField("impuesto", e.target.value)}
                  placeholder="0.00"
                />
              </div>
            </div>

            {/* Total auto-calculated */}
            <div className="rounded-lg bg-blue-50 px-4 py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-blue-700">
                  Total (Subtotal + Impuesto)
                </span>
                <span className="font-mono text-lg font-bold text-blue-800">
                  {formatCurrency(totalCalculado)}
                </span>
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
                onClick={() => navigate("/documentos/facturas")}
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
