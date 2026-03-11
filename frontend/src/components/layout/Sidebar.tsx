import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingCart, Ship, FileText, Package,
  Users, Warehouse, DollarSign, Calculator, ClipboardList,
  ArrowRightLeft, BarChart3, LogOut, ChevronDown,
} from 'lucide-react';
import { useState } from 'react';
import { useAuthStore } from '@/store/authStore';

interface MenuItem {
  label: string;
  path?: string;
  icon: React.ReactNode;
  children?: { label: string; path: string }[];
}

const menuItems: MenuItem[] = [
  { label: 'Dashboard', path: '/', icon: <LayoutDashboard size={18} /> },
  {
    label: 'Compras', icon: <ShoppingCart size={18} />,
    children: [
      { label: 'Ordenes de Compra', path: '/ordenes-compra' },
      { label: 'Proveedores', path: '/proveedores' },
      { label: 'Productos', path: '/productos' },
    ],
  },
  {
    label: 'Importaciones', icon: <Ship size={18} />,
    children: [
      { label: 'Importaciones', path: '/importaciones' },
      { label: 'DUA', path: '/dua' },
      { label: 'Gastos', path: '/gastos' },
    ],
  },
  {
    label: 'Costeo', icon: <Calculator size={18} />,
    children: [
      { label: 'Prorrateo', path: '/prorrateo' },
    ],
  },
  {
    label: 'Inventario', icon: <Package size={18} />,
    children: [
      { label: 'Stock', path: '/inventario' },
      { label: 'Movimientos', path: '/movimientos' },
      { label: 'Almacenes', path: '/almacenes' },
    ],
  },
];

export default function Sidebar() {
  const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({ Compras: true, Importaciones: true });
  const { user, logout } = useAuthStore();

  const toggleMenu = (label: string) => {
    setOpenMenus((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  return (
    <aside className="w-60 h-screen bg-sidebar flex flex-col fixed left-0 top-0 z-50">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
            <Ship size={16} className="text-white" />
          </div>
          <div>
            <h1 className="text-white font-bold text-sm">ImportCost Pro</h1>
            <p className="text-gray-400 text-[10px]">Sistema de Costeo</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-3">
        {menuItems.map((item) =>
          item.path ? (
            <NavLink
              key={item.label}
              to={item.path}
              end
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm mb-0.5 transition-colors ${
                  isActive ? 'bg-sidebar-active text-white' : 'text-gray-400 hover:bg-sidebar-hover hover:text-gray-200'
                }`
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ) : (
            <div key={item.label} className="mb-1">
              <button
                onClick={() => toggleMenu(item.label)}
                className="w-full flex items-center justify-between gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-sidebar-hover hover:text-gray-200 transition-colors"
              >
                <span className="flex items-center gap-2.5">
                  {item.icon}
                  {item.label}
                </span>
                <ChevronDown
                  size={14}
                  className={`transition-transform ${openMenus[item.label] ? 'rotate-180' : ''}`}
                />
              </button>
              {openMenus[item.label] && item.children && (
                <div className="ml-5 mt-0.5 space-y-0.5 border-l border-white/10 pl-3">
                  {item.children.map((child) => (
                    <NavLink
                      key={child.path}
                      to={child.path}
                      className={({ isActive }) =>
                        `block px-3 py-1.5 rounded-md text-xs transition-colors ${
                          isActive ? 'text-primary-400 bg-sidebar-active' : 'text-gray-500 hover:text-gray-300 hover:bg-sidebar-hover'
                        }`
                      }
                    >
                      {child.label}
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          )
        )}
      </nav>

      {/* User */}
      <div className="p-3 border-t border-white/10">
        <div className="flex items-center gap-2.5 px-3 py-2">
          <div className="w-7 h-7 bg-primary-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
            {user?.nombre?.[0]}{user?.apellido?.[0]}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-white text-xs font-medium truncate">{user?.nombre} {user?.apellido}</p>
            <p className="text-gray-500 text-[10px] truncate">{user?.email}</p>
          </div>
          <button onClick={logout} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors" title="Cerrar sesion">
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}
