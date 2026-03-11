import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';

// Layouts
import AppLayout from '@/components/layout/AppLayout';

// Pages
import LoginPage from '@/pages/auth/LoginPage';
import DashboardPage from '@/pages/dashboard/DashboardPage';
import ProveedoresPage from '@/pages/proveedores/ProveedoresPage';
import ProductosPage from '@/pages/productos/ProductosPage';
import AlmacenesPage from '@/pages/almacenes/AlmacenesPage';
import OrdenesCompraPage from '@/pages/ordenes-compra/OrdenesCompraPage';
import ImportacionesPage from '@/pages/importaciones/ImportacionesPage';
import PlaceholderPage from '@/pages/PlaceholderPage';

export default function App() {
  const { loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: { fontSize: '14px', borderRadius: '10px' },
        }}
      />
      <Routes>
        {/* Auth */}
        <Route path="/login" element={<LoginPage />} />

        {/* App protegida */}
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />

          {/* Compras */}
          <Route path="/ordenes-compra" element={<OrdenesCompraPage />} />
          <Route path="/proveedores" element={<ProveedoresPage />} />
          <Route path="/productos" element={<ProductosPage />} />

          {/* Importaciones */}
          <Route path="/importaciones" element={<ImportacionesPage />} />
          <Route path="/dua" element={<PlaceholderPage title="DUA" subtitle="Declaraciones Aduaneras de Mercancias" />} />
          <Route path="/gastos" element={<PlaceholderPage title="Gastos" subtitle="Gastos de importacion" />} />

          {/* Costeo */}
          <Route path="/prorrateo" element={<PlaceholderPage title="Prorrateo" subtitle="Distribucion de costos" />} />

          {/* Inventario */}
          <Route path="/inventario" element={<PlaceholderPage title="Inventario" subtitle="Stock por almacen" />} />
          <Route path="/movimientos" element={<PlaceholderPage title="Movimientos" subtitle="Ingresos, transferencias y salidas" />} />
          <Route path="/almacenes" element={<AlmacenesPage />} />
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
