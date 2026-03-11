import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Calculator,
  CheckCircle2,
  FileSpreadsheet,
  Loader2,
} from "lucide-react";
import type {
  Importacion,
  ImportacionDetail,
  ProrrateoResult,
} from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import {
  METODOS_PRORRATEO,
  PRORRATEO_STATUS_COLORS,
  PRORRATEO_STATUS_LABELS,
} from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function ProrrateoPage() {
  const queryClient = useQueryClient();
  const [importacionId, setImportacionId] = useState("");
  const [ocId, setOcId] = useState("");
  const [metodo, setMetodo] = useState("valor_fob");
  const [resultado, setResultado] = useState<ProrrateoResult | null>(null);

  // Fetch importaciones list
  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-prorrateo"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  // Fetch importacion detail to get its ordenes
  const { data: importacionDetail } = useQuery({
    queryKey: ["importacion-detail-prorrateo", importacionId],
    queryFn: () =>
      api
        .get<ImportacionDetail>(`/api/importaciones/${importacionId}`)
        .then((r) => r.data),
    enabled: !!importacionId,
  });

  // Calcular prorrateo mutation
  const calcularMutation = useMutation({
    mutationFn: () =>
      api
        .post<ProrrateoResult>("/api/prorrateo/calcular", {
          importacion_id: Number(importacionId),
          oc_id: Number(ocId),
          metodo,
        })
        .then((r) => r.data),
    onSuccess: (data) => {
      setResultado(data);
    },
  });

  // Aplicar prorrateo mutation
  const aplicarMutation = useMutation({
    mutationFn: (prorrateoId: number) =>
      api
        .post<ProrrateoResult>(`/api/prorrateo/${prorrateoId}/aplicar`)
        .then((r) => r.data),
    onSuccess: (data) => {
      setResultado(data);
      queryClient.invalidateQueries({ queryKey: ["importacion-detail-prorrateo"] });
    },
  });

  const handleImportacionChange = (val: string) => {
    setImportacionId(val);
    setOcId("");
    setResultado(null);
  };

  const handleOcChange = (val: string) => {
    setOcId(val);
    setResultado(null);
  };

  const ordenes = importacionDetail?.ordenes || [];
  const cabecera = resultado?.cabecera;
  const detalle = resultado?.detalle || [];
  const isAplicado = cabecera?.estado === "aplicado";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold">Prorrateo de Costos</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Calcule la distribucion de costos de importacion por producto
        </p>
      </div>

      {/* Step 1: Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5" />
            Parametros de Calculo
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Importacion select */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Importacion *</label>
              <Select
                value={importacionId}
                onValueChange={handleImportacionChange}
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

            {/* OC select */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Orden de Compra *</label>
              <Select
                value={ocId}
                onValueChange={handleOcChange}
                disabled={!importacionId || ordenes.length === 0}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Seleccionar OC" />
                </SelectTrigger>
                <SelectContent>
                  {ordenes.map((oc) => (
                    <SelectItem key={oc.id} value={String(oc.id)}>
                      {oc.numero_oc || oc.numero} -{" "}
                      {oc.proveedor_nombre || "Sin proveedor"} (
                      {formatCurrency(oc.total_fob)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Metodo select */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Metodo de Prorrateo</label>
              <Select value={metodo} onValueChange={(val) => setMetodo(val ?? "")}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {METODOS_PRORRATEO.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Button */}
            <div className="flex items-end">
              <Button
                onClick={() => calcularMutation.mutate()}
                disabled={
                  !importacionId ||
                  !ocId ||
                  calcularMutation.isPending
                }
                className="w-full"
              >
                {calcularMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4" />
                )}
                {calcularMutation.isPending
                  ? "Calculando..."
                  : "Calcular Prorrateo"}
              </Button>
            </div>
          </div>

          {calcularMutation.isError && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              Error al calcular el prorrateo. Verifique que la importacion tenga
              gastos registrados y la OC tenga items.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Step 2: Results */}
      {resultado && cabecera && (
        <>
          {/* Status bar */}
          <div className="flex items-center justify-between rounded-lg border bg-white p-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">
                Estado del Prorrateo:
              </span>
              <Badge
                variant="secondary"
                className={PRORRATEO_STATUS_COLORS[cabecera.estado] || ""}
              >
                {PRORRATEO_STATUS_LABELS[cabecera.estado] || cabecera.estado}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              {!isAplicado && (
                <Button
                  onClick={() => aplicarMutation.mutate(cabecera.id)}
                  disabled={aplicarMutation.isPending}
                >
                  {aplicarMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4" />
                  )}
                  {aplicarMutation.isPending
                    ? "Aplicando..."
                    : "Aplicar Prorrateo"}
                </Button>
              )}
              {isAplicado && (
                <Button
                  variant="outline"
                  render={
                    <Link to={`/prorrateo/ficha-costeo/${ocId}`} />
                  }
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Ver Ficha de Costeo
                </Button>
              )}
            </div>
          </div>

          {/* Summary Totals */}
          <Card>
            <CardHeader>
              <CardTitle>Resumen de Costos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-7">
                <div className="rounded-lg border bg-blue-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total FOB</p>
                  <p className="mt-1 text-lg font-bold text-blue-700">
                    {formatCurrency(cabecera.total_fob)}
                  </p>
                </div>
                <div className="rounded-lg border bg-cyan-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total Flete</p>
                  <p className="mt-1 text-lg font-bold text-cyan-700">
                    {formatCurrency(cabecera.total_flete)}
                  </p>
                </div>
                <div className="rounded-lg border bg-purple-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total Seguro</p>
                  <p className="mt-1 text-lg font-bold text-purple-700">
                    {formatCurrency(cabecera.total_seguro)}
                  </p>
                </div>
                <div className="rounded-lg border bg-indigo-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total CIF</p>
                  <p className="mt-1 text-lg font-bold text-indigo-700">
                    {formatCurrency(cabecera.total_cif)}
                  </p>
                </div>
                <div className="rounded-lg border bg-red-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total Tributos</p>
                  <p className="mt-1 text-lg font-bold text-red-700">
                    {formatCurrency(cabecera.total_tributos)}
                  </p>
                </div>
                <div className="rounded-lg border bg-orange-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Total Gastos</p>
                  <p className="mt-1 text-lg font-bold text-orange-700">
                    {formatCurrency(cabecera.total_gastos)}
                  </p>
                </div>
                <div className="rounded-lg border bg-green-50 p-3 text-center">
                  <p className="text-xs text-muted-foreground">Costo Total</p>
                  <p className="mt-1 text-lg font-bold text-green-700">
                    {formatCurrency(cabecera.total_costo_importacion)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detail Table */}
          <Card>
            <CardHeader>
              <CardTitle>Detalle del Prorrateo por Producto</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Producto</TableHead>
                      <TableHead>SKU</TableHead>
                      <TableHead className="text-right">Cantidad</TableHead>
                      <TableHead className="text-right">Valor FOB</TableHead>
                      <TableHead className="text-right">% Part.</TableHead>
                      <TableHead className="text-right">Prorr. Flete</TableHead>
                      <TableHead className="text-right">Prorr. Seguro</TableHead>
                      <TableHead className="text-right">Prorr. Tributos</TableHead>
                      <TableHead className="text-right">Prorr. Gastos</TableHead>
                      <TableHead className="text-right">Costo Total</TableHead>
                      <TableHead className="text-right">C.U. Landed</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {detalle.length === 0 ? (
                      <TableRow>
                        <TableCell
                          colSpan={11}
                          className="py-8 text-center text-muted-foreground"
                        >
                          Sin items en el prorrateo
                        </TableCell>
                      </TableRow>
                    ) : (
                      detalle.map((item) => (
                        <TableRow key={item.id}>
                          <TableCell className="max-w-[180px] truncate text-xs font-medium">
                            {item.producto_nombre}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {item.producto_sku}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            {item.cantidad}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-blue-700">
                            {formatCurrency(item.valor_fob)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            {item.porcentaje_participacion.toFixed(2)}%
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-cyan-700">
                            {formatCurrency(item.prorrateo_flete)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-purple-700">
                            {formatCurrency(item.prorrateo_seguro)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-red-700">
                            {formatCurrency(item.prorrateo_tributos)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-orange-700">
                            {formatCurrency(item.prorrateo_gastos)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs font-semibold">
                            {formatCurrency(item.costo_total)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs font-bold text-green-700">
                            {formatCurrency(item.costo_unitario_landed)}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                    {detalle.length > 0 && (
                      <>
                        <TableRow className="border-t-2 bg-muted/50 font-semibold">
                          <TableCell colSpan={2} className="text-xs">
                            TOTALES
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            {detalle.reduce((s, d) => s + d.cantidad, 0)}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-blue-700">
                            {formatCurrency(
                              detalle.reduce((s, d) => s + d.valor_fob, 0)
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            100.00%
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-cyan-700">
                            {formatCurrency(
                              detalle.reduce(
                                (s, d) => s + d.prorrateo_flete,
                                0
                              )
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-purple-700">
                            {formatCurrency(
                              detalle.reduce(
                                (s, d) => s + d.prorrateo_seguro,
                                0
                              )
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-red-700">
                            {formatCurrency(
                              detalle.reduce(
                                (s, d) => s + d.prorrateo_tributos,
                                0
                              )
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-orange-700">
                            {formatCurrency(
                              detalle.reduce(
                                (s, d) => s + d.prorrateo_gastos,
                                0
                              )
                            )}
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs">
                            {formatCurrency(
                              detalle.reduce((s, d) => s + d.costo_total, 0)
                            )}
                          </TableCell>
                          <TableCell />
                        </TableRow>
                      </>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Aplicar result feedback */}
          {aplicarMutation.isError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              Error al aplicar el prorrateo. Intente nuevamente.
            </div>
          )}

          {isAplicado && (
            <>
              <Separator />
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileSpreadsheet className="h-5 w-5" />
                    Ficha de Costeo
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between rounded-lg border bg-green-50 p-4">
                    <div>
                      <p className="text-sm font-medium text-green-800">
                        Prorrateo aplicado exitosamente
                      </p>
                      <p className="mt-1 text-xs text-green-600">
                        Los costos han sido distribuidos a cada producto. Puede
                        ver la ficha de costeo completa.
                      </p>
                    </div>
                    <Button
                      render={
                        <Link to={`/prorrateo/ficha-costeo/${ocId}`} />
                      }
                    >
                      <FileSpreadsheet className="h-4 w-4" />
                      Ver Ficha de Costeo
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}
