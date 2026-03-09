-- ============================================================================
-- IMPORTCOST PRO - Migracion Sprint 10: Administracion (Usuarios + Config)
-- ============================================================================

USE importcost_pro;

-- ============================================================================
-- 1. EXTENDER TABLA usuarios: almacen por defecto
-- ============================================================================
ALTER TABLE usuarios
  ADD COLUMN almacen_default_id INT NULL AFTER status,
  ADD FOREIGN KEY fk_usuario_almacen (almacen_default_id) REFERENCES almacenes(id);

-- ============================================================================
-- 2. NUEVA TABLA: configuracion_sistema
-- ============================================================================
CREATE TABLE configuracion_sistema (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    seccion     VARCHAR(50) NOT NULL,
    clave       VARCHAR(100) NOT NULL,
    valor       TEXT NULL,
    tipo_dato   ENUM('string','number','boolean','json') DEFAULT 'string',
    descripcion VARCHAR(255) NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_config_empresa_seccion_clave (empresa_id, seccion, clave),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 3. SEED: Configuracion por defecto (empresa 1)
-- ============================================================================
INSERT INTO configuracion_sistema (empresa_id, seccion, clave, valor, tipo_dato, descripcion) VALUES
-- General
(1, 'general', 'nombre_empresa', 'Mi Empresa S.A.C.', 'string', 'Nombre comercial de la empresa'),
(1, 'general', 'ruc', '20123456789', 'string', 'RUC de la empresa'),
(1, 'general', 'direccion', '', 'string', 'Direccion fiscal'),
(1, 'general', 'telefono', '', 'string', 'Telefono principal'),
(1, 'general', 'email', '', 'string', 'Email de contacto'),
(1, 'general', 'moneda_default', 'PEN', 'string', 'Moneda por defecto'),
-- Inventario
(1, 'inventario', 'metodo_costeo', 'promedio', 'string', 'Metodo de costeo (promedio/fifo/lifo)'),
(1, 'inventario', 'alerta_stock_minimo', 'true', 'boolean', 'Activar alertas de stock minimo'),
(1, 'inventario', 'igv_porcentaje', '18', 'number', 'Porcentaje de IGV'),
(1, 'inventario', 'permitir_stock_negativo', 'false', 'boolean', 'Permitir stock negativo en salidas'),
-- Compras
(1, 'compras', 'aprobacion_requerida', 'true', 'boolean', 'Requerir aprobacion para OCs'),
(1, 'compras', 'dias_entrega_default', '30', 'number', 'Dias de entrega por defecto'),
(1, 'compras', 'incoterm_default', 'FOB', 'string', 'Incoterm por defecto'),
-- Documentos
(1, 'documentos', 'prefijo_vale_ingreso', 'VLE', 'string', 'Prefijo para vales de ingreso'),
(1, 'documentos', 'prefijo_vale_salida', 'VLS', 'string', 'Prefijo para vales de salida'),
(1, 'documentos', 'prefijo_requerimiento', 'REQ', 'string', 'Prefijo para requerimientos'),
(1, 'documentos', 'prefijo_toma_inventario', 'TIF', 'string', 'Prefijo para tomas de inventario');
