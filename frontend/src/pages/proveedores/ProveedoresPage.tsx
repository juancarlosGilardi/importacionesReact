import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/layout/Header';
import DataTable from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import type { Proveedor } from '@/types';

const mockProveedores: Proveedor[] = [
  { id: 1, ruc: '12345678901', razon_social: 'TECHNOLOGY IMPORT LTD', nombre_comercial: 'TechImports', pais: 'Estados Unidos', pais_codigo: 'US', moneda: 'USD', incoterm_default: 'FOB', es_extranjero: true, email: 'sales@techimport.com', status: 'active', total_ocs: 8, created_at: '2025-12-22' },
  { id: 2, ruc: '87654321098', razon_social: 'ASIA ELECTRONICS CO', nombre_comercial: 'AsiaElec', pais: 'China', pais_codigo: 'CN', moneda: 'USD', incoterm_default: 'CIF', es_extranjero: true, email: 'info@asiaelectronics.cn', status: 'active', total_ocs: 15, created_at: '2025-12-22' },
  { id: 3, ruc: '56789012345', razon_social: 'EUROPE MACHINERY GMBH', nombre_comercial: 'EuroMach', pais: 'Alemania', pais_codigo: 'DE', moneda: 'EUR', incoterm_default: 'EXW', es_extranjero: true, email: 'export@euromach.de', status: 'active', total_ocs: 3, created_at: '2025-12-22' },
];

export default function ProveedoresPage() {
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);

  const columns = [
    { key: 'ruc', label: 'RUC', className: 'font-mono text-xs' },
    {
      key: 'razon_social', label: 'Razon Social',
      render: (p: Proveedor) => (
        <div>
          <p className="font-medium text-gray-900">{p.razon_social}</p>
          {p.nombre_comercial && <p className="text-xs text-gray-400">{p.nombre_comercial}</p>}
        </div>
      ),
    },
    {
      key: 'pais', label: 'Pais',
      render: (p: Proveedor) => (
        <span className="inline-flex items-center gap-1.5 text-xs">
          <span className="text-base">{getFlagEmoji(p.pais_codigo || '')}</span>
          {p.pais}
        </span>
      ),
    },
    { key: 'incoterm_default', label: 'Incoterm', className: 'font-mono' },
    { key: 'moneda', label: 'Moneda' },
    { key: 'total_ocs', label: 'OCs', className: 'text-center' },
    {
      key: 'status', label: 'Estado',
      render: (p: Proveedor) => (
        <StatusBadge label={p.status === 'active' ? 'Activo' : 'Inactivo'} color={p.status === 'active' ? '#10B981' : '#94A3B8'} />
      ),
    },
  ];

  return (
    <div>
      <Header
        title="Proveedores"
        subtitle="Gestion de proveedores nacionales e internacionales"
        actions={
          <button
            onClick={() => setShowForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700"
          >
            <Plus size={16} /> Nuevo Proveedor
          </button>
        }
      />
      <div className="p-6">
        <DataTable
          columns={columns}
          data={mockProveedores}
          total={3}
          onSearch={(s) => console.log('search', s)}
          searchPlaceholder="Buscar por RUC, razon social..."
          onRowClick={(p) => console.log('click', p)}
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

      {/* Modal form placeholder */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-2xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <h2 className="text-lg font-bold text-gray-900 mb-4">Nuevo Proveedor</h2>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">RUC</label>
                  <input className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500" placeholder="20100000001" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Incoterm</label>
                  <select className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20">
                    <option>FOB</option><option>CIF</option><option>EXW</option><option>CFR</option><option>DAP</option><option>DDP</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Razon Social</label>
                <input className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Nombre Comercial</label>
                <input className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input type="email" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Telefono</label>
                  <input className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20" />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancelar</button>
              <button className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700">Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function getFlagEmoji(code: string): string {
  if (!code || code.length !== 2) return '';
  const codePoints = code.toUpperCase().split('').map((c) => 127397 + c.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}
