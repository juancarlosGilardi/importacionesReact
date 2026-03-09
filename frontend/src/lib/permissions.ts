/**
 * Sistema de permisos RBAC para ImportCost Pro
 * Roles: admin, usuario, readonly
 */

export type UserRole = "admin" | "usuario" | "readonly";

export interface Permission {
  module: string;
  action: "ver" | "crear" | "editar" | "eliminar" | "aprobar";
}

/**
 * Matriz de permisos por rol
 */
const ROLE_PERMISSIONS: Record<UserRole, Record<string, string[]>> = {
  admin: {
    dashboard: ["ver"],
    proveedores: ["ver", "crear", "editar", "eliminar"],
    productos: ["ver", "crear", "editar", "eliminar"],
    ordenes: ["ver", "crear", "editar", "eliminar", "aprobar"],
    importaciones: ["ver", "crear", "editar", "eliminar"],
    gastos: ["ver", "crear", "editar", "eliminar", "aprobar"],
    documentos: ["ver", "crear", "editar", "eliminar"],
    prorrateo: ["ver", "crear", "editar", "eliminar"],
    almacenes: ["ver", "crear", "editar", "eliminar"],
    inventario: ["ver", "crear", "editar", "eliminar"],
    vales: ["ver", "crear", "editar", "eliminar"],
    requerimientos: ["ver", "crear", "editar", "eliminar", "aprobar"],
    reportes: ["ver"],
    usuarios: ["ver", "crear", "editar", "eliminar"],
    configuracion: ["ver", "editar"],
    toma_inventario: ["ver", "crear", "editar", "eliminar"],
  },
  usuario: {
    dashboard: ["ver"],
    proveedores: ["ver", "crear", "editar"],
    productos: ["ver", "crear", "editar"],
    ordenes: ["ver", "crear", "editar"],
    importaciones: ["ver", "crear", "editar"],
    gastos: ["ver", "crear", "editar"],
    documentos: ["ver", "crear", "editar"],
    prorrateo: ["ver", "crear", "editar"],
    almacenes: ["ver"],
    inventario: ["ver", "crear", "editar"],
    vales: ["ver", "crear", "editar"],
    requerimientos: ["ver", "crear", "editar"],
    reportes: ["ver"],
    usuarios: [],
    configuracion: ["ver"],
    toma_inventario: ["ver", "crear", "editar"],
  },
  readonly: {
    dashboard: ["ver"],
    proveedores: ["ver"],
    productos: ["ver"],
    ordenes: ["ver"],
    importaciones: ["ver"],
    gastos: ["ver"],
    documentos: ["ver"],
    prorrateo: ["ver"],
    almacenes: ["ver"],
    inventario: ["ver"],
    vales: ["ver"],
    requerimientos: ["ver"],
    reportes: ["ver"],
    usuarios: [],
    configuracion: [],
    toma_inventario: ["ver"],
  },
};

/**
 * Verifica si un rol tiene permiso para una acción en un módulo
 */
export function hasPermission(
  rol: UserRole,
  module: string,
  action: string
): boolean {
  const perms = ROLE_PERMISSIONS[rol];
  if (!perms) return false;
  const modulePerms = perms[module];
  if (!modulePerms) return false;
  return modulePerms.includes(action);
}

/**
 * Verifica si un rol puede ver un módulo
 */
export function canView(rol: UserRole, module: string): boolean {
  return hasPermission(rol, module, "ver");
}

/**
 * Verifica si un rol puede crear en un módulo
 */
export function canCreate(rol: UserRole, module: string): boolean {
  return hasPermission(rol, module, "crear");
}

/**
 * Verifica si un rol puede editar en un módulo
 */
export function canEdit(rol: UserRole, module: string): boolean {
  return hasPermission(rol, module, "editar");
}

/**
 * Verifica si un rol puede eliminar en un módulo
 */
export function canDelete(rol: UserRole, module: string): boolean {
  return hasPermission(rol, module, "eliminar");
}

/**
 * Verifica si un rol puede aprobar en un módulo
 */
export function canApprove(rol: UserRole, module: string): boolean {
  return hasPermission(rol, module, "aprobar");
}

/**
 * Verifica si el rol es administrador
 */
export function isAdmin(rol: UserRole): boolean {
  return rol === "admin";
}

/**
 * Obtiene todos los módulos accesibles para un rol
 */
export function getAccessibleModules(rol: UserRole): string[] {
  const perms = ROLE_PERMISSIONS[rol];
  if (!perms) return [];
  return Object.entries(perms)
    .filter(([, actions]) => actions.length > 0)
    .map(([module]) => module);
}

/**
 * Obtiene label del rol en español
 */
export function getRolLabel(rol: UserRole): string {
  const labels: Record<UserRole, string> = {
    admin: "Administrador",
    usuario: "Usuario",
    readonly: "Solo Lectura",
  };
  return labels[rol] || rol;
}
