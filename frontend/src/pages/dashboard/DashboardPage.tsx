import { useState } from 'react';
import Header from '@/components/layout/Header';
import MetricCard from '@/components/ui/MetricCard';
import StatusBadge from '@/components/ui/StatusBadge';
import { formatCurrency, STATUS_COLORS } from '@/lib/api';
import {
  ShoppingCart, Ship, Package, Users, DollarSign, TrendingUp,
  BarChart3, ArrowRight, Clock,
} from 'lucide-react';
import type { DashboardMetricas, PipelineItem } from '@/types';

// Mock data (se reemplazara por API)
const mockMetricas: DashboardMetricas = {
  ocs_borrador: 3, ocs_confirmadas: 5, ocs_en_transito: 4,
  ocs_en_aduana: 2, ocs_prorrateadas: 1, ocs_en_almacen: 3,
  ocs_completadas: 28, importaciones_activas: 4,
  fob_mes_actual: 125000, costo_total_mes_actual: 168500,
  costo_total_mes_anterior: 142300,
  total_productos: 45, total_proveedores: 12, valor_inventario: 385000,
};

const mockPipeline: PipelineItem[] = [
  { id: 1, numero_oc: 'OC-2026-001', fecha_orden: '2026-02-15', proveedor: 'TECH IMPORTS LTD', pais_codigo: 'US', moneda_simbolo: '$', total_fob: 15200, estado: 'en_transito', estado_nombre: 'En Transito', estado_color: '#F59E0B', estado_icono: 'ship', estado_orden: 3, items_count: 5, dias_transcurridos: 20 },
  { id: 2, numero_oc: 'OC-2026-002', fecha_orden: '2026-02-20', proveedor: 'ASIA ELECTRONICS', pais_codigo: 'CN', moneda_simbolo: '$', total_fob: 42800, estado: 'en_aduana', estado_nombre: 'En Aduana', estado_color: '#EF4444', estado_icono: 'gavel', estado_orden: 4, items_count: 12, dias_transcurridos: 15 },
  { id: 3, numero_oc: 'OC-2026-003', fecha_orden: '2026-03-01', proveedor: 'EURO MACHINERY', pais_codigo: 'DE', moneda_simbolo: '€', total_fob: 8500, estado: 'confirmada', estado_nombre: 'Confirmada', estado_color: '#3B82F6', estado_icono: 'check', estado_orden: 2, items_count: 3, dias_transcurridos: 6 },
  { id: 4, numero_oc: 'OC-2026-004', fecha_orden: '2026-03-05', proveedor: 'TECH IMPORTS LTD', pais_codigo: 'US', moneda_simbolo: '$', total_fob: 6200, estado: 'borrador', estado_nombre: 'Borrador', estado_color: '#94A3B8', estado_icono: 'edit', estado_orden: 1, items_count: 2, dias_transcurridos: 2 },
];

export default function DashboardPage() {
  const m = mockMetricas;
  const trend = m.costo_total_mes_anterior > 0
    ? Math.round(((m.costo_total_mes_actual - m.costo_total_mes_anterior) / m.costo_total_mes_anterior) * 100)
    : 0;

  // Agrupar pipeline por estado
  const estados = ['borrador', 'confirmada', 'en_transito', 'en_aduana', 'prorrateado', 'en_almacen'];
  const estadoLabels: Record<string, string> = {
    borrador: 'Borrador', confirmada: 'Confirmada', en_transito: 'En Transito',
    en_aduana: 'En Aduana', prorrateado: 'Prorrateado', en_almacen: 'En Almacen',
  };

  return (
    <div>
      <Header title="Dashboard" subtitle="Resumen general del sistema" />

      <div className="p-6 space-y-6">
        {/* Metricas principales */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="OC Activas"
            value={m.ocs_borrador + m.ocs_confirmadas + m.ocs_en_transito + m.ocs_en_aduana}
            subtitle="En proceso"
            icon={ShoppingCart}
            color="#3B82F6"
          />
          <MetricCard
            title="Importaciones Activas"
            value={m.importaciones_activas}
            subtitle="En curso"
            icon={Ship}
            color="#F59E0B"
          />
          <MetricCard
            title="Costo Mes Actual"
            value={formatCurrency(m.costo_total_mes_actual)}
            icon={DollarSign}
            color="#10B981"
            trend={{ value: trend, isPositive: trend >= 0 }}
          />
          <MetricCard
            title="Valor Inventario"
            value={formatCurrency(m.valor_inventario)}
            subtitle={`${m.total_productos} productos`}
            icon={Package}
            color="#8B5CF6"
          />
        </div>

        {/* Contadores por estado */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {[
            { label: 'Borrador', count: m.ocs_borrador, color: STATUS_COLORS.borrador },
            { label: 'Confirmada', count: m.ocs_confirmadas, color: STATUS_COLORS.confirmada },
            { label: 'En Transito', count: m.ocs_en_transito, color: STATUS_COLORS.en_transito },
            { label: 'En Aduana', count: m.ocs_en_aduana, color: STATUS_COLORS.en_aduana },
            { label: 'Prorrateado', count: m.ocs_prorrateadas, color: STATUS_COLORS.prorrateado },
            { label: 'En Almacen', count: m.ocs_en_almacen, color: STATUS_COLORS.en_almacen },
            { label: 'Completada', count: m.ocs_completadas, color: STATUS_COLORS.completada },
            { label: 'Proveedores', count: m.total_proveedores, color: '#0891B2' },
          ].map((item) => (
            <div key={item.label} className="bg-white rounded-xl border border-gray-100 p-3 text-center">
              <p className="text-2xl font-bold" style={{ color: item.color }}>{item.count}</p>
              <p className="text-[10px] text-gray-500 mt-0.5">{item.label}</p>
            </div>
          ))}
        </div>

        {/* Pipeline Kanban */}
        <div>
          <h2 className="text-base font-bold text-gray-900 mb-3 flex items-center gap-2">
            <BarChart3 size={18} className="text-primary-500" />
            Pipeline de Ordenes
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
            {estados.map((estado) => {
              const items = mockPipeline.filter((p) => p.estado === estado);
              return (
                <div key={estado} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                  <div className="px-3 py-2 border-b border-gray-50 flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-600">{estadoLabels[estado]}</span>
                    <span
                      className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                      style={{ backgroundColor: STATUS_COLORS[estado] }}
                    >
                      {items.length}
                    </span>
                  </div>
                  <div className="p-2 space-y-2 min-h-[100px]">
                    {items.map((item) => (
                      <div key={item.id} className="bg-gray-50 rounded-lg p-2.5 hover:bg-gray-100 cursor-pointer transition-colors">
                        <p className="text-xs font-bold text-gray-800">{item.numero_oc}</p>
                        <p className="text-[10px] text-gray-500 mt-0.5 truncate">{item.proveedor}</p>
                        <div className="flex items-center justify-between mt-1.5">
                          <span className="text-[10px] font-medium text-gray-700">
                            {item.moneda_simbolo}{item.total_fob.toLocaleString()}
                          </span>
                          <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                            <Clock size={9} />{item.dias_transcurridos}d
                          </span>
                        </div>
                      </div>
                    ))}
                    {items.length === 0 && (
                      <p className="text-[10px] text-gray-300 text-center py-4">Sin ordenes</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
