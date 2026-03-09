import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle,
  RefreshCw,
  Save,
  AlertTriangle,
} from "lucide-react";
import type { TomaInventario, TomaInventarioItem } from "@/lib/types";
import { TOMA_ESTADOS, TOMA_STATUS_COLORS } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

interface TomaDetailResponse {
  cabecera: TomaInventario;
  items: TomaInventarioItem[];
}

interface EditingItem {
  id: number;
  stock_contado: string;
  observacion: string;
}

export default function TomaInventarioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [editingItem, setEditingItem] = useState<EditingItem | null>(null);
  const [showCompletarDialog, setShowCompletarDialog] = useState(false);
  const [showRegularizarDialog, setShowRegularizarDialog] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["toma-inventario", id],
    queryFn: () =>
      api
        .get<TomaDetailResponse>(`/api/toma-inventario/${id}`)
        .then((r) => r.data),
  });

  const updateItemMutation = useMutation({
    mutationFn: (payload: {
      itemId: number;
      stock_contado: number;
      observacion?: string;
    }) =>
      api.put(`/api/toma-inventario/${id}/items/${payload.itemId}`, {
        stock_contado: payload.stock_contado,
        observacion: payload.observacion,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["toma-inventario", id] });
      setEditingItem(null);
    },
  });

  const completarMutation = useMutation({
    mutationFn: () => api.post(`/api/toma-inventario/${id}/completar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["toma-inventario", id] });
      setShowCompletarDialog(false);
    },
  });

  const regularizarMutation = useMutation({
    mutationFn: () => api.post(`/api/toma-inventario/${id}/regularizar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["toma-inventario", id] });
      setShowRegularizarDialog(false);
    },
  });

  const handleSaveItem = () => {
    if (!editingItem || editingItem.stock_contado === "") return;
    updateItemMutation.mutate({
      itemId: editingItem.id,
      stock_contado: Number(editingItem.stock_contado),
      observacion: editingItem.observacion || undefined,
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="h-96 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!data?.cabecera) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Toma de inventario no encontrada
      </div>
    );
  }

  const cab = data.cabecera;
  const items = data.items;
  const canEdit = cab.estado === "pendiente" || cab.estado === "en_proceso";
  const canComplete = canEdit;
  const canRegularize = cab.estado === "completado";
  const totalItems = items.length;
  const itemsContados = items.filter((i) => i.stock_contado !== null).length;
  const itemsConDiferencia = items.filter((i) => i.diferencia !== 0).length;
  const todosContados = totalItems > 0 && itemsContados === totalItems;
  const sobrantes = items.filter((i) => i.diferencia > 0).length;
  const faltantes = items.filter((i) => i.diferencia < 0).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/inventario/toma")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{cab.numero}</h1>
            <Badge
              variant="secondary"
              className={
                TOMA_STATUS_COLORS[cab.estado] || "bg-gray-100 text-gray-700"
              }
            >
              {TOMA_ESTADOS.find((e) => e.value === cab.estado)?.label ||
                cab.estado}
            </Badge>
          </div>
          <div className="flex gap-2">
            {canComplete && todosContados && (
              <Button onClick={() => setShowCompletarDialog(true)}>
                <CheckCircle className="h-4 w-4" />
                Completar
              </Button>
            )}
            {canRegularize && (
              <Button
                variant="secondary"
                onClick={() => setShowRegularizarDialog(true)}
              >
                <RefreshCw className="h-4 w-4" />
                Regularizar
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion de la Toma</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <InfoField label="Almacen" value={cab.almacen_nombre || "-"} />
            <InfoField label="Responsable" value={cab.responsable} />
            <InfoField
              label="Fecha Inicio"
              value={formatDate(cab.fecha_inicio)}
            />
            {cab.fecha_fin && (
              <InfoField label="Fecha Fin" value={formatDate(cab.fecha_fin)} />
            )}
            {cab.notas && (
              <div className="sm:col-span-2 lg:col-span-4">
                <InfoField label="Notas" value={cab.notas} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Progress Summary */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <SummaryCard label="Total Items" value={String(totalItems)} />
        <SummaryCard
          label="Contados"
          value={`${itemsContados}/${totalItems}`}
          highlight={todosContados}
        />
        <SummaryCard
          label="Sobrantes"
          value={String(sobrantes)}
          color="text-emerald-700"
        />
        <SummaryCard
          label="Faltantes"
          value={String(faltantes)}
          color="text-red-700"
        />
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-3">
        <div className="h-3 flex-1 rounded-full bg-muted">
          <div
            className="h-3 rounded-full bg-primary transition-all"
            style={{
              width: `${totalItems > 0 ? (itemsContados / totalItems) * 100 : 0}%`,
            }}
          />
        </div>
        <span className="text-sm font-medium">
          {totalItems > 0
            ? Math.round((itemsContados / totalItems) * 100)
            : 0}
          %
        </span>
      </div>

      <Separator />

      {/* Items Table */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Conteo de Productos</h2>

        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>SKU</TableHead>
                <TableHead>Producto</TableHead>
                <TableHead className="text-right">Stock Sistema</TableHead>
                <TableHead className="text-right">Stock Contado</TableHead>
                <TableHead className="text-right">Diferencia</TableHead>
                <TableHead>Observacion</TableHead>
                {canEdit && <TableHead className="w-20" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={canEdit ? 7 : 6}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No hay items en esta toma
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => {
                  const isEditing = editingItem?.id === item.id;
                  const hasDiff = item.diferencia !== 0;

                  return (
                    <TableRow
                      key={item.id}
                      className={
                        item.stock_contado === null
                          ? "bg-amber-50/30"
                          : hasDiff
                            ? item.diferencia > 0
                              ? "bg-emerald-50/30"
                              : "bg-red-50/30"
                            : ""
                      }
                    >
                      <TableCell className="font-mono text-xs">
                        {item.sku}
                      </TableCell>
                      <TableCell className="font-medium">
                        {item.producto_nombre}
                        {item.unidad_medida && (
                          <span className="ml-1 text-xs text-muted-foreground">
                            ({item.unidad_medida})
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {Number(item.stock_sistema).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right">
                        {isEditing ? (
                          <Input
                            type="number"
                            step="0.01"
                            value={editingItem.stock_contado}
                            onChange={(e) =>
                              setEditingItem((prev) =>
                                prev
                                  ? { ...prev, stock_contado: e.target.value }
                                  : null
                              )
                            }
                            className="w-28 text-right"
                            autoFocus
                          />
                        ) : item.stock_contado !== null ? (
                          <span className="font-mono font-semibold">
                            {Number(item.stock_contado).toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-sm italic text-muted-foreground">
                            Sin contar
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {item.stock_contado !== null ? (
                          <span
                            className={`font-mono font-semibold ${
                              item.diferencia > 0
                                ? "text-emerald-700"
                                : item.diferencia < 0
                                  ? "text-red-700"
                                  : "text-muted-foreground"
                            }`}
                          >
                            {item.diferencia > 0 ? "+" : ""}
                            {Number(item.diferencia).toLocaleString()}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input
                            value={editingItem.observacion}
                            onChange={(e) =>
                              setEditingItem((prev) =>
                                prev
                                  ? { ...prev, observacion: e.target.value }
                                  : null
                              )
                            }
                            placeholder="Observacion"
                            className="w-40"
                          />
                        ) : (
                          <span className="text-sm text-muted-foreground">
                            {item.observacion || "-"}
                          </span>
                        )}
                      </TableCell>
                      {canEdit && (
                        <TableCell>
                          {isEditing ? (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={handleSaveItem}
                                disabled={updateItemMutation.isPending}
                              >
                                <Save className="h-4 w-4 text-green-600" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => setEditingItem(null)}
                              >
                                <span className="text-xs text-red-500">✕</span>
                              </Button>
                            </div>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                setEditingItem({
                                  id: item.id,
                                  stock_contado:
                                    item.stock_contado !== null
                                      ? String(item.stock_contado)
                                      : "",
                                  observacion: item.observacion || "",
                                })
                              }
                              className="text-xs"
                            >
                              Contar
                            </Button>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Completar Dialog */}
      <Dialog
        open={showCompletarDialog}
        onOpenChange={(open) => {
          if (!open) setShowCompletarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Completar Toma de Inventario</DialogTitle>
            <DialogDescription>
              Se verificara que todos los {totalItems} items hayan sido contados.
              {itemsConDiferencia > 0 && (
                <span className="mt-1 block font-medium text-amber-700">
                  Se encontraron {itemsConDiferencia} items con diferencias (
                  {sobrantes} sobrantes, {faltantes} faltantes).
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCompletarDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => completarMutation.mutate()}
              disabled={completarMutation.isPending}
            >
              {completarMutation.isPending
                ? "Procesando..."
                : "Completar Toma"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Regularizar Dialog */}
      <Dialog
        open={showRegularizarDialog}
        onOpenChange={(open) => {
          if (!open) setShowRegularizarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regularizar Inventario</DialogTitle>
            <DialogDescription>
              Se generaran vales de ajuste automaticos para corregir las
              diferencias encontradas:
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 rounded-lg bg-muted p-3 text-sm">
            {sobrantes > 0 && (
              <div className="flex items-center gap-2 text-emerald-700">
                <AlertTriangle className="h-4 w-4" />
                <span>
                  {sobrantes} productos con sobrantes → Vale de Ingreso
                  (ajuste)
                </span>
              </div>
            )}
            {faltantes > 0 && (
              <div className="flex items-center gap-2 text-red-700">
                <AlertTriangle className="h-4 w-4" />
                <span>
                  {faltantes} productos con faltantes → Vale de Salida (ajuste)
                </span>
              </div>
            )}
            {sobrantes === 0 && faltantes === 0 && (
              <p className="text-muted-foreground">
                No hay diferencias que regularizar.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRegularizarDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => regularizarMutation.mutate()}
              disabled={
                regularizarMutation.isPending ||
                (sobrantes === 0 && faltantes === 0)
              }
            >
              {regularizarMutation.isPending
                ? "Regularizando..."
                : "Regularizar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-sm">{value}</p>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  highlight,
  color,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  color?: string;
}) {
  return (
    <Card className={highlight ? "border-primary/30 bg-primary/5" : ""}>
      <CardContent className="p-4">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p
          className={`mt-1 text-xl font-bold ${color || (highlight ? "text-primary" : "")}`}
        >
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
