import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search, Package } from "lucide-react";
import type { Almacen, StockItem } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
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

export default function InventarioPage() {
  const [almacenId, setAlmacenId] = useState("");
  const [search, setSearch] = useState("");
  const [soloConStock, setSoloConStock] = useState(true);

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api.get<Almacen[]>("/api/almacenes", { params: { status: "activo" } }).then((r) => r.data),
  });

  const { data: stock, isLoading } = useQuery({
    queryKey: ["inventario-stock", almacenId, search, soloConStock],
    queryFn: () =>
      api
        .get<StockItem[]>("/api/inventario/stock", {
          params: {
            almacen_id: almacenId || undefined,
            search: search || undefined,
            solo_con_stock: soloConStock ? 1 : undefined,
          },
        })
        .then((r) => r.data),
  });

  const totalCantidad = stock?.reduce((sum, item) => sum + item.cantidad, 0) ?? 0;
  const totalValor = stock?.reduce((sum, item) => sum + item.valor_total, 0) ?? 0;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center gap-3">
        <Package className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-bold">Inventario</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="w-56">
          <Select
            value={almacenId}
            onValueChange={(val) => setAlmacenId(val === "all" ? "" : val)}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Todos los almacenes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los almacenes</SelectItem>
              {almacenes?.map((alm) => (
                <SelectItem key={alm.id} value={String(alm.id)}>
                  {alm.nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar producto..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={soloConStock}
            onChange={(e) => setSoloConStock(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300"
          />
          Solo con stock
        </label>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Producto</TableHead>
              <TableHead>SKU</TableHead>
              <TableHead>Almacen</TableHead>
              <TableHead>Lote</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead className="text-right">Costo Unit.</TableHead>
              <TableHead className="text-right">Valor Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !stock || stock.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                  No se encontraron registros de inventario
                </TableCell>
              </TableRow>
            ) : (
              <>
                {stock.map((item, idx) => (
                  <TableRow
                    key={`${item.producto_id}-${item.almacen_id}-${item.lote ?? ""}-${idx}`}
                    className={cn(
                      item.cantidad === 0 && "bg-red-50",
                      item.cantidad > 0 && item.cantidad < 10 && "bg-yellow-50"
                    )}
                  >
                    <TableCell className="font-medium">{item.producto_nombre}</TableCell>
                    <TableCell className="font-mono text-xs">{item.producto_sku}</TableCell>
                    <TableCell>{item.almacen_nombre}</TableCell>
                    <TableCell>{item.lote || "-"}</TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-mono",
                        item.cantidad === 0 && "text-red-600 font-semibold",
                        item.cantidad > 0 && item.cantidad < 10 && "text-yellow-700 font-semibold"
                      )}
                    >
                      {item.cantidad}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.costo_unitario)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {formatCurrency(item.valor_total)}
                    </TableCell>
                  </TableRow>
                ))}

                {/* Summary row */}
                <TableRow className="bg-muted/50 font-semibold">
                  <TableCell colSpan={4} className="text-right">
                    Totales
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {totalCantidad}
                  </TableCell>
                  <TableCell />
                  <TableCell className="text-right font-mono">
                    {formatCurrency(totalValor)}
                  </TableCell>
                </TableRow>
              </>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
