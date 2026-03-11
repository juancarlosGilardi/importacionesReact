import { useState, useEffect } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import type { Proveedor, Pais } from "@/lib/types";
import { INCOTERMS, MONEDAS } from "@/lib/constants";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface ProveedorForm {
  ruc: string;
  razon_social: string;
  nombre_comercial: string;
  pais: string;
  email: string;
  telefono: string;
  contacto: string;
  moneda: string;
  incoterm_default: string;
  es_extranjero: boolean;
}

const emptyForm: ProveedorForm = {
  ruc: "",
  razon_social: "",
  nombre_comercial: "",
  pais: "",
  email: "",
  telefono: "",
  contacto: "",
  moneda: "USD",
  incoterm_default: "FOB",
  es_extranjero: true,
};

export default function ProveedorFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEdit = Boolean(id);
  const [form, setForm] = useState<ProveedorForm>(emptyForm);
  const [error, setError] = useState("");

  const { data: paises } = useQuery({
    queryKey: ["paises"],
    queryFn: () =>
      api.get<Pais[]>("/api/paises").then((r) => r.data),
  });

  const { data: existing } = useQuery({
    queryKey: ["proveedor", id],
    queryFn: () =>
      api.get<Proveedor>(`/api/proveedores/${id}`).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      setForm({
        ruc: existing.ruc,
        razon_social: existing.razon_social,
        nombre_comercial: existing.nombre_comercial || "",
        pais: existing.pais,
        email: existing.email || "",
        telefono: existing.telefono || "",
        contacto: existing.contacto || "",
        moneda: existing.moneda,
        incoterm_default: existing.incoterm_default || "FOB",
        es_extranjero: existing.es_extranjero,
      });
    }
  }, [existing]);

  const mutation = useMutation({
    mutationFn: (data: ProveedorForm) => {
      if (isEdit) {
        return api.put(`/api/proveedores/${id}`, data);
      }
      return api.post("/api/proveedores", data);
    },
    onSuccess: () => {
      navigate("/proveedores");
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

  const updateField = <K extends keyof ProveedorForm>(
    key: K,
    value: ProveedorForm[K]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar Proveedor" : "Nuevo Proveedor"}
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Datos del Proveedor</CardTitle>
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
                <Label htmlFor="ruc">RUC</Label>
                <Input
                  id="ruc"
                  value={form.ruc}
                  onChange={(e) => updateField("ruc", e.target.value)}
                  required
                  placeholder="20123456789"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="razon_social">Razon Social</Label>
                <Input
                  id="razon_social"
                  value={form.razon_social}
                  onChange={(e) => updateField("razon_social", e.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="nombre_comercial">Nombre Comercial</Label>
                <Input
                  id="nombre_comercial"
                  value={form.nombre_comercial}
                  onChange={(e) =>
                    updateField("nombre_comercial", e.target.value)
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="pais">Pais</Label>
                <Select
                  value={form.pais}
                  onValueChange={(val) => updateField("pais", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar pais" />
                  </SelectTrigger>
                  <SelectContent>
                    {paises?.map((p) => (
                      <SelectItem key={p.codigo} value={p.codigo}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  placeholder="contacto@proveedor.com"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="telefono">Telefono</Label>
                <Input
                  id="telefono"
                  value={form.telefono}
                  onChange={(e) => updateField("telefono", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="contacto">Contacto</Label>
                <Input
                  id="contacto"
                  value={form.contacto}
                  onChange={(e) => updateField("contacto", e.target.value)}
                  placeholder="Nombre de persona de contacto"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="moneda">Moneda</Label>
                <Select
                  value={form.moneda}
                  onValueChange={(val) => updateField("moneda", val ?? "")}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccionar moneda" />
                  </SelectTrigger>
                  <SelectContent>
                    {MONEDAS.map((m) => (
                      <SelectItem key={m.value} value={m.value}>
                        {m.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="incoterm">Incoterm Default</Label>
                <Select
                  value={form.incoterm_default}
                  onValueChange={(val) => updateField("incoterm_default", val ?? "")}
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

              <div className="flex items-end space-x-2 pb-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.es_extranjero}
                    onChange={(e) =>
                      updateField("es_extranjero", e.target.checked)
                    }
                    className="h-4 w-4 rounded border-gray-300"
                  />
                  <span className="text-sm font-medium">Es Extranjero</span>
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate("/proveedores")}
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
