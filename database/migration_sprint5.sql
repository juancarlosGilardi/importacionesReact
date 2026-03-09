-- ============================================================================
-- IMPORTCOST PRO - Migración Sprint 5: Vales + Conceptos + Stock Mínimo
-- ============================================================================

USE importcost_pro;

-- ============================================================================
-- 1. EXTENDER TABLA productos: stock mínimo y punto de reposición
-- ============================================================================
ALTER TABLE productos
  ADD COLUMN stock_minimo DECIMAL(15,4) DEFAULT 0 AFTER proveedor_default_id,
  ADD COLUMN punto_reposicion DECIMAL(15,4) DEFAULT 0 AFTER stock_minimo;

-- ============================================================================
-- 2. NUEVA TABLA: conceptos_almacen
-- ============================================================================
CREATE TABLE conceptos_almacen (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    codigo      VARCHAR(10) NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    tipo        ENUM('ingreso','salida') NOT NULL,
    afecta_costo TINYINT(1) DEFAULT 1,
    activo      TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_concepto_empresa_codigo (empresa_id, codigo),
    KEY idx_concepto_tipo (tipo),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 3. NUEVA TABLA: concepto_almacen_config (habilitación por almacén)
-- ============================================================================
CREATE TABLE concepto_almacen_config (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    almacen_id  INT NOT NULL,
    concepto_id INT NOT NULL,
    habilitado  TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_config_almacen_concepto (almacen_id, concepto_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (almacen_id) REFERENCES almacenes(id) ON DELETE CASCADE,
    FOREIGN KEY (concepto_id) REFERENCES conceptos_almacen(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- 4. EXTENDER TABLA movimientos_almacen: campos de vale formal
-- ============================================================================
ALTER TABLE movimientos_almacen
  ADD COLUMN concepto_id INT NULL AFTER oc_id,
  ADD COLUMN centro_costo VARCHAR(50) NULL AFTER concepto_id,
  ADD COLUMN solicitante VARCHAR(100) NULL AFTER centro_costo,
  ADD COLUMN proveedor_id INT NULL AFTER solicitante,
  ADD COLUMN subtotal DECIMAL(15,4) DEFAULT 0 AFTER valor_total,
  ADD COLUMN igv DECIMAL(15,4) DEFAULT 0 AFTER subtotal,
  ADD COLUMN total DECIMAL(15,4) DEFAULT 0 AFTER igv,
  ADD KEY idx_mov_concepto (concepto_id),
  ADD KEY idx_mov_proveedor (proveedor_id),
  ADD FOREIGN KEY (concepto_id) REFERENCES conceptos_almacen(id),
  ADD FOREIGN KEY (proveedor_id) REFERENCES proveedores(id);

-- ============================================================================
-- 5. NUEVA TABLA: correlativos (generación secuencial por tipo)
-- ============================================================================
CREATE TABLE correlativos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id      INT NOT NULL,
    tipo            VARCHAR(50) NOT NULL,
    prefijo         VARCHAR(20) NOT NULL,
    ultimo_numero   INT DEFAULT 0,
    anio            INT NOT NULL,
    UNIQUE KEY uk_correlativo_empresa_tipo_anio (empresa_id, tipo, anio),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 6. SEED: Conceptos de almacén para empresa demo
-- ============================================================================
INSERT INTO conceptos_almacen (empresa_id, codigo, nombre, tipo, afecta_costo) VALUES
-- Conceptos de Ingreso
(1, 'ING-01', 'Compra Local', 'ingreso', 1),
(1, 'ING-02', 'Compra Importación', 'ingreso', 1),
(1, 'ING-03', 'Devolución de Cliente', 'ingreso', 0),
(1, 'ING-04', 'Transferencia Recibida', 'ingreso', 0),
(1, 'ING-05', 'Sobrante de Inventario', 'ingreso', 0),
-- Conceptos de Salida
(1, 'SAL-01', 'Consumo Interno', 'salida', 0),
(1, 'SAL-02', 'Transferencia Enviada', 'salida', 0),
(1, 'SAL-03', 'Devolución a Proveedor', 'salida', 0),
(1, 'SAL-04', 'Ajuste de Inventario', 'salida', 0),
(1, 'SAL-05', 'Faltante de Inventario', 'salida', 0);

-- ============================================================================
-- 7. SEED: Correlativos iniciales
-- ============================================================================
INSERT INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio) VALUES
(1, 'vale_ingreso', 'VLE', 0, 2026),
(1, 'vale_salida', 'VLS', 0, 2026),
(1, 'requerimiento', 'REQ', 0, 2026);
