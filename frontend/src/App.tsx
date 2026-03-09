import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, ProtectedRoute } from "@/lib/auth";
import AppLayout from "@/components/layout/AppLayout";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ProveedoresPage from "@/pages/proveedores/ProveedoresPage";
import ProveedorFormPage from "@/pages/proveedores/ProveedorFormPage";
import ProductosPage from "@/pages/productos/ProductosPage";
import ProductoFormPage from "@/pages/productos/ProductoFormPage";
import OrdenesPage from "@/pages/ordenes/OrdenesPage";
import OrdenFormPage from "@/pages/ordenes/OrdenFormPage";
import OrdenDetailPage from "@/pages/ordenes/OrdenDetailPage";
import ImportacionesPage from "@/pages/importaciones/ImportacionesPage";
import ImportacionFormPage from "@/pages/importaciones/ImportacionFormPage";
import ImportacionDetailPage from "@/pages/importaciones/ImportacionDetailPage";
import GastosPage from "@/pages/gastos/GastosPage";
import GastoFormPage from "@/pages/gastos/GastoFormPage";
import ProrrateoPage from "@/pages/prorrateo/ProrrateoPage";
import FichaCosteoPage from "@/pages/prorrateo/FichaCosteoPage";
import DuaListPage from "@/pages/documentos/DuaListPage";
import DuaFormPage from "@/pages/documentos/DuaFormPage";
import TransporteFormPage from "@/pages/documentos/TransporteFormPage";
import FacturasPage from "@/pages/documentos/FacturasPage";
import FacturaFormPage from "@/pages/documentos/FacturaFormPage";
import AlmacenesPage from "@/pages/almacenes/AlmacenesPage";
import InventarioPage from "@/pages/almacenes/InventarioPage";
import MovimientosPage from "@/pages/movimientos/MovimientosPage";
import MovimientoFormPage from "@/pages/movimientos/MovimientoFormPage";
import MovimientoDetailPage from "@/pages/movimientos/MovimientoDetailPage";
import KardexPage from "@/pages/inventario/KardexPage";
import StockDisponiblePage from "@/pages/inventario/StockDisponiblePage";
import AlertasStockPage from "@/pages/inventario/AlertasStockPage";
import InventarioValorizadoPage from "@/pages/inventario/InventarioValorizadoPage";
import TomaInventarioPage from "@/pages/inventario/TomaInventarioPage";
import TomaInventarioDetailPage from "@/pages/inventario/TomaInventarioDetailPage";
import ReportesPage from "@/pages/reportes/ReportesPage";
import ReportesInventarioPage from "@/pages/reportes/ReportesInventarioPage";
import ReportesAlmacenPage from "@/pages/reportes/ReportesAlmacenPage";
import ReportesComprasPage from "@/pages/reportes/ReportesComprasPage";
import RequerimientosPage from "@/pages/requerimientos/RequerimientosPage";
import RequerimientoDetailPage from "@/pages/requerimientos/RequerimientoDetailPage";
import ValeIngresoPage from "@/pages/vales/ValeIngresoPage";
import ValeIngresoDetailPage from "@/pages/vales/ValeIngresoDetailPage";
import ValeSalidaPage from "@/pages/vales/ValeSalidaPage";
import ValeSalidaDetailPage from "@/pages/vales/ValeSalidaDetailPage";
import ListaValesPage from "@/pages/vales/ListaValesPage";
import ConceptosAlmacenPage from "@/pages/vales/ConceptosAlmacenPage";
import UsuariosPage from "@/pages/admin/UsuariosPage";
import ConfiguracionPage from "@/pages/admin/ConfiguracionPage";
import ManualPage from "@/pages/ManualPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20 p-12">
      <div className="text-center">
        <h2 className="text-xl font-semibold text-muted-foreground">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground/70">Proximamente</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/manual" element={<ManualPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/proveedores" element={<ProveedoresPage />} />
              <Route path="/proveedores/nuevo" element={<ProveedorFormPage />} />
              <Route path="/proveedores/:id/editar" element={<ProveedorFormPage />} />
              <Route path="/productos" element={<ProductosPage />} />
              <Route path="/productos/nuevo" element={<ProductoFormPage />} />
              <Route path="/productos/:id/editar" element={<ProductoFormPage />} />
              <Route path="/ordenes" element={<OrdenesPage />} />
              <Route path="/ordenes/nueva" element={<OrdenFormPage />} />
              <Route path="/ordenes/:id" element={<OrdenDetailPage />} />
              <Route path="/ordenes/:id/editar" element={<OrdenFormPage />} />
              <Route path="/importaciones" element={<ImportacionesPage />} />
              <Route path="/importaciones/nueva" element={<ImportacionFormPage />} />
              <Route path="/importaciones/:id" element={<ImportacionDetailPage />} />
              <Route path="/importaciones/:id/editar" element={<ImportacionFormPage />} />
              <Route path="/gastos" element={<GastosPage />} />
              <Route path="/gastos/nuevo" element={<GastoFormPage />} />
              <Route path="/gastos/:id/editar" element={<GastoFormPage />} />
              <Route path="/prorrateo" element={<ProrrateoPage />} />
              <Route path="/prorrateo/ficha-costeo/:oc_id" element={<FichaCosteoPage />} />
              <Route path="/documentos/duas" element={<DuaListPage />} />
              <Route path="/documentos/dua/nueva" element={<DuaFormPage />} />
              <Route path="/documentos/dua/:id/editar" element={<DuaFormPage />} />
              <Route path="/documentos/transporte/nuevo" element={<TransporteFormPage />} />
              <Route path="/documentos/transporte/:id/editar" element={<TransporteFormPage />} />
              <Route path="/documentos/facturas" element={<FacturasPage />} />
              <Route path="/documentos/facturas/nueva" element={<FacturaFormPage />} />
              <Route path="/documentos/facturas/:id/editar" element={<FacturaFormPage />} />
              <Route path="/requerimientos" element={<RequerimientosPage />} />
              <Route path="/requerimientos/:id" element={<RequerimientoDetailPage />} />
              <Route path="/almacenes" element={<AlmacenesPage />} />
              <Route path="/inventario" element={<InventarioPage />} />
              <Route path="/movimientos" element={<MovimientosPage />} />
              <Route path="/movimientos/nuevo" element={<MovimientoFormPage />} />
              <Route path="/movimientos/:id" element={<MovimientoDetailPage />} />
              <Route path="/inventario/kardex" element={<KardexPage />} />
              <Route path="/inventario/stock" element={<StockDisponiblePage />} />
              <Route path="/inventario/alertas" element={<AlertasStockPage />} />
              <Route path="/inventario/valorizado" element={<InventarioValorizadoPage />} />
              <Route path="/inventario/toma" element={<TomaInventarioPage />} />
              <Route path="/inventario/toma/:id" element={<TomaInventarioDetailPage />} />
              <Route path="/vales/ingreso" element={<ValeIngresoPage />} />
              <Route path="/vales/ingreso/:id" element={<ValeIngresoDetailPage />} />
              <Route path="/vales/salida" element={<ValeSalidaPage />} />
              <Route path="/vales/salida/:id" element={<ValeSalidaDetailPage />} />
              <Route path="/vales/lista" element={<ListaValesPage />} />
              <Route path="/vales/conceptos" element={<ConceptosAlmacenPage />} />
              <Route path="/reportes" element={<ReportesPage />} />
              <Route path="/reportes/inventario" element={<ReportesInventarioPage />} />
              <Route path="/reportes/almacen" element={<ReportesAlmacenPage />} />
              <Route path="/reportes/compras" element={<ReportesComprasPage />} />
              <Route path="/admin/usuarios" element={<UsuariosPage />} />
              <Route path="/admin/configuracion" element={<ConfiguracionPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
