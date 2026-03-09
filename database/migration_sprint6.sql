-- =============================================================================
-- Sprint 6: Requerimientos Internos — Migracion
-- =============================================================================

-- ----------------------------------------------------------------------------
-- 6.1 Tabla requerimientos (cabecera)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS requerimientos (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id              INT NOT NULL,
    numero                  VARCHAR(20) NOT NULL,
    fecha                   DATE NOT NULL,
    almacen_id              INT NULL,
    centro_costo            VARCHAR(50) NULL,
    prioridad               ENUM('alta','media','baja') DEFAULT 'media',
    moneda_id               INT NULL,
    tipo_cambio             DECIMAL(10,4) NULL,
    proveedor_sugerido_id   INT NULL,
    solicitante             VARCHAR(100) NOT NULL,
    estado                  ENUM('abierto','firmado','derivado','cerrado') DEFAULT 'abierto',
    firmado_por             VARCHAR(100) NULL,
    fecha_firma             DATETIME NULL,
    notas                   TEXT NULL,
    created_by              INT NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (almacen_id) REFERENCES almacenes(id),
    FOREIGN KEY (proveedor_sugerido_id) REFERENCES proveedores(id),
    KEY idx_req_empresa_estado (empresa_id, estado),
    KEY idx_req_numero (numero)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6.2 Tabla requerimiento_items (detalle)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS requerimiento_items (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    requerimiento_id    INT NOT NULL,
    producto_id         INT NOT NULL,
    cantidad            DECIMAL(15,4) NOT NULL,
    precio_estimado     DECIMAL(15,4) DEFAULT 0,
    total               DECIMAL(15,4) DEFAULT 0,
    notas               VARCHAR(255) NULL,
    FOREIGN KEY (requerimiento_id) REFERENCES requerimientos(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 6.3 Correlativo para requerimientos
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio)
VALUES (1, 'requerimiento', 'REQ', 0, YEAR(CURDATE()));
