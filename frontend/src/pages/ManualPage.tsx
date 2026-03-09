import { useState } from "react";
import {
  Ship, LayoutDashboard, Users, Package, ShoppingCart,
  Receipt, Calculator, FileText, Warehouse, Boxes,
  ArrowLeftRight, BookOpen, BarChart3, ChevronRight,
  CheckCircle2, AlertCircle, Info, ArrowDown, ArrowRight,
  Search, Plus, Edit, Trash2, Eye, Filter, Download,
  LogIn, Shield, Settings, HelpCircle, Printer,
  TrendingUp, DollarSign, MapPin, Globe, Truck,
  ClipboardList, Hash, Calendar, CreditCard, Layers,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// ============================================================================
// MOCK DATA
// ============================================================================
const mockProveedores = [
  { id: 1, ruc: "20501234567", razon_social: "SHANGHAI TOOLS CO LTD", pais: "China", moneda: "USD", incoterm: "FOB", ocs: 12, status: "active" },
  { id: 2, ruc: "20509876543", razon_social: "KOREA STEEL SUPPLIES", pais: "Corea del Sur", moneda: "USD", incoterm: "CIF", ocs: 8, status: "active" },
  { id: 3, ruc: "B12345678", razon_social: "FERRAMENTAS EUROPA SL", pais: "Espana", moneda: "EUR", incoterm: "FOB", ocs: 3, status: "active" },
];

const mockProductos = [
  { sku: "HER-001", nombre: "Taladro Percutor 800W", categoria: "Herramientas", hs: "8467.21.00", peso: 2.5, stock: 150, costo: 45.80 },
  { sku: "HER-002", nombre: "Amoladora Angular 4.5\"", categoria: "Herramientas", hs: "8467.29.00", peso: 1.8, stock: 200, costo: 32.50 },
  { sku: "FER-001", nombre: "Tornillo Hex M8x50 (Caja x1000)", categoria: "Ferreteria", hs: "7318.15.00", peso: 15.0, stock: 80, costo: 28.00 },
  { sku: "ELE-001", nombre: "Cable THW 14 AWG (Rollo 100m)", categoria: "Electrico", hs: "8544.49.00", peso: 5.2, stock: 120, costo: 38.90 },
];

const mockOrden = {
  numero: "OC-2026-0045",
  proveedor: "SHANGHAI TOOLS CO LTD",
  fecha: "2026-02-15",
  moneda: "USD",
  incoterm: "FOB",
  estado: "confirmada",
  items: [
    { producto: "Taladro Percutor 800W", cantidad: 500, precio: 22.50, subtotal: 11250.00 },
    { producto: "Amoladora Angular 4.5\"", cantidad: 300, precio: 18.00, subtotal: 5400.00 },
  ],
  total_fob: 16650.00,
};

const mockImportacion = {
  numero: "IMP-2026-0012",
  descripcion: "Embarque Herramientas Q1 - China",
  via: "maritimo",
  bl: "COSCO2026SH0045",
  container: "CSLU1234567",
  nave: "COSCO SHIPPING GEMINI",
  estado: "en_aduana",
  ocs: ["OC-2026-0045", "OC-2026-0046"],
  fob_total: 28500.00,
};

const mockGastos = [
  { tipo: "Flete Internacional", monto: 2850.00, moneda: "USD", comprobante: "FV-001-2345", estado: "pagado" },
  { tipo: "Seguro", monto: 285.00, moneda: "USD", comprobante: "POL-2026-100", estado: "pagado" },
  { tipo: "Almacenaje", monto: 1200.00, moneda: "PEN", comprobante: "FV-004-5678", estado: "pendiente" },
  { tipo: "Agente Aduanas", monto: 850.00, moneda: "PEN", comprobante: "FV-003-9012", estado: "pagado" },
  { tipo: "Transporte Local", monto: 650.00, moneda: "PEN", comprobante: "FV-005-3456", estado: "pendiente" },
];

const mockDUA = {
  numero: "235-2026-10-012345-01",
  fecha: "2026-03-01",
  regimen: "10",
  cif_soles: 112500.00,
  ad_valorem: 6750.00,
  igv: 21465.00,
  ipm: 2385.00,
  percepcion: 4944.00,
  total_tributos: 35544.00,
};

const mockProrrateo = {
  metodo: "valor_fob",
  total_fob: 28500.00,
  total_flete: 2850.00,
  total_seguro: 285.00,
  total_tributos: 35544.00,
  total_gastos: 2700.00,
  items: [
    { producto: "Taladro Percutor 800W", fob: 11250.00, pct: 39.47, flete: 1125.00, seguro: 112.50, tributos: 14028.00, gastos: 1065.80, landed: 27581.30, qty: 500, unit_cost: 55.16 },
    { producto: "Amoladora Angular 4.5\"", fob: 5400.00, pct: 18.95, flete: 540.00, seguro: 54.00, tributos: 6735.84, gastos: 511.50, landed: 13241.34, qty: 300, unit_cost: 44.14 },
  ],
};

const mockKardex = [
  { fecha: "2026-03-05", tipo: "INGRESO", doc: "MOV-001", entrada_qty: 500, entrada_cu: 55.16, entrada_ct: 27580.00, saldo_qty: 500, saldo_cu: 55.16, saldo_ct: 27580.00 },
  { fecha: "2026-03-07", tipo: "SALIDA", doc: "MOV-003", salida_qty: 50, salida_cu: 55.16, salida_ct: 2758.00, saldo_qty: 450, saldo_cu: 55.16, saldo_ct: 24822.00 },
  { fecha: "2026-03-10", tipo: "INGRESO", doc: "MOV-005", entrada_qty: 200, entrada_cu: 52.30, entrada_ct: 10460.00, saldo_qty: 650, saldo_cu: 54.28, saldo_ct: 35282.00 },
];

// ============================================================================
// COMPONENTS
// ============================================================================

function SectionTitle({ icon: Icon, title, id }: { icon: React.ElementType; title: string; id: string }) {
  return (
    <h2 id={id} className="mt-12 mb-6 flex scroll-mt-20 items-center gap-3 border-b border-slate-200 pb-3 text-2xl font-bold text-slate-800">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 text-white">
        <Icon className="h-5 w-5" />
      </div>
      {title}
    </h2>
  );
}

function SubSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h3 className="mb-3 text-lg font-semibold text-slate-700">{title}</h3>
      {children}
    </div>
  );
}

