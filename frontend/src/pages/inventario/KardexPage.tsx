import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Printer, BookOpen } from "lucide-react";
import type { KardexEntry, Producto, Almacen } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
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

interface ProductosResponse {
  items: Producto[];
  total: number;
}

export default function KardexPage() {
  const [productoId, setProductoId] = useState("");
  const [almacenId, setAlmacenId] = useState("");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");
  const [queryParams, setQueryParams] = useState<{
    producto_id: string;
    almacen_id: string;
    fecha_desde: string;
    fecha_hasta: string;
  } | null>(null);

  const { data: productos } = useQuery({
    queryKey: ["productos-kardex"],
    queryFn: () =>
      api
        .get<ProductosResponse>("/api/productos", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes-kardex"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes").then((r) => r.data),
  });

  const {
    data: kardexEntries,
    isLoading,
    isFetching,
  } = useQuery({
    queryKey: ["kardex", queryParams],
    queryFn: () =>
      api
        .get<KardexEntry[]>("/api/inventario/kardex", {
          params: {
            producto_id: queryParams!.producto_id,
            almacen_id: queryParams!.almacen_id || undefined,
            fecha_desde: queryParams!.fecha_desde || undefined,
            fecha_hasta: queryParams!.fecha_hasta || undefined,
          },
        })
        .then((r) => r.data),
    enabled: !!queryParams?.producto_id,
  });

  const handleConsultar = () => {
    if (!productoId) return;
    setQueryParams({
      producto_id: productoId,
      almacen_id: almacenId,
      fecha_desde: fechaDesde,
      fecha_hasta: fechaHasta,
    });
  };

  const handlePrint = () => {
    window.print();
  };

  const selectedProducto = productos?.items.find(
    (p) => String(p.id) === productoId
  );

  // Compute totals
  const totals = kardexEntries?.reduce(
    (acc, entry) => ({
      cantidad_entrada: acc.cantidad_entrada + entry.cantidad_entrada,
      costo_total_entrada: acc.costo_total_entrada + entry.costo_total_entrada,
      cantidad_salida: acc.cantidad_salida + entry.cantidad_salida,
      costo_total_salida: acc.costo_total_salida + entry.costo_total_salida,
    }),
    {
      cantidad_entrada: 0,
      costo_total_entrada: 0,
      cantidad_salida: 0,
      costo_total_salida: 0,
    }
  );

  const lastEntry = kardexEntries?.length
    ? kardexEntries[kardexEntries.length - 1]
    : null;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BookOpen className="h-7 w-7 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold">Kardex SUNAT</h1>
            <p className="text-sm text-muted-foreground">
              Registro permanente de inventario valorizado - Formato SUNAT
            </p>
          </div>
        </div>
        {kardexEntries && kardexEntries.length > 0 && (
          <Button variant="outline" onClick={handlePrint}>
            <Printer className="h-4 w-4" />
            Imprimir
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="rounded-lg border bg-white p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div className="min-w-[240px] flex-1">
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Producto *
            </label>
            <Select
              value={productoId}
              onValueChange={(val) => setProductoId(val)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleccionar producto" />
              </SelectTrigger>
              <SelectContent>
                {productos?.items.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.sku} - {p.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="min-w-[180px]">
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Almacen
            </label>
            <Select
              value={almacenId}
              onValueChange={(val) =>
                setAlmacenId(val === "__all__" ? "" : val)
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Todos" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__all__">Todos</SelectItem>
                {almacenes?.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="min-w-[150px]">
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Desde
            </label>
            <Input
              type="date"
              value={fechaDesde}
              onChange={(e) => setFechaDesde(e.target.value)}
            />
          </div>

          <div className="min-w-[150px]">
            <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
              Hasta
            </label>
            <Input
              type="date"
              value={fechaHasta}
              onChange={(e) => setFechaHasta(e.target.value)}
            />
          </div>

          <Button onClick={handleConsultar} disabled={!productoId}>
            <Search className="h-4 w-4" />
            Consultar
          </Button>
        </div>
      </div>

      {/* Empty state */}
      {!queryParams && (
        <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20 p-16">
          <BookOpen className="mb-4 h-12 w-12 text-muted-foreground/40" />
          <p className="text-lg font-medium text-muted-foreground">
            Seleccione un producto para consultar
          </p>
          <p className="mt-1 text-sm text-muted-foreground/70">
            Elija un producto y presione "Consultar" para ver el Kardex
          </p>
        </div>
      )}

      {/* Kardex table */}
      {queryParams && (
        <div className="rounded-lg border bg-white print:border-black">
          {/* Print header info */}
          {selectedProducto && (
            <div className="border-b px-4 py-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">Producto</p>
                  <p className="font-semibold">
                    {selectedProducto.sku} - {selectedProducto.nombre}
                  </p>
                </div>
                <div className="text-right text-sm text-muted-foreground">
                  {fechaDesde && (
                    <span>Desde: {formatDate(fechaDesde)} </span>
                  )}
                  {fechaHasta && <span>Hasta: {formatDate(fechaHasta)}</span>}
                </div>
              </div>
            </div>
          )}

          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead rowSpan={2} className="border-r text-center align-middle">
                  Fecha
                </TableHead>
                <TableHead rowSpan={2} className="border-r text-center align-middle">
                  Tipo
                </TableHead>
                <TableHead rowSpan={2} className="border-r text-center align-middle">
                  Doc. Referencia
                </TableHead>
                <TableHead
                  colSpan={3}
                  className="border-r border-b text-center text-xs font-bold text-green-700"
                >
                  ENTRADAS
                </TableHead>
                <TableHead
                  colSpan={3}
                  className="border-r border-b text-center text-xs font-bold text-red-700"
                >
                  SALIDAS
                </TableHead>
                <TableHead
                  colSpan={3}
                  className="border-b text-center text-xs font-bold text-blue-700"
                >
                  SALDO
                </TableHead>
              </TableRow>
              <TableRow className="bg-muted/20">
                {/* Entradas */}
                <TableHead className="border-r text-center text-xs">
                  Cantidad
                </TableHead>
                <TableHead className="border-r text-center text-xs">
                  C.U.
                </TableHead>
                <TableHead className="border-r text-center text-xs">
                  C.T.
                </TableHead>
                {/* Salidas */}
                <TableHead className="border-r text-center text-xs">
                  Cantidad
                </TableHead>
                <TableHead className="border-r text-center text-xs">
                  C.U.
                </TableHead>
                <TableHead className="border-r text-center text-xs">
                  C.T.
                </TableHead>
                {/* Saldo */}
                <TableHead className="text-center text-xs">Cantidad</TableHead>
                <TableHead className="text-center text-xs">C.U.</TableHead>
                <TableHead className="text-center text-xs">C.T.</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading || isFetching ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    {Array.from({ length: 12 }).map((_, j) => (
                      <TableCell key={j}>
                        <div className="h-4 w-16 animate-pulse rounded bg-muted" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : !kardexEntries || kardexEntries.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={12}
                    className="py-8 text-center text-muted-foreground"
                  >
                    No se encontraron movimientos para este producto
                  </TableCell>
                </TableRow>
              ) : (
                kardexEntries.map((entry, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="border-r text-center text-xs">
                      {formatDate(entry.fecha)}
                    </TableCell>
                    <TableCell className="border-r text-center">
                      <Badge
                        variant="secondary"
                        className={
                          entry.tipo_movimiento === "ingreso"
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        }
                      >
                        {entry.tipo_movimiento === "ingreso"
                          ? "Ingreso"
                          : "Salida"}
                      </Badge>
                    </TableCell>
                    <TableCell className="border-r text-center text-xs">
                      {entry.documento_referencia || "-"}
                    </TableCell>
                    {/* Entradas */}
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_entrada > 0
                        ? entry.cantidad_entrada.toLocaleString()
                        : ""}
                    </TableCell>
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_entrada > 0
                        ? formatCurrency(entry.costo_unitario_entrada)
                        : ""}
                    </TableCell>
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_entrada > 0
                        ? formatCurrency(entry.costo_total_entrada)
                        : ""}
                    </TableCell>
                    {/* Salidas */}
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_salida > 0
                        ? entry.cantidad_salida.toLocaleString()
                        : ""}
                    </TableCell>
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_salida > 0
                        ? formatCurrency(entry.costo_unitario_salida)
                        : ""}
                    </TableCell>
                    <TableCell className="border-r text-right font-mono text-xs">
                      {entry.cantidad_salida > 0
                        ? formatCurrency(entry.costo_total_salida)
                        : ""}
                    </TableCell>
                    {/* Saldo */}
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {entry.saldo_cantidad.toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(entry.saldo_costo_unitario)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-semibold">
                      {formatCurrency(entry.saldo_costo_total)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
            {kardexEntries && kardexEntries.length > 0 && totals && (
              <TableFooter>
                <TableRow className="font-bold">
                  <TableCell
                    colSpan={3}
                    className="border-r text-right text-xs"
                  >
                    TOTALES
                  </TableCell>
                  {/* Entradas totals */}
                  <TableCell className="border-r text-right font-mono text-xs">
                    {totals.cantidad_entrada.toLocaleString()}
                  </TableCell>
                  <TableCell className="border-r text-right font-mono text-xs">
                    -
                  </TableCell>
                  <TableCell className="border-r text-right font-mono text-xs">
                    {formatCurrency(totals.costo_total_entrada)}
                  </TableCell>
                  {/* Salidas totals */}
                  <TableCell className="border-r text-right font-mono text-xs">
                    {totals.cantidad_salida.toLocaleString()}
                  </TableCell>
                  <TableCell className="border-r text-right font-mono text-xs">
                    -
                  </TableCell>
                  <TableCell className="border-r text-right font-mono text-xs">
                    {formatCurrency(totals.costo_total_salida)}
                  </TableCell>
                  {/* Saldo final */}
                  <TableCell className="text-right font-mono text-xs text-blue-700">
                    {lastEntry?.saldo_cantidad.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-blue-700">
                    {lastEntry
                      ? formatCurrency(lastEntry.saldo_costo_unitario)
                      : ""}
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-blue-700">
                    {lastEntry
                      ? formatCurrency(lastEntry.saldo_costo_total)
                      : ""}
                  </TableCell>
                </TableRow>
              </TableFooter>
            )}
          </Table>
        </div>
      )}
    </div>
  );
}
