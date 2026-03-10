import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Pencil,
  Plus,
  Trash2,
  Check,
  X,
  ChevronDown,
  ArrowLeft,
} from "lucide-react";
import type {
  OrdenCompraDetalle,
  OrdenCompraItem,
  Producto,
  PaginatedResponse,
} from "@/lib/types";
import { STATUS_COLORS, STATUS_LABELS, UNIDADES_MEDIDA } from "@/lib/constants";
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const ESTADO_TRANSITIONS: Record<string, string[]> = {
  borrador: ["confirmada", "cancelada"],
  confirmada: ["en_transito", "cancelada"],
  en_transito: ["en_aduana", "cancelada"],
  en_aduana: ["completada", "cancelada"],
  completada: [],
  cancelada: [],
};

interface NewItemForm {
  producto_id: string;
  cantidad: string;
  precio_unitario: string;
  unidad_medida: string;
  peso_kg: string;
  volumen_m3: string;
}

const emptyNewItem: NewItemForm = {
  producto_id: "",
  cantidad: "",
  precio_unitario: "",
  unidad_medida: "UND",
  peso_kg: "",
  volumen_m3: "",
};

interface EditItemForm {
  cantidad: string;
  precio_unitario: string;
  peso_kg: string;
  volumen_m3: string;
}

