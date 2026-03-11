import { useState } from 'react';
import Header from '@/components/layout/Header';
import DataTable from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import { Plus, Pencil, Trash2, Package } from 'lucide-react';
import type { Producto } from '@/types';

const mockProductos: Producto[] = [
  { id: 1, sku: 'LAP-001', nombre: 'Laptop Gaming Pro', codigo_hs: '8471.30.00', unidad_medida: 'NIU', peso_kg: 2.5, categoria: 'Electrónica', tasa_ad_valorem: 0, color_ui: '#3B82F6', icono_ui: 'laptop', status: 'active', stock_total: 25, created_at: '2025-12-22' },
  { id: 2, sku: 'MON-002', nombre: 'Monitor LED 24"', codigo_hs: '8528.52.10', unidad_medida: 'NIU', peso_kg: 4.2, categoria: 'Electrónica', tasa_ad_valorem: 0, color_ui: '#8B5CF6', icono_ui: 'monitor', status: 'active', stock_total: 50, created_at: '2025-12-22' },
  { id: 3, sku: 'PHO-003', nombre: 'Smartphone Android', codigo_hs: '8517.12.00', unidad_medida: 'NIU', peso_kg: 0.3, categoria: 'Electrónica', tasa_ad_valorem: 0, color_ui: '#EF4444', icono_ui: 'phone', status: 'active', stock_total: 120, created_at: '2025-12-22' },
  { id: 4, sku: 'COM-004', nombre: 'Componentes Electrónicos', codigo_hs: '8542.39.00', unidad_medida: 'KGM', peso_kg: 0.5, categoria: 'Componentes', tasa_ad_valorem: 0, color_ui: '#10B981', icono_ui: 'cpu', status: 'active', stock_total: 500, created_at: '2025-12-22' },
];

export default function ProductosPage() {
  const [showForm, setShowForm] = useState(false);

  const columns = [
    {
      key: 'sku', label: 'SKU',
      render: (p: Producto) => (
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${p.color_ui}15` }}>
            <Package size={14} style={{ color: p.color_ui }} />
          </div>
          <span className="font-mono text-xs font-medium">{p.sku}</span>
        </div>
      ),
    },
    {
      key: 'nombre', label: 'Producto',
      render: (p: Producto) => (
        <div>
          <p className="font-medium text-gray-900 text-sm">{p.nombre}</p>
          {p.categoria && <p className="text-xs text-gray-400">{p.categoria}</p>}
        </div>
      ),
    },
    { key: 'codigo_hs', label: 'Partida HS', className: 'font-mono text-xs' },
    { key: 'unidad_medida', label: 'Unidad', className: 'text-center' },
    {
      key: 'tasa_ad_valorem', label: 'Ad Valorem',
      render: (p: Producto) => <span className="text-xs">{p.tasa_ad_valorem}%</span>,
    },
    {
      key: 'stock_total', label: 'Stock',
      render: (p: Producto) => (
        <span className={`text-sm font-medium ${(p.stock_total || 0) > 0 ? 'text-green-600' : 'text-gray-400'}`}>
          {p.stock_total || 0}
        </span>
      ),
      className: 'text-center',
    },
    {
      key: 'status', label: 'Estado',
      render: (p: Producto) => (
        <StatusBadge label={p.status === 'active' ? 'Activo' : 'Inactivo'} color={p.status === 'active' ? '#10B981' : '#94A3B8'} />
      ),
    },
  ];

  return (
    <div>
      <Header
        title="Productos"
        subtitle="Catalogo de productos importados"
        actions={
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            <Plus size={16} /> Nuevo Producto
          </button>
        }
      />
      <div className="p-6">
        <DataTable
          columns={columns}
          data={mockProductos}
          total={4}
          onSearch={(s) => console.log('search', s)}
          searchPlaceholder="Buscar por SKU, nombre, partida HS..."
          actions={(p) => (
            <div className="flex items-center gap-1">
              <button className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg">
                <Pencil size={14} />
              </button>
              <button className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg">
                <Trash2 size={14} />
              </button>
            </div>
          )}
        />
      </div>
    </div>
  );
}
