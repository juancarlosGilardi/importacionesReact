import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor: agregar token JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor: manejar 401 (token expirado)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Helper para formatear moneda
export const formatCurrency = (amount: number, symbol = 'S/'): string => {
  return `${symbol} ${amount.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

// Helper para formatear fecha
export const formatDate = (date: string): string => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('es-PE', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  });
};

// Colores de estado
export const STATUS_COLORS: Record<string, string> = {
  borrador: '#94A3B8',
  confirmada: '#3B82F6',
  en_transito: '#F59E0B',
  en_aduana: '#EF4444',
  prorrateado: '#8B5CF6',
  en_almacen: '#10B981',
  completada: '#059669',
  cancelada: '#DC2626',
};