function Tip({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-4 flex gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-sm text-blue-800">
      <Info className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

function Warning({ children }: { children: React.ReactNode }) {
  return (
    <div className="my-4 flex gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{children}</div>
    </div>
  );
}

function Step({ number, title, children }: { number: number; title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4 flex gap-4">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
        {number}
      </div>
      <div className="flex-1">
        <p className="font-medium text-slate-800">{title}</p>
        <div className="mt-1 text-sm text-slate-600">{children}</div>
      </div>
    </div>
  );
}

function MockTable({ headers, rows }: { headers: string[]; rows: (string | number | React.ReactNode)[][] }) {
  return (
    <div className="my-4 overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50">
            {headers.map((h, i) => (
              <th key={i} className="whitespace-nowrap px-4 py-2.5 text-left font-semibold text-slate-700">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-slate-50/50">
              {row.map((cell, j) => (
                <td key={j} className="whitespace-nowrap px-4 py-2 text-slate-600">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PipelineArrow() {
  return (
    <div className="flex justify-center py-2">
      <ArrowDown className="h-5 w-5 text-blue-400" />
    </div>
  );
}

function StatusBadge({ status, label }: { status: string; label: string }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-700",
    confirmada: "bg-blue-100 text-blue-700",
    en_aduana: "bg-amber-100 text-amber-700",
    pagado: "bg-green-100 text-green-700",
    pendiente: "bg-yellow-100 text-yellow-700",
    borrador: "bg-slate-100 text-slate-600",
    liquidada: "bg-emerald-100 text-emerald-700",
  };
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${colors[status] || "bg-slate-100 text-slate-600"}`}>
      {label}
    </span>
  );
}

// ============================================================================
// TABLE OF CONTENTS
// ============================================================================
const tocItems = [
  { id: "inicio", icon: LogIn, label: "Inicio de Sesion" },
  { id: "dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { id: "proveedores", icon: Users, label: "Proveedores" },
  { id: "productos", icon: Package, label: "Productos" },
  { id: "ordenes", icon: ShoppingCart, label: "Ordenes de Compra" },
  { id: "importaciones", icon: Ship, label: "Importaciones" },
  { id: "gastos", icon: Receipt, label: "Gastos" },
  { id: "documentos", icon: FileText, label: "Documentos (DUA, Facturas)" },
  { id: "prorrateo", icon: Calculator, label: "Prorrateo y Costeo" },
  { id: "almacenes", icon: Warehouse, label: "Almacenes e Inventario" },
  { id: "movimientos", icon: ArrowLeftRight, label: "Movimientos" },
  { id: "kardex", icon: BookOpen, label: "Kardex SUNAT" },
  { id: "reportes", icon: BarChart3, label: "Reportes" },
  { id: "flujo", icon: Layers, label: "Flujo Completo" },
  { id: "glosario", icon: HelpCircle, label: "Glosario" },
];

// ============================================================================
// MAIN COMPONENT
// ============================================================================
export default function ManualPage() {
  const [activeSection, setActiveSection] = useState("inicio");

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <div className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-6 py-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600">
            <Ship className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-800">ImportCost Pro</h1>
            <p className="text-xs text-slate-500">Manual de Usuario v1.0</p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => window.print()}>
              <Printer className="mr-1.5 h-3.5 w-3.5" />
              Imprimir
            </Button>
          </div>
        </div>
      </div>

      <div className="mx-auto flex max-w-7xl gap-8 px-6 py-8">
        {/* Sidebar TOC */}
        <nav className="sticky top-24 hidden h-fit w-64 shrink-0 lg:block">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">Contenido</p>
          <div className="space-y-0.5">
            {tocItems.map((item) => (
              <a
                key={item.id}
                href={`#${item.id}`}
                onClick={() => setActiveSection(item.id)}
                className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition-colors ${
                  activeSection === item.id
                    ? "bg-blue-50 font-medium text-blue-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-800"
                }`}
              >
                <item.icon className="h-3.5 w-3.5 shrink-0" />
                {item.label}
              </a>
            ))}
          </div>
        </nav>

        {/* Content */}
        <main className="min-w-0 flex-1">
          {/* ================================================================ */}
          {/* INTRODUCCION */}
          {/* ================================================================ */}
          <div className="mb-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 p-8 text-white">
            <h1 className="mb-2 text-3xl font-bold">Manual de Usuario</h1>
            <p className="mb-6 text-blue-100">
              Sistema de Costeo de Importaciones para Pymes peruanas.
              Gestione todo el ciclo de importacion desde la orden de compra hasta el costeo final y control de inventario.
            </p>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[
                { icon: ShoppingCart, label: "Ordenes", value: "Gestion OC" },
                { icon: Ship, label: "Importaciones", value: "Pipeline 5 etapas" },
                { icon: Calculator, label: "Prorrateo", value: "Costeo exacto" },
                { icon: BookOpen, label: "Kardex", value: "Formato SUNAT" },
              ].map((item, i) => (
                <div key={i} className="rounded-lg bg-white/10 p-3 backdrop-blur">
                  <item.icon className="mb-1 h-5 w-5 text-blue-200" />
                  <p className="text-xs text-blue-200">{item.label}</p>
                  <p className="text-sm font-semibold">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ================================================================ */}
          {/* 1. INICIO DE SESION */}
          {/* ================================================================ */}
          <SectionTitle icon={LogIn} title="1. Inicio de Sesion" id="inicio" />

          <p className="mb-4 text-slate-600">
            Al acceder al sistema, se mostrara la pantalla de login. Ingrese sus credenciales para acceder.
          </p>

          <Card className="mb-6 max-w-sm mx-auto">
            <CardContent className="p-6">
              <div className="mb-4 flex flex-col items-center">
                <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600">
                  <Ship className="h-7 w-7 text-white" />
                </div>
                <p className="font-bold text-slate-800">ImportCost Pro</p>
                <p className="text-xs text-slate-500">Sistema de Costeo de Importaciones</p>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="mb-1 text-xs font-medium text-slate-600">Correo electronico</p>
                  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">admin@importdemo.pe</div>
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium text-slate-600">Contrasena</p>
                  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">********</div>
                </div>
                <div className="rounded-md bg-blue-600 py-2 text-center text-sm font-medium text-white">Iniciar Sesion</div>
              </div>
            </CardContent>
          </Card>

          <Tip>
            <strong>Credenciales de demo:</strong> admin@importdemo.pe / admin123
          </Tip>

          <SubSection title="Roles de usuario">
            <MockTable
              headers={["Rol", "Permisos"]}
              rows={[
                [<Badge key="a" className="bg-purple-100 text-purple-700">admin</Badge>, "Acceso total: CRUD, configuracion, reportes, usuarios"],
                [<Badge key="u" className="bg-blue-100 text-blue-700">usuario</Badge>, "Crear y editar registros, ver reportes"],
                [<Badge key="r" className="bg-slate-100 text-slate-700">readonly</Badge>, "Solo lectura: consultas y reportes"],
              ]}
            />
          </SubSection>

          {/* ================================================================ */}
          {/* 2. DASHBOARD */}
          {/* ================================================================ */}
          <SectionTitle icon={LayoutDashboard} title="2. Dashboard" id="dashboard" />

          <p className="mb-4 text-slate-600">
            El dashboard muestra un resumen ejecutivo de sus operaciones de importacion.
          </p>

          <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { label: "Importaciones Activas", value: "8", icon: Ship, color: "text-blue-600 bg-blue-50" },
              { label: "FOB Total (USD)", value: "$125,430", icon: DollarSign, color: "text-green-600 bg-green-50" },
              { label: "OCs Pendientes", value: "12", icon: ShoppingCart, color: "text-amber-600 bg-amber-50" },
              { label: "Gastos del Mes", value: "S/ 45,200", icon: CreditCard, color: "text-red-600 bg-red-50" },
            ].map((m, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <div className={`mb-2 flex h-8 w-8 items-center justify-center rounded-lg ${m.color}`}>
                    <m.icon className="h-4 w-4" />
                  </div>
                  <p className="text-2xl font-bold text-slate-800">{m.value}</p>
                  <p className="text-xs text-slate-500">{m.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          <SubSection title="Pipeline de Importaciones">
            <p className="mb-3 text-sm text-slate-600">
              Visualice el estado de todas sus importaciones en las 5 etapas del proceso:
            </p>
            <div className="flex flex-wrap items-center gap-2">
              {[
                { label: "Borrador", count: 2, color: "bg-slate-200 text-slate-700" },
                { label: "Confirmada", count: 3, color: "bg-blue-200 text-blue-700" },
                { label: "En Transito", count: 2, color: "bg-cyan-200 text-cyan-700" },
                { label: "En Aduana", count: 1, color: "bg-amber-200 text-amber-700" },
                { label: "Liquidada", count: 5, color: "bg-green-200 text-green-700" },
              ].map((s, i) => (
                <div key={i} className="flex items-center gap-1">
                  <div className={`rounded-lg px-3 py-2 text-center ${s.color}`}>
                    <p className="text-lg font-bold">{s.count}</p>
                    <p className="text-xs">{s.label}</p>
                  </div>
                  {i < 4 && <ArrowRight className="h-4 w-4 text-slate-300" />}
                </div>
              ))}
            </div>
          </SubSection>

          <SubSection title="Buscador Global">
            <p className="text-sm text-slate-600">
              Use la barra de busqueda para encontrar rapidamente cualquier registro: ordenes, importaciones, proveedores o productos por numero o nombre.
            </p>
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
              <Search className="h-4 w-4 text-slate-400" />
              <span className="text-sm text-slate-400">Buscar OC, importacion, proveedor...</span>
            </div>
          </SubSection>

          {/* ================================================================ */}
          {/* 3. PROVEEDORES */}
          {/* ================================================================ */}
          <SectionTitle icon={Users} title="3. Proveedores" id="proveedores" />

          <p className="mb-4 text-slate-600">
            Registre y gestione sus proveedores internacionales. Cada proveedor queda vinculado a sus ordenes de compra y gastos.
          </p>

          <SubSection title="Lista de Proveedores">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-500">
                  <Search className="h-3.5 w-3.5" /> Buscar proveedor...
                </div>
                <div className="flex items-center gap-1.5 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-500">
                  <Filter className="h-3.5 w-3.5" /> Estado
                </div>
              </div>
              <div className="flex items-center gap-1 rounded-md bg-blue-600 px-3 py-1.5 text-sm text-white">
                <Plus className="h-3.5 w-3.5" /> Nuevo Proveedor
              </div>
            </div>
            <MockTable
              headers={["RUC", "Razon Social", "Pais", "Moneda", "Incoterm", "OCs", "Estado", "Acciones"]}
              rows={mockProveedores.map((p) => [
                p.ruc,
                <span key={p.id} className="font-medium text-slate-800">{p.razon_social}</span>,
                <span key={p.id} className="flex items-center gap-1"><Globe className="h-3 w-3" />{p.pais}</span>,
                <Badge key={p.id} variant="outline">{p.moneda}</Badge>,
                p.incoterm,
                <span key={p.id} className="font-medium">{p.ocs}</span>,
                <StatusBadge key={p.id} status={p.status} label="Activo" />,
                <span key={p.id} className="flex gap-1">
                  <Eye className="h-4 w-4 text-slate-400" />
                  <Edit className="h-4 w-4 text-blue-400" />
                  <Trash2 className="h-4 w-4 text-red-400" />
                </span>,
              ])}
            />
          </SubSection>

          <SubSection title="Campos del Proveedor">
            <MockTable
              headers={["Campo", "Descripcion", "Requerido"]}
              rows={[
                ["RUC / Tax ID", "Registro fiscal del proveedor", <CheckCircle2 key="1" className="h-4 w-4 text-green-500" />],
                ["Razon Social", "Nombre legal completo", <CheckCircle2 key="2" className="h-4 w-4 text-green-500" />],
                ["Nombre Comercial", "Nombre corto o marca", "No"],
                ["Pais", "Pais de origen (seleccion de 30+)", <CheckCircle2 key="3" className="h-4 w-4 text-green-500" />],
                ["Es Extranjero", "Indica si aplica regimen de importacion", <CheckCircle2 key="4" className="h-4 w-4 text-green-500" />],
                ["Moneda Default", "USD, EUR, CNY, etc.", <CheckCircle2 key="5" className="h-4 w-4 text-green-500" />],
                ["Incoterm Default", "FOB, CIF, EXW, CFR, etc.", "No"],
                ["Email / Telefono", "Datos de contacto", "No"],
                ["Contacto", "Nombre del representante", "No"],
              ]}
            />
          </SubSection>

          {/* ================================================================ */}
          {/* 4. PRODUCTOS */}
          {/* ================================================================ */}
          <SectionTitle icon={Package} title="4. Productos" id="productos" />

          <p className="mb-4 text-slate-600">
            Mantenga su catalogo de productos con clasificacion arancelaria, pesos y volumenes necesarios para el calculo de tributos y prorrateo.
          </p>

          <MockTable
            headers={["SKU", "Nombre", "Categoria", "Codigo HS", "Peso (kg)", "Stock", "Costo Landed"]}
            rows={mockProductos.map((p) => [
              <span key={p.sku} className="font-mono text-xs">{p.sku}</span>,
              <span key={p.sku} className="font-medium text-slate-800">{p.nombre}</span>,
              <Badge key={p.sku} variant="outline">{p.categoria}</Badge>,
              <span key={p.sku} className="font-mono text-xs">{p.hs}</span>,
              p.peso.toFixed(1),
              <span key={p.sku} className={p.stock < 100 ? "font-medium text-amber-600" : "text-green-600"}>{p.stock}</span>,
              <span key={p.sku} className="font-medium">S/ {p.costo.toFixed(2)}</span>,
            ])}
          />

          <Tip>
            <strong>Codigo HS (Partida Arancelaria):</strong> Al ingresar el codigo HS, el sistema busca automaticamente la partida arancelaria correspondiente y su tasa de Ad Valorem para el calculo de tributos en la DUA.
          </Tip>

          <SubSection title="Campos importantes">
            <MockTable
              headers={["Campo", "Para que sirve"]}
              rows={[
                ["Codigo HS", "Clasificacion arancelaria - determina la tasa de Ad Valorem"],
                ["Peso (kg)", "Usado en prorrateo por peso"],
                ["Volumen (m3)", "Usado en prorrateo por volumen"],
                ["Unidad Medida", "NIU (unidad), KG, LT, MT - para Kardex SUNAT"],
                ["Proveedor Default", "Pre-seleccionado al crear OC"],
              ]}
            />
          </SubSection>

          {/* ================================================================ */}
          {/* 5. ORDENES DE COMPRA */}
          {/* ================================================================ */}
          <SectionTitle icon={ShoppingCart} title="5. Ordenes de Compra" id="ordenes" />

          <p className="mb-4 text-slate-600">
            Las Ordenes de Compra son el punto de partida del proceso de importacion. Aqui registra que compra, a quien, y a que precio FOB.
          </p>

          <SubSection title="Ejemplo de OC">
            <Card className="mb-4">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">{mockOrden.numero}</CardTitle>
                    <p className="text-sm text-slate-500">{mockOrden.proveedor} | {mockOrden.fecha}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{mockOrden.moneda}</Badge>
                    <Badge variant="outline">{mockOrden.incoterm}</Badge>
                    <StatusBadge status={mockOrden.estado} label="Confirmada" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <MockTable
                  headers={["Producto", "Cantidad", "Precio Unit.", "Subtotal"]}
                  rows={[
                    ...mockOrden.items.map((it) => [
                      it.producto,
                      it.cantidad.toLocaleString(),
                      `$ ${it.precio.toFixed(2)}`,
                      `$ ${it.subtotal.toLocaleString("en", { minimumFractionDigits: 2 })}`,
                    ]),
                    [
                      <span key="t" className="font-bold">TOTAL FOB</span>,
                      "",
                      "",
                      <span key="tv" className="font-bold text-blue-700">$ {mockOrden.total_fob.toLocaleString("en", { minimumFractionDigits: 2 })}</span>,
                    ],
                  ]}
                />
              </CardContent>
            </Card>
          </SubSection>

          <SubSection title="Estados de la OC">
            <div className="flex flex-wrap gap-2">
              {[
                { status: "borrador", label: "Borrador", desc: "OC en preparacion" },
                { status: "confirmada", label: "Confirmada", desc: "Enviada al proveedor" },
                { status: "en_transito", label: "En Transito", desc: "Mercancia embarcada" },
                { status: "en_aduana", label: "En Aduana", desc: "Despacho aduanero" },
                { status: "liquidada", label: "Liquidada", desc: "Proceso completo" },
              ].map((s) => (
                <div key={s.status} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2">
                  <StatusBadge status={s.status} label={s.label} />
                  <span className="text-xs text-slate-500">{s.desc}</span>
                </div>
              ))}
            </div>
          </SubSection>

          <SubSection title="Detalle de la OC">
            <Step number={1} title="Agregar Items">
              En el detalle de la OC, use el boton "Agregar Item" para anadir productos con cantidad y precio unitario.
            </Step>
            <Step number={2} title="Cambiar Estado">
              Use los botones de transicion de estado (ej: Borrador &rarr; Confirmada) para avanzar la OC en el pipeline.
            </Step>
            <Step number={3} title="Vincular a Importacion">
              Asocie la OC a una importacion para que participe en el calculo de prorrateo.
            </Step>
          </SubSection>

          {/* ================================================================ */}
          {/* 6. IMPORTACIONES */}
          {/* ================================================================ */}
          <SectionTitle icon={Ship} title="6. Importaciones" id="importaciones" />

          <p className="mb-4 text-slate-600">
            Una importacion agrupa una o varias OCs que viajan en un mismo embarque. Aqui registra datos de transporte, BL, container, etc.
          </p>

          <Card className="mb-6">
            <CardContent className="p-5">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-lg font-bold text-slate-800">{mockImportacion.numero}</p>
                  <p className="text-sm text-slate-500">{mockImportacion.descripcion}</p>
                </div>
                <StatusBadge status={mockImportacion.estado} label="En Aduana" />
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                <div>
                  <p className="text-slate-500">Via</p>
                  <p className="flex items-center gap-1 font-medium"><Truck className="h-3.5 w-3.5" /> Maritimo</p>
                </div>
                <div>
                  <p className="text-slate-500">BL</p>
                  <p className="font-mono text-xs font-medium">{mockImportacion.bl}</p>
                </div>
                <div>
                  <p className="text-slate-500">Container</p>
                  <p className="font-mono text-xs font-medium">{mockImportacion.container}</p>
                </div>
                <div>
                  <p className="text-slate-500">FOB Total</p>
                  <p className="font-bold text-blue-700">$ {mockImportacion.fob_total.toLocaleString()}</p>
                </div>
              </div>
              <div className="mt-4 border-t border-slate-100 pt-3">
                <p className="mb-1 text-xs font-medium text-slate-500">OCs Asociadas:</p>
                <div className="flex gap-2">
                  {mockImportacion.ocs.map((oc) => (
                    <Badge key={oc} variant="outline" className="font-mono text-xs">{oc}</Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <SubSection title="Vias de Transporte">
            <div className="flex flex-wrap gap-2">
              {[
                { via: "Maritimo", icon: Ship },
                { via: "Aereo", icon: Globe },
                { via: "Terrestre", icon: Truck },
                { via: "Multimodal", icon: Layers },
              ].map((v) => (
                <div key={v.via} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                  <v.icon className="h-4 w-4 text-blue-500" />
                  {v.via}
                </div>
              ))}
            </div>
          </SubSection>

          <Warning>
            <strong>Importante:</strong> Asocie las OCs a la importacion ANTES de registrar gastos y documentos. Esto permite que el prorrateo distribuya correctamente los costos entre los items de todas las OCs.
          </Warning>

          {/* ================================================================ */}
          {/* 7. GASTOS */}
          {/* ================================================================ */}
          <SectionTitle icon={Receipt} title="7. Gastos de Importacion" id="gastos" />

          <p className="mb-4 text-slate-600">
            Registre todos los gastos asociados a cada importacion. El sistema categoriza los gastos por tipo para el prorrateo.
          </p>

          <MockTable
            headers={["Tipo", "Monto", "Moneda", "Comprobante", "Estado"]}
            rows={mockGastos.map((g, i) => [
              <span key={i} className="font-medium">{g.tipo}</span>,
              g.monto.toLocaleString("en", { minimumFractionDigits: 2 }),
              <Badge key={i} variant="outline">{g.moneda}</Badge>,
              <span key={i} className="font-mono text-xs">{g.comprobante}</span>,
              <StatusBadge key={i} status={g.estado} label={g.estado === "pagado" ? "Pagado" : "Pendiente"} />,
            ])}
          />

          <SubSection title="Tipos de Gasto">
            <p className="mb-3 text-sm text-slate-600">El sistema incluye 11 tipos de gasto predefinidos:</p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {[
                "Flete Internacional", "Seguro", "Agente de Aduanas",
                "Almacenaje", "Transporte Local", "Handling",
                "Comision Bancaria", "Estiba", "Inspeccion",
                "Documentacion", "Otros Gastos",
              ].map((t) => (
                <div key={t} className="flex items-center gap-2 rounded border border-slate-100 px-2 py-1.5 text-xs text-slate-600">
                  <div className="h-2 w-2 rounded-full bg-blue-400" />
                  {t}
                </div>
              ))}
            </div>
          </SubSection>

          <Tip>
            Los gastos en moneda extranjera se convierten automaticamente a PEN usando el tipo de cambio registrado. Puede registrar el tipo de cambio del dia en <strong>Catalogos &rarr; Tipo de Cambio</strong>.
          </Tip>

          {/* ================================================================ */}
          {/* 8. DOCUMENTOS */}
          {/* ================================================================ */}
          <SectionTitle icon={FileText} title="8. Documentos" id="documentos" />

          <SubSection title="DUA - Declaracion Unica de Aduanas">
            <p className="mb-4 text-sm text-slate-600">
              La DUA es el documento clave para el calculo de tributos de importacion. El sistema calcula automaticamente todos los tributos basado en las formulas de SUNAT.
            </p>

            <Card className="mb-4">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="h-4 w-4 text-blue-500" />
                  DUA {mockDUA.numero}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">CIF (S/)</p>
                    <p className="text-lg font-bold">S/ {mockDUA.cif_soles.toLocaleString()}</p>
                  </div>
                  <div className="rounded-lg bg-blue-50 p-3">
                    <p className="text-xs text-blue-600">Ad Valorem</p>
                    <p className="text-lg font-bold text-blue-700">S/ {mockDUA.ad_valorem.toLocaleString()}</p>
                  </div>
                  <div className="rounded-lg bg-amber-50 p-3">
                    <p className="text-xs text-amber-600">IGV (18%)</p>
                    <p className="text-lg font-bold text-amber-700">S/ {mockDUA.igv.toLocaleString()}</p>
                  </div>
                  <div className="rounded-lg bg-orange-50 p-3">
                    <p className="text-xs text-orange-600">IPM (2%)</p>
                    <p className="text-lg font-bold text-orange-700">S/ {mockDUA.ipm.toLocaleString()}</p>
                  </div>
                  <div className="rounded-lg bg-purple-50 p-3">
                    <p className="text-xs text-purple-600">Percepcion (3.5%)</p>
                    <p className="text-lg font-bold text-purple-700">S/ {mockDUA.percepcion.toLocaleString()}</p>
                  </div>
                  <div className="rounded-lg bg-red-50 p-3">
                    <p className="text-xs text-red-600">Total Tributos</p>
                    <p className="text-lg font-bold text-red-700">S/ {mockDUA.total_tributos.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <SubSection title="Formulas de Calculo de Tributos">
              <div className="space-y-2 rounded-lg bg-slate-900 p-4 font-mono text-xs text-green-400">
                <p><span className="text-slate-500">// Base</span></p>
                <p>CIF = FOB + Flete + Seguro</p>
                <p>&nbsp;</p>
                <p><span className="text-slate-500">// Tributos</span></p>
                <p>Ad Valorem = CIF * tasa_partida (ej: 6%)</p>
                <p>Base IGV  = CIF + Ad Valorem</p>
                <p>IGV       = Base IGV * 16%</p>
                <p>IPM       = Base IGV * 2%</p>
                <p>&nbsp;</p>
                <p><span className="text-slate-500">// Percepcion</span></p>
                <p>Base Perc  = CIF + Ad Valorem + IGV + IPM</p>
                <p>Percepcion = Base Perc * 3.5%</p>
              </div>
            </SubSection>
          </SubSection>

          <SubSection title="Facturas del Proveedor">
            <p className="text-sm text-slate-600">
              Registre las facturas comerciales (Commercial Invoice) emitidas por el proveedor. Incluya numero, fecha, monto y detalle de items.
            </p>
          </SubSection>

          <SubSection title="Documento de Transporte">
            <p className="text-sm text-slate-600">
              Registre el BL (Bill of Lading), AWB (Air Waybill) o Carta Porte segun la via de transporte utilizada.
            </p>
          </SubSection>

          {/* ================================================================ */}
          {/* 9. PRORRATEO */}
          {/* ================================================================ */}
          <SectionTitle icon={Calculator} title="9. Prorrateo y Costeo" id="prorrateo" />

          <p className="mb-4 text-slate-600">
            El prorrateo es el <strong>corazon del sistema</strong>. Distribuye todos los costos (flete, seguro, tributos, gastos) entre los items de las OCs para obtener el costo landed (costo real) de cada producto.
          </p>

          <SubSection title="Proceso de 3 Pasos">
            <div className="mb-6 space-y-1">
              <Step number={1} title="Seleccionar Importacion">
                Elija la importacion que desea costear. El sistema muestra todas las OCs asociadas y sus totales.
              </Step>
              <Step number={2} title="Calcular Prorrateo">
                Seleccione el metodo de distribucion y presione "Calcular". El sistema genera la propuesta de distribucion sin aplicarla.
              </Step>
              <Step number={3} title="Aplicar Prorrateo">
                Revise los resultados y presione "Aplicar" para guardar los costos prorrateados en cada item.
              </Step>
            </div>
          </SubSection>

          <SubSection title="Metodos de Prorrateo">
            <MockTable
              headers={["Metodo", "Distribuye segun", "Cuando usar"]}
              rows={[
                [<span key="1" className="font-medium">valor_fob</span>, "Proporcion del valor FOB de cada item", "Metodo mas comun y recomendado"],
                [<span key="2" className="font-medium">peso</span>, "Peso (kg) de cada item", "Cuando el flete se cobra por peso"],
                [<span key="3" className="font-medium">volumen</span>, "Volumen (m3) de cada item", "Cuando el flete se cobra por volumen"],
                [<span key="4" className="font-medium">cantidad</span>, "Cantidad de unidades", "Items homogeneos del mismo tipo"],
              ]}
            />
          </SubSection>

          <SubSection title="Resultado del Prorrateo (Ejemplo)">
            <div className="overflow-x-auto">
              <MockTable
                headers={["Producto", "FOB", "%", "Flete", "Seguro", "Tributos", "Gastos", "Landed", "Qty", "Costo/U"]}
                rows={mockProrrateo.items.map((it) => [
                  <span key={it.producto} className="font-medium text-slate-800">{it.producto}</span>,
                  `$ ${it.fob.toLocaleString()}`,
                  `${it.pct.toFixed(1)}%`,
                  `$ ${it.flete.toLocaleString()}`,
                  `$ ${it.seguro.toFixed(0)}`,
                  `S/ ${it.tributos.toLocaleString()}`,
                  `S/ ${it.gastos.toLocaleString()}`,
                  <span key={it.producto} className="font-bold text-emerald-700">S/ {it.landed.toLocaleString()}</span>,
                  it.qty,
                  <span key={it.producto} className="font-bold text-blue-700">S/ {it.unit_cost.toFixed(2)}</span>,
                ])}
              />
            </div>
          </SubSection>

          <SubSection title="Ficha de Costeo">
            <p className="text-sm text-slate-600">
              Acceda a la <strong>Ficha de Costeo</strong> desde el detalle de cada OC. Muestra el desglose completo del costo landed por producto, lista para imprimir o exportar.
            </p>
            <Tip>
              La Ficha de Costeo es el reporte que normalmente se entrega a contabilidad o gerencia para justificar el costo de cada producto importado.
            </Tip>
          </SubSection>

          {/* ================================================================ */}
          {/* 10. ALMACENES */}
          {/* ================================================================ */}
          <SectionTitle icon={Warehouse} title="10. Almacenes e Inventario" id="almacenes" />

          <SubSection title="Gestion de Almacenes">
            <p className="mb-3 text-sm text-slate-600">
              Cree y administre sus almacenes o bodegas. Cada almacen tiene su propio stock independiente.
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                { nombre: "Almacen Central", ubicacion: "Lima - Ate", items: 45, valor: "S/ 125,000" },
                { nombre: "Deposito Callao", ubicacion: "Callao", items: 12, valor: "S/ 42,500" },
                { nombre: "Tienda San Isidro", ubicacion: "Lima - San Isidro", items: 28, valor: "S/ 68,200" },
              ].map((a) => (
                <Card key={a.nombre}>
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <Warehouse className="h-4 w-4 text-blue-500" />
                      <p className="font-semibold text-slate-800">{a.nombre}</p>
                    </div>
                    <p className="flex items-center gap-1 text-xs text-slate-500"><MapPin className="h-3 w-3" />{a.ubicacion}</p>
                    <div className="mt-3 flex justify-between text-sm">
                      <span className="text-slate-500">{a.items} productos</span>
                      <span className="font-bold text-green-700">{a.valor}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </SubSection>

          <SubSection title="Vista de Inventario">
            <p className="text-sm text-slate-600">
              La pagina de Inventario muestra el stock actual por almacen con indicadores de color:
              <span className="text-green-600 font-medium"> verde</span> (suficiente),
              <span className="text-amber-600 font-medium"> amarillo</span> (bajo), y
              <span className="text-red-600 font-medium"> rojo</span> (critico/agotado).
            </p>
          </SubSection>

          {/* ================================================================ */}
          {/* 11. MOVIMIENTOS */}
          {/* ================================================================ */}
          <SectionTitle icon={ArrowLeftRight} title="11. Movimientos de Almacen" id="movimientos" />

          <SubSection title="Tipos de Movimiento">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                { tipo: "Ingreso", desc: "Recepcion de mercaderia importada al almacen. Se ingresa con el costo landed del prorrateo.", color: "bg-green-100 text-green-700 border-green-200", icon: ArrowDown },
                { tipo: "Transferencia", desc: "Movimiento entre almacenes propios. Origen y destino deben ser diferentes.", color: "bg-blue-100 text-blue-700 border-blue-200", icon: ArrowLeftRight },
                { tipo: "Salida", desc: "Despacho o venta. Reduce el stock del almacen de origen.", color: "bg-red-100 text-red-700 border-red-200", icon: TrendingUp },
              ].map((m) => (
                <Card key={m.tipo} className={`border ${m.color.split(" ")[2]}`}>
                  <CardContent className="p-4">
                    <div className="mb-2 flex items-center gap-2">
                      <m.icon className="h-5 w-5" />
                      <Badge className={m.color}>{m.tipo}</Badge>
                    </div>
                    <p className="text-xs text-slate-600">{m.desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </SubSection>

          <SubSection title="Flujo de un Movimiento">
            <Step number={1} title="Crear Movimiento">Seleccione tipo, almacen origen (y destino si es transferencia), y referencia.</Step>
            <Step number={2} title="Agregar Items">Indique producto, cantidad y costo unitario para cada linea.</Step>
            <Step number={3} title="Completar">Presione "Completar" para ejecutar el movimiento y actualizar el stock.</Step>
          </SubSection>

          <Warning>
            Una vez completado, el movimiento no se puede revertir. Verifique las cantidades antes de completar.
          </Warning>

          {/* ================================================================ */}
          {/* 12. KARDEX */}
          {/* ================================================================ */}
          <SectionTitle icon={BookOpen} title="12. Kardex SUNAT" id="kardex" />

          <p className="mb-4 text-slate-600">
            El Kardex sigue el formato requerido por SUNAT (Registro de Inventario Permanente Valorizado). Muestra entradas, salidas y saldos valorados.
          </p>

          <SubSection title="Formato Kardex">
            <div className="overflow-x-auto">
              <MockTable
                headers={["Fecha", "Tipo", "Documento", "Entrada Qty", "Entrada C/U", "Entrada Total", "Salida Qty", "Salida C/U", "Salida Total", "Saldo Qty", "Saldo C/U", "Saldo Total"]}
                rows={mockKardex.map((k, i) => [
                  k.fecha,
                  <Badge key={i} className={k.tipo === "INGRESO" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}>{k.tipo}</Badge>,
                  <span key={i} className="font-mono text-xs">{k.doc}</span>,
                  k.entrada_qty || "-",
                  k.entrada_cu ? `S/ ${k.entrada_cu.toFixed(2)}` : "-",
                  k.entrada_ct ? `S/ ${k.entrada_ct.toLocaleString()}` : "-",
                  k.salida_qty || "-",
                  k.salida_cu ? `S/ ${k.salida_cu.toFixed(2)}` : "-",
                  k.salida_ct ? `S/ ${k.salida_ct.toLocaleString()}` : "-",
                  <span key={i} className="font-medium">{k.saldo_qty}</span>,
                  `S/ ${k.saldo_cu.toFixed(2)}`,
                  <span key={i} className="font-bold">S/ {k.saldo_ct.toLocaleString()}</span>,
                ])}
              />
            </div>
          </SubSection>

          <SubSection title="Filtros">
            <p className="text-sm text-slate-600">Filtre el Kardex por producto, almacen y rango de fechas. El sistema calcula automaticamente los saldos acumulados.</p>
          </SubSection>

          {/* ================================================================ */}
          {/* 13. REPORTES */}
          {/* ================================================================ */}
          <SectionTitle icon={BarChart3} title="13. Reportes" id="reportes" />

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-blue-500" />
                  <p className="font-semibold">Resumen Mensual</p>
                </div>
                <p className="text-xs text-slate-600">Total FOB, CIF, tributos y gastos agrupados por mes. Ideal para analisis de tendencias.</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Users className="h-4 w-4 text-green-500" />
                  <p className="font-semibold">Por Proveedor</p>
                </div>
                <p className="text-xs text-slate-600">Comparativo de costos por proveedor: FOB promedio, tiempo de entrega, frecuencia de compra.</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Package className="h-4 w-4 text-purple-500" />
                  <p className="font-semibold">Por Producto</p>
                </div>
                <p className="text-xs text-slate-600">Evolucion del costo landed por producto. Identifique variaciones y tendencias de precio.</p>
              </CardContent>
            </Card>
          </div>

          {/* ================================================================ */}
          {/* 14. FLUJO COMPLETO */}
          {/* ================================================================ */}
          <SectionTitle icon={Layers} title="14. Flujo Completo de Importacion" id="flujo" />

          <p className="mb-6 text-slate-600">
            A continuacion se muestra el flujo completo de una importacion tipica, paso a paso:
          </p>

          <div className="mx-auto max-w-lg space-y-0">
            {[
              { icon: Settings, label: "1. Configuracion Inicial", desc: "Registrar proveedores, productos, almacenes", color: "bg-slate-600" },
              { icon: ShoppingCart, label: "2. Crear Orden de Compra", desc: "Seleccionar proveedor, agregar items, precio FOB", color: "bg-blue-600" },
              { icon: Ship, label: "3. Crear Importacion", desc: "Datos de embarque: BL, container, via transporte", color: "bg-cyan-600" },
              { icon: ClipboardList, label: "4. Asociar OCs", desc: "Vincular ordenes de compra a la importacion", color: "bg-indigo-600" },
              { icon: Receipt, label: "5. Registrar Gastos", desc: "Flete, seguro, agente, almacenaje, etc.", color: "bg-amber-600" },
              { icon: FileText, label: "6. Registrar DUA", desc: "Numero DUA, items, calculo de tributos", color: "bg-orange-600" },
              { icon: Calculator, label: "7. Ejecutar Prorrateo", desc: "Distribuir costos entre items por metodo elegido", color: "bg-red-600" },
              { icon: Eye, label: "8. Revisar Ficha de Costeo", desc: "Verificar costo landed por producto", color: "bg-pink-600" },
              { icon: ArrowDown, label: "9. Ingreso a Almacen", desc: "Crear movimiento de ingreso con costo landed", color: "bg-green-600" },
              { icon: BookOpen, label: "10. Consultar Kardex", desc: "Verificar stock valorizado formato SUNAT", color: "bg-emerald-600" },
            ].map((step, i) => (
              <div key={i}>
                <div className="flex items-start gap-3">
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white ${step.color}`}>
                    <step.icon className="h-5 w-5" />
                  </div>
                  <div className="pt-1">
                    <p className="font-semibold text-slate-800">{step.label}</p>
                    <p className="text-sm text-slate-500">{step.desc}</p>
                  </div>
                </div>
                {i < 9 && (
                  <div className="ml-5 flex h-6 items-center">
                    <div className="h-full w-px bg-slate-300" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* ================================================================ */}
          {/* 15. GLOSARIO */}
          {/* ================================================================ */}
          <SectionTitle icon={HelpCircle} title="15. Glosario" id="glosario" />

          <MockTable
            headers={["Termino", "Definicion"]}
            rows={[
              [<span key="1" className="font-mono font-bold">FOB</span>, "Free On Board - Precio de la mercancia puesta en el puerto de origen"],
              [<span key="2" className="font-mono font-bold">CIF</span>, "Cost, Insurance & Freight - FOB + Flete + Seguro"],
              [<span key="3" className="font-mono font-bold">DUA</span>, "Declaracion Unica de Aduanas - Documento de despacho aduanero peruano"],
              [<span key="4" className="font-mono font-bold">Ad Valorem</span>, "Arancel de importacion calculado sobre el CIF segun partida arancelaria"],
              [<span key="5" className="font-mono font-bold">IGV</span>, "Impuesto General a las Ventas (18% = 16% IGV + 2% IPM)"],
              [<span key="6" className="font-mono font-bold">IPM</span>, "Impuesto de Promocion Municipal (2%)"],
              [<span key="7" className="font-mono font-bold">Percepcion</span>, "Pago adelantado de IGV (3.5% sobre CIF + tributos)"],
              [<span key="8" className="font-mono font-bold">Incoterm</span>, "Termino de comercio internacional que define responsabilidades (FOB, CIF, EXW, etc.)"],
              [<span key="9" className="font-mono font-bold">BL</span>, "Bill of Lading - Conocimiento de embarque maritimo"],
              [<span key="10" className="font-mono font-bold">AWB</span>, "Air Waybill - Guia aerea de transporte"],
              [<span key="11" className="font-mono font-bold">Partida Arancelaria</span>, "Codigo HS de 10 digitos que clasifica la mercancia para tributos"],
              [<span key="12" className="font-mono font-bold">Prorrateo</span>, "Distribucion proporcional de costos entre los items importados"],
              [<span key="13" className="font-mono font-bold">Costo Landed</span>, "Costo total real del producto: FOB + todos los gastos prorrateados"],
              [<span key="14" className="font-mono font-bold">Kardex</span>, "Registro de inventario permanente valorizado (requerido por SUNAT)"],
              [<span key="15" className="font-mono font-bold">TLC</span>, "Tratado de Libre Comercio - Puede reducir/eliminar el Ad Valorem"],
            ]}
          />

          {/* Footer */}
          <div className="mt-16 border-t border-slate-200 pt-8 text-center text-sm text-slate-400">
            <div className="mb-2 flex justify-center">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                <Ship className="h-5 w-5 text-white" />
              </div>
            </div>
            <p className="font-medium text-slate-600">ImportCost Pro v1.0</p>
            <p>Sistema de Costeo de Importaciones para Pymes - Peru</p>
            <p className="mt-1">Manual generado el {new Date().toLocaleDateString("es-PE")}</p>
          </div>
        </main>
      </div>
    </div>
  );
}
