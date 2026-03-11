import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Save,
  ChevronDown,
  ChevronRight,
  Building2,
  Boxes,
  ShoppingCart,
  FileText,
  RefreshCw,
  Check,
  SlidersHorizontal,
} from "lucide-react";
import type { ConfiguracionItem, ConfiguracionSeccion } from "@/lib/types";
import api from "@/lib/api";
import { CONFIG_SECCIONES_LABELS } from "@/lib/constants";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ---------- Icon map ----------
const seccionIcons: Record<string, typeof Building2> = {
  general: Building2,
  inventario: Boxes,
  compras: ShoppingCart,
  documentos: FileText,
};

const seccionDescriptions: Record<string, string> = {
  general: "Datos generales de la empresa",
  inventario: "Parametros de control de inventario",
  compras: "Configuracion de ordenes de compra",
  documentos: "Prefijos y formatos de documentos",
};

// ---------- Component ----------
export default function ConfiguracionPage() {
  const queryClient = useQueryClient();
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({ general: true });
  const [editedValues, setEditedValues] = useState<
    Record<string, Record<string, string>>
  >({});
  const [savingSection, setSavingSection] = useState<string | null>(null);
  const [savedSection, setSavedSection] = useState<string | null>(null);

  // ---------- Queries ----------
  const { data: secciones } = useQuery({
    queryKey: ["config-secciones"],
    queryFn: () =>
      api
        .get<ConfiguracionSeccion[]>("/api/configuracion/secciones")
        .then((r) => r.data),
  });

  const { data: configItems, isLoading } = useQuery({
    queryKey: ["config-items"],
    queryFn: () =>
      api
        .get<ConfiguracionItem[]>("/api/configuracion")
        .then((r) => r.data),
  });

  // ---------- Mutation ----------
  const saveSectionMutation = useMutation({
    mutationFn: ({
      seccion,
      items,
    }: {
      seccion: string;
      items: { clave: string; valor: string }[];
    }) =>
      api.put("/api/configuracion/batch", { seccion, items }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["config-items"] });
      // Clear edited values for this section
      setEditedValues((prev) => {
        const next = { ...prev };
        delete next[variables.seccion];
        return next;
      });
      setSavingSection(null);
      setSavedSection(variables.seccion);
      setTimeout(() => setSavedSection(null), 2000);
    },
    onError: () => {
      setSavingSection(null);
    },
  });

  // ---------- Helpers ----------
  const toggleSection = (seccion: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [seccion]: !prev[seccion],
    }));
  };

  const getItemsBySection = (seccion: string): ConfiguracionItem[] => {
    return configItems?.filter((item) => item.seccion === seccion) || [];
  };

  const getCurrentValue = (seccion: string, clave: string, original: string | null): string => {
    return editedValues[seccion]?.[clave] ?? (original || "");
  };

  const handleValueChange = (
    seccion: string,
    clave: string,
    valor: string
  ) => {
    setEditedValues((prev) => ({
      ...prev,
      [seccion]: {
        ...(prev[seccion] || {}),
        [clave]: valor,
      },
    }));
  };

  const hasSectionChanges = (seccion: string): boolean => {
    const edited = editedValues[seccion];
    if (!edited) return false;
    const items = getItemsBySection(seccion);
    return Object.entries(edited).some(([clave, valor]) => {
      const original = items.find((i) => i.clave === clave);
      return original && valor !== (original.valor || "");
    });
  };

  const handleSaveSection = (seccion: string) => {
    const edited = editedValues[seccion];
    if (!edited) return;
    const items = Object.entries(edited).map(([clave, valor]) => ({
      clave,
      valor,
    }));
    setSavingSection(seccion);
    saveSectionMutation.mutate({ seccion, items });
  };

  const handleResetSection = (seccion: string) => {
    setEditedValues((prev) => {
      const next = { ...prev };
      delete next[seccion];
      return next;
    });
  };

  // ---------- Renderers ----------
  const renderValueInput = (item: ConfiguracionItem) => {
    const val = getCurrentValue(item.seccion, item.clave, item.valor);

    if (item.tipo_dato === "boolean") {
      return (
        <Select
          value={val}
          onValueChange={(v) =>
            handleValueChange(item.seccion, item.clave, v ?? "")
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="true">Sí</SelectItem>
            <SelectItem value="false">No</SelectItem>
          </SelectContent>
        </Select>
      );
    }

    if (item.tipo_dato === "number") {
      return (
        <Input
          type="number"
          value={val}
          onChange={(e) =>
            handleValueChange(item.seccion, item.clave, e.target.value)
          }
          className="w-[140px]"
        />
      );
    }

    // Special handling for some keys
    if (item.clave === "moneda_default") {
      return (
        <Select
          value={val}
          onValueChange={(v) =>
            handleValueChange(item.seccion, item.clave, v ?? "")
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="PEN">PEN - Sol Peruano</SelectItem>
            <SelectItem value="USD">USD - Dólar Americano</SelectItem>
          </SelectContent>
        </Select>
      );
    }

    if (item.clave === "metodo_costeo") {
      return (
        <Select
          value={val}
          onValueChange={(v) =>
            handleValueChange(item.seccion, item.clave, v ?? "")
          }
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="promedio">Costo Promedio</SelectItem>
            <SelectItem value="fifo">FIFO (PEPS)</SelectItem>
            <SelectItem value="lifo">LIFO (UEPS)</SelectItem>
          </SelectContent>
        </Select>
      );
    }

    if (item.clave === "incoterm_default") {
      return (
        <Select
          value={val}
          onValueChange={(v) =>
            handleValueChange(item.seccion, item.clave, v ?? "")
          }
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {["EXW", "FCA", "FOB", "CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP"].map(
              (inc) => (
                <SelectItem key={inc} value={inc}>
                  {inc}
                </SelectItem>
              )
            )}
          </SelectContent>
        </Select>
      );
    }

    return (
      <Input
        value={val}
        onChange={(e) =>
          handleValueChange(item.seccion, item.clave, e.target.value)
        }
        className="max-w-sm"
      />
    );
  };

  const formatClave = (clave: string): string => {
    return clave
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const sectionOrder = ["general", "inventario", "compras", "documentos"];
  const orderedSections =
    secciones?.sort(
      (a, b) =>
        sectionOrder.indexOf(a.seccion) - sectionOrder.indexOf(b.seccion)
    ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Configuración del Sistema</h1>
          <p className="text-sm text-muted-foreground">
            Administre los parámetros generales del sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="bg-blue-100 text-blue-700">
            <SlidersHorizontal className="mr-1 h-3 w-3" />
            {configItems?.length || 0} parámetros
          </Badge>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-16 animate-pulse rounded-lg border bg-muted"
            />
          ))}
        </div>
      )}

      {/* Sections */}
      {!isLoading && (
        <div className="space-y-4">
          {orderedSections.map((sec) => {
            const Icon = seccionIcons[sec.seccion] || Building2;
            const isExpanded = expandedSections[sec.seccion];
            const items = getItemsBySection(sec.seccion);
            const hasChanges = hasSectionChanges(sec.seccion);
            const isSaving = savingSection === sec.seccion;
            const justSaved = savedSection === sec.seccion;

            return (
              <div
                key={sec.seccion}
                className="rounded-lg border bg-white overflow-hidden"
              >
                {/* Section header */}
                <button
                  type="button"
                  onClick={() => toggleSection(sec.seccion)}
                  className="flex w-full items-center justify-between px-6 py-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50">
                      <Icon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold">
                        {CONFIG_SECCIONES_LABELS[sec.seccion] || sec.seccion}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {seccionDescriptions[sec.seccion] ||
                          `${sec.total_claves} parametros`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {hasChanges && (
                      <Badge
                        variant="secondary"
                        className="bg-amber-100 text-amber-700"
                      >
                        Cambios sin guardar
                      </Badge>
                    )}
                    {justSaved && (
                      <Badge
                        variant="secondary"
                        className="bg-green-100 text-green-700"
                      >
                        <Check className="mr-1 h-3 w-3" />
                        Guardado
                      </Badge>
                    )}
                    <Badge variant="outline">{sec.total_claves}</Badge>
                    {isExpanded ? (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                </button>

                {/* Section content */}
                {isExpanded && (
                  <div className="border-t">
                    <div className="divide-y">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between px-6 py-3 hover:bg-muted/30"
                        >
                          <div className="space-y-0.5 flex-1 min-w-0 pr-4">
                            <Label className="text-sm font-medium">
                              {formatClave(item.clave)}
                            </Label>
                            {item.descripcion && (
                              <p className="text-xs text-muted-foreground">
                                {item.descripcion}
                              </p>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {renderValueInput(item)}
                            <Badge variant="outline" className="text-xs shrink-0">
                              {item.tipo_dato}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Section footer with save/reset */}
                    <div className="flex items-center justify-end gap-2 border-t bg-muted/30 px-6 py-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleResetSection(sec.seccion)}
                        disabled={!hasChanges || isSaving}
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                        Descartar
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => handleSaveSection(sec.seccion)}
                        disabled={!hasChanges || isSaving}
                      >
                        {isSaving ? (
                          <>
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            Guardando...
                          </>
                        ) : (
                          <>
                            <Save className="h-3.5 w-3.5" />
                            Guardar Sección
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
