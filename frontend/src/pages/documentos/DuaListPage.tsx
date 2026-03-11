import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, MoreHorizontal, Pencil, FileText } from "lucide-react";
import type { DuaDocumento, Importacion } from "@/lib/types";
import api from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";
import { DUA_STATUS_COLORS, DUA_ESTADOS } from "@/lib/constants";
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

interface ImportacionesListResponse {
  items: Importacion[];
  total: number;
  page: number;
  per_page: number;
}

interface DuaListResponse {
  items: DuaDocumento[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export default function DuaListPage() {
  const [importacionId, setImportacionId] = useState("");
  const [estado, setEstado] = useState("");
  const [page, setPage] = useState(1);

  const { data: duas, isLoading } = useQuery({
    queryKey: ["duas", importacionId, estado, page],
    queryFn: () =>
      api
        .get<DuaListResponse>("/api/documentos/dua", {
          params: {
            importacion_id: importacionId || undefined,
            estado: estado || undefined,
            page,
            per_page: 20,
          },
        })
        .then((r) => r.data),
  });

  const { data: importaciones } = useQuery({
    queryKey: ["importaciones-list-dua"],
    queryFn: () =>
      api
        .get<ImportacionesListResponse>("/api/importaciones", {
          params: { page: 1, per_page: 999 },
        })
        .then((r) => r.data),
  });

  const duaStatusLabel = (estado: string) => {
    const found = DUA_ESTADOS.find((e) => e.value === estado);
    return found ? found.label : estado;
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="h-7 w-7 text-blue-600" />
          <h1 className="text-2xl font-bold">Declaraciones Aduaneras (DUA)</h1>
        </div>
        <Button render={<Link to="/documentos/dua/nueva" />}>
          <Plus className="h-4 w-4" />
          Nueva DUA
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <Select
          value={importacionId}
          onValueChange={(val) => {
            setImportacionId(val === "__all__" ? "" : val ?? "");
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Todas las importaciones" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="__all__">Todas las importaciones</SelectItem>
            {importaciones?.items.map((imp) => (
              <SelectItem key={imp.id} value={String(imp.id)}>
                {imp.numero_importacion}
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
            {DUA_ESTADOS.map((e) => (
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
              <TableHead>Numero DUA</TableHead>
              <TableHead>Importacion</TableHead>
              <TableHead>Fecha Registro</TableHead>
              <TableHead className="text-right">FOB USD</TableHead>
              <TableHead className="text-right">CIF USD</TableHead>
              <TableHead className="text-right">Total Tributos</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 8 }).map((_, j) => (
                    <TableCell key={j}>
                      <div className="h-4 w-20 animate-pulse rounded bg-muted" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : !duas || duas.items.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={8}
                  className="py-8 text-center text-muted-foreground"
                >
                  No se encontraron declaraciones aduaneras
                </TableCell>
              </TableRow>
            ) : (
              duas.items.map((dua) => (
                <TableRow key={dua.id}>
                  <TableCell className="font-mono text-sm font-medium">
                    {dua.numero_dua}
                  </TableCell>
                  <TableCell className="text-sm">
                    {dua.importacion_numero || `IMP-${dua.importacion_id}`}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDate(dua.fecha_registro)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(dua.valor_fob_usd)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(dua.valor_cif_usd)}
                  </TableCell>
                  <TableCell className="text-right font-mono text-sm">
                    {formatCurrency(dua.total_tributos)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={DUA_STATUS_COLORS[dua.estado] || ""}
                    >
                      {duaStatusLabel(dua.estado)}
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
                            <Link to={`/documentos/dua/${dua.id}/editar`} />
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
      {duas && duas.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Mostrando pagina {duas.page} de {duas.pages} ({duas.total} registros)
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
              disabled={page >= duas.pages}
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
