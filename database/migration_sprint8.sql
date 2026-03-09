-- =============================================================================
-- Sprint 8: Toma de Inventario Fisico — Migracion
-- =============================================================================

-- ----------------------------------------------------------------------------
-- 8.1 Tabla toma_inventario (cabecera)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toma_inventario (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id      INT NOT NULL,
    numero          VARCHAR(20) NOT NULL,
    almacen_id      INT NOT NULL,
    fecha_inicio    DATE NOT NULL,
    fecha_fin       DATE NULL,
    responsable     VARCHAR(100) NOT NULL,
    estado          ENUM('pendiente','en_proceso','completado','regularizado') DEFAULT 'pendiente',
    notas           TEXT NULL,
    created_by      INT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (almacen_id) REFERENCES almacenes(id),
    KEY idx_toma_empresa_estado (empresa_id, estado)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8.2 Tabla toma_inventario_items (detalle de conteo)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS toma_inventario_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    toma_id         INT NOT NULL,
    producto_id     INT NOT NULL,
    stock_sistema   DECIMAL(15,4) DEFAULT 0,
    stock_contado   DECIMAL(15,4) NULL,
    diferencia      DECIMAL(15,4) DEFAULT 0,
    observacion     VARCHAR(255) NULL,
    FOREIGN KEY (toma_id) REFERENCES toma_inventario(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 8.3 Correlativo para toma de inventario
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio)
VALUES (1, 'toma_inventario', 'TIF', 0, YEAR(CURDATE()));
