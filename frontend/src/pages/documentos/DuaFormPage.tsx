import { useState, useEffect, useMemo } from "react";
import type { FormEvent } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Loader2, Calculator } from "lucide-react";
import type { DuaDocumento, DuaItem, Importacion } from "@/lib/types";
import { DUA_ESTADOS } from "@/lib/constants";
import api from "@/lib/api";
import { formatCurrency, calcularTributos } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface DuaForm {
  importacion_id: string;
  numero_dua: string;
  fecha_registro: string;
  fecha_levante: string;
  agencia_aduanas: string;
  ruc_agente: string;
  numero_operacion: string;
  tipo_cambio: string;
  valor_fob_usd: string;
  flete_usd: string;
  seguro_usd: string;
  tasa_ad_valorem: string;
  tasa_igv: string;
  tasa_ipm: string;
  monto_isc: string;
  monto_antidumping: string;
  tasa_percepcion: string;
  gastos_despacho: string;
  honorarios_agente: string;
  almacenaje: string;
  otros_gastos: string;
  estado: string;
  notas: string;
}

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

interface DuaDetailResponse {
  cabecera: DuaDocumento;
  items: DuaItem[];
}

export default function DuaFormPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const preselectedImportacionId = searchParams.get("importacion_id") || "";

  const [form, setForm] = useState<DuaForm>({
    importacion_id: preselectedImportacionId,
    numero_dua: "",
    fecha_registro: "",
    fecha_levante: "",
    agencia_aduanas: "",
    ruc_agente: "",
    numero_operacion: "",
    tipo_cambio: "",
    valor_fob_usd: "",
    flete_usd: "",
    seguro_usd: "",
    tasa_ad_valorem: "",
    tasa_igv: "18",
    tasa_ipm: "0",
    monto_isc: "0",
    monto_antidumping: "0",
    tasa_percepcion: "3.5",
    gastos_despacho: "0",
    honorarios_agente: "0",
    almacenaje: "0",
    otros_gastos: "0",
    estado: "registrada",
    notas: "",
  });
  const [error, setError] = useState("");

  // Load importaciones catalog
  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-for-dua"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  // Load existing DUA if editing
  const { data: existing } = useQuery({
    queryKey: ["dua", id],
    queryFn: () =>
      api.get<DuaDetailResponse>(`/api/documentos/dua/${id}`).then((r) => r.data),
    enabled: isEdit,
  });

  useEffect(() => {
    if (existing) {
      const d = existing.cabecera;
      setForm({
        importacion_id: String(d.importacion_id),
        numero_dua: d.numero_dua,
        fecha_registro: d.fecha_registro,
        fecha_levante: d.fecha_levante || "",
        agencia_aduanas: d.agencia_aduanas || "",
        ruc_agente: d.ruc_agente || "",
        numero_operacion: d.numero_operacion || "",
        tipo_cambio: String(d.tipo_cambio),
        valor_fob_usd: String(d.valor_fob_usd),
        flete_usd: String(d.flete_usd),
        seguro_usd: String(d.seguro_usd),
        tasa_ad_valorem: String(d.tasa_ad_valorem),
        tasa_igv: String(d.tasa_igv),
        tasa_ipm: String(d.tasa_ipm),
        monto_isc: String(d.monto_isc),
        monto_antidumping: String(d.monto_antidumping),
        tasa_percepcion: String(d.tasa_percepcion),
        gastos_despacho: String(d.gastos_despacho),
        honorarios_agente: String(d.honorarios_agente),
        almacenaje: String(d.almacenaje),
        otros_gastos: String(d.otros_gastos_aduana),
        estado: d.estado,
        notas: d.notas || "",
      });
    }
  }, [existing]);

  // Live tax preview calculation
  const tributos = useMemo(() => {
    const fob = Number(form.valor_fob_usd) || 0;
    const flete = Number(form.flete_usd) || 0;
    const seguro = Number(form.seguro_usd) || 0;
    const tasaAdValorem = Number(form.tasa_ad_valorem) || 0;
    const tasaIgv = Number(form.tasa_igv) || 18;
    const tasaIpm = Number(form.tasa_ipm) || 0;
    const tasaPercepcion = Number(form.tasa_percepcion) || 3.5;
    const montoIsc = Number(form.monto_isc) || 0;

    return calcularTributos(
      fob,
      flete,
      seguro,
      tasaAdValorem,
      tasaIgv,
      tasaIpm,
      tasaPercepcion,
      montoIsc
    );
  }, [
    form.valor_fob_usd,
    form.flete_usd,
    form.seguro_usd,
    form.tasa_ad_valorem,
    form.tasa_igv,
    form.tasa_ipm,
    form.tasa_percepcion,
    form.monto_isc,
  ]);

  const totalGastosAduana = useMemo(() => {
    return (
      (Number(form.gastos_despacho) || 0) +
      (Number(form.honorarios_agente) || 0) +
      (Number(form.almacenaje) || 0) +
      (Number(form.otros_gastos) || 0)
    );
  }, [form.gastos_despacho, form.honorarios_agente, form.almacenaje, form.otros_gastos]);

  const mutation = useMutation({
    mutationFn: (data: DuaForm) => {
      const payload: Record<string, unknown> = {
        importacion_id: Number(data.importacion_id),
        numero_dua: data.numero_dua,
        fecha_registro: data.fecha_registro,
        fecha_levante: data.fecha_levante || null,
        agencia_aduanas: data.agencia_aduanas || null,
        ruc_agente: data.ruc_agente || null,
        numero_operacion: data.numero_operacion || null,
        tipo_cambio: Number(data.tipo_cambio) || 0,
        valor_fob_usd: Number(data.valor_fob_usd) || 0,
        flete_usd: Number(data.flete_usd) || 0,
        seguro_usd: Number(data.seguro_usd) || 0,
        tasa_ad_valorem: Number(data.tasa_ad_valorem) || 0,
        tasa_igv: Number(data.tasa_igv) || 18,
        tasa_ipm: Number(data.tasa_ipm) || 0,
        monto_isc: Number(data.monto_isc) || 0,
        monto_antidumping: Number(data.monto_antidumping) || 0,
        tasa_percepcion: Number(data.tasa_percepcion) || 3.5,
        gastos_despacho: Number(data.gastos_despacho) || 0,
        honorarios_agente: Number(data.honorarios_agente) || 0,
        almacenaje: Number(data.almacenaje) || 0,
        otros_gastos: Number(data.otros_gastos) || 0,
        notas: data.notas || null,
      };

      if (isEdit) {
        payload.estado = data.estado;
        return api.put(`/api/documentos/dua/${id}`, payload);
      }
      return api.post("/api/documentos/dua", payload);
    },
    onSuccess: () => {
      navigate("/documentos/duas");
    },
    onError: (err: unknown) => {
      if (err && typeof err === "object" && "response" in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || "Error al guardar la DUA");
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

  const updateField = <K extends keyof DuaForm>(key: K, value: DuaForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-bold">
        {isEdit ? "Editar DUA" : "Nueva Declaracion Aduanera (DUA)"}
      </h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left column - form fields */}
          <div className="space-y-6 lg:col-span-2">
            {/* Datos Generales */}
            <Card>
              <CardHeader>
                <CardTitle>Datos Generales</CardTitle>
              </CardHeader>
              <CardContent>
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
                    <Label htmlFor="numero_dua">Numero DUA</Label>
                    <Input
                      id="numero_dua"
                      value={form.numero_dua}
                      onChange={(e) => updateField("numero_dua", e.target.value)}
                      required
                      placeholder="118-2024-10-123456"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_registro">Fecha Registro</Label>
                    <Input
                      id="fecha_registro"
                      type="date"
                      value={form.fecha_registro}
                      onChange={(e) => updateField("fecha_registro", e.target.value)}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fecha_levante">Fecha Levante</Label>
                    <Input
                      id="fecha_levante"
                      type="date"
                      value={form.fecha_levante}
                      onChange={(e) => updateField("fecha_levante", e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="agencia_aduanas">Agencia de Aduanas</Label>
                    <Input
                      id="agencia_aduanas"
                      value={form.agencia_aduanas}
                      onChange={(e) => updateField("agencia_aduanas", e.target.value)}
                      placeholder="Nombre de la agencia"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ruc_agente">RUC Agente</Label>
                    <Input
                      id="ruc_agente"
                      value={form.ruc_agente}
                      onChange={(e) => updateField("ruc_agente", e.target.value)}
                      placeholder="20123456789"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="numero_operacion">Numero Operacion</Label>
                    <Input
                      id="numero_operacion"
                      value={form.numero_operacion}
                      onChange={(e) => updateField("numero_operacion", e.target.value)}
                      placeholder="Numero de operacion"
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
                      placeholder="3.7500"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Valores FOB/Flete/Seguro */}
            <Card>
              <CardHeader>
                <CardTitle>Valores FOB / Flete / Seguro</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="valor_fob_usd">FOB (USD)</Label>
                    <Input
                      id="valor_fob_usd"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.valor_fob_usd}
                      onChange={(e) => updateField("valor_fob_usd", e.target.value)}
                      required
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="flete_usd">Flete (USD)</Label>
                    <Input
                      id="flete_usd"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.flete_usd}
                      onChange={(e) => updateField("flete_usd", e.target.value)}
                      required
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="seguro_usd">Seguro (USD)</Label>
                    <Input
                      id="seguro_usd"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.seguro_usd}
                      onChange={(e) => updateField("seguro_usd", e.target.value)}
                      required
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="mt-4 rounded-lg bg-blue-50 px-4 py-3">
                  <p className="text-sm font-medium text-blue-700">
                    CIF = FOB + Flete + Seguro ={" "}
                    <span className="text-lg font-bold">
                      {formatCurrency(tributos.cif)}
                    </span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Tasas y Tributos */}
            <Card>
              <CardHeader>
                <CardTitle>Tasas y Tributos</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="tasa_ad_valorem">Ad Valorem (%)</Label>
                    <Input
                      id="tasa_ad_valorem"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.tasa_ad_valorem}
                      onChange={(e) => updateField("tasa_ad_valorem", e.target.value)}
                      required
                      placeholder="6"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tasa_igv">IGV (%)</Label>
                    <Input
                      id="tasa_igv"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.tasa_igv}
                      onChange={(e) => updateField("tasa_igv", e.target.value)}
                      placeholder="18"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tasa_ipm">IPM (%)</Label>
                    <Input
                      id="tasa_ipm"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.tasa_ipm}
                      onChange={(e) => updateField("tasa_ipm", e.target.value)}
                      placeholder="0"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="monto_isc">ISC (monto USD)</Label>
                    <Input
                      id="monto_isc"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.monto_isc}
                      onChange={(e) => updateField("monto_isc", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="monto_antidumping">Antidumping (USD)</Label>
                    <Input
                      id="monto_antidumping"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.monto_antidumping}
                      onChange={(e) => updateField("monto_antidumping", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="tasa_percepcion">Percepcion (%)</Label>
                    <Input
                      id="tasa_percepcion"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.tasa_percepcion}
                      onChange={(e) => updateField("tasa_percepcion", e.target.value)}
                      placeholder="3.5"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Gastos Aduaneros */}
            <Card>
              <CardHeader>
                <CardTitle>Gastos Aduaneros</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="gastos_despacho">Gastos de Despacho</Label>
                    <Input
                      id="gastos_despacho"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.gastos_despacho}
                      onChange={(e) => updateField("gastos_despacho", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="honorarios_agente">Honorarios Agente</Label>
                    <Input
                      id="honorarios_agente"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.honorarios_agente}
                      onChange={(e) => updateField("honorarios_agente", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="almacenaje">Almacenaje</Label>
                    <Input
                      id="almacenaje"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.almacenaje}
                      onChange={(e) => updateField("almacenaje", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="otros_gastos">Otros Gastos</Label>
                    <Input
                      id="otros_gastos"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.otros_gastos}
                      onChange={(e) => updateField("otros_gastos", e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="mt-4 rounded-lg bg-gray-50 px-4 py-3">
                  <p className="text-sm font-medium text-gray-700">
                    Total Gastos Aduaneros ={" "}
                    <span className="text-lg font-bold">
                      {formatCurrency(totalGastosAduana)}
                    </span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Estado (edit only) + Notas */}
            <Card>
              <CardHeader>
                <CardTitle>Informacion Adicional</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {isEdit && (
                  <div className="space-y-2">
                    <Label htmlFor="estado">Estado</Label>
                    <Select
                      value={form.estado}
                      onValueChange={(val) => updateField("estado", val ?? "")}
                    >
                      <SelectTrigger className="w-full sm:w-[220px]">
                        <SelectValue placeholder="Seleccionar estado" />
                      </SelectTrigger>
                      <SelectContent>
                        {DUA_ESTADOS.map((e) => (
                          <SelectItem key={e.value} value={e.value}>
                            {e.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="notas">Notas</Label>
                  <Textarea
                    id="notas"
                    value={form.notas}
                    onChange={(e) => updateField("notas", e.target.value)}
                    placeholder="Notas adicionales..."
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right column - Live tax preview */}
          <div className="lg:col-span-1">
            <div className="sticky top-6">
              <Card className="border-blue-200 bg-blue-50/50">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-2 text-blue-800">
                    <Calculator className="h-5 w-5" />
                    Calculo de Tributos
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">CIF (FOB + Flete + Seguro)</span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.cif)}
                      </span>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        Ad Valorem ({form.tasa_ad_valorem || 0}%)
                      </span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.adValorem)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Base IGV</span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.baseIgv)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        IGV ({form.tasa_igv || 18}%)
                      </span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.igv)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        IPM ({form.tasa_ipm || 0}%)
                      </span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.ipm)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">
                        Percepcion ({form.tasa_percepcion || 3.5}%)
                      </span>
                      <span className="font-mono font-medium">
                        {formatCurrency(tributos.percepcion)}
                      </span>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-blue-800">
                        Total Tributos
                      </span>
                      <span className="font-mono text-lg font-bold text-blue-800">
                        {formatCurrency(tributos.totalTributos)}
                      </span>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Gastos Aduaneros</span>
                      <span className="font-mono font-medium">
                        {formatCurrency(totalGastosAduana)}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Antidumping</span>
                      <span className="font-mono font-medium">
                        {formatCurrency(Number(form.monto_antidumping) || 0)}
                      </span>
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-800">
                        Costo Total DUA
                      </span>
                      <span className="font-mono text-lg font-bold text-gray-900">
                        {formatCurrency(
                          tributos.totalTributos +
                            totalGastosAduana +
                            (Number(form.monto_antidumping) || 0)
                        )}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex justify-end gap-3 pt-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate("/documentos/duas")}
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
    </div>
  );
}