export default function OrdenDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showAddRow, setShowAddRow] = useState(false);
  const [newItem, setNewItem] = useState<NewItemForm>(emptyNewItem);
  const [editingItemId, setEditingItemId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<EditItemForm>({
    cantidad: "",
    precio_unitario: "",
    peso_kg: "",
    volumen_m3: "",
  });

  const { data, isLoading } = useQuery({
    queryKey: ["orden", id],
    queryFn: () =>
      api.get<OrdenCompraDetalle>(`/api/ordenes/${id}`).then((r) => r.data),
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

  const changeEstadoMutation = useMutation({
    mutationFn: (estado: string) =>
      api.patch(`/api/ordenes/${id}/estado`, { estado }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orden", id] });
    },
  });

  const addItemMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post(`/api/ordenes/${id}/items`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orden", id] });
      setShowAddRow(false);
      setNewItem(emptyNewItem);
    },
  });

  const updateItemMutation = useMutation({
    mutationFn: ({
      itemId,
      payload,
    }: {
      itemId: number;
      payload: Record<string, unknown>;
    }) => api.put(`/api/ordenes/items/${itemId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orden", id] });
      setEditingItemId(null);
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) => api.delete(`/api/ordenes/items/${itemId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orden", id] });
    },
  });

  const handleAddItem = () => {
    if (!newItem.producto_id || !newItem.cantidad || !newItem.precio_unitario)
      return;

    const payload: Record<string, unknown> = {
      producto_id: Number(newItem.producto_id),
      cantidad: Number(newItem.cantidad),
      precio_unitario: Number(newItem.precio_unitario),
      unidad_medida: newItem.unidad_medida,
    };
    if (newItem.peso_kg) payload.peso_kg = Number(newItem.peso_kg);
    if (newItem.volumen_m3) payload.volumen_m3 = Number(newItem.volumen_m3);

    addItemMutation.mutate(payload);
  };

  const handleStartEdit = (item: OrdenCompraItem) => {
    setEditingItemId(item.id);
    setEditForm({
      cantidad: String(item.cantidad),
      precio_unitario: String(item.precio_unitario),
      peso_kg: item.peso_kg != null ? String(item.peso_kg) : "",
      volumen_m3: item.volumen_m3 != null ? String(item.volumen_m3) : "",
    });
  };

  const handleSaveEdit = () => {
    if (!editingItemId) return;

    const payload: Record<string, unknown> = {
      cantidad: Number(editForm.cantidad),
      precio_unitario: Number(editForm.precio_unitario),
    };
    if (editForm.peso_kg) payload.peso_kg = Number(editForm.peso_kg);
    if (editForm.volumen_m3) payload.volumen_m3 = Number(editForm.volumen_m3);

    updateItemMutation.mutate({ itemId: editingItemId, payload });
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
        Orden no encontrada
      </div>
    );
  }

  const cab = data.cabecera;
  const items = data.items;
  const totalFob = items.reduce((sum, it) => sum + (it.valor_fob || 0), 0);
  const availableTransitions = ESTADO_TRANSITIONS[cab.estado] || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/ordenes")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">
              {cab.numero_oc || cab.numero}
            </h1>
            <Badge
              variant="secondary"
              className={STATUS_COLORS[cab.estado] || "bg-gray-100 text-gray-700"}
            >
              {STATUS_LABELS[cab.estado] || cab.estado}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              render={<Link to={`/ordenes/${id}/editar`} />}
            >
              <Pencil className="h-4 w-4" />
              Editar
            </Button>
            {availableTransitions.length > 0 && (
              <DropdownMenu>
                <DropdownMenuTrigger
                  render={<Button variant="outline" />}
                >
                  Cambiar Estado
                  <ChevronDown className="h-4 w-4" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {availableTransitions.map((est) => (
                    <DropdownMenuItem
                      key={est}
                      onClick={() => changeEstadoMutation.mutate(est)}
                    >
                      <Badge
                        variant="secondary"
                        className={STATUS_COLORS[est] || "bg-gray-100 text-gray-700"}
                      >
                        {STATUS_LABELS[est] || est}
                      </Badge>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion General</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <InfoField label="Proveedor" value={cab.proveedor_nombre || "-"} />
            <InfoField label="RUC Proveedor" value={cab.proveedor_ruc || "-"} />
            <InfoField
              label="Fecha de Orden"
              value={cab.fecha_orden ? formatDate(cab.fecha_orden) : "-"}
            />
            <InfoField
              label="Fecha Llegada Est."
              value={
                cab.fecha_llegada_est
                  ? formatDate(cab.fecha_llegada_est)
                  : "-"
              }
            />
            <InfoField label="Incoterm" value={cab.incoterm || "-"} />
            <InfoField
              label="Moneda"
              value={cab.moneda_codigo || cab.moneda || "-"}
            />
            <InfoField
              label="Tipo de Cambio"
              value={cab.tipo_cambio ? String(cab.tipo_cambio) : "-"}
            />
            <InfoField
              label="Puerto de Embarque"
              value={cab.puerto_embarque || "-"}
            />
            <InfoField
              label="Puerto de Destino"
              value={cab.puerto_destino || "-"}
            />
            <InfoField
              label="Agente Aduanero"
              value={cab.agente_aduanero || "-"}
            />
            <InfoField
              label="Agente de Carga"
              value={cab.agente_carga || "-"}
            />
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
          <h2 className="text-lg font-semibold">Items de la Orden</h2>
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
        </div>

        <div className="rounded-lg border bg-white">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="min-w-[180px]">Producto</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">Precio Unit.</TableHead>
                <TableHead className="text-right">Valor FOB</TableHead>
                <TableHead className="text-right">Peso (kg)</TableHead>
                <TableHead className="text-right">Volumen (m3)</TableHead>
                <TableHead className="w-24" />
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
                      value={newItem.precio_unitario}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          precio_unitario: e.target.value,
                        }))
                      }
                      placeholder="0.0000"
                      className="w-28 text-right"
                    />
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {newItem.cantidad && newItem.precio_unitario
                      ? formatCurrency(
                          Number(newItem.cantidad) *
                            Number(newItem.precio_unitario)
                        )
                      : "-"}
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={newItem.peso_kg}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          peso_kg: e.target.value,
                        }))
                      }
                      placeholder="0.00"
                      className="w-24 text-right"
                    />
                  </TableCell>
                  <TableCell>
                    <Input
                      type="number"
                      step="0.01"
                      value={newItem.volumen_m3}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          volumen_m3: e.target.value,
                        }))
                      }
                      placeholder="0.00"
                      className="w-24 text-right"
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
                    colSpan={7}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No hay items en esta orden
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) =>
                  editingItemId === item.id ? (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        {item.producto_nombre ||
                          (item.producto_sku
                            ? `${item.producto_sku}`
                            : `Producto #${item.producto_id}`)}
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          value={editForm.cantidad}
                          onChange={(e) =>
                            setEditForm((prev) => ({
                              ...prev,
                              cantidad: e.target.value,
                            }))
                          }
                          className="w-24 text-right"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.0001"
                          value={editForm.precio_unitario}
                          onChange={(e) =>
                            setEditForm((prev) => ({
                              ...prev,
                              precio_unitario: e.target.value,
                            }))
                          }
                          className="w-28 text-right"
                        />
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm text-muted-foreground">
                        {editForm.cantidad && editForm.precio_unitario
                          ? formatCurrency(
                              Number(editForm.cantidad) *
                                Number(editForm.precio_unitario)
                            )
                          : "-"}
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          value={editForm.peso_kg}
                          onChange={(e) =>
                            setEditForm((prev) => ({
                              ...prev,
                              peso_kg: e.target.value,
                            }))
                          }
                          className="w-24 text-right"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          value={editForm.volumen_m3}
                          onChange={(e) =>
                            setEditForm((prev) => ({
                              ...prev,
                              volumen_m3: e.target.value,
                            }))
                          }
                          className="w-24 text-right"
                        />
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={handleSaveEdit}
                            disabled={updateItemMutation.isPending}
                          >
                            <Check className="h-4 w-4 text-green-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => setEditingItemId(null)}
                          >
                            <X className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">
                        {item.producto_nombre ||
                          (item.producto_sku
                            ? `${item.producto_sku}`
                            : `Producto #${item.producto_id}`)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {item.cantidad}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(item.precio_unitario)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {formatCurrency(item.valor_fob)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-muted-foreground">
                        {item.peso_kg != null ? item.peso_kg : "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-muted-foreground">
                        {item.volumen_m3 != null ? item.volumen_m3 : "-"}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => handleStartEdit(item)}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            onClick={() => deleteItemMutation.mutate(item.id)}
                            disabled={deleteItemMutation.isPending}
                          >
                            <Trash2 className="h-3.5 w-3.5 text-red-500" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                )
              )}

              {/* Total FOB row */}
              {items.length > 0 && (
                <TableRow className="bg-muted/50 font-semibold">
                  <TableCell colSpan={3} className="text-right">
                    Total FOB
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(totalFob)}
                  </TableCell>
                  <TableCell colSpan={3} />
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen de Costos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <SummaryItem
              label="Total FOB"
              value={formatCurrency(cab.total_fob || totalFob)}
            />
            <SummaryItem
              label="Total Flete"
              value={formatCurrency(cab.total_flete || 0)}
            />
            <SummaryItem
              label="Total Seguro"
              value={formatCurrency(cab.total_seguro || 0)}
            />
            <SummaryItem
              label="Total CIF"
              value={formatCurrency(cab.total_cif || 0)}
              highlight
            />
          </div>
        </CardContent>
      </Card>
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
