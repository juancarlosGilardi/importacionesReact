import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Printer } from "lucide-react";
import type { FichaCosteo } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
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

export default function FichaCosteoPage() {
  const { oc_id } = useParams<{ oc_id: string }>();
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ["ficha-costeo", oc_id],
    queryFn: () =>
      api
        .get<FichaCosteo>(`/api/prorrateo/ficha-costeo/${oc_id}`)
        .then((r) => r.data),
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
        Ficha de costeo no encontrada
      </div>
    );
  }

  const { cabecera, items, gastos } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between print:hidden">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => navigate("/prorrateo")}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Ficha de Costeo</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              OC {cabecera.numero_oc} - {cabecera.proveedor_nombre}
            </p>
          </div>
        </div>
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="h-4 w-4" />
          Imprimir
        </Button>
      </div>

      {/* Print-only header */}
      <div className="hidden print:block">
        <h1 className="text-xl font-bold">FICHA DE COSTEO DE IMPORTACION</h1>
        <Separator className="my-2" />
      </div>

      {/* OC Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Datos de la Orden de Compra</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-3 lg:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Numero OC</p>
              <p className="text-sm font-medium">{cabecera.numero_oc}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Proveedor</p>
              <p className="text-sm font-medium">{cabecera.proveedor_nombre}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">RUC Proveedor</p>
              <p className="text-sm font-medium">{cabecera.proveedor_ruc || "-"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Fecha</p>
              <p className="text-sm font-medium">
                {cabecera.fecha_orden ? formatDate(cabecera.fecha_orden) : "-"}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Moneda</p>
              <p className="text-sm font-medium">{cabecera.moneda}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Incoterm</p>
              <p className="text-sm font-medium">{cabecera.incoterm}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Items Table with full costs */}
      <Card>
        <CardHeader>
          <CardTitle>Detalle de Productos con Costos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Producto</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">Cant.</TableHead>
                  <TableHead className="text-right">FOB</TableHead>
                  <TableHead className="text-right">Flete</TableHead>
                  <TableHead className="text-right">Seguro</TableHead>
                  <TableHead className="text-right">Tributos</TableHead>
                  <TableHead className="text-right">Gastos</TableHead>
                  <TableHead className="text-right">Costo Total</TableHead>
                  <TableHead className="text-right">C.U. Landed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={10}
                      className="py-8 text-center text-muted-foreground"
                    >
                      No hay items en la ficha de costeo
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="max-w-[180px] truncate text-xs font-medium">
                        {item.producto_nombre}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {item.producto_sku}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {item.cantidad}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-blue-700">
                        {formatCurrency(item.valor_fob)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-cyan-700">
                        {formatCurrency(item.prorrateo_flete)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-purple-700">
                        {formatCurrency(item.prorrateo_seguro)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-red-700">
                        {formatCurrency(item.prorrateo_tributos)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-orange-700">
                        {formatCurrency(item.prorrateo_gastos)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-semibold">
                        {formatCurrency(item.costo_total)}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-bold text-green-700">
                        {formatCurrency(item.costo_unitario_landed)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
                {items.length > 0 && (
                  <TableRow className="border-t-2 bg-muted/50 font-semibold">
                    <TableCell colSpan={2} className="text-xs">
                      TOTALES
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {items.reduce((s, d) => s + d.cantidad, 0)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-blue-700">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.valor_fob, 0)
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-cyan-700">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.prorrateo_flete, 0)
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-purple-700">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.prorrateo_seguro, 0)
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-red-700">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.prorrateo_tributos, 0)
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs text-orange-700">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.prorrateo_gastos, 0)
                      )}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(
                        items.reduce((s, d) => s + d.costo_total, 0)
                      )}
                    </TableCell>
                    <TableCell />
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Gastos Breakdown */}
      {gastos.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Desglose de Gastos</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Descripcion</TableHead>
                    <TableHead>Proveedor</TableHead>
                    <TableHead className="text-right">Monto</TableHead>
                    <TableHead>Moneda</TableHead>
                    <TableHead className="text-right">Monto (PEN)</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {gastos.map((gasto) => (
                    <TableRow key={gasto.id}>
                      <TableCell className="text-xs font-medium">
                        {gasto.tipo_gasto_nombre || gasto.tipo_gasto_codigo}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-xs">
                        {gasto.descripcion || "-"}
                      </TableCell>
                      <TableCell className="text-xs">
                        {gasto.proveedor_nombre || "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs">
                        {formatCurrency(gasto.monto)}
                      </TableCell>
                      <TableCell className="text-xs">
                        {gasto.moneda_codigo || "-"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-medium">
                        {formatCurrency(gasto.monto_pen, "S/")}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="border-t-2 bg-muted/50 font-semibold">
                    <TableCell colSpan={5} className="text-xs">
                      TOTAL GASTOS
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs">
                      {formatCurrency(
                        gastos.reduce((s, g) => s + g.monto_pen, 0),
                        "S/"
                      )}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Resumen de Costos de Importacion</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            <div className="rounded-lg border bg-blue-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total FOB</p>
              <p className="mt-1 text-xl font-bold text-blue-700">
                {formatCurrency(cabecera.total_fob)}
              </p>
            </div>
            <div className="rounded-lg border bg-cyan-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total Flete</p>
              <p className="mt-1 text-xl font-bold text-cyan-700">
                {formatCurrency(cabecera.total_flete)}
              </p>
            </div>
            <div className="rounded-lg border bg-purple-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total Seguro</p>
              <p className="mt-1 text-xl font-bold text-purple-700">
                {formatCurrency(cabecera.total_seguro)}
              </p>
            </div>
            <div className="rounded-lg border bg-indigo-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total CIF</p>
              <p className="mt-1 text-xl font-bold text-indigo-700">
                {formatCurrency(cabecera.total_cif)}
              </p>
            </div>
            <div className="rounded-lg border bg-red-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total Tributos</p>
              <p className="mt-1 text-xl font-bold text-red-700">
                {formatCurrency(cabecera.total_tributos)}
              </p>
            </div>
            <div className="rounded-lg border bg-orange-50 p-4 text-center">
              <p className="text-xs text-muted-foreground">Total Gastos</p>
              <p className="mt-1 text-xl font-bold text-orange-700">
                {formatCurrency(cabecera.total_gastos)}
              </p>
            </div>
            <div className="col-span-2 rounded-lg border bg-green-50 p-4 text-center sm:col-span-1 lg:col-span-2">
              <p className="text-xs text-muted-foreground">
                Costo Total de Importacion
              </p>
              <p className="mt-1 text-2xl font-bold text-green-700">
                {formatCurrency(cabecera.total_costo_importacion)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
