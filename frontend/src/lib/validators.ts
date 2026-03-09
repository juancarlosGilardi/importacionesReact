/**
 * Validadores para datos comunes en el sistema peruano
 */

/**
 * Valida un RUC peruano (11 dígitos, empieza con 10 o 20)
 */
export function validarRUC(ruc: string): boolean {
  if (!/^\d{11}$/.test(ruc)) return false;
  if (!ruc.startsWith("10") && !ruc.startsWith("20")) return false;

  // Verificación con dígito de control
  const factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2];
  let suma = 0;
  for (let i = 0; i < 10; i++) {
    suma += parseInt(ruc[i]) * factores[i];
  }
  const residuo = 11 - (suma % 11);
  const digitoControl = residuo === 10 ? 0 : residuo === 11 ? 1 : residuo;
  return digitoControl === parseInt(ruc[10]);
}

/**
 * Valida un DNI peruano (8 dígitos)
 */
export function validarDNI(dni: string): boolean {
  return /^\d{8}$/.test(dni);
}

/**
 * Valida formato de email
 */
export function validarEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Valida teléfono peruano (9 dígitos celular o 7 dígitos fijo con prefijo)
 */
export function validarTelefono(telefono: string): boolean {
  const limpio = telefono.replace(/[\s\-\(\)]/g, "");
  // Celular: 9 dígitos empezando con 9
  if (/^9\d{8}$/.test(limpio)) return true;
  // Fijo con código de área: 01XXXXXXX o similar
  if (/^0\d{1,2}\d{6,7}$/.test(limpio)) return true;
  // Con prefijo internacional +51
  if (/^\+51\d{9}$/.test(limpio)) return true;
  return false;
}

/**
 * Valida que un string no esté vacío y tenga longitud mínima
 */
export function validarRequerido(valor: string, minLength = 1): boolean {
  return valor.trim().length >= minLength;
}

/**
 * Valida que un número esté en rango
 */
export function validarRango(
  valor: number,
  min: number,
  max: number
): boolean {
  return valor >= min && valor <= max;
}

/**
 * Valida que un valor decimal tenga máximo N decimales
 */
export function validarDecimales(valor: number, maxDecimales = 2): boolean {
  const partes = valor.toString().split(".");
  if (partes.length === 1) return true;
  return partes[1].length <= maxDecimales;
}

/**
 * Sanitiza un string removiendo caracteres especiales
 */
export function sanitizar(valor: string): string {
  return valor.replace(/[<>\"'&]/g, "").trim();
}

/**
 * Valida formato de código (alfanumérico con guiones)
 */
export function validarCodigo(codigo: string): boolean {
  return /^[A-Za-z0-9\-_]+$/.test(codigo);
}
