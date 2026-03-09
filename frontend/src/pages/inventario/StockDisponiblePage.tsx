import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  PackageSearch,
  Boxes,
  Warehouse as WarehouseIcon,
  DollarSign,
  Package,
  PackageX,
} from "lucide-react";
import type { StockResumen, StockPorAlmacen, Almacen } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface StockItem {
  producto_id: number;
  sku: string;
  producto_nombre: string;
  almacen_nombre: string;
  almacen_codigo: string;
  categoria_nombre?: string;
  cantidad: number;
  costo_unitario: number;
  valor_total: number;
  lote?: string;
  unidad_medida?: string;
}

export default function StockDisponiblePage() {
  const [almacenId, setAlmacenId] = useState("");
  const [search, setSearch] = useState("");
  const [soloConStock, setSoloConStock] = useState(true);

  const { data: resumen } = useQuery({
    queryKey: ["stock-resumen"],
    queryFn: () =>
      api.get<StockResumen>("/api/inventario/stock/resumen").then((r) => r.data),
  });

  const { data: stockPorAlmacen } = useQuery({
    queryKey: ["stock-por-almacen"],
    queryFn: () =>
      api
        .get<StockPorAlmacen[]>("/api/inventario/stock/por-almacen")
        .then((r) => r.data),
  });

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data: stockItems, isLoading } = useQuery({
    queryKey: ["stock-items", almacenId, search, soloConStock],
    queryFn: () =>
      api
        .get<StockItem[]>("/api/inventario/stock", {
          params: {
            almacen_id: almacenId || undefined,
            search: search || undefined,
            solo_con_stock: soloConStock ? 1 : 0,
          },
        })
        .then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <PackageSearch className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-bold">Stock Disponible</h1>
      </div>

      {/* Summary Cards */}
      {resumen && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <SummaryCard
            icon={<Package className="h-5 w-5 text-blue-600" />}
            label="Total Productos"
            value={String(resumen.total_productos)}
          />
          <SummaryCard
            icon={<Boxes className="h-5 w-5 text-emerald-600" />}
            label="Con Stock"
            value={String(resumen.productos_con_stock)}
          />
          <SummaryCard
            icon={<PackageX className="h-5 w-5 text-red-600" />}
            label="Sin Stock"
            value={String(resumen.productos_sin_stock)}
          />
          <SummaryCard
            icon={<WarehouseIcon className="h-5 w-5 text-purple-600" />}
            label="Almacenes"
            value={String(resumen.almacenes_activos)}
          />
          <SummaryCard
            icon={<Boxes className="h-5 w-5 text-amber-600" />}
            label="Items Stock"
            value={String(resumen.items_con_stock)}
          />
          <SummaryCard
            icon={<DollarSign className="h-5 w-5 text-green-600" />}
            label="Valor Total"
            value={formatCurrency(resumen.valor_total_inventario)}
            highlight
          />
        </div>
      )}

      {/* Stock por Almacen */}
      {stockPorAlmacen && stockPorAlmacen.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Distribucion por Almacen
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {stockPorAlmacen.map((alm) => (
                <div
                  key={alm.almacen_id}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p className="font-medium">{alm.almacen_nombre}</p>
                    <p className="text-xs text-muted-foreground">
                      {alm.almacen_codigo} &bull; {alm.total_productos}{" "}
                      productos
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono font-semibold text-primary">
                      {formatCurrency(alm.valor_total)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {Number(alm.total_cantidad).toLocaleString()} und.
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Select
          value={almacenId}
          onValueChange={(val) => setAlmacenId(val === "all" ? "" : val)}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Todos los almacenes" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los almacenes</SelectItem>
            {almacenes?.map((alm) => (
              <SelectItem key={alm.id} value={String(alm.id)}>
                {alm.codigo} - {alm.nombre}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          placeholder="Buscar por SKU o nombre..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64"
        />

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={soloConStock}
            onChange={(e) => setSoloConStock(e.target.checked)}
            className="rounded border-input"
          />
          Solo con stock
        </label>
      </div>

      {/* Stock Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>SKU</TableHead>
              <TableHead>Producto</TableHead>
              <TableHead>Almacen</TableHead>
              <TableHead>Categoria</TableHead>
              <TableHead className="text-right">Cantidad</TableHead>
              <TableHead className="text-right">Costo Unit.</TableHead>
              <TableHead className="text-right">Valor Total</TableHead>
              <TableHead>Lote</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !stockItems || stockItems.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron productos con stock
                </TableCell>
              </TableRow>
            ) : (
              stockItems.map((item, idx) => (
                <TableRow key={`${item.producto_id}-${item.almacen_codigo}-${item.lote || idx}`}>
                  <TableCell className="font-mono text-xs">
                    {item.sku}
                  </TableCell>
                  <TableCell className="font-medium">
                    {item.producto_nombre}
                  </TableCell>
                  <TableCell>
                    <Badge variant="secondary" className="text-xs">
                      {item.almacen_codigo}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {item.categoria_nombre || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {Number(item.cantidad).toLocaleString()}
                    {item.unidad_medida && (
                      <span className="ml-1 text-xs text-muted-foreground">
                        {item.unidad_medida}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right font-mono">
                    {formatCurrency(item.costo_unitario)}
                  </TableCell>
                  <TableCell className="text-right font-mono font-semibold">
                    {formatCurrency(item.valor_total)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {item.lote || "-"}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function SummaryCard({
  icon,
  label,
  value,
  highlight,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <Card
      className={highlight ? "border-primary/30 bg-primary/5" : ""}
    >
      <CardContent className="flex items-center gap-3 p-4">
        {icon}
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p
            className={`font-mono text-sm font-semibold ${highlight ? "text-primary" : ""}`}
          >
            {value}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
