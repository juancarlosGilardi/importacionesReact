import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { useState } from 'react';

interface Column<T> {
  key: string;
  label: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  total?: number;
  page?: number;
  perPage?: number;
  onPageChange?: (page: number) => void;
  onSearch?: (search: string) => void;
  searchPlaceholder?: string;
  onRowClick?: (item: T) => void;
  actions?: (item: T) => React.ReactNode;
  emptyMessage?: string;
  loading?: boolean;
}

export default function DataTable<T extends { id: number }>({
  columns, data, total = 0, page = 1, perPage = 20,
  onPageChange, onSearch, searchPlaceholder = 'Buscar...',
  onRowClick, actions, emptyMessage = 'No hay datos', loading,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const totalPages = Math.ceil(total / perPage);

  const handleSearch = (value: string) => {
    setSearch(value);
    onSearch?.(value);
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      {onSearch && (
        <div className="p-4 border-b border-gray-100">
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            />
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50/80">
              {columns.map((col) => (
                <th key={col.key} className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${col.className || ''}`}>
                  {col.label}
                </th>
              ))}
              {actions && <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Acciones</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-12 text-center text-gray-400">
                <div className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                  Cargando...
                </div>
              </td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={columns.length + (actions ? 1 : 0)} className="px-4 py-12 text-center text-gray-400">{emptyMessage}</td></tr>
            ) : (
              data.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => onRowClick?.(item)}
                  className={`hover:bg-gray-50/80 ${onRowClick ? 'cursor-pointer' : ''}`}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={`px-4 py-3 text-sm text-gray-700 ${col.className || ''}`}>
                      {col.render ? col.render(item) : (item as Record<string, unknown>)[col.key] as React.ReactNode}
                    </td>
                  ))}
                  {actions && <td className="px-4 py-3 text-right">{actions(item)}</td>}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
          <p className="text-sm text-gray-500">{total} registros</p>
          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange?.(page - 1)} disabled={page <= 1}
              className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronLeft size={16} />
            </button>
            <span className="px-3 py-1 text-sm text-gray-600">{page} / {totalPages}</span>
            <button onClick={() => onPageChange?.(page + 1)} disabled={page >= totalPages}
              className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
