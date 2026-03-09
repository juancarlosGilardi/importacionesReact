import { useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Pencil,
  Plus,
  Trash2,
  Ship,
  Plane,
  Truck,
  ArrowLeft,
} from "lucide-react";
import type {
  ImportacionDetail,
  OrdenCompra,
  GastoResumen,
} from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  STATUS_COLORS,
  STATUS_LABELS,
  VIA_TRANSPORTE_COLORS,
  GASTO_STATUS_COLORS,
  GASTO_STATUS_LABELS,
} from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface PaginatedOC {
  items: OrdenCompra[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const VIA_LABELS: Record<string, string> = {
  maritimo: "Marítimo",
  aereo: "Aéreo",
  terrestre: "Terrestre",
  multimodal: "Multimodal",
};

const VIA_ICONS: Record<string, typeof Ship> = {
  maritimo: Ship,
  aereo: Plane,
  terrestre: Truck,
  multimodal: Ship,
};

export default function ImportacionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showAsociarDialog, setShowAsociarDialog] = useState(false);
  const [selectedOcId, setSelectedOcId] = useState("");
  const [desasociarOcId, setDesasociarOcId] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["importacion-detail", id],
    queryFn: () =>
      api.get<ImportacionDetail>(`/api/importaciones/${id}`).then((r) => r.data),
  });

  const { data: allOCs } = useQuery({
    queryKey: ["ordenes-for-asociar"],
    queryFn: () =>
      api
        .get<PaginatedOC>("/api/ordenes", { params: { page: 1, per_page: 999 } })
        .then((r) => r.data),
    enabled: showAsociarDialog,
  });

  const { data: gastoResumen } = useQuery({
    queryKey: ["gastos-resumen", id],
    queryFn: () =>
      api.get<GastoResumen[]>(`/api/gastos/resumen/${id}`).then((r) => r.data),
  });

  const asociarMutation = useMutation({
    mutationFn: (ocId: number) =>
      api.post(`/api/importaciones/${id}/asociar-oc`, { oc_id: ocId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["importacion-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["gastos-resumen", id] });
      setShowAsociarDialog(false);
      setSelectedOcId("");
    },
  });

  const desasociarMutation = useMutation({
    mutationFn: (ocId: number) =>
      api.delete(`/api/importaciones/${id}/desasociar-oc/${ocId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["importacion-detail", id] });
      queryClient.invalidateQueries({ queryKey: ["gastos-resumen", id] });
      setDesasociarOcId(null);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Importación no encontrada
      </div>
    );
  }

  const imp = data.cabecera;
  const ViaIcon = VIA_ICONS[imp.via_transporte] || Ship;

  // Filter available OCs: exclude already associated ones
  const associatedOcIds = new Set(data.ordenes.map((o) => o.id));
  const availableOCs = allOCs?.items.filter((oc) => !associatedOcIds.has(oc.id)) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/importaciones")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <ViaIcon className="h-5 w-5 text-muted-foreground" />
            <h1 className="text-2xl font-bold">{imp.numero_importacion}</h1>
            <Badge
              variant="secondary"
              className={STATUS_COLORS[imp.estado] || ""}
            >
              {STATUS_LABELS[imp.estado] || imp.estado}
            </Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">{imp.descripcion}</p>
        </div>
        <Button render={<Link to={`/importaciones/${id}/editar`} />}>
          <Pencil className="h-4 w-4" />
          Editar
        </Button>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Información General</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-3 lg:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Vía de Transporte</p>
              <Badge
                variant="secondary"
                className={VIA_TRANSPORTE_COLORS[imp.via_transporte] || ""}
              >
                {VIA_LABELS[imp.via_transporte] || imp.via_transporte}
              </Badge>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">B/L</p>
              <p className="text-sm font-medium">{imp.bl_number || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Contenedor</p>
              <p className="text-sm font-medium">{imp.container_number || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Nave</p>
              <p className="text-sm font-medium">{imp.nombre_nave || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Viaje</p>
              <p className="text-sm font-medium">{imp.numero_viaje || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Fecha Embarque</p>
              <p className="text-sm font-medium">
                {imp.fecha_embarque ? formatDate(imp.fecha_embarque) : "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Arribo Estimado</p>
              <p className="text-sm font-medium">
                {imp.fecha_arribo_estimada
                  ? formatDate(imp.fecha_arribo_estimada)
                  : "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Arribo Real</p>
              <p className="text-sm font-medium">
                {imp.fecha_arribo_real
                  ? formatDate(imp.fecha_arribo_real)
                  : "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Desaduanaje</p>
              <p className="text-sm font-medium">
                {imp.fecha_desaduanaje
                  ? formatDate(imp.fecha_desaduanaje)
                  : "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Agente Aduanero</p>
              <p className="text-sm font-medium">{imp.agente_aduanero || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Agente de Carga</p>
              <p className="text-sm font-medium">{imp.agente_carga || "-"}</p>
            </div>
          </div>
          {imp.notas && (
            <>
              <Separator className="my-4" />
              <div>
                <p className="text-xs text-muted-foreground">Notas</p>
                <p className="mt-1 text-sm whitespace-pre-wrap">{imp.notas}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Órdenes Asociadas */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Órdenes de Compra Asociadas</CardTitle>
            <Button size="sm" onClick={() => setShowAsociarDialog(true)}>
              <Plus className="h-4 w-4" />
              Asociar OC
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Número OC</TableHead>
                  <TableHead>Proveedor</TableHead>
                  <TableHead className="text-right">Total FOB</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.ordenes.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="py-6 text-center text-muted-foreground"
                    >
                      No hay órdenes de compra asociadas
                    </TableCell>
                  </TableRow>
                ) : (
                  data.ordenes.map((oc) => (
                    <TableRow key={oc.id}>
                      <TableCell className="font-mono text-xs font-medium">
                        {oc.numero_oc || oc.numero}
                      </TableCell>
                      <TableCell>
                        {oc.proveedor_nombre || oc.proveedor?.razon_social || "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {formatCurrency(oc.total_fob)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={STATUS_COLORS[oc.estado] || ""}
                        >
                          {STATUS_LABELS[oc.estado] || oc.estado}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => setDesasociarOcId(oc.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Gastos */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Gastos de Importación</CardTitle>
            <Button
              size="sm"
              render={<Link to={`/gastos/nuevo?importacion_id=${id}`} />}
            >
              <Plus className="h-4 w-4" />
              Agregar Gasto
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                  <TableHead>Moneda</TableHead>
                  <TableHead>Estado</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.gastos.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      className="py-6 text-center text-muted-foreground"
                    >
                      No hay gastos registrados
                    </TableCell>
                  </TableRow>
                ) : (
                  data.gastos.map((gasto) => (
                    <TableRow key={gasto.id}>
                      <TableCell className="text-xs font-medium">
                        {gasto.tipo_gasto_nombre || gasto.tipo_gasto_codigo}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-xs">
                        {gasto.descripcion || "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {formatCurrency(gasto.monto)}
                      </TableCell>
                      <TableCell className="text-xs">
                        {gasto.moneda_codigo || "-"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={GASTO_STATUS_COLORS[gasto.estado] || ""}
                        >
                          {GASTO_STATUS_LABELS[gasto.estado] || gasto.estado}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Resumen por tipo */}
          {gastoResumen && gastoResumen.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="mb-2 text-sm font-medium">Resumen por Tipo de Gasto</h4>
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Tipo de Gasto</TableHead>
                        <TableHead className="text-center">Cantidad</TableHead>
                        <TableHead className="text-right">Total (PEN)</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {gastoResumen.map((r) => (
                        <TableRow key={r.tipo_gasto_codigo}>
                          <TableCell className="text-sm">
                            {r.tipo_gasto_nombre}
                          </TableCell>
                          <TableCell className="text-center text-sm">
                            {r.cantidad}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm">
                            {formatCurrency(r.total, "S/")}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Totales */}
      <Card>
        <CardHeader>
          <CardTitle>Totales de la Importación</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-lg border bg-blue-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total FOB</p>
              <p className="mt-1 text-xl font-bold text-blue-700">
                {formatCurrency(imp.total_fob_importacion)}
              </p>
            </div>
            <div className="rounded-lg border bg-amber-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total Gastos</p>
              <p className="mt-1 text-xl font-bold text-amber-700">
                {formatCurrency(imp.total_gastos_importacion)}
              </p>
            </div>
            <div className="rounded-lg border bg-green-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Costo Total Importación</p>
              <p className="mt-1 text-xl font-bold text-green-700">
                {formatCurrency(imp.total_costo_importacion)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Asociar OC Dialog */}
      <Dialog
        open={showAsociarDialog}
        onOpenChange={(open) => {
          if (!open) {
            setShowAsociarDialog(false);
            setSelectedOcId("");
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Asociar Orden de Compra</DialogTitle>
            <DialogDescription>
              Seleccione una orden de compra para asociarla a esta importación.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Select
              value={selectedOcId}
              onValueChange={(val) => setSelectedOcId(val)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleccionar orden de compra" />
              </SelectTrigger>
              <SelectContent>
                {availableOCs.length === 0 ? (
                  <SelectItem value="__none__" disabled>
                    No hay OCs disponibles
                  </SelectItem>
                ) : (
                  availableOCs.map((oc) => (
                    <SelectItem key={oc.id} value={String(oc.id)}>
                      {oc.numero_oc || oc.numero} -{" "}
                      {oc.proveedor_nombre || oc.proveedor?.razon_social || "Sin proveedor"}{" "}
                      ({formatCurrency(oc.total_fob)})
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowAsociarDialog(false);
                setSelectedOcId("");
              }}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => {
                if (selectedOcId) {
                  asociarMutation.mutate(Number(selectedOcId));
                }
              }}
              disabled={!selectedOcId || asociarMutation.isPending}
            >
              {asociarMutation.isPending ? "Asociando..." : "Asociar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Desasociar OC Confirmation */}
      <Dialog
        open={desasociarOcId !== null}
        onOpenChange={(open) => {
          if (!open) setDesasociarOcId(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar desasociación</DialogTitle>
            <DialogDescription>
              ¿Está seguro de que desea desasociar esta orden de compra de la
              importación?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDesasociarOcId(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (desasociarOcId) {
                  desasociarMutation.mutate(desasociarOcId);
                }
              }}
              disabled={desasociarMutation.isPending}
            >
              {desasociarMutation.isPending ? "Desasociando..." : "Desasociar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
