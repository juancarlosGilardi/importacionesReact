import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Settings2 } from "lucide-react";
import type { Almacen, ConceptoAlmacen } from "@/lib/types";
import api from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import { Switch } from "@/components/ui/switch";

export default function ConceptosAlmacenPage() {
  const queryClient = useQueryClient();
  const [almacenId, setAlmacenId] = useState("");

  const { data: almacenes } = useQuery({
    queryKey: ["almacenes"],
    queryFn: () =>
      api
        .get<Almacen[]>("/api/almacenes", { params: { status: "activo" } })
        .then((r) => r.data),
  });

  const { data: conceptos, isLoading } = useQuery({
    queryKey: ["conceptos-almacen", almacenId],
    queryFn: () =>
      api
        .get<ConceptoAlmacen[]>(`/api/vales/conceptos/${almacenId}`)
        .then((r) => r.data),
    enabled: !!almacenId,
  });

  const toggleMutation = useMutation({
    mutationFn: (payload: { concepto_id: number; habilitado: boolean }) =>
      api.put(`/api/vales/conceptos/${almacenId}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["conceptos-almacen", almacenId],
      });
    },
  });

  const ingresoConceptos = conceptos?.filter((c) => c.tipo === "ingreso") || [];
  const salidaConceptos = conceptos?.filter((c) => c.tipo === "salida") || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Settings2 className="h-6 w-6 text-muted-foreground" />
        <h1 className="text-2xl font-bold">Conceptos de Almacen</h1>
      </div>

      <p className="text-sm text-muted-foreground">
        Configure los conceptos de movimiento habilitados para cada almacen.
        Puede activar o desactivar conceptos segun las operaciones permitidas en
        cada almacen.
      </p>

      {/* Almacen selector */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Seleccionar Almacen:</label>
            <Select
              value={almacenId}
              onValueChange={(val) => setAlmacenId(val ?? "")}
            >
              <SelectTrigger className="w-72">
                <SelectValue placeholder="Seleccione un almacen" />
              </SelectTrigger>
              <SelectContent>
                {almacenes?.map((alm) => (
                  <SelectItem key={alm.id} value={String(alm.id)}>
                    {alm.codigo} - {alm.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {!almacenId ? (
        <div className="rounded-lg border-2 border-dashed border-muted-foreground/20 p-12 text-center">
          <Settings2 className="mx-auto h-10 w-10 text-muted-foreground/40" />
          <p className="mt-3 text-muted-foreground">
            Seleccione un almacen para ver y configurar sus conceptos
          </p>
        </div>
      ) : isLoading ? (
        <div className="space-y-4">
          <div className="h-48 animate-pulse rounded-lg bg-muted" />
          <div className="h-48 animate-pulse rounded-lg bg-muted" />
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Conceptos de Ingreso */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Badge className="bg-emerald-100 text-emerald-700">
                  Ingreso
                </Badge>
                Conceptos de Ingreso
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ingresoConceptos.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No hay conceptos de ingreso configurados
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Codigo</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead className="text-center">
                        Afecta Costo
                      </TableHead>
                      <TableHead className="text-center w-24">
                        Habilitado
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ingresoConceptos.map((concepto) => (
                      <TableRow key={concepto.id}>
                        <TableCell className="font-mono text-xs">
                          {concepto.codigo}
                        </TableCell>
                        <TableCell className="font-medium">
                          {concepto.nombre}
                        </TableCell>
                        <TableCell className="text-center">
                          {concepto.afecta_costo ? (
                            <Badge
                              variant="secondary"
                              className="bg-blue-100 text-blue-700"
                            >
                              Si
                            </Badge>
                          ) : (
                            <Badge variant="secondary">No</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Switch
                            checked={concepto.habilitado !== false}
                            onCheckedChange={(checked) =>
                              toggleMutation.mutate({
                                concepto_id: concepto.id,
                                habilitado: checked,
                              })
                            }
                            disabled={toggleMutation.isPending}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Conceptos de Salida */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Badge className="bg-rose-100 text-rose-700">Salida</Badge>
                Conceptos de Salida
              </CardTitle>
            </CardHeader>
            <CardContent>
              {salidaConceptos.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No hay conceptos de salida configurados
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Codigo</TableHead>
                      <TableHead>Nombre</TableHead>
                      <TableHead className="text-center">
                        Afecta Costo
                      </TableHead>
                      <TableHead className="text-center w-24">
                        Habilitado
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {salidaConceptos.map((concepto) => (
                      <TableRow key={concepto.id}>
                        <TableCell className="font-mono text-xs">
                          {concepto.codigo}
                        </TableCell>
                        <TableCell className="font-medium">
                          {concepto.nombre}
                        </TableCell>
                        <TableCell className="text-center">
                          {concepto.afecta_costo ? (
                            <Badge
                              variant="secondary"
                              className="bg-blue-100 text-blue-700"
                            >
                              Si
                            </Badge>
                          ) : (
                            <Badge variant="secondary">No</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-center">
                          <Switch
                            checked={concepto.habilitado !== false}
                            onCheckedChange={(checked) =>
                              toggleMutation.mutate({
                                concepto_id: concepto.id,
                                habilitado: checked,
                              })
                            }
                            disabled={toggleMutation.isPending}
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
