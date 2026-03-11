import Header from '@/components/layout/Header';
import { Warehouse, Package, DollarSign, Plus } from 'lucide-react';
import { formatCurrency } from '@/lib/api';
import { useState } from 'react';

const mockAlmacenes = [
  { id: 1, codigo: 'ALM-01', nombre: 'Almacen Principal', responsable: 'Juan Pérez', direccion: 'Av. Argentina 1234, Callao', status: 'active', total_productos: 32, valor_total: 285000 },
  { id: 2, codigo: 'ALM-02', nombre: 'Almacen Norte', responsable: 'María López', direccion: 'Jr. Industrial 567, SMP', status: 'active', total_productos: 15, valor_total: 98000 },
];

export default function AlmacenesPage() {
  return (
    <div>
      <Header
        title="Almacenes"
        subtitle="Gestion de ubicaciones de almacenamiento"
        actions={
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            <Plus size={16} /> Nuevo Almacen
          </button>
        }
      />
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockAlmacenes.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-gray-100 p-5 hover:shadow-md transition-shadow cursor-pointer">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-primary-50 rounded-lg">
                    <Warehouse size={20} className="text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 text-sm">{a.nombre}</h3>
                    <p className="text-xs text-gray-400 font-mono">{a.codigo}</p>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${a.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {a.status === 'active' ? 'Activo' : 'Inactivo'}
                </span>
              </div>

              {a.responsable && <p className="text-xs text-gray-500 mb-1">Responsable: {a.responsable}</p>}
              {a.direccion && <p className="text-xs text-gray-400 mb-3">{a.direccion}</p>}

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-50">
                <div className="flex items-center gap-2">
                  <Package size={14} className="text-gray-400" />
                  <div>
                    <p className="text-sm font-bold text-gray-900">{a.total_productos}</p>
                    <p className="text-[10px] text-gray-400">Productos</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign size={14} className="text-gray-400" />
                  <div>
                    <p className="text-sm font-bold text-gray-900">{formatCurrency(a.valor_total)}</p>
                    <p className="text-[10px] text-gray-400">Valor Total</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
