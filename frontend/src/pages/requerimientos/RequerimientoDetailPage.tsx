import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Plus,
  Check,
  X,
  Trash2,
  Signature,
  Forward,
  Lock,
} from "lucide-react";
import type {
  Requerimiento,
  RequerimientoItem,
  Producto,
  PaginatedResponse,
} from "@/lib/types";
import {
  REQ_ESTADOS,
  REQ_STATUS_COLORS,
  REQ_PRIORIDADES,
  REQ_PRIORIDAD_COLORS,
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

interface RequerimientoDetailResponse {
  cabecera: Requerimiento;
  items: RequerimientoItem[];
}

interface NewItemForm {
  producto_id: string;
  cantidad: string;
  precio_estimado: string;
  notas: string;
}

const emptyNewItem: NewItemForm = {
  producto_id: "",
  cantidad: "",
  precio_estimado: "",
  notas: "",
};

export default function RequerimientoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [showAddRow, setShowAddRow] = useState(false);
  const [newItem, setNewItem] = useState<NewItemForm>(emptyNewItem);
  const [showFirmarDialog, setShowFirmarDialog] = useState(false);
  const [showDerivarDialog, setShowDerivarDialog] = useState(false);
  const [showCerrarDialog, setShowCerrarDialog] = useState(false);
  const [firmadoPor, setFirmadoPor] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["requerimiento", id],
    queryFn: () =>
      api
        .get<RequerimientoDetailResponse>(`/api/requerimientos/${id}`)
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
      api.post(`/api/requerimientos/${id}/items`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requerimiento", id] });
      setShowAddRow(false);
      setNewItem(emptyNewItem);
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: number) =>
      api.delete(`/api/requerimientos/${id}/items/${itemId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requerimiento", id] });
    },
  });

  const firmarMutation = useMutation({
    mutationFn: () =>
      api.post(`/api/requerimientos/${id}/firmar`, {
        firmado_por: firmadoPor,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requerimiento", id] });
      setShowFirmarDialog(false);
    },
  });

  const derivarMutation = useMutation({
    mutationFn: () => api.post(`/api/requerimientos/${id}/derivar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requerimiento", id] });
      setShowDerivarDialog(false);
    },
  });

  const cerrarMutation = useMutation({
    mutationFn: () => api.post(`/api/requerimientos/${id}/cerrar`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["requerimiento", id] });
      setShowCerrarDialog(false);
    },
  });

  const handleAddItem = () => {
    if (!newItem.producto_id || !newItem.cantidad) return;
    const payload: Record<string, unknown> = {
      producto_id: Number(newItem.producto_id),
      cantidad: Number(newItem.cantidad),
    };
    if (newItem.precio_estimado)
      payload.precio_estimado = Number(newItem.precio_estimado);
    if (newItem.notas) payload.notas = newItem.notas;
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

  if (!data?.cabecera) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Requerimiento no encontrado
      </div>
    );
  }

  const cab = data.cabecera;
  const items = data.items;
  const totalValor = items.reduce((sum, it) => sum + it.total, 0);
  const isAbierto = cab.estado === "abierto";
  const isFirmado = cab.estado === "firmado";
  const isDerivado = cab.estado === "derivado";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => navigate("/requerimientos")}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex flex-1 items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{cab.numero}</h1>
            <Badge
              variant="secondary"
              className={
                REQ_PRIORIDAD_COLORS[cab.prioridad] ||
                "bg-gray-100 text-gray-700"
              }
            >
              {REQ_PRIORIDADES.find((p) => p.value === cab.prioridad)?.label ||
                cab.prioridad}
            </Badge>
            <Badge
              variant="secondary"
              className={
                REQ_STATUS_COLORS[cab.estado] || "bg-gray-100 text-gray-700"
              }
            >
              {REQ_ESTADOS.find((e) => e.value === cab.estado)?.label ||
                cab.estado}
            </Badge>
          </div>
          <div className="flex gap-2">
            {isAbierto && items.length > 0 && (
              <Button onClick={() => setShowFirmarDialog(true)}>
                <Signature className="h-4 w-4" />
                Firmar
              </Button>
            )}
            {isFirmado && (
              <Button
                variant="secondary"
                onClick={() => setShowDerivarDialog(true)}
              >
                <Forward className="h-4 w-4" />
                Derivar
              </Button>
            )}
            {(isFirmado || isDerivado) && (
              <Button
                variant="outline"
                onClick={() => setShowCerrarDialog(true)}
              >
                <Lock className="h-4 w-4" />
                Cerrar
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Informacion del Requerimiento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <InfoField label="Solicitante" value={cab.solicitante} />
            <InfoField label="Fecha" value={formatDate(cab.fecha)} />
            <InfoField
              label="Prioridad"
              value={
                REQ_PRIORIDADES.find((p) => p.value === cab.prioridad)?.label ||
                cab.prioridad
              }
            />
            {cab.almacen_nombre && (
              <InfoField label="Almacen" value={cab.almacen_nombre} />
            )}
            {cab.centro_costo && (
              <InfoField label="Centro de Costo" value={cab.centro_costo} />
            )}
            {cab.proveedor_nombre && (
              <InfoField
                label="Proveedor Sugerido"
                value={cab.proveedor_nombre}
              />
            )}
            {cab.firmado_por && (
              <InfoField label="Firmado por" value={cab.firmado_por} />
            )}
            {cab.fecha_firma && (
              <InfoField
                label="Fecha de Firma"
                value={formatDate(cab.fecha_firma)}
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
          <h2 className="text-lg font-semibold">Items del Requerimiento</h2>
          {isAbierto && (
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
                <TableHead className="text-right">Precio Est.</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead>Notas</TableHead>
                {isAbierto && <TableHead className="w-20" />}
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
                      step="0.01"
                      value={newItem.precio_estimado}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          precio_estimado: e.target.value,
                        }))
                      }
                      placeholder="0.00"
                      className="w-28 text-right"
                    />
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm text-muted-foreground">
                    {newItem.cantidad && newItem.precio_estimado
                      ? formatCurrency(
                          Number(newItem.cantidad) *
                            Number(newItem.precio_estimado)
                        )
                      : "-"}
                  </TableCell>
                  <TableCell>
                    <Input
                      value={newItem.notas}
                      onChange={(e) =>
                        setNewItem((prev) => ({
                          ...prev,
                          notas: e.target.value,
                        }))
                      }
                      placeholder="Notas"
                      className="w-32"
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
                    colSpan={isAbierto ? 6 : 5}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No hay items. Agregue productos para continuar.
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
                      {formatCurrency(item.precio_estimado)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.total)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {item.notas || "-"}
                    </TableCell>
                    {isAbierto && (
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
                    Total Estimado
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(totalValor)}
                  </TableCell>
                  <TableCell colSpan={isAbierto ? 2 : 1} />
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Summary Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <SummaryItem
              label="Total Items"
              value={String(items.length)}
            />
            <SummaryItem
              label="Valor Estimado"
              value={formatCurrency(totalValor)}
              highlight
            />
            <SummaryItem
              label="Prioridad"
              value={
                REQ_PRIORIDADES.find((p) => p.value === cab.prioridad)?.label ||
                cab.prioridad
              }
            />
            <SummaryItem
              label="Estado"
              value={
                REQ_ESTADOS.find((e) => e.value === cab.estado)?.label ||
                cab.estado
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Firmar Dialog */}
      <Dialog
        open={showFirmarDialog}
        onOpenChange={(open) => {
          if (!open) setShowFirmarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Firmar Requerimiento</DialogTitle>
            <DialogDescription>
              Al firmar, el requerimiento quedara aprobado y no se podran
              modificar los items.
            </DialogDescription>
          </DialogHeader>
          <div>
            <label className="text-sm font-medium">Firmado por</label>
            <Input
              value={firmadoPor}
              onChange={(e) => setFirmadoPor(e.target.value)}
              placeholder="Nombre de quien firma"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowFirmarDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => firmarMutation.mutate()}
              disabled={firmarMutation.isPending || !firmadoPor.trim()}
            >
              {firmarMutation.isPending ? "Firmando..." : "Firmar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Derivar Dialog */}
      <Dialog
        open={showDerivarDialog}
        onOpenChange={(open) => {
          if (!open) setShowDerivarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Derivar Requerimiento</DialogTitle>
            <DialogDescription>
              Derivar este requerimiento al area de compras para su
              procesamiento.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDerivarDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => derivarMutation.mutate()}
              disabled={derivarMutation.isPending}
            >
              {derivarMutation.isPending ? "Derivando..." : "Derivar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cerrar Dialog */}
      <Dialog
        open={showCerrarDialog}
        onOpenChange={(open) => {
          if (!open) setShowCerrarDialog(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cerrar Requerimiento</DialogTitle>
            <DialogDescription>
              Cerrar este requerimiento. Esta accion indica que ya fue atendido.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCerrarDialog(false)}
            >
              Cancelar
            </Button>
            <Button
              onClick={() => cerrarMutation.mutate()}
              disabled={cerrarMutation.isPending}
            >
              {cerrarMutation.isPending ? "Cerrando..." : "Cerrar"}
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
