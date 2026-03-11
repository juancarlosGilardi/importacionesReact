import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { DollarSign, PieChart } from "lucide-react";
import type {
  InventarioValorizado,
  ValorizadoPorFamilia,
  Almacen,
  PaginatedResponse,
} from "@/lib/types";
import { MONEDAS_VALORIZADO } from "@/lib/constants";
import { formatCurrency, formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface CategoriaProducto {
  id: number;
  nombre: string;
}

export default function InventarioValorizadoPage() {
  const [almacenId, setAlmacenId] = useState("");
  const [categoriaId, setCategoriaId] = useState("");
  const [moneda, setMoneda] = useState("PEN");
  const [tipoCambio, setTipoCambio] = useState("3.75");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data: categorias } = useQuery({
    queryKey: ["categorias"],
    queryFn: () =>
      api
        .get<CategoriaProducto[]>("/api/productos/categorias")
        .then((r) => r.data),
  });

  const tc = parseFloat(tipoCambio) || 3.75;

  const { data: valorizado, isLoading: loadingValorizado } = useQuery({
    queryKey: ["inventario-valorizado", almacenId, categoriaId, moneda, tc, search, page],
    queryFn: () =>
      api
        .get<PaginatedResponse<InventarioValorizado>>(
          "/api/inventario/valorizado",
          {
            params: {
              almacen_id: almacenId || undefined,
              categoria_id: categoriaId || undefined,
              moneda,
              tipo_cambio: tc,
              search: search || undefined,
              page,
              per_page: 50,
            },
          }
        )
        .then((r) => r.data),
  });

  const { data: porFamilia, isLoading: loadingFamilia } = useQuery({
    queryKey: ["valorizado-familia", almacenId, moneda, tc],
    queryFn: () =>
      api
        .get<ValorizadoPorFamilia[]>("/api/inventario/valorizado/por-familia", {
          params: {
            almacen_id: almacenId || undefined,
            moneda,
            tipo_cambio: tc,
          },
        })
        .then((r) => r.data),
  });

  const monedaSymbol = moneda === "USD" ? "US$" : "S/";
  const totalGeneral =
    porFamilia && porFamilia.length > 0
      ? porFamilia[0].total_general_moneda
      : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <DollarSign className="h-6 w-6 text-green-600" />
        <h1 className="text-2xl font-bold">Inventario Valorizado</h1>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Almacen
              </label>
              <Select
                value={almacenId}
                onValueChange={(val) => {
                  setAlmacenId(val === "all" ? "" : val ?? "");
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Todos" />
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
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Moneda
              </label>
              <Select value={moneda} onValueChange={(val) => setMoneda(val ?? "")}>
                <SelectTrigger className="w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MONEDAS_VALORIZADO.map((m) => (
                    <SelectItem key={m.value} value={m.value}>
                      {m.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {moneda === "USD" && (
              <div>
                <label className="text-xs font-medium text-muted-foreground">
                  Tipo Cambio
                </label>
                <Input
                  type="number"
                  step="0.01"
                  value={tipoCambio}
                  onChange={(e) => setTipoCambio(e.target.value)}
                  className="w-28"
                />
              </div>
            )}

            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Categoria
              </label>
              <Select
                value={categoriaId}
                onValueChange={(val) => {
                  setCategoriaId(val === "all" ? "" : val ?? "");
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas las categorias</SelectItem>
                  {categorias?.map((cat) => (
                    <SelectItem key={cat.id} value={String(cat.id)}>
                      {cat.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Buscar
              </label>
              <Input
                placeholder="SKU o nombre..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-56"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Total Card */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-primary" />
            <div>
              <p className="text-sm text-muted-foreground">
                Valor Total del Inventario
              </p>
              <p className="text-2xl font-bold text-primary">
                {monedaSymbol}{" "}
                {totalGeneral
                  ? Number(totalGeneral).toLocaleString("es-PE", {
                      minimumFractionDigits: 2,
                    })
                  : "0.00"}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className="text-sm">
            {moneda}
          </Badge>
        </CardContent>
      </Card>

      {/* Tabs: Detallado / Por Familia */}
      <Tabs defaultValue="detallado">
        <TabsList>
          <TabsTrigger value="detallado">Detallado</TabsTrigger>
          <TabsTrigger value="familia">Por Familia</TabsTrigger>
        </TabsList>

        <TabsContent value="detallado" className="mt-4">
          <div className="rounded-lg border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>SKU</TableHead>
                  <TableHead>Producto</TableHead>
                  <TableHead>Almacen</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead className="text-right">Cantidad</TableHead>
                  <TableHead className="text-right">
                    Costo Unit. ({moneda})
                  </TableHead>
                  <TableHead className="text-right">
                    Valor ({moneda})
                  </TableHead>
                  <TableHead>Lote</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingValorizado ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 8 }).map((_, j) => (
                        <TableCell key={j}>
                          <div className="h-4 animate-pulse rounded bg-muted" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !valorizado?.items || valorizado.items.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={8}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No se encontraron registros
                    </TableCell>
                  </TableRow>
                ) : (
                  valorizado.items.map((item, idx) => (
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
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {monedaSymbol}{" "}
                        {Number(item.costo_unitario_moneda).toLocaleString(
                          "es-PE",
                          { minimumFractionDigits: 4 }
                        )}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold">
                        {monedaSymbol}{" "}
                        {Number(item.valor_total_moneda).toLocaleString(
                          "es-PE",
                          { minimumFractionDigits: 2 }
                        )}
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

          {/* Pagination */}
          {valorizado && valorizado.pages > 1 && (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Pagina {valorizado.page} de {valorizado.pages} ({valorizado.total} registros)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= valorizado.pages}
                  onClick={() => setPage(page + 1)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="familia" className="mt-4 space-y-4">
          <div className="rounded-lg border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Categoria</TableHead>
                  <TableHead className="text-right">Productos</TableHead>
                  <TableHead className="text-right">Cantidad</TableHead>
                  <TableHead className="text-right">
                    Valor ({moneda})
                  </TableHead>
                  <TableHead className="text-right">% del Total</TableHead>
                  <TableHead className="w-48">Distribucion</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingFamilia ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <TableRow key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <TableCell key={j}>
                          <div className="h-4 animate-pulse rounded bg-muted" />
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : !porFamilia || porFamilia.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={6}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No hay datos de inventario
                    </TableCell>
                  </TableRow>
                ) : (
                  <>
                    {porFamilia.map((fam) => (
                      <TableRow key={fam.categoria_id}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <PieChart className="h-4 w-4 text-muted-foreground" />
                            {fam.categoria_nombre}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {fam.total_productos}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {Number(fam.total_cantidad).toLocaleString()}
                        </TableCell>
                        <TableCell className="text-right font-mono font-semibold">
                          {monedaSymbol}{" "}
                          {Number(fam.valor_total_moneda).toLocaleString(
                            "es-PE",
                            { minimumFractionDigits: 2 }
                          )}
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {fam.porcentaje}%
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="h-2 flex-1 rounded-full bg-muted">
                              <div
                                className="h-2 rounded-full bg-primary"
                                style={{
                                  width: `${Math.min(fam.porcentaje, 100)}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {fam.porcentaje}%
                            </span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}

                    {/* Total row */}
                    <TableRow className="bg-muted/50 font-semibold">
                      <TableCell>Total</TableCell>
                      <TableCell className="text-right font-mono">
                        {porFamilia.reduce((s, f) => s + f.total_productos, 0)}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {porFamilia
                          .reduce((s, f) => s + f.total_cantidad, 0)
                          .toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {monedaSymbol}{" "}
                        {totalGeneral
                          ? Number(totalGeneral).toLocaleString("es-PE", {
                              minimumFractionDigits: 2,
                            })
                          : "0.00"}
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        100%
                      </TableCell>
                      <TableCell />
                    </TableRow>
                  </>
                )}
              </TableBody>
            </Table>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
