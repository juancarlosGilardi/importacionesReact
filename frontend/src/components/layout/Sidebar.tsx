import { NavLink } from "react-router-dom";
import {
  Ship,
  LayoutDashboard,
  Users,
  Package,
  ShoppingCart,
  Receipt,
  Calculator,
  Warehouse,
  Boxes,
  BarChart3,
  LogOut,
  FileText,
  BookOpen,
  ArrowLeftRight,
  HelpCircle,
  ClipboardPlus,
  ClipboardMinus,
  ClipboardList,
  Settings2,
  PackageSearch,
  AlertTriangle,
  DollarSign,
  FileCheck,
  ClipboardCheck,
  PieChart,
  TrendingUp,
  UserCog,
  SlidersHorizontal,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/proveedores", icon: Users, label: "Proveedores" },
  { to: "/productos", icon: Package, label: "Productos" },
  { to: "/ordenes", icon: ShoppingCart, label: "Órdenes de Compra" },
  { to: "/requerimientos", icon: FileCheck, label: "Requerimientos" },
  { to: "/importaciones", icon: Ship, label: "Importaciones" },
  { to: "/gastos", icon: Receipt, label: "Gastos" },
  { to: "/prorrateo", icon: Calculator, label: "Prorrateo" },
];

const documentosItems = [
  { to: "/documentos/duas", icon: FileText, label: "DUAs" },
  { to: "/documentos/facturas", icon: Receipt, label: "Facturas" },
];

const almacenItems = [
  { to: "/almacenes", icon: Warehouse, label: "Almacenes" },
  { to: "/vales/ingreso", icon: ClipboardPlus, label: "Vales de Ingreso" },
  { to: "/vales/salida", icon: ClipboardMinus, label: "Vales de Salida" },
  { to: "/vales/lista", icon: ClipboardList, label: "Lista de Vales" },
  { to: "/vales/conceptos", icon: Settings2, label: "Conceptos" },
];

const inventarioItems = [
  { to: "/inventario", icon: Boxes, label: "Inventario" },
  { to: "/inventario/stock", icon: PackageSearch, label: "Stock Disponible" },
  { to: "/inventario/alertas", icon: AlertTriangle, label: "Alertas de Stock" },
  { to: "/inventario/valorizado", icon: DollarSign, label: "Inv. Valorizado" },
  { to: "/inventario/toma", icon: ClipboardCheck, label: "Toma Inventario" },
  { to: "/movimientos", icon: ArrowLeftRight, label: "Movimientos" },
  { to: "/inventario/kardex", icon: BookOpen, label: "Kardex" },
];

const reportesItems = [
  { to: "/reportes/inventario", icon: PieChart, label: "Reportes Inventario" },
  { to: "/reportes/almacen", icon: Warehouse, label: "Reportes Almacen" },
  { to: "/reportes/compras", icon: TrendingUp, label: "Reportes Compras" },
  { to: "/reportes", icon: BarChart3, label: "Reportes Costeo" },
];

const adminItems = [
  { to: "/admin/usuarios", icon: UserCog, label: "Usuarios" },
  { to: "/admin/configuracion", icon: SlidersHorizontal, label: "Configuración" },
];

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-[260px] flex-col bg-[#1e293b] text-white">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600">
          <Ship className="h-5 w-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold leading-tight tracking-tight">
            ImportCost Pro
          </h1>
        </div>
      </div>

      <Separator className="mx-4 bg-white/10" />

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Documentos group */}
        <div className="mt-4 mb-2 px-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Documentos
          </p>
        </div>
        <ul className="space-y-1">
          {documentosItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Almacén section */}
        <div className="mt-4 mb-2 px-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Almacén
          </p>
        </div>
        <ul className="space-y-1">
          {almacenItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Inventario section */}
        <div className="mt-4 mb-2 px-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Inventario
          </p>
        </div>
        <ul className="space-y-1">
          {inventarioItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Reportes section */}
        <div className="mt-4 mb-2 px-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Reportes
          </p>
        </div>
        <ul className="space-y-1">
          {reportesItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Administración section */}
        <div className="mt-4 mb-2 px-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Administración
          </p>
        </div>
        <ul className="space-y-1">
          {adminItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-white/15 text-white"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  )
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Manual link */}
      <div className="px-3 pb-2">
        <NavLink
          to="/manual"
          target="_blank"
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
        >
          <HelpCircle className="h-4 w-4 shrink-0" />
          <span>Manual de Usuario</span>
        </NavLink>
      </div>

      {/* User info + logout */}
      <div className="border-t border-white/10 px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold">
              {user?.nombre?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{user?.nombre}</p>
              <p className="truncate text-xs text-slate-400">{user?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={logout}
            className="shrink-0 text-slate-400 hover:bg-white/10 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
