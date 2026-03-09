import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { Producto } from "@/lib/types";
import { UNIDADES_MEDIDA } from "@/lib/constants";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ProductoForm {
  sku: string;
  nombre: string;
  descripcion: string;
  codigo_hs: string;
  categoria: string;
  unidad_medida: string;
  peso_kg: string;
  volumen_m3: string;
}

const emptyForm: ProductoForm = {
  sku: "",
  nombre: "",
  descripcion: "",
  codigo_hs: "",
  categoria: "",
  unidad_medida: "UND",
  peso_kg: "",
  volumen_m3: "",
};

export default function ProductoFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form, setForm] = useState<ProductoForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: existing } = useQuery({
    queryKey: ["producto", id],
    queryFn: () =>
      api.get<Producto>(`/api/productos/${id}`).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        sku: existing.sku,
        nombre: existing.nombre,
        descripcion: existing.descripcion || "",
        codigo_hs: existing.codigo_hs || "",
        categoria: existing.categoria || "",
        unidad_medida: existing.unidad_medida,
        peso_kg: existing.peso_kg?.toString() || "",
        volumen_m3: existing.volumen_m3?.toString() || "",
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (data: ProductoForm) => {
      const payload = {
        ...data,
        peso_kg: data.peso_kg ? parseFloat(data.peso_kg) : null,
        volumen_m3: data.volumen_m3 ? parseFloat(data.volumen_m3) : null,
      };
      if (isEdit) {
        return api.put(`/api/productos/${id}`, payload);
      }
      return api.post("/api/productos", payload);
    },
    onSuccess: () => {
      navigate("/productos");
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

  const updateField = <K extends keyof ProductoForm>(
    key: K,
    value: ProductoForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Producto" : "Nuevo Producto"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Producto</CardTitle>
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
                <Label htmlFor="sku">SKU</Label>
                <Input
                  id="sku"
                  value={form.sku}
                  onChange={(e) => updateField("sku", e.target.value)}
                  required
                  placeholder="PROD-001"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="nombre">Nombre</Label>
                <Input
                  id="nombre"
                  value={form.nombre}
                  onChange={(e) => updateField("nombre", e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="descripcion">Descripcion</Label>
                <Textarea
                  id="descripcion"
                  value={form.descripcion}
                  onChange={(e) => updateField("descripcion", e.target.value)}
                  rows={3}
                  placeholder="Descripcion del producto..."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="codigo_hs">Codigo HS</Label>
                <Input
                  id="codigo_hs"
                  value={form.codigo_hs}
                  onChange={(e) => updateField("codigo_hs", e.target.value)}
                  placeholder="8471.30.00"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="categoria">Categoria</Label>
                <Input
                  id="categoria"
                  value={form.categoria}
                  onChange={(e) => updateField("categoria", e.target.value)}
                  placeholder="Electronica, Textil, etc."
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="unidad_medida">Unidad de Medida</Label>
                <Select
                  value={form.unidad_medida}
                  onValueChange={(val) => updateField("unidad_medida", val)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar unidad" />
                  </SelectTrigger>
                  <SelectContent>
                    {UNIDADES_MEDIDA.map((u) => (
                      <SelectItem key={u.value} value={u.value}>
                        {u.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="peso_kg">Peso (kg)</Label>
                <Input
                  id="peso_kg"
                  type="number"
                  step="0.001"
                  min="0"
                  value={form.peso_kg}
                  onChange={(e) => updateField("peso_kg", e.target.value)}
                  placeholder="0.000"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="volumen_m3">Volumen (m3)</Label>
                <Input
                  id="volumen_m3"
                  type="number"
                  step="0.0001"
                  min="0"
                  value={form.volumen_m3}
                  onChange={(e) => updateField("volumen_m3", e.target.value)}
                  placeholder="0.0000"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/productos")}
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
