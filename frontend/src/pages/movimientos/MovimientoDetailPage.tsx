import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Plus,
  Check,
  X,
  Trash2,
  CheckCircle,
} from "lucide-react";
import type {
  MovimientoAlmacen,
  MovimientoDetalle,
  Producto,
  PaginatedResponse,
} from "@/lib/types";
import {
  TIPO_MOVIMIENTO_COLORS,
  TIPO_MOVIMIENTO_LABELS,
  MOVIMIENTO_STATUS_COLORS,
  MOVIMIENTO_ESTADOS,
} from "@/lib/constants";
import { formatCurrency, formatDate } from "@/lib/utils";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface MovimientoDetailResponse {
  cabecera: MovimientoAlmacen;
  detalle: MovimientoDetalle[];
}

interface NewItemForm {
  producto_id: string;
  cantidad: string;
  costo_unitario: string;
  lote: string;
  fecha_vencimiento: string;
  ubicacion: string;
}

const emptyNewItem: NewItemForm = {
  producto_id: "",
  cantidad: "",
  costo_unitario: "",
  lote: "",
  fecha_vencimiento: "",
  ubicacion: "",
};

export default function MovimientoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showAddRow, setShowAddRow] = useState(false);
  const [newItem, setNewItem] = useState<NewItemForm>(emptyNewItem);
  const [showCompletarDialog, setShowCompletarDialog] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["movimiento", id],
    queryFn: () =>
      api
        .get<MovimientoDetailResponse>(`/api/inventario/movimientos/${id}`)
        .then((r) => r.data),
  });

  const { data: productos } = useQuery({
    queryKey: ["productos-list"],
    queryFn: () =>
      api
        .get<PaginatedResponse<Producto>>("/api/productos", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const addItemMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post(`/api/inventario/movimientos/${id}/items`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movimiento", id] });
      setShowAddRow(false);
      setNewItem(emptyNewItem);
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) =>
      api.delete(`/api/inventario/movimientos/${id}/items/${itemId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movimiento", id] });
    },
  });

  const completarMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/inventario/movimientos/${id}/completar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["movimiento", id] });
      setShowCompletarDialog(false);
    },
  });

  const handleAddItem = () => {
    if (!newItem.producto_id || !newItem.cantidad || !newItem.costo_unitario)
      return;

    const payload: Record<string, unknown> = {
      producto_id: Number(newItem.producto_id),
      cantidad: Number(newItem.cantidad),
      costo_unitario: Number(newItem.costo_unitario),
    };
    if (newItem.lote) payload.lote = newItem.lote;
    if (newItem.fecha_vencimiento) payload.fecha_vencimiento = newItem.fecha_vencimiento;
    if (newItem.ubicacion) payload.ubicacion = newItem.ubicacion;

    addItemMutation.mutate(payload);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-64 animate-pulse rounded bg-muted" />
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Movimiento no encontrado
      </div>
    );
  }

  const cab = data.cabecera;
  const items = data.detalle;
  const totalValor = items.reduce((sum, it) => sum + it.costo_total, 0);
  const isBorrador = cab.estado === "borrador";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/movimientos")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{cab.numero_movimiento}</h1>
            <Badge
              variant="secondary"
              className={TIPO_MOVIMIENTO_COLORS[cab.tipo_movimiento] || "bg-gray-100 text-gray-700"}
            >
              {TIPO_MOVIMIENTO_LABELS[cab.tipo_movimiento] || cab.tipo_movimiento}
            </Badge>
            <Badge
              variant="secondary"
              className={MOVIMIENTO_STATUS_COLORS[cab.estado] || "bg-gray-100 text-gray-700"}
            >
              {MOVIMIENTO_ESTADOS.find((e) => e.value === cab.estado)?.label || cab.estado}
            </Badge>
          </div>
          {isBorrador && (
            <Button onClick={() => setShowCompletarDialog(true)}>
              <CheckCircle className="h-4 w-4" />
              Completar Movimiento
            </Button>
          )}
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion del Movimiento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <InfoField
              label="Tipo"
              value={TIPO_MOVIMIENTO_LABELS[cab.tipo_movimiento] || cab.tipo_movimiento}
            />
            <InfoField
              label="Fecha"
              value={formatDate(cab.fecha_movimiento)}
            />
            {cab.almacen_nombre && (
              <InfoField
                label={cab.tipo_movimiento === "transferencia" ? "Almacen Origen" : "Almacen"}
                value={cab.almacen_nombre}
              />
            )}
            {cab.almacen_destino_nombre && (
              <InfoField
                label="Almacen Destino"
                value={cab.almacen_destino_nombre}
              />
            )}
            {cab.oc_numero && (
              <InfoField label="Orden de Compra" value={cab.oc_numero} />
            )}
            {cab.documento_referencia && (
              <InfoField
                label="Documento Referencia"
                value={cab.documento_referencia}
              />
            )}
            {cab.notas && (
              <div className="sm:col-span-2 lg:col-span-3">
                <InfoField label="Notas" value={cab.notas} />
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Separator />

      {/* Items Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Items del Movimiento</h2>
          {isBorrador && (
            <Button
              size="sm"
              onClick={() => {
                setShowAddRow(true);
                setNewItem(emptyNewItem);
              }}
              disabled={showAddRow}
            >
              <Plus className="h-4 w-4" />
              Agregar Item
            </Button>
          )}
        </div>

        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[180px]">Producto</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">Costo Unit.</TableHead>
                <TableHead className="text-right">Costo Total</TableHead>
                <TableHead>Lote</TableHead>
                <TableHead>Ubicacion</TableHead>
                {isBorrador && <TableHead className="w-20" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Add item row */}
              {showAddRow && (
                <TableRow>
                  <TableCell>
                    <Select
                      value={newItem.producto_id}
                      onValueChange={(val) =>
                        setNewItem((prev) => ({ ...prev, producto_id: val }))
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Seleccionar producto" />
                      </SelectTrigger>
                      <SelectContent>
                        {productos?.items.map((prod) => (
                          <SelectItem key={prod.id} value={String(prod.id)}>
                            {prod.sku} - {prod.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={newItem.cantidad}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          cantidad: e.target.value,
                        }))
                      }
                      placeholder="0.00"
                      className="w-24 text-right"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.0001"
                      value={newItem.costo_unitario}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          costo_unitario: e.target.value,
                        }))
                      }
                      placeholder="0.0000"
                      className="w-28 text-right"
                    />
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {newItem.cantidad && newItem.costo_unitario
                      ? formatCurrency(
                          Number(newItem.cantidad) * Number(newItem.costo_unitario)
                        )
                      : "-"}
                  </TableCell>
                  <TableCell>
                    <Input
                      value={newItem.lote}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          lote: e.target.value,
                        }))
                      }
                      placeholder="Lote"
                      className="w-24"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      value={newItem.ubicacion}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          ubicacion: e.target.value,
                        }))
                      }
                      placeholder="Ubicacion"
                      className="w-24"
                    />
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={handleAddItem}
                        disabled={addItemMutation.isPending}
                      >
                        <Check className="h-4 w-4 text-green-600" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => {
                          setShowAddRow(false);
                          setNewItem(emptyNewItem);
                        }}
                      >
                        <X className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )}

              {/* Existing items */}
              {items.length === 0 && !showAddRow ? (
                <TableRow>
                  <TableCell
                    colSpan={isBorrador ? 7 : 6}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No hay items en este movimiento
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">
                      {item.producto_nombre ||
                        (item.producto_sku
                          ? item.producto_sku
                          : `Producto #${item.producto_id}`)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {item.cantidad}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.costo_unitario)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.costo_total)}
                    </TableCell>
                    <TableCell>{item.lote || "-"}</TableCell>
                    <TableCell>{item.ubicacion || "-"}</TableCell>
                    {isBorrador && (
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => deleteItemMutation.mutate(item.id)}
                          disabled={deleteItemMutation.isPending}
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-500" />
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                ))
              )}

              {/* Total row */}
              {items.length > 0 && (
                <TableRow className="bg-muted/50 font-semibold">
                  <TableCell colSpan={3} className="text-right">
                    Total
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(totalValor)}
                  </TableCell>
                  <TableCell colSpan={isBorrador ? 3 : 2} />
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Value Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <SummaryItem
              label="Total Productos"
              value={String(cab.total_productos)}
            />
            <SummaryItem
              label="Valor Total"
              value={formatCurrency(cab.valor_total || totalValor)}
              highlight
            />
            <SummaryItem
              label="Estado"
              value={MOVIMIENTO_ESTADOS.find((e) => e.value === cab.estado)?.label || cab.estado}
            />
          </div>
        </CardContent>
      </Card>

      {/* Completar dialog */}
      <Dialog
        open={showCompletarDialog}
        onOpenChange={(open) => { if (!open) setShowCompletarDialog(false); }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Completar Movimiento</DialogTitle>
            <DialogDescription>
              Esta seguro de que desea completar este movimiento? Esta accion
              actualizara el inventario y no se podra deshacer.
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
                : "Confirmar y Completar"}
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

function SummaryItem({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border p-3 ${highlight ? "border-primary/30 bg-primary/5" : ""}`}
    >
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p
        className={`mt-1 font-mono text-lg font-semibold ${highlight ? "text-primary" : ""}`}
      >
        {value}
      </p>
    </div>
  );
}
