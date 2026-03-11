import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, MoreHorizontal, Pencil, Receipt } from "lucide-react";
import type { FacturaProveedor, Proveedor, OrdenCompra } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { FACTURA_STATUS_COLORS, FACTURA_ESTADOS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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

interface FacturasListResponse {
  items: FacturaProveedor[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

interface OrdenesListResponse {
  items: OrdenCompra[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export default function FacturasPage() {
  const [proveedorId, setProveedorId] = useState("");
  const [ocId, setOcId] = useState("");
  const [estado, setEstado] = useState("");
  const [page, setPage] = useState(1);

  const { data: facturas, isLoading } = useQuery({
    queryKey: ["facturas", proveedorId, ocId, estado, page],
    queryFn: () =>
      api
        .get<FacturasListResponse>("/api/documentos/facturas", {
          params: {
            proveedor_id: proveedorId || undefined,
            oc_id: ocId || undefined,
            estado: estado || undefined,
            page,
            per_page: 20,
          },
        })
        .then((r) => r.data),
  });

  const { data: proveedores } = useQuery({
    queryKey: ["proveedores-for-facturas"],
    queryFn: () =>
      api
        .get<{ items: Proveedor[]; total: number }>("/api/proveedores", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data.items),
  });

  const { data: ordenes } = useQuery({
    queryKey: ["ordenes-for-facturas"],
    queryFn: () =>
      api
        .get<OrdenesListResponse>("/api/ordenes", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const facturaStatusLabel = (estado: string) => {
    const found = FACTURA_ESTADOS.find((e) => e.value === estado);
    return found ? found.label : estado;
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Receipt className="h-7 w-7 text-blue-600" />
          <h1 className="text-2xl font-bold">Facturas de Proveedor</h1>
        </div>
        <Button render={<Link to="/documentos/facturas/nueva" />}>
          <Plus className="h-4 w-4" />
          Nueva Factura
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <Select
          value={proveedorId}
          onValueChange={(val) => {
            setProveedorId(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Todos los proveedores" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los proveedores</SelectItem>
            {proveedores?.map((p) => (
              <SelectItem key={p.id} value={String(p.id)}>
                {p.razon_social}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={ocId}
          onValueChange={(val) => {
            setOcId(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Todas las OC" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todas las OC</SelectItem>
            {ordenes?.items.map((oc) => (
              <SelectItem key={oc.id} value={String(oc.id)}>
                {oc.numero_oc || oc.numero}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={estado}
          onValueChange={(val) => {
            setEstado(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todos los estados</SelectItem>
            {FACTURA_ESTADOS.map((e) => (
              <SelectItem key={e.value} value={e.value}>
                {e.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Numero</TableHead>
              <TableHead>Proveedor</TableHead>
              <TableHead>OC</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead>Moneda</TableHead>
              <TableHead className="text-right">Subtotal</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 9 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !facturas || facturas.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={9}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron facturas
                </TableCell>
              </TableRow>
            ) : (
              facturas.items.map((factura) => (
                <TableRow key={factura.id}>
                  <TableCell className="font-mono text-sm font-medium">
                    {factura.numero_factura}
                  </TableCell>
                  <TableCell className="text-sm">
                    {factura.proveedor_nombre || "-"}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {factura.oc_numero || "-"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDate(factura.fecha_factura)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {factura.moneda_codigo || "-"}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(factura.subtotal)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(factura.total)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={FACTURA_STATUS_COLORS[factura.estado] || ""}
                    >
                      {facturaStatusLabel(factura.estado)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        render={
                          <Button variant="ghost" size="icon-sm" />
                        }
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem
                          render={
                            <Link
                              to={`/documentos/facturas/${factura.id}/editar`}
                            />
                          }
                        >
                          <Pencil className="h-4 w-4" />
                          Editar
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {facturas && facturas.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Mostrando pagina {facturas.page} de {facturas.pages} ({facturas.total}{" "}
            registros)
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= facturas.pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
