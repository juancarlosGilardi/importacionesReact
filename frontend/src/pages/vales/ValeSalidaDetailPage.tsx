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
  AlertTriangle,
} from "lucide-react";
import type {
  ValeSalida,
  ValeItem,
  Producto,
  PaginatedResponse,
} from "@/lib/types";
import { VALE_ESTADOS, VALE_STATUS_COLORS } from "@/lib/constants";
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

interface ValeSalidaDetailResponse {
  cabecera: ValeSalida;
  items: ValeItem[];
}

interface NewItemForm {
  producto_id: string;
  cantidad: string;
  lote: string;
}

const emptyNewItem: NewItemForm = {
  producto_id: "",
  cantidad: "",
  lote: "",
};

export default function ValeSalidaDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showAddRow, setShowAddRow] = useState(false);
  const [newItem, setNewItem] = useState<NewItemForm>(emptyNewItem);
  const [showCompletarDialog, setShowCompletarDialog] = useState(false);
  const [addError, setAddError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["vale-salida", id],
    queryFn: () =>
      api
        .get<ValeSalidaDetailResponse>(`/api/vales/salida/${id}`)
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
      api.post(`/api/vales/salida/${id}/items`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vale-salida", id] });
      setShowAddRow(false);
      setNewItem(emptyNewItem);
      setAddError("");
    },
    onError: (err: any) => {
      setAddError(
        err.response?.data?.detail || "Error al agregar item. Verifique stock."
      );
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) =>
      api.delete(`/api/vales/salida/${id}/items/${itemId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vale-salida", id] });
    },
  });

  const completarMutation = useMutation({
    mutationFn: () => api.post(`/api/vales/salida/${id}/completar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vale-salida", id] });
      setShowCompletarDialog(false);
    },
  });

  const handleAddItem = () => {
    if (!newItem.producto_id || !newItem.cantidad) return;
    setAddError("");

    const payload: Record<string, unknown> = {
      producto_id: Number(newItem.producto_id),
      cantidad: Number(newItem.cantidad),
    };
    if (newItem.lote) payload.lote = newItem.lote;

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
        Vale de salida no encontrado
      </div>
    );
  }

  const cab = data.cabecera;
  const items = data.items;
  const totalValor = items.reduce((sum, it) => sum + it.costo_total, 0);
  const isBorrador = cab.estado === "borrador";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/vales/salida")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{cab.numero_movimiento}</h1>
            <Badge
              variant="secondary"
              className="bg-rose-100 text-rose-700"
            >
              Salida
            </Badge>
            <Badge
              variant="secondary"
              className={
                VALE_STATUS_COLORS[cab.estado] || "bg-gray-100 text-gray-700"
              }
            >
              {VALE_ESTADOS.find((e) => e.value === cab.estado)?.label ||
                cab.estado}
            </Badge>
          </div>
          {isBorrador && items.length > 0 && (
            <Button onClick={() => setShowCompletarDialog(true)}>
              <CheckCircle className="h-4 w-4" />
              Completar Vale
            </Button>
          )}
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion del Vale</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <InfoField label="Almacen" value={cab.almacen_nombre || "-"} />
            <InfoField label="Concepto" value={cab.concepto_nombre || "-"} />
            <InfoField label="Fecha" value={formatDate(cab.fecha_movimiento)} />
            {cab.solicitante && (
              <InfoField label="Solicitante" value={cab.solicitante} />
            )}
            {cab.centro_costo && (
              <InfoField label="Centro de Costo" value={cab.centro_costo} />
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
          <h2 className="text-lg font-semibold">Items del Vale</h2>
          {isBorrador && (
            <Button
              size="sm"
              onClick={() => {
                setShowAddRow(true);
                setNewItem(emptyNewItem);
                setAddError("");
              }}
              disabled={showAddRow}
            >
              <Plus className="h-4 w-4" />
              Agregar Item
            </Button>
          )}
        </div>

        {addError && (
          <div className="flex items-center gap-2 rounded-md bg-red-50 p-3 text-sm text-red-700">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {addError}
          </div>
        )}

        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[180px]">Producto</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">Costo Unit.</TableHead>
                <TableHead className="text-right">Costo Total</TableHead>
                <TableHead className="text-right">Stock Disp.</TableHead>
                <TableHead>Lote</TableHead>
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
                        setNewItem((prev) => ({ ...prev, producto_id: val ?? "" }))
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
                  <TableCell className="text-right text-sm text-muted-foreground">
                    Auto
                  </TableCell>
                  <TableCell className="text-right text-sm text-muted-foreground">
                    Auto
                  </TableCell>
                  <TableCell className="text-right text-sm text-muted-foreground">
                    -
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
                          setAddError("");
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
                    No hay items en este vale. Agregue productos para continuar.
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">
                      <div>
                        {item.producto_nombre ||
                          (item.sku
                            ? item.sku
                            : `Producto #${item.producto_id}`)}
                      </div>
                      {item.sku && item.producto_nombre && (
                        <div className="text-xs text-muted-foreground">
                          {item.sku}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {item.cantidad}
                      {item.unidad_medida && (
                        <span className="ml-1 text-xs text-muted-foreground">
                          {item.unidad_medida}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.costo_unitario)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.costo_total)}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.stock_disponible != null ? (
                        <span
                          className={
                            item.stock_disponible < item.cantidad
                              ? "font-semibold text-red-600"
                              : "text-muted-foreground"
                          }
                        >
                          {item.stock_disponible}
                        </span>
                      ) : (
                        "-"
                      )}
                    </TableCell>
                    <TableCell>{item.lote || "-"}</TableCell>
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
              value={String(cab.total_productos || items.length)}
            />
            <SummaryItem
              label="Total"
              value={formatCurrency(cab.total || totalValor)}
              highlight
            />
            <SummaryItem
              label="Estado"
              value={
                VALE_ESTADOS.find((e) => e.value === cab.estado)?.label ||
                cab.estado
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Completar dialog */}
      <Dialog
        open={showCompletarDialog}
        onOpenChange={(open) => {
          if (!open) setShowCompletarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Completar Vale de Salida</DialogTitle>
            <DialogDescription>
              Esta seguro de completar este vale? Se descontara el inventario
              con los {items.length} productos del vale. Se validara que haya
              stock suficiente. Esta accion no se puede deshacer.
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
