import Header from '@/components/layout/Header';
import DataTable from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import { Plus } from 'lucide-react';
import { formatCurrency, formatDate, STATUS_COLORS } from '@/lib/api';
import type { OrdenCompra } from '@/types';

const mockOCs: OrdenCompra[] = [
  { id: 1, numero_oc: 'OC-2026-001', fecha_orden: '2026-02-15', incoterm: 'FOB', estado: 'en_transito', total_fob: 15200, total_cif: 16800, total_costo_importacion: 19500, proveedor: 'TECHNOLOGY IMPORT LTD', proveedor_comercial: 'TechImports', pais_codigo: 'US', pais_origen: 'Estados Unidos', moneda: 'USD', moneda_simbolo: '$', tipo_cambio: 3.75, estado_nombre: 'En Transito', estado_color: '#F59E0B', estado_icono: 'ship', total_items: 5, total_cantidad: 120, created_at: '2026-02-15' },
  { id: 2, numero_oc: 'OC-2026-002', fecha_orden: '2026-02-20', incoterm: 'CIF', estado: 'en_aduana', total_fob: 42800, total_cif: 45200, total_costo_importacion: 52000, proveedor: 'ASIA ELECTRONICS CO', proveedor_comercial: 'AsiaElec', pais_codigo: 'CN', pais_origen: 'China', moneda: 'USD', moneda_simbolo: '$', tipo_cambio: 3.75, estado_nombre: 'En Aduana', estado_color: '#EF4444', estado_icono: 'gavel', total_items: 12, total_cantidad: 500, created_at: '2026-02-20' },
  { id: 3, numero_oc: 'OC-2026-003', fecha_orden: '2026-03-01', incoterm: 'EXW', estado: 'confirmada', total_fob: 8500, total_cif: 0, total_costo_importacion: 0, proveedor: 'EUROPE MACHINERY GMBH', proveedor_comercial: 'EuroMach', pais_codigo: 'DE', pais_origen: 'Alemania', moneda: 'EUR', moneda_simbolo: '€', tipo_cambio: 4.10, estado_nombre: 'Confirmada', estado_color: '#3B82F6', estado_icono: 'check', total_items: 3, total_cantidad: 25, created_at: '2026-03-01' },
  { id: 4, numero_oc: 'OC-2026-004', fecha_orden: '2026-03-05', incoterm: 'FOB', estado: 'borrador', total_fob: 6200, total_cif: 0, total_costo_importacion: 0, proveedor: 'TECHNOLOGY IMPORT LTD', pais_codigo: 'US', pais_origen: 'Estados Unidos', moneda: 'USD', moneda_simbolo: '$', tipo_cambio: 3.75, estado_nombre: 'Borrador', estado_color: '#94A3B8', estado_icono: 'edit', total_items: 2, total_cantidad: 50, created_at: '2026-03-05' },
];

export default function OrdenesCompraPage() {
  const columns = [
    {
      key: 'numero_oc', label: 'N° OC',
      render: (oc: OrdenCompra) => <span className="font-mono text-xs font-bold text-primary-600">{oc.numero_oc}</span>,
    },
    { key: 'fecha_orden', label: 'Fecha', render: (oc: OrdenCompra) => <span className="text-xs">{formatDate(oc.fecha_orden)}</span> },
    {
      key: 'proveedor', label: 'Proveedor',
      render: (oc: OrdenCompra) => (
        <div>
          <p className="text-sm font-medium text-gray-900">{oc.proveedor}</p>
          <p className="text-xs text-gray-400">{getFlagEmoji(oc.pais_codigo || '')} {oc.pais_origen}</p>
        </div>
      ),
    },
    { key: 'incoterm', label: 'Incoterm', className: 'font-mono text-xs text-center' },
    {
      key: 'total_fob', label: 'FOB',
      render: (oc: OrdenCompra) => <span className="text-sm font-medium">{oc.moneda_simbolo}{oc.total_fob.toLocaleString()}</span>,
      className: 'text-right',
    },
    {
      key: 'total_costo_importacion', label: 'Costo Total',
      render: (oc: OrdenCompra) => (
        <span className={`text-sm font-medium ${oc.total_costo_importacion > 0 ? 'text-gray-900' : 'text-gray-300'}`}>
          {oc.total_costo_importacion > 0 ? formatCurrency(oc.total_costo_importacion) : '-'}
        </span>
      ),
      className: 'text-right',
    },
    { key: 'total_items', label: 'Items', className: 'text-center' },
    {
      key: 'estado', label: 'Estado',
      render: (oc: OrdenCompra) => <StatusBadge label={oc.estado_nombre} color={oc.estado_color} />,
    },
  ];

  return (
    <div>
      <Header
        title="Ordenes de Compra"
        subtitle="Gestion de ordenes de compra a proveedores"
        actions={
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            <Plus size={16} /> Nueva OC
          </button>
        }
      />
      <div className="p-6">
        <DataTable
          columns={columns}
          data={mockOCs}
          total={4}
          onSearch={(s) => console.log('search', s)}
          searchPlaceholder="Buscar por numero OC, proveedor..."
          onRowClick={(oc) => console.log('click OC', oc)}
        />
      </div>
    </div>
  );
}

function getFlagEmoji(code: string): string {
  if (!code || code.length !== 2) return '';
  const codePoints = code.toUpperCase().split('').map((c) => 127397 + c.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}
