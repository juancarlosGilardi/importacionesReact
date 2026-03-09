-- ============================================================================
-- IMPORTCOST PRO - Sistema de Importaciones y Costeo para Pymes
-- Base de Datos MySQL 8.0+
-- Archivo: schema.sql (Tablas, Indices, Constraints, Triggers)
-- ============================================================================

DROP DATABASE IF EXISTS importcost_pro;
CREATE DATABASE importcost_pro
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE importcost_pro;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. TABLAS MAESTRAS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1.1 Empresas (multi-tenant)
-- ----------------------------------------------------------------------------
CREATE TABLE empresas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    ruc         VARCHAR(11)  NOT NULL,
    razon_social VARCHAR(200) NOT NULL,
    nombre_comercial VARCHAR(200),
    direccion   TEXT,
    telefono    VARCHAR(20),
    email       VARCHAR(100),
    logo_path   VARCHAR(500),
    moneda_default_id INT,
    status      ENUM('active','inactive','suspended') DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_empresa_ruc (ruc)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.2 Usuarios
-- ----------------------------------------------------------------------------
CREATE TABLE usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    email       VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    apellido    VARCHAR(100) NOT NULL,
    rol         ENUM('admin','usuario','readonly') DEFAULT 'usuario',
    avatar_path VARCHAR(500),
    ultimo_login TIMESTAMP NULL,
    status      ENUM('active','inactive','blocked') DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_usuario_email (email),
    KEY idx_usuario_empresa (empresa_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.3 Paises
-- ----------------------------------------------------------------------------
CREATE TABLE paises (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    codigo  VARCHAR(2)  NOT NULL,
    nombre  VARCHAR(100) NOT NULL,
    region  VARCHAR(50),
    tiene_tlc_peru TINYINT(1) DEFAULT 0,
    UNIQUE KEY uk_pais_codigo (codigo)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.4 Monedas
-- ----------------------------------------------------------------------------
CREATE TABLE monedas (
    id      INT AUTO_INCREMENT PRIMARY KEY,
    codigo  VARCHAR(3)  NOT NULL,
    nombre  VARCHAR(50) NOT NULL,
    simbolo VARCHAR(5)  NOT NULL,
    UNIQUE KEY uk_moneda_codigo (codigo)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.5 Tipos de Cambio (historial diario SUNAT/SBS)
-- ----------------------------------------------------------------------------
CREATE TABLE tipos_cambio (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    moneda_id      INT NOT NULL,
    fecha          DATE NOT NULL,
    tc_compra      DECIMAL(10,4) NOT NULL,
    tc_venta       DECIMAL(10,4) NOT NULL,
    fuente         ENUM('sunat','sbs','manual') DEFAULT 'sunat',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tc_moneda_fecha (moneda_id, fecha),
    FOREIGN KEY (moneda_id) REFERENCES monedas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.6 Acuerdos TLC
-- ----------------------------------------------------------------------------
CREATE TABLE tlc_acuerdos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    pais_id         INT NOT NULL,
    nombre_acuerdo  VARCHAR(200) NOT NULL,
    fecha_vigencia  DATE NOT NULL,
    tasa_preferencial DECIMAL(5,2) DEFAULT 0.00,
    requisitos      TEXT,
    status          ENUM('vigente','suspendido','terminado') DEFAULT 'vigente',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pais_id) REFERENCES paises(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.7 Partidas Arancelarias
-- ----------------------------------------------------------------------------
CREATE TABLE partidas_arancelarias (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    codigo_hs       VARCHAR(12) NOT NULL,
    descripcion     VARCHAR(500) NOT NULL,
    tasa_ad_valorem DECIMAL(5,2) DEFAULT 0.00,
    tasa_igv        DECIMAL(5,2) DEFAULT 18.00,
    tasa_ipm        DECIMAL(5,2) DEFAULT 0.00,
    tasa_isc        DECIMAL(5,2) DEFAULT 0.00,
    tiene_antidumping TINYINT(1) DEFAULT 0,
    tasa_antidumping  DECIMAL(5,2) DEFAULT 0.00,
    unidad_medida   VARCHAR(10) DEFAULT 'NIU',
    vigente_desde   DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_hs_code (codigo_hs)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.8 Categorias de Producto
-- ----------------------------------------------------------------------------
CREATE TABLE categorias_producto (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    color_ui    VARCHAR(7) DEFAULT '#3B82F6',
    icono_ui    VARCHAR(50) DEFAULT 'category',
    status      ENUM('active','inactive') DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_cat_empresa_nombre (empresa_id, nombre),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.9 Proveedores
-- ----------------------------------------------------------------------------
CREATE TABLE proveedores (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id      INT NOT NULL,
    ruc             VARCHAR(20) NOT NULL,
    razon_social    VARCHAR(200) NOT NULL,
    nombre_comercial VARCHAR(200),
    pais_id         INT,
    direccion       TEXT,
    email           VARCHAR(100),
    telefono        VARCHAR(30),
    contacto_nombre VARCHAR(100),
    moneda_id       INT DEFAULT 1,
    incoterm_default VARCHAR(10) DEFAULT 'FOB',
    es_extranjero   TINYINT(1) DEFAULT 1,
    status          ENUM('active','inactive') DEFAULT 'active',
    created_by      INT,
    updated_by      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_proveedor_empresa_ruc (empresa_id, ruc),
    KEY idx_prov_pais (pais_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (pais_id) REFERENCES paises(id),
    FOREIGN KEY (moneda_id) REFERENCES monedas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.10 Productos
-- ----------------------------------------------------------------------------
CREATE TABLE productos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id      INT NOT NULL,
    sku             VARCHAR(50) NOT NULL,
    nombre          VARCHAR(200) NOT NULL,
    descripcion     TEXT,
    codigo_hs       VARCHAR(12),
    partida_id      INT,
    categoria_id    INT,
    unidad_medida   VARCHAR(20) DEFAULT 'NIU',
    peso_kg         DECIMAL(10,3),
    volumen_m3      DECIMAL(10,6),
    proveedor_default_id INT,
    color_ui        VARCHAR(7) DEFAULT '#3B82F6',
    icono_ui        VARCHAR(50) DEFAULT 'inventory_2',
    status          ENUM('active','inactive') DEFAULT 'active',
    created_by      INT,
    updated_by      INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_producto_empresa_sku (empresa_id, sku),
    KEY idx_prod_hs (codigo_hs),
    KEY idx_prod_cat (categoria_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (partida_id) REFERENCES partidas_arancelarias(id),
    FOREIGN KEY (categoria_id) REFERENCES categorias_producto(id),
    FOREIGN KEY (proveedor_default_id) REFERENCES proveedores(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.11 Almacenes
-- ----------------------------------------------------------------------------
CREATE TABLE almacenes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT NOT NULL,
    codigo      VARCHAR(10) NOT NULL,
    nombre      VARCHAR(100) NOT NULL,
    responsable VARCHAR(100),
    direccion   TEXT,
    notas       TEXT,
    status      ENUM('active','inactive') DEFAULT 'active',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_almacen_empresa_codigo (empresa_id, codigo),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.12 Tipos de Gasto (catalogo configurable)
-- ----------------------------------------------------------------------------
CREATE TABLE tipos_gasto (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    codigo              VARCHAR(50) NOT NULL,
    nombre              VARCHAR(100) NOT NULL,
    descripcion         TEXT,
    color_ui            VARCHAR(7) DEFAULT '#3B82F6',
    icono_ui            VARCHAR(50),
    requiere_proveedor  TINYINT(1) DEFAULT 1,
    afecta_cif          TINYINT(1) DEFAULT 0,
    orden               INT DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tipo_gasto_codigo (codigo)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 1.13 Estados de Importacion (catalogo configurable)
-- ----------------------------------------------------------------------------
CREATE TABLE estados_importacion (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    codigo      VARCHAR(30) NOT NULL,
    nombre      VARCHAR(50) NOT NULL,
    descripcion TEXT,
    orden       INT DEFAULT 0,
    color_ui    VARCHAR(7) DEFAULT '#3B82F6',
    icono_ui    VARCHAR(50),
    es_final    TINYINT(1) DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_estado_codigo (codigo)
) ENGINE=InnoDB;

-- ============================================================================
-- 2. TABLAS DE OPERACION
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 2.1 Ordenes de Compra
-- ----------------------------------------------------------------------------
CREATE TABLE ordenes_compra (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    numero_oc           VARCHAR(50) NOT NULL,
    proveedor_id        INT NOT NULL,
    fecha_orden         DATE NOT NULL,
    fecha_llegada_est   DATE,
    incoterm            VARCHAR(10) NOT NULL DEFAULT 'FOB',
    moneda_id           INT NOT NULL,
    tipo_cambio         DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    puerto_embarque     VARCHAR(100),
    puerto_destino      VARCHAR(100),
    agente_aduanero     VARCHAR(150),
    agente_carga        VARCHAR(150),
    -- Totales calculados
    total_fob           DECIMAL(15,2) DEFAULT 0.00,
    total_flete         DECIMAL(15,2) DEFAULT 0.00,
    total_seguro        DECIMAL(15,2) DEFAULT 0.00,
    total_cif           DECIMAL(15,2) DEFAULT 0.00,
    total_costo_importacion DECIMAL(15,2) DEFAULT 0.00,
    -- Estado
    estado              VARCHAR(30) DEFAULT 'borrador',
    notas               TEXT,
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_oc_empresa_numero (empresa_id, numero_oc),
    KEY idx_oc_proveedor (proveedor_id),
    KEY idx_oc_estado (estado),
    KEY idx_oc_fecha (fecha_orden),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (moneda_id) REFERENCES monedas(id),
    FOREIGN KEY (estado) REFERENCES estados_importacion(codigo)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2.2 Items de Orden de Compra
-- ----------------------------------------------------------------------------
CREATE TABLE orden_compra_items (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    oc_id               INT NOT NULL,
    producto_id         INT NOT NULL,
    cantidad            DECIMAL(10,2) NOT NULL,
    precio_unitario     DECIMAL(15,4) NOT NULL,
    unidad_medida       VARCHAR(20) NOT NULL DEFAULT 'NIU',
    valor_fob           DECIMAL(15,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
    peso_kg             DECIMAL(10,3),
    volumen_m3          DECIMAL(10,6),
    -- Costos prorrateados (se llenan al prorratear)
    prorrateo_flete     DECIMAL(15,2) DEFAULT 0.00,
    prorrateo_seguro    DECIMAL(15,2) DEFAULT 0.00,
    prorrateo_tributos  DECIMAL(15,2) DEFAULT 0.00,
    prorrateo_gastos    DECIMAL(15,2) DEFAULT 0.00,
    costo_total         DECIMAL(15,2) DEFAULT 0.00,
    costo_unitario_landed DECIMAL(18,4) DEFAULT 0.0000,
    lote_ingreso        VARCHAR(50),
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_oci_oc (oc_id),
    KEY idx_oci_producto (producto_id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2.3 Importaciones (contenedor/embarque)
-- ----------------------------------------------------------------------------
CREATE TABLE importaciones (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id              INT NOT NULL,
    numero_importacion      VARCHAR(20) NOT NULL,
    descripcion             VARCHAR(200) NOT NULL,
    fecha_creacion          DATE NOT NULL,
    -- Transporte
    bl_number               VARCHAR(100),
    container_number        VARCHAR(50),
    via_transporte          ENUM('maritimo','aereo','terrestre','multimodal') DEFAULT 'maritimo',
    nombre_nave             VARCHAR(100),
    numero_viaje            VARCHAR(50),
    -- Fechas clave
    fecha_embarque          DATE,
    fecha_arribo_estimada   DATE,
    fecha_arribo_real       DATE,
    fecha_desaduanaje       DATE,
    -- Agentes
    agente_aduanero         VARCHAR(150),
    agente_carga            VARCHAR(150),
    -- Estado
    estado                  VARCHAR(30) DEFAULT 'planificada',
    -- Totales calculados
    total_fob_importacion   DECIMAL(15,2) DEFAULT 0.00,
    total_gastos_importacion DECIMAL(15,2) DEFAULT 0.00,
    total_costo_importacion DECIMAL(15,2) DEFAULT 0.00,
    notas                   TEXT,
    created_by              INT,
    updated_by              INT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_imp_empresa_numero (empresa_id, numero_importacion),
    KEY idx_imp_estado (estado),
    KEY idx_imp_fecha (fecha_creacion),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 2.4 Relacion Importacion <-> Ordenes de Compra
-- ----------------------------------------------------------------------------
CREATE TABLE importacion_ocs (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    importacion_id          INT NOT NULL,
    oc_id                   INT NOT NULL,
    porcentaje_participacion DECIMAL(5,2),
    peso_total              DECIMAL(10,3),
    volumen_total           DECIMAL(10,6),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_imp_oc (importacion_id, oc_id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- 3. TABLAS DOCUMENTARIAS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 DUA (Declaracion Aduanera de Mercancias)
-- ----------------------------------------------------------------------------
CREATE TABLE dua_documentos (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id              INT NOT NULL,
    importacion_id          INT NOT NULL,
    numero_dua              VARCHAR(50) NOT NULL,
    fecha_registro          DATE NOT NULL,
    fecha_levante           DATE,
    agencia_aduanas         VARCHAR(150),
    ruc_agente              VARCHAR(11),
    numero_operacion        VARCHAR(50),
    -- Valores
    valor_fob_usd           DECIMAL(15,2),
    flete_usd               DECIMAL(15,2),
    seguro_usd              DECIMAL(15,2),
    valor_cif_usd           DECIMAL(15,2),
    -- Tributos
    tasa_ad_valorem         DECIMAL(5,2) DEFAULT 0.00,
    monto_ad_valorem        DECIMAL(15,2) DEFAULT 0.00,
    tasa_igv                DECIMAL(5,2) DEFAULT 18.00,
    monto_igv               DECIMAL(15,2) DEFAULT 0.00,
    tasa_ipm                DECIMAL(5,2) DEFAULT 0.00,
    monto_ipm               DECIMAL(15,2) DEFAULT 0.00,
    monto_isc               DECIMAL(15,2) DEFAULT 0.00,
    monto_antidumping       DECIMAL(15,2) DEFAULT 0.00,
    monto_percepcion        DECIMAL(15,2) DEFAULT 0.00,
    tasa_percepcion         DECIMAL(5,2) DEFAULT 3.50,
    -- Gastos aduaneros
    gastos_despacho         DECIMAL(15,2) DEFAULT 0.00,
    honorarios_agente       DECIMAL(15,2) DEFAULT 0.00,
    almacenaje              DECIMAL(15,2) DEFAULT 0.00,
    otros_gastos_aduana     DECIMAL(15,2) DEFAULT 0.00,
    -- Totales
    total_tributos          DECIMAL(15,2) DEFAULT 0.00,
    total_gastos_aduana     DECIMAL(15,2) DEFAULT 0.00,
    -- Tipo de cambio del dia de registro
    tipo_cambio             DECIMAL(10,4) DEFAULT 1.0000,
    -- Estado y archivos
    estado                  ENUM('registrada','en_proceso','levantada','cancelada') DEFAULT 'registrada',
    archivo_pdf             VARCHAR(500),
    notas                   TEXT,
    created_by              INT,
    updated_by              INT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_dua_empresa_numero (empresa_id, numero_dua),
    KEY idx_dua_importacion (importacion_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3.2 Items de DUA (detalle por serie/producto)
-- ----------------------------------------------------------------------------
CREATE TABLE dua_items (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    dua_id              INT NOT NULL,
    numero_serie        INT NOT NULL,
    producto_id         INT,
    codigo_hs           VARCHAR(12) NOT NULL,
    descripcion         VARCHAR(500),
    cantidad            DECIMAL(10,2),
    unidad_medida       VARCHAR(10),
    valor_fob_usd       DECIMAL(15,2),
    peso_kg             DECIMAL(10,3),
    tasa_ad_valorem     DECIMAL(5,2) DEFAULT 0.00,
    monto_ad_valorem    DECIMAL(15,2) DEFAULT 0.00,
    monto_igv           DECIMAL(15,2) DEFAULT 0.00,
    monto_ipm           DECIMAL(15,2) DEFAULT 0.00,
    monto_isc           DECIMAL(15,2) DEFAULT 0.00,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_dua_item_dua (dua_id),
    FOREIGN KEY (dua_id) REFERENCES dua_documentos(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3.3 Documentos de Transporte (BL, AWB, Carta Porte)
-- ----------------------------------------------------------------------------
CREATE TABLE documentos_transporte (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    importacion_id      INT NOT NULL,
    tipo_documento      ENUM('bill_of_lading','air_waybill','carta_porte','otro') NOT NULL,
    numero_documento    VARCHAR(100) NOT NULL,
    transportista       VARCHAR(150),
    nombre_nave         VARCHAR(100),
    numero_viaje        VARCHAR(50),
    fecha_etd           DATE,
    fecha_eta           DATE,
    fecha_arribo_real   DATE,
    total_bultos        INT,
    peso_bruto_kg       DECIMAL(10,2),
    volumen_m3          DECIMAL(10,3),
    archivo_path        VARCHAR(500),
    tracking_url        VARCHAR(500),
    notas               TEXT,
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_dt_importacion (importacion_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3.4 Facturas de Proveedor
-- ----------------------------------------------------------------------------
CREATE TABLE facturas_proveedor (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    numero_factura      VARCHAR(100) NOT NULL,
    oc_id               INT,
    proveedor_id        INT NOT NULL,
    fecha_factura       DATE NOT NULL,
    moneda_id           INT NOT NULL,
    tipo_cambio         DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    subtotal            DECIMAL(15,2) NOT NULL,
    impuesto            DECIMAL(15,2) DEFAULT 0.00,
    total               DECIMAL(15,2) NOT NULL,
    xml_file_path       VARCHAR(500),
    xml_hash            VARCHAR(64),
    archivo_pdf         VARCHAR(500),
    estado              ENUM('pendiente','validada','pagada','cancelada') DEFAULT 'pendiente',
    notas               TEXT,
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_factura_hash (xml_hash),
    KEY idx_fact_oc (oc_id),
    KEY idx_fact_prov (proveedor_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (moneda_id) REFERENCES monedas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 3.5 Items de Factura
-- ----------------------------------------------------------------------------
CREATE TABLE factura_items (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    factura_id      INT NOT NULL,
    producto_id     INT NOT NULL,
    cantidad        DECIMAL(10,2) NOT NULL,
    precio_unitario DECIMAL(15,4) NOT NULL,
    precio_total    DECIMAL(15,2) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_fi_factura (factura_id),
    FOREIGN KEY (factura_id) REFERENCES facturas_proveedor(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 4. TABLAS DE COSTOS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 4.1 Gastos de Importacion
-- ----------------------------------------------------------------------------
CREATE TABLE gastos_importacion (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    importacion_id      INT,
    oc_id               INT,
    tipo_gasto_codigo   VARCHAR(50) NOT NULL,
    descripcion         VARCHAR(200),
    proveedor_ruc       VARCHAR(20),
    proveedor_nombre    VARCHAR(150),
    moneda_id           INT NOT NULL,
    monto               DECIMAL(15,2) NOT NULL,
    tipo_cambio         DECIMAL(10,4) NOT NULL DEFAULT 1.0000,
    monto_pen           DECIMAL(15,2) GENERATED ALWAYS AS (monto * tipo_cambio) STORED,
    numero_comprobante  VARCHAR(100),
    fecha_gasto         DATE,
    prorrateado         TINYINT(1) DEFAULT 0,
    estado              ENUM('pendiente','aprobado','pagado') DEFAULT 'pendiente',
    notas               TEXT,
    comprobante_path    VARCHAR(500),
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_gi_importacion (importacion_id),
    KEY idx_gi_oc (oc_id),
    KEY idx_gi_tipo (tipo_gasto_codigo),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id),
    FOREIGN KEY (tipo_gasto_codigo) REFERENCES tipos_gasto(codigo),
    FOREIGN KEY (moneda_id) REFERENCES monedas(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4.2 Prorrateo de Costos (cabecera)
-- ----------------------------------------------------------------------------
CREATE TABLE prorrateos (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    importacion_id      INT,
    oc_id               INT,
    fecha_prorrateo     DATE NOT NULL,
    metodo_prorrateo    ENUM('valor_fob','peso','volumen','cantidad','manual') DEFAULT 'valor_fob',
    -- Totales
    total_fob           DECIMAL(15,2) DEFAULT 0.00,
    total_flete         DECIMAL(15,2) DEFAULT 0.00,
    total_seguro        DECIMAL(15,2) DEFAULT 0.00,
    total_tributos      DECIMAL(15,2) DEFAULT 0.00,
    total_gastos        DECIMAL(15,2) DEFAULT 0.00,
    total_cif           DECIMAL(15,2) DEFAULT 0.00,
    total_landed_cost   DECIMAL(15,2) DEFAULT 0.00,
    -- Factores de prorrateo
    factor_flete        DECIMAL(10,8) DEFAULT 0.00000000,
    factor_seguro       DECIMAL(10,8) DEFAULT 0.00000000,
    factor_tributos     DECIMAL(10,8) DEFAULT 0.00000000,
    factor_gastos       DECIMAL(10,8) DEFAULT 0.00000000,
    estado              ENUM('calculado','aplicado','cancelado') DEFAULT 'calculado',
    fecha_aplicacion    DATE,
    notas               TEXT,
    created_by          INT,
    updated_by          INT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_prr_importacion (importacion_id),
    KEY idx_prr_oc (oc_id),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4.3 Detalle de Prorrateo (por item de OC)
-- ----------------------------------------------------------------------------
CREATE TABLE prorrateo_detalle (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    prorrateo_id        INT NOT NULL,
    oc_item_id          INT NOT NULL,
    producto_id         INT NOT NULL,
    cantidad            DECIMAL(10,2) NOT NULL,
    valor_fob           DECIMAL(15,2) NOT NULL,
    peso_kg             DECIMAL(10,3),
    volumen_m3          DECIMAL(10,6),
    -- Factor de distribucion de este item
    factor_item         DECIMAL(10,8) NOT NULL,
    -- Montos prorrateados
    flete_prorrateado   DECIMAL(15,2) DEFAULT 0.00,
    seguro_prorrateado  DECIMAL(15,2) DEFAULT 0.00,
    tributos_prorrateados DECIMAL(15,2) DEFAULT 0.00,
    gastos_prorrateados DECIMAL(15,2) DEFAULT 0.00,
    costo_total         DECIMAL(15,2) DEFAULT 0.00,
    costo_unitario      DECIMAL(18,4) DEFAULT 0.0000,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_pd_prorrateo (prorrateo_id),
    KEY idx_pd_oc_item (oc_item_id),
    FOREIGN KEY (prorrateo_id) REFERENCES prorrateos(id) ON DELETE CASCADE,
    FOREIGN KEY (oc_item_id) REFERENCES orden_compra_items(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 4.4 Reportes de Costeo
-- ----------------------------------------------------------------------------
CREATE TABLE reportes_costeo (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id              INT NOT NULL,
    numero_reporte          VARCHAR(50) NOT NULL,
    oc_id                   INT,
    importacion_id          INT,
    fecha_reporte           DATE NOT NULL,
    total_costo_producto    DECIMAL(15,2),
    total_costo_flete       DECIMAL(15,2),
    total_costo_seguro      DECIMAL(15,2),
    total_costo_tributos    DECIMAL(15,2),
    total_costo_gastos      DECIMAL(15,2),
    total_landed_cost       DECIMAL(15,2),
    incremento_promedio_pct DECIMAL(5,2),
    archivo_path            VARCHAR(500),
    generado_por            INT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_reporte_numero (empresa_id, numero_reporte),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 5. TABLAS DE INVENTARIO
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 5.1 Inventario (stock actual)
-- ----------------------------------------------------------------------------
CREATE TABLE inventario (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id          INT NOT NULL,
    producto_id         INT NOT NULL,
    almacen_id          INT NOT NULL,
    lote                VARCHAR(50),
    cantidad            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    costo_unitario      DECIMAL(15,4) NOT NULL DEFAULT 0.0000,
    valor_total         DECIMAL(15,2) GENERATED ALWAYS AS (cantidad * costo_unitario) STORED,
    fecha_ultimo_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_inv_prod_alm_lote (empresa_id, producto_id, almacen_id, lote),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (almacen_id) REFERENCES almacenes(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5.2 Movimientos de Almacen (cabecera)
-- ----------------------------------------------------------------------------
CREATE TABLE movimientos_almacen (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id              INT NOT NULL,
    numero_movimiento       VARCHAR(50) NOT NULL,
    tipo_movimiento         ENUM('ingreso','transferencia','ajuste','salida') NOT NULL,
    fecha_movimiento        DATE NOT NULL,
    almacen_id              INT,
    almacen_destino_id      INT,
    oc_id                   INT,
    documento_referencia    VARCHAR(100),
    total_productos         INT DEFAULT 0,
    valor_total             DECIMAL(15,2) DEFAULT 0.00,
    estado                  ENUM('borrador','confirmado','completado','cancelado') DEFAULT 'borrador',
    notas                   TEXT,
    created_by              INT,
    updated_by              INT,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_mov_empresa_numero (empresa_id, numero_movimiento),
    KEY idx_mov_fecha (fecha_movimiento),
    KEY idx_mov_tipo (tipo_movimiento),
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (almacen_id) REFERENCES almacenes(id),
    FOREIGN KEY (almacen_destino_id) REFERENCES almacenes(id),
    FOREIGN KEY (oc_id) REFERENCES ordenes_compra(id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
-- 5.3 Detalle de Movimiento
-- ----------------------------------------------------------------------------
CREATE TABLE movimiento_detalle (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    movimiento_id       INT NOT NULL,
    producto_id         INT NOT NULL,
    oc_item_id          INT,
    cantidad            DECIMAL(10,2) NOT NULL,
    costo_unitario      DECIMAL(15,4) NOT NULL,
    costo_total         DECIMAL(15,2) NOT NULL,
    lote                VARCHAR(50),
    fecha_vencimiento   DATE,
    ubicacion           VARCHAR(50),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_md_movimiento (movimiento_id),
    KEY idx_md_producto (producto_id),
    FOREIGN KEY (movimiento_id) REFERENCES movimientos_almacen(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (oc_item_id) REFERENCES orden_compra_items(id)
) ENGINE=InnoDB;

-- ============================================================================
-- 6. TABLA DE AUDITORIA
-- ============================================================================
CREATE TABLE audit_log (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    empresa_id  INT,
    usuario_id  INT,
    tabla       VARCHAR(50) NOT NULL,
    registro_id INT NOT NULL,
    accion      ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    datos_antes JSON,
    datos_despues JSON,
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    KEY idx_audit_tabla (tabla, registro_id),
    KEY idx_audit_usuario (usuario_id),
    KEY idx_audit_fecha (created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

DELIMITER //

-- Auto-numeracion de importaciones: YYYY-NNN
CREATE TRIGGER trg_importacion_numero
BEFORE INSERT ON importaciones
FOR EACH ROW
BEGIN
    DECLARE anio INT;
    DECLARE sig INT;
    IF NEW.numero_importacion IS NULL OR NEW.numero_importacion = '' THEN
        SET anio = YEAR(CURDATE());
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_importacion, 6) AS UNSIGNED)), 0) + 1
        INTO sig
        FROM importaciones
        WHERE empresa_id = NEW.empresa_id
          AND numero_importacion LIKE CONCAT(anio, '-%');
        SET NEW.numero_importacion = CONCAT(anio, '-', LPAD(sig, 3, '0'));
    END IF;
END //

-- Recalcular total_fob de OC al insertar/actualizar items
CREATE TRIGGER trg_oci_after_insert
AFTER INSERT ON orden_compra_items
FOR EACH ROW
BEGIN
    UPDATE ordenes_compra
    SET total_fob = (SELECT COALESCE(SUM(valor_fob), 0) FROM orden_compra_items WHERE oc_id = NEW.oc_id)
    WHERE id = NEW.oc_id;
END //

CREATE TRIGGER trg_oci_after_update
AFTER UPDATE ON orden_compra_items
FOR EACH ROW
BEGIN
    UPDATE ordenes_compra
    SET total_fob = (SELECT COALESCE(SUM(valor_fob), 0) FROM orden_compra_items WHERE oc_id = NEW.oc_id)
    WHERE id = NEW.oc_id;
END //

CREATE TRIGGER trg_oci_after_delete
AFTER DELETE ON orden_compra_items
FOR EACH ROW
BEGIN
    UPDATE ordenes_compra
    SET total_fob = (SELECT COALESCE(SUM(valor_fob), 0) FROM orden_compra_items WHERE oc_id = OLD.oc_id)
    WHERE id = OLD.oc_id;
END //

DELIMITER ;

SET FOREIGN_KEY_CHECKS = 1;
