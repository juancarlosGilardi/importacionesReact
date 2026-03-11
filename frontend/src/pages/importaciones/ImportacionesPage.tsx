import Header from '@/components/layout/Header';
import DataTable from '@/components/ui/DataTable';
import StatusBadge from '@/components/ui/StatusBadge';
import { Plus, Ship, Plane, Truck } from 'lucide-react';
import { formatCurrency, formatDate, STATUS_COLORS } from '@/lib/api';
import type { Importacion } from '@/types';

const mockImportaciones: Importacion[] = [
  { id: 1, numero_importacion: '2026-001', descripcion: 'Electrónicos Miami Q1', fecha_creacion: '2026-01-15', bl_number: 'MSCUAB123456', container_number: 'MSCU1234567', via_transporte: 'maritimo', fecha_embarque: '2026-01-20', fecha_arribo_estimada: '2026-02-25', estado: 'en_aduana', total_fob_importacion: 58000, total_gastos_importacion: 12500, total_costo_importacion: 70500, agente_aduanero: 'Agencia Aduanas SAC', total_ocs: 2, ocs_asociadas: 'OC-2026-001, OC-2026-002', created_at: '2026-01-15' },
  { id: 2, numero_importacion: '2026-002', descripcion: 'Maquinaria Europa', fecha_creacion: '2026-02-10', bl_number: 'HLCUEU789012', via_transporte: 'maritimo', fecha_embarque: '2026-02-15', fecha_arribo_estimada: '2026-03-20', estado: 'en_transito', total_fob_importacion: 8500, total_gastos_importacion: 0, total_costo_importacion: 0, total_ocs: 1, ocs_asociadas: 'OC-2026-003', created_at: '2026-02-10' },
  { id: 3, numero_importacion: '2026-003', descripcion: 'Componentes China', fecha_creacion: '2026-03-01', via_transporte: 'aereo', estado: 'planificada', total_fob_importacion: 6200, total_gastos_importacion: 0, total_costo_importacion: 0, total_ocs: 1, ocs_asociadas: 'OC-2026-004', created_at: '2026-03-01' },
];

const viaIcons: Record<string, React.ReactNode> = {
  maritimo: <Ship size={14} className="text-blue-500" />,
  aereo: <Plane size={14} className="text-amber-500" />,
  terrestre: <Truck size={14} className="text-green-500" />,
};

export default function ImportacionesPage() {
  const columns = [
    {
      key: 'numero_importacion', label: 'N° Imp.',
      render: (i: Importacion) => <span className="font-mono text-xs font-bold text-primary-600">{i.numero_importacion}</span>,
    },
    {
      key: 'descripcion', label: 'Descripcion',
      render: (i: Importacion) => (
        <div>
          <p className="text-sm font-medium text-gray-900">{i.descripcion}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {viaIcons[i.via_transporte]}
            {i.bl_number && <span className="text-[10px] font-mono text-gray-400">BL: {i.bl_number}</span>}
          </div>
        </div>
      ),
    },
    {
      key: 'ocs_asociadas', label: 'OCs',
      render: (i: Importacion) => (
        <div>
          <span className="text-xs font-medium text-gray-700">{i.total_ocs} OC{i.total_ocs > 1 ? 's' : ''}</span>
          {i.ocs_asociadas && <p className="text-[10px] text-gray-400 mt-0.5">{i.ocs_asociadas}</p>}
        </div>
      ),
    },
    {
      key: 'fechas', label: 'Embarque / Arribo',
      render: (i: Importacion) => (
        <div className="text-xs">
          {i.fecha_embarque && <p>ETD: {formatDate(i.fecha_embarque)}</p>}
          {i.fecha_arribo_estimada && <p className="text-gray-400">ETA: {formatDate(i.fecha_arribo_estimada)}</p>}
        </div>
      ),
    },
    {
      key: 'total_fob_importacion', label: 'FOB',
      render: (i: Importacion) => <span className="text-sm font-medium">{formatCurrency(i.total_fob_importacion, '$')}</span>,
      className: 'text-right',
    },
    {
      key: 'total_costo_importacion', label: 'Costo Total',
      render: (i: Importacion) => (
        <span className={`text-sm font-medium ${i.total_costo_importacion > 0 ? '' : 'text-gray-300'}`}>
          {i.total_costo_importacion > 0 ? formatCurrency(i.total_costo_importacion) : '-'}
        </span>
      ),
      className: 'text-right',
    },
    {
      key: 'estado', label: 'Estado',
      render: (i: Importacion) => <StatusBadge label={i.estado.replace('_', ' ')} color={STATUS_COLORS[i.estado] || '#94A3B8'} />,
    },
  ];

  return (
    <div>
      <Header
        title="Importaciones"
        subtitle="Gestion de embarques e importaciones"
        actions={
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            <Plus size={16} /> Nueva Importacion
          </button>
        }
      />
      <div className="p-6">
        <DataTable
          columns={columns}
          data={mockImportaciones}
          total={3}
          onSearch={(s) => console.log('search', s)}
          searchPlaceholder="Buscar por numero, BL, descripcion..."
          onRowClick={(i) => console.log('click imp', i)}
        />
      </div>
    </div>
  );
}
