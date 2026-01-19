/*
Navicat MySQL Data Transfer

Source Server         : LocalHost
Source Server Version : 50743
Source Host           : localhost:3306
Source Database       : importaciones_costeo

Target Server Type    : MYSQL
Target Server Version : 50743
File Encoding         : 65001

Date: 2025-12-23 00:19:35
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for costing_reports
-- ----------------------------
DROP TABLE IF EXISTS `costing_reports`;
CREATE TABLE `costing_reports` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `report_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `po_id` int(11) NOT NULL,
  `report_date` date NOT NULL,
  `total_product_cost` decimal(15,2) DEFAULT NULL,
  `total_freight_cost` decimal(15,2) DEFAULT NULL,
  `total_insurance_cost` decimal(15,2) DEFAULT NULL,
  `total_tax_cost` decimal(15,2) DEFAULT NULL,
  `total_expense_cost` decimal(15,2) DEFAULT NULL,
  `total_landed_cost` decimal(15,2) DEFAULT NULL,
  `avg_cost_increase` decimal(5,2) DEFAULT NULL,
  `avg_landed_cost_per_unit` decimal(15,4) DEFAULT NULL,
  `avg_landed_cost_per_kg` decimal(15,4) DEFAULT NULL,
  `report_file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `generated_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `report_number` (`report_number`),
  KEY `po_id` (`po_id`),
  CONSTRAINT `costing_reports_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of costing_reports
-- ----------------------------

-- ----------------------------
-- Table structure for cost_prorating
-- ----------------------------
DROP TABLE IF EXISTS `cost_prorating`;
CREATE TABLE `cost_prorating` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_id` int(11) NOT NULL,
  `prorating_date` date NOT NULL,
  `prorating_method` enum('value','weight','volume','manual') COLLATE utf8mb4_unicode_ci DEFAULT 'value',
  `total_fob` decimal(15,2) DEFAULT NULL,
  `total_freight` decimal(15,2) DEFAULT NULL,
  `total_insurance` decimal(15,2) DEFAULT NULL,
  `total_taxes` decimal(15,2) DEFAULT NULL,
  `total_expenses` decimal(15,2) DEFAULT NULL,
  `total_cif` decimal(15,2) DEFAULT NULL,
  `total_landed_cost` decimal(15,2) DEFAULT NULL,
  `freight_factor` decimal(10,8) DEFAULT NULL,
  `insurance_factor` decimal(10,8) DEFAULT NULL,
  `taxes_factor` decimal(10,8) DEFAULT NULL,
  `expenses_factor` decimal(10,8) DEFAULT NULL,
  `status` enum('calculated','applied','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'calculated',
  `calculated_by` int(11) DEFAULT NULL,
  `applied_date` date DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `po_id` (`po_id`),
  CONSTRAINT `cost_prorating_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of cost_prorating
-- ----------------------------
DROP TABLE IF EXISTS `importaciones`;
CREATE TABLE importaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    
    -- NÚMERO DE IMPORTACIÓN (como pide tu jefe)
    numero_importacion VARCHAR(255) UNIQUE NOT NULL,  -- '2026-001', '2026-002'
    
    -- DESCRIPCIÓN
    descripcion VARCHAR(200) NOT NULL,               -- "Importación Miami - Componentes"
    fecha_creacion DATE NOT NULL DEFAULT (CURDATE()),
    
    -- TRANSPORTE (aquí centralizas lo de shipping_documents)
    bl_number VARCHAR(100),                          -- Bill of Lading
    container_number VARCHAR(50),
    via_transporte ENUM('maritimo', 'aereo', 'terrestre', 'multimodal') DEFAULT 'maritimo',
    nombre_nave VARCHAR(100),                        -- Nombre del barco
    numero_viaje VARCHAR(50),                        -- Voyage number
    
    -- FECHAS CLAVE
    fecha_embarque DATE,                             -- ETD
    fecha_arribo_estimada DATE,                      -- ETA
    fecha_arribo_real DATE,
    fecha_desaduanaje DATE,
    
    -- AGENTES
    agente_aduanero VARCHAR(150),
    agente_carga VARCHAR(150),
    
    -- ESTADO
    estado ENUM('planificada', 'en_transito', 'en_aduana', 'completada', 'cancelada') DEFAULT 'planificada',
    
    -- RESUMEN DE COSTOS (se calculan automáticamente)
    total_fob_importacion DECIMAL(15,2) DEFAULT 0.00,
    total_gastos_importacion DECIMAL(15,2) DEFAULT 0.00,
    total_costo_importacion DECIMAL(15,2) DEFAULT 0.00,
    
    notas TEXT,
    created_by INT NULL,
    updated_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
DROP TABLE IF EXISTS `importacion_pos`;
CREATE TABLE importacion_pos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    importacion_id INT NOT NULL,
    po_id INT NOT NULL,
    
    -- Para prorrateo
    porcentaje_participacion DECIMAL(5,2) DEFAULT NULL,  -- % en valor FOB
    peso_total DECIMAL(10,3) DEFAULT NULL,               -- Peso total de esta PO
    volumen_total DECIMAL(10,3) DEFAULT NULL,            -- Volumen total
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_importacion_po (importacion_id, po_id),
    FOREIGN KEY (importacion_id) REFERENCES importaciones(id) ON DELETE CASCADE,
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id) ON DELETE CASCADE
);
-- ----------------------------
-- Table structure for countries
-- ----------------------------
DROP TABLE IF EXISTS `countries`;
CREATE TABLE `countries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `region` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of countries
-- ----------------------------
INSERT INTO `countries` VALUES ('1', 'PE', 'Perú', 'Sudamérica');
INSERT INTO `countries` VALUES ('2', 'US', 'Estados Unidos', 'Norteamérica');
INSERT INTO `countries` VALUES ('3', 'CN', 'China', 'Asia');
INSERT INTO `countries` VALUES ('4', 'DE', 'Alemania', 'Europa');
INSERT INTO `countries` VALUES ('5', 'JP', 'Japón', 'Asia');
INSERT INTO `countries` VALUES ('6', 'MX', 'México', 'Norteamérica');
INSERT INTO `countries` VALUES ('7', 'BR', 'Brasil', 'Sudamérica');
INSERT INTO `countries` VALUES ('8', 'CL', 'Chile', 'Sudamérica');

-- ----------------------------
-- Table structure for currencies
-- ----------------------------
DROP TABLE IF EXISTS `currencies`;
CREATE TABLE `currencies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `symbol` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `exchange_rate` decimal(10,4) NOT NULL,
  `effective_date` date NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of currencies
-- ----------------------------
INSERT INTO `currencies` VALUES ('1', 'USD', 'Dólar Americano', '$', '3.7500', '2025-12-22', '2025-12-22 23:25:57');
INSERT INTO `currencies` VALUES ('2', 'EUR', 'Euro', '€', '4.1000', '2025-12-22', '2025-12-22 23:25:57');
INSERT INTO `currencies` VALUES ('3', 'CNY', 'Yuan Chino', '¥', '0.5300', '2025-12-22', '2025-12-22 23:25:57');
INSERT INTO `currencies` VALUES ('4', 'PEN', 'Nuevo Sol', 'S/', '1.0000', '2025-12-22', '2025-12-22 23:25:57');

-- ----------------------------
-- Table structure for dua_documents
-- ----------------------------
DROP TABLE IF EXISTS `dua_documents`;
CREATE TABLE `dua_documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_id` int(11) NOT NULL,
  `dua_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `registration_date` date NOT NULL,
  `clearance_date` date DEFAULT NULL,
  `customs_agency` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customs_agent_ruc` varchar(11) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `numero_operacion` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fob_value_usd` decimal(15,2) DEFAULT NULL,
  `freight_usd` decimal(15,2) DEFAULT NULL,
  `insurance_usd` decimal(15,2) DEFAULT NULL,
  `cif_value_usd` decimal(15,2) DEFAULT NULL,
  `ad_valorem_rate` decimal(5,2) DEFAULT NULL,
  `ad_valorem_amount` decimal(15,2) DEFAULT NULL,
  `igv_rate` decimal(5,2) DEFAULT '18.00',
  `igv_amount` decimal(15,2) DEFAULT NULL,
  `ipm_rate` decimal(5,2) DEFAULT '0.00',
  `ipm_amount` decimal(15,2) DEFAULT NULL,
  `selective_consumption` decimal(15,2) DEFAULT '0.00',
  `antidumping` decimal(15,2) DEFAULT '0.00',
  `customs_fees` decimal(15,2) DEFAULT NULL,
  `agency_fees` decimal(15,2) DEFAULT NULL,
  `storage_fees` decimal(15,2) DEFAULT NULL,
  `other_customs_expenses` decimal(15,2) DEFAULT NULL,
  `total_taxes` decimal(15,2) DEFAULT NULL,
  `total_customs_expenses` decimal(15,2) DEFAULT NULL,
  `status` enum('registered','in_process','cleared','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'registered',
  `archivo_pdf` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dua_number` (`dua_number`),
  KEY `idx_dua_po` (`po_id`),
  CONSTRAINT `dua_documents_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------
-- Table structure for expense_types_ui
-- ----------------------------
DROP TABLE IF EXISTS `expense_types_ui`;
CREATE TABLE `expense_types_ui` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_gasto` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre_ui` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `color_ui` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3B82F6',
  `icono_ui` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `requiere_proveedor` tinyint(1) DEFAULT '1',
  `orden` int(11) DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `tipo_gasto` (`tipo_gasto`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of expense_types_ui
-- ----------------------------
INSERT INTO `expense_types_ui` VALUES ('1', 'international_freight', 'Flete Internacional', 'Transporte internacional', '#3B82F6', 'flight_rounded', '1', '1', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('2', 'insurance', 'Seguro', 'Seguro de transporte', '#10B981', 'security_rounded', '1', '2', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('3', 'local_freight', 'Flete Local', 'Transporte nacional', '#F59E0B', 'local_shipping_rounded', '1', '3', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('4', 'customs_fees', 'Gastos Aduaneros', 'Honorarios de agencia aduanal', '#EF4444', 'gavel_rounded', '1', '4', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('5', 'agency_fees', 'Honorarios Agente', 'Honorarios de agente de carga', '#8B5CF6', 'badge_rounded', '1', '5', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('6', 'storage', 'Almacenaje', 'Almacenamiento temporal', '#6366F1', 'warehouse_rounded', '1', '6', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('7', 'bank_charges', 'Gastos Bancarios', 'Comisiones bancarias', '#059669', 'account_balance_rounded', '1', '7', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('8', 'inspection', 'Inspección', 'Gastos de inspección', '#D97706', 'search_rounded', '1', '8', '2025-12-22 23:25:57');
INSERT INTO `expense_types_ui` VALUES ('9', 'other', 'Otros Gastos', 'Otros gastos varios', '#94A3B8', 'payments_rounded', '0', '9', '2025-12-22 23:25:57');

-- ----------------------------
-- Table structure for import_expenses
-- ----------------------------
DROP TABLE IF EXISTS `import_expenses`;
CREATE TABLE `import_expenses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_id` int(11) NOT NULL,
  `expense_type` enum('international_freight','insurance','local_freight','customs_fees','agency_fees','storage','bank_charges','inspection','other') COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `supplier_ruc` varchar(11) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `supplier_name` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `currency_id` int(11) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `exchange_rate` decimal(10,4) NOT NULL,
  `amount_pen` decimal(15,2) GENERATED ALWAYS AS ((`amount` * `exchange_rate`)) STORED,
  `invoice_number` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `expense_date` date DEFAULT NULL,
  `notes` TEXT,
  `comprobante_pago` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('pending','approved','paid') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `currency_id` (`currency_id`),
  KEY `idx_expenses_po` (`po_id`,`expense_type`),
  KEY `idx_expenses_type` (`expense_type`,`status`),
  CONSTRAINT `import_expenses_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`),
  CONSTRAINT `import_expenses_ibfk_2` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of import_expenses
-- ----------------------------

-- ----------------------------
-- Table structure for import_statuses
-- ----------------------------
DROP TABLE IF EXISTS `import_statuses`;
CREATE TABLE `import_statuses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `orden` int(11) NOT NULL DEFAULT '0',
  `color_ui` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3B82F6',
  `icono_ui` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `es_final` tinyint(1) DEFAULT '0',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of import_statuses
-- ----------------------------
INSERT INTO `import_statuses` VALUES ('1', 'borrador', 'Borrador', 'Orden de compra en preparación', '1', '#94A3B8', 'edit_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('2', 'confirmada', 'Confirmada', 'PO confirmada con proveedor', '2', '#3B82F6', 'check_circle_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('3', 'en_transito', 'En Tránsito', 'Mercancía en camino', '3', '#F59E0B', 'local_shipping_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('4', 'en_aduana', 'En Aduana', 'Proceso de desaduanaje', '4', '#EF4444', 'gavel_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('5', 'prorrateado', 'Prorrateado', 'Costos calculados', '5', '#8B5CF6', 'calculate_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('6', 'en_almacen', 'En Almacén', 'Mercancía recibida', '6', '#10B981', 'inventory_rounded', '0', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('7', 'completada', 'Completada', 'Importación finalizada', '7', '#059669', 'done_all_rounded', '1', '2025-12-22 23:25:57');
INSERT INTO `import_statuses` VALUES ('8', 'cancelada', 'Cancelada', 'Importación cancelada', '8', '#DC2626', 'cancel_rounded', '1', '2025-12-22 23:25:57');

-- ----------------------------
-- Table structure for inventory
-- ----------------------------
CREATE TABLE `inventory` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `product_id` int(11) NOT NULL,
  `warehouse_id` int(11) DEFAULT NULL, -- Nueva columna relacional
  `batch_number` varchar(50) DEFAULT NULL,
  `quantity` decimal(10,2) NOT NULL DEFAULT '0.00',
  `unit_cost` decimal(15,4) NOT NULL,
  `total_value` decimal(15,2) GENERATED ALWAYS AS ((`quantity` * `unit_cost`)) STORED,
  `last_movement_date` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  -- Regla de oro: Un producto + Un almacén = Un solo registro de stock
  UNIQUE KEY `unique_inventory_relational` (`product_id`, `warehouse_id`, `batch_number`),
  CONSTRAINT `fk_inventory_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `fk_inventory_warehouse` FOREIGN KEY (`warehouse_id`) REFERENCES `warehouses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- ----------------------------
-- Records of inventory
-- ----------------------------

-- ----------------------------
-- Table structure for invoice_items
-- ----------------------------
DROP TABLE IF EXISTS `invoice_items`;
CREATE TABLE `invoice_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `invoice_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `unit_price` decimal(15,4) NOT NULL,
  `total_price` decimal(15,2) NOT NULL,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `invoice_id` (`invoice_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `invoice_items_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `supplier_invoices` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invoice_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of invoice_items
-- ----------------------------

-- ----------------------------
-- Table structure for movement_details
-- ----------------------------
DROP TABLE IF EXISTS `movement_details`;
CREATE TABLE `movement_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `movement_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `po_item_id` int(11) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `unit_cost` decimal(15,4) NOT NULL,
  `total_cost` decimal(15,2) NOT NULL,
  `batch_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `expiration_date` date DEFAULT NULL,
  `location_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `movement_id` (`movement_id`),
  KEY `product_id` (`product_id`),
  KEY `po_item_id` (`po_item_id`),
  CONSTRAINT `movement_details_ibfk_1` FOREIGN KEY (`movement_id`) REFERENCES `warehouse_movements` (`id`) ON DELETE CASCADE,
  CONSTRAINT `movement_details_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`),
  CONSTRAINT `movement_details_ibfk_3` FOREIGN KEY (`po_item_id`) REFERENCES `purchase_order_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of movement_details
-- ----------------------------

-- ----------------------------
-- Table structure for products
-- ----------------------------
DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sku` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `hs_code` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `unit_measure` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `weight_kg` decimal(10,3) DEFAULT NULL,
  `volume_m3` decimal(10,3) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `producto_factupro_id` int(11) DEFAULT NULL,
  `color_ui` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3B82F6',
  `icono_ui` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'inventory_2_rounded',
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sku` (`sku`),
  KEY `idx_products_sku` (`sku`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of products
-- ----------------------------
INSERT INTO `products` VALUES ('1', 'LAP-001', 'Laptop Gaming Pro', 'Laptop 15.6\" Intel i7, 16GB RAM, 1TB SSD', '84713000', 'NIU', '2.500', '0.005', null, 'active', null, '#3B82F6', 'laptop_rounded', null, null, '2025-12-22 23:25:58', '2025-12-22 23:25:58');
INSERT INTO `products` VALUES ('2', 'MON-002', 'Monitor LED 24\"', 'Monitor Full HD 1920x1080, HDMI/VGA', '85285210', 'NIU', '4.200', '0.015', null, 'active', null, '#8B5CF6', 'desktop_windows_rounded', null, null, '2025-12-22 23:25:58', '2025-12-22 23:25:58');
INSERT INTO `products` VALUES ('3', 'PHO-003', 'Smartphone Android', 'Teléfono 6.5\", 128GB, 5G', '85171200', 'NIU', '0.300', '0.000', null, 'active', null, '#EF4444', 'smartphone_rounded', null, null, '2025-12-22 23:25:58', '2025-12-22 23:25:58');
INSERT INTO `products` VALUES ('4', 'COM-004', 'Componentes Electrónicos', 'Circuitos integrados y semiconductores', '85423900', 'KGM', '0.500', '0.001', null, 'active', null, '#10B981', 'memory_rounded', null, null, '2025-12-22 23:25:58', '2025-12-22 23:25:58');

-- ----------------------------
-- Table structure for purchase_orders
-- ----------------------------
DROP TABLE IF EXISTS `purchase_orders`;
CREATE TABLE `purchase_orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `supplier_id` int(11) NOT NULL,
  `order_date` date NOT NULL,
  `expected_arrival` date DEFAULT NULL,
  `incoterm` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `currency_id` int(11) NOT NULL,
  `exchange_rate` decimal(10,4) NOT NULL,
  `port_loading` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port_discharge` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `port_arrival` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `customs_agent` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `freight_forwarder` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_fob` decimal(15,2) DEFAULT '0.00',
  `total_freight` decimal(15,2) DEFAULT '0.00',
  `total_insurance` decimal(15,2) DEFAULT '0.00',
  `total_cif` decimal(15,2) DEFAULT '0.00',
  `total_import_cost` decimal(15,2) DEFAULT '0.00',
  `status` enum('borrador','confirmada','en_transito','en_aduana','prorrateado','en_almacen','completada','cancelada') COLLATE utf8mb4_unicode_ci DEFAULT 'borrador',
  `color_estado` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#94A3B8',
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `po_number` (`po_number`),
  KEY `currency_id` (`currency_id`),
  KEY `idx_po_status` (`status`,`color_estado`),
  KEY `idx_po_supplier` (`supplier_id`),
  KEY `idx_po_number` (`po_number`),
  KEY `idx_po_user` (`created_by`,`updated_by`),
  CONSTRAINT `purchase_orders_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `purchase_orders_ibfk_2` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of purchase_orders
-- ----------------------------

-- ----------------------------
-- Table structure for purchase_order_items
-- ----------------------------
DROP TABLE IF EXISTS `purchase_order_items`;
CREATE TABLE `purchase_order_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` decimal(10,2) NOT NULL,
  `unit_price` decimal(15,4) NOT NULL,
  `unit_measure` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fob_value` decimal(15,2) GENERATED ALWAYS AS ((`quantity` * `unit_price`)) STORED,
  `weight_kg` decimal(10,3) DEFAULT NULL,
  `volume_m3` decimal(10,3) DEFAULT NULL,
  `prorated_freight` decimal(15,2) DEFAULT '0.00',
  `prorated_insurance` decimal(15,2) DEFAULT '0.00',
  `prorated_taxes` decimal(15,2) DEFAULT '0.00',
  `prorated_expenses` decimal(15,2) DEFAULT '0.00',
  `total_cost` decimal(15,2) DEFAULT '0.00',
  `lote_ingreso` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `po_id` (`po_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `purchase_order_items_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `purchase_order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of purchase_order_items
-- ----------------------------

-- ----------------------------
-- Table structure for shipping_documents
-- ----------------------------
DROP TABLE IF EXISTS `shipping_documents`;
CREATE TABLE `shipping_documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `po_id` int(11) NOT NULL,
  `document_type` enum('bill_of_lading','air_waybill','carta_porte','other') COLLATE utf8mb4_unicode_ci NOT NULL,
  `document_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `carrier` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `vessel_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `voyage_number` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `etd_date` date DEFAULT NULL,
  `eta_date` date DEFAULT NULL,
  `actual_arrival` date DEFAULT NULL,
  `total_packages` int(11) DEFAULT NULL,
  `gross_weight` decimal(10,2) DEFAULT NULL,
  `volume` decimal(10,3) DEFAULT NULL,
  `document_file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tracking_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `po_id` (`po_id`),
  CONSTRAINT `shipping_documents_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of shipping_documents
-- ----------------------------

-- ----------------------------
-- Table structure for suppliers
-- ----------------------------
DROP TABLE IF EXISTS `suppliers`;
CREATE TABLE `suppliers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ruc` varchar(11) COLLATE utf8mb4_unicode_ci NOT NULL,
  `business_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `trade_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `country_id` int(11) DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `currency_id` int(11) DEFAULT '1',
  `incoterm_default` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_foreign` tinyint(1) DEFAULT '1',
  `status` enum('active','inactive') COLLATE utf8mb4_unicode_ci DEFAULT 'active',
  `proveedor_factupro_id` int(11) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ruc` (`ruc`),
  KEY `idx_suppliers_ruc` (`ruc`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of suppliers
-- ----------------------------
INSERT INTO `suppliers` VALUES ('1', '12345678901', 'TECHNOLOGY IMPORT LTD', 'TechImports', '2', null, 'sales@techimport.com', '+1-555-1234', '1', 'FOB', '1', 'active', null, null, null, '2025-12-22 23:25:57', '2025-12-22 23:25:57');
INSERT INTO `suppliers` VALUES ('2', '87654321098', 'ASIA ELECTRONICS CO', 'AsiaElec', '3', null, 'info@asiaelectronics.cn', '+86-10-8765', '1', 'CIF', '1', 'active', null, null, null, '2025-12-22 23:25:57', '2025-12-22 23:25:57');
INSERT INTO `suppliers` VALUES ('3', '56789012345', 'EUROPE MACHINERY GMBH', 'EuroMach', '4', null, 'export@euromach.de', '+49-30-5678', '2', 'EXW', '1', 'active', null, null, null, '2025-12-22 23:25:57', '2025-12-22 23:25:57');

-- ----------------------------
-- Table structure for supplier_invoices
-- ----------------------------
DROP TABLE IF EXISTS `supplier_invoices`;
CREATE TABLE `supplier_invoices` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `invoice_number` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `po_id` int(11) NOT NULL,
  `invoice_date` date NOT NULL,
  `supplier_id` int(11) NOT NULL,
  `currency_id` int(11) NOT NULL,
  `exchange_rate` decimal(10,4) NOT NULL,
  `subtotal` decimal(15,2) NOT NULL,
  `tax_amount` decimal(15,2) DEFAULT '0.00',
  `total_amount` decimal(15,2) NOT NULL,
  `xml_file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `xml_hash` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `archivo_pdf` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('pending','validated','paid','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `xml_hash` (`xml_hash`),
  KEY `supplier_id` (`supplier_id`),
  KEY `currency_id` (`currency_id`),
  KEY `idx_invoice_po` (`po_id`),
  CONSTRAINT `supplier_invoices_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`),
  CONSTRAINT `supplier_invoices_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `supplier_invoices_ibfk_3` FOREIGN KEY (`currency_id`) REFERENCES `currencies` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of supplier_invoices
-- ----------------------------

-- ----------------------------
-- Table structure for warehouse_movements
-- ----------------------------
DROP TABLE IF EXISTS `warehouse_movements`;
CREATE TABLE `warehouse_movements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `movement_number` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `po_id` int(11) NOT NULL,
  `movement_type` enum('receipt','transfer','adjustment','output') COLLATE utf8mb4_unicode_ci NOT NULL,
  `movement_date` date NOT NULL,
  `warehouse_location` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reference_document` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('draft','confirmed','completed','cancelled') COLLATE utf8mb4_unicode_ci DEFAULT 'draft',
  `total_products` int(11) DEFAULT '0',
  `total_value` decimal(15,2) DEFAULT '0.00',
  `notes` text COLLATE utf8mb4_unicode_ci,
  `created_by` int(11) DEFAULT NULL,
  `updated_by` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `movement_number` (`movement_number`),
  KEY `idx_movement_po` (`po_id`),
  KEY `idx_movements_date` (`movement_date`,`status`),
  CONSTRAINT `warehouse_movements_ibfk_1` FOREIGN KEY (`po_id`) REFERENCES `purchase_orders` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `warehouses` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- Ej: Almacén Principal, Almacén Norte
    code VARCHAR(10) UNIQUE NOT NULL, -- Ej: ALM-01, ALM-02
    manager_name VARCHAR(100),
    notes TEXT,
    address TEXT,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE shipping_documents;
ADD COLUMN notes TEXT NULL;
AFTER tracking_url;

-- 1. Agregar columnas de almacén origen y destino a los movimientos
ALTER TABLE warehouse_movements 
ADD COLUMN warehouse_id INT AFTER movement_type,
ADD COLUMN destination_warehouse_id INT AFTER warehouse_id;

-- 2. Establecer las relaciones de integridad (Llaves Foráneas)
ALTER TABLE warehouse_movements 
ADD CONSTRAINT fk_movement_warehouse 
FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
ADD CONSTRAINT fk_movement_dest_warehouse 
FOREIGN KEY (destination_warehouse_id) REFERENCES warehouses(id);

INSERT INTO products (sku, name, description, hs_code, unit_measure, weight_kg, volume_m3, status) VALUES
('6G7PTUT#ABA', 'Laptop HP EliteBook 840 G9', 'Intel Core i7-1255U, 16GB DDR4 RAM, 512GB SSD, 14" FHD Display', '8471.30.00', 'NIU', 1.5, 0.005, 'active'),
('C11CJ43201', 'Impresora Multifuncional Epson L3520', 'Print/Scan/Copy, Ink Tank System, Wi-Fi Direct, ADF Capability', '8443.31.10', 'NIU', 5.0, 0.015, 'active');

INSERT INTO suppliers (ruc, business_name, trade_name, country_id, currency_id, incoterm_default, is_foreign, status) 
VALUES ('58-1775406', 'HOME DEPOT CORP.', 'Home Depot', 2, 1, 'FOB', 1, 'active');

ALTER TABLE supplier_invoices MODIFY COLUMN po_id INT NULL;
ALTER TABLE supplier_invoices ADD COLUMN notes TEXT;
ALTER TABLE warehouse_movements MODIFY COLUMN po_id INT NULL;
ALTER TABLE movement_details MODIFY COLUMN po_item_id INT NULL;

ALTER TABLE dua_documents 
DROP FOREIGN KEY dua_documents_ibfk_1,
DROP COLUMN po_id,
ADD COLUMN importacion_id INT NOT NULL,
ADD FOREIGN KEY (importacion_id) REFERENCES importaciones(id);

ALTER TABLE shipping_documents 
DROP FOREIGN KEY shipping_documents_ibfk_1,
DROP COLUMN po_id,
ADD COLUMN importacion_id INT NOT NULL,
ADD FOREIGN KEY (importacion_id) REFERENCES importaciones(id);

ALTER TABLE import_expenses 
ADD COLUMN importacion_id INT NULL,
ADD COLUMN prorrateado BOOLEAN DEFAULT FALSE,
ADD FOREIGN KEY (importacion_id) REFERENCES importaciones(id);

ALTER TABLE cost_prorating 
ADD COLUMN importacion_id INT NULL,
ADD FOREIGN KEY (importacion_id) REFERENCES importaciones(id);
ALTER TABLE cost_prorating MODIFY COLUMN po_id INT NULL;
ALTER TABLE movement_details MODIFY COLUMN po_item_id INT NULL;

ALTER TABLE purchase_order_items 
ADD COLUMN unit_landed_cost DECIMAL(18, 4) DEFAULT 0.0000;

-- 2. Ampliar la columna 'estado' para que acepte la palabra 'prorrateado'
ALTER TABLE importaciones 
MODIFY COLUMN estado VARCHAR(50);

-- 3. Ampliar la columna de método de prorrateo
ALTER TABLE cost_prorating 
MODIFY COLUMN prorating_method VARCHAR(50);


-- ----------------------------
-- Records of warehouse_movements
-- ----------------------------

-- ----------------------------
-- View structure for vw_dashboard_metrics
-- ----------------------------
DROP VIEW IF EXISTS `vw_dashboard_metrics`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_dashboard_metrics` AS select (select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'borrador')) AS `borradores`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'confirmada')) AS `confirmadas`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'en_transito')) AS `en_transito`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'en_aduana')) AS `en_aduana`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'prorrateado')) AS `prorrateadas`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'en_almacen')) AS `en_almacen`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'completada')) AS `completadas`,(select count(0) from `purchase_orders` where (`purchase_orders`.`status` = 'cancelada')) AS `canceladas`,(select coalesce(sum(`purchase_orders`.`total_import_cost`),0) from `purchase_orders` where ((`purchase_orders`.`status` = 'completada') and (month(`purchase_orders`.`order_date`) = month(curdate())))) AS `total_mes`,(select coalesce(sum(`purchase_orders`.`total_import_cost`),0) from `purchase_orders` where ((`purchase_orders`.`status` = 'completada') and (month(`purchase_orders`.`order_date`) = (month(curdate()) - 1)))) AS `total_mes_anterior`,(select count(0) from `purchase_orders` where ((`purchase_orders`.`status` = 'completada') and ((to_days(curdate()) - to_days(`purchase_orders`.`order_date`)) <= 30))) AS `completadas_30dias` ;

-- ----------------------------
-- View structure for vw_import_pipeline
-- ----------------------------
DROP VIEW IF EXISTS `vw_import_pipeline`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_import_pipeline` AS select `po`.`id` AS `id`,`po`.`po_number` AS `po_number`,`po`.`order_date` AS `order_date`,`s`.`business_name` AS `supplier`,`s`.`country_id` AS `origin_country`,`po`.`incoterm` AS `incoterm`,`po`.`total_fob` AS `total_fob`,`po`.`total_import_cost` AS `total_import_cost`,`po`.`status` AS `status`,`ists`.`nombre` AS `estado_nombre`,`ists`.`color_ui` AS `estado_color`,`ists`.`icono_ui` AS `estado_icono`,`ists`.`orden` AS `estado_orden`,count(`poi`.`id`) AS `items_count`,sum(`poi`.`quantity`) AS `total_quantity`,(to_days(curdate()) - to_days(`po`.`order_date`)) AS `dias_transcurridos` from (((`purchase_orders` `po` left join `suppliers` `s` on((`po`.`supplier_id` = `s`.`id`))) left join `import_statuses` `ists` on((`po`.`status` = `ists`.`codigo`))) left join `purchase_order_items` `poi` on((`po`.`id` = `poi`.`po_id`))) group by `po`.`id` order by `ists`.`orden`,`po`.`order_date` desc ;

-- ----------------------------
-- View structure for vw_product_cost_summary
-- ----------------------------
DROP VIEW IF EXISTS `vw_product_cost_summary`;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_product_cost_summary` AS select `p`.`sku` AS `sku`,`p`.`name` AS `producto`,`p`.`hs_code` AS `hs_code`,count(distinct `po`.`id`) AS `importaciones`,sum(`poi`.`quantity`) AS `cantidad_total`,avg(`poi`.`unit_price`) AS `precio_fob_promedio`,avg((`poi`.`total_cost` / `poi`.`quantity`)) AS `costo_unitario_promedio`,max(`po`.`order_date`) AS `ultima_importacion` from ((`products` `p` join `purchase_order_items` `poi` on((`p`.`id` = `poi`.`product_id`))) join `purchase_orders` `po` on(((`poi`.`po_id` = `po`.`id`) and (`po`.`status` = 'completada')))) group by `p`.`id` order by `cantidad_total` desc ;


CREATE OR REPLACE VIEW vw_kardex_sunat AS
SELECT 
    md.id AS detalle_id,
    p.id AS producto_id,
    p.sku AS producto_codigo,
    p.name AS producto_descripcion,
    p.unit_measure AS unidad,
    wm.movement_date AS fecha,
    wm.created_at,
    CASE 
        WHEN wm.movement_type = 'receipt' AND wm.po_id IS NOT NULL THEN '02' -- Compra
        WHEN wm.movement_type = 'receipt' AND wm.po_id IS NULL THEN '16'     -- Saldo Inicial
        WHEN wm.movement_type = 'output' THEN '01'                          -- Venta
        WHEN wm.movement_type = 'transfer' THEN '11'                        -- Transferencia
        ELSE '99' 
    END AS operacion_tipo,
    '09' AS doc_tipo,
    -- Si no hay guion, la serie será '001' y el número el documento completo
    IF(LOCATE('-', wm.reference_document) > 0, SUBSTRING_INDEX(wm.reference_document, '-', 1), '001') AS doc_serie,
    IF(LOCATE('-', wm.reference_document) > 0, SUBSTRING_INDEX(wm.reference_document, '-', -1), wm.reference_document) AS doc_numero,
    wm.movement_type,
    md.quantity AS cantidad,
    md.unit_cost AS costo_unitario,
    md.total_cost AS costo_total_origen 
FROM movement_details md
JOIN warehouse_movements wm ON md.movement_id = wm.id
JOIN products p ON md.product_id = p.id;
------------------------------
-- Trigger para numeración automática de importaciones
-- ----------------------------
DELIMITER //
CREATE TRIGGER generar_numero_importacion
BEFORE INSERT ON importaciones
FOR EACH ROW
BEGIN
    DECLARE año_actual INT;
    DECLARE siguiente_numero INT;
    
    IF NEW.numero_importacion IS NULL THEN
        SET año_actual = YEAR(CURDATE());
        
        SELECT COALESCE(MAX(CAST(SUBSTRING(numero_importacion, 6) AS UNSIGNED)), 0)
        INTO siguiente_numero
        FROM importaciones 
        WHERE numero_importacion LIKE CONCAT(año_actual, '-%');
        
        SET NEW.numero_importacion = CONCAT(año_actual, '-', LPAD(siguiente_numero + 1, 3, '0'));
    END IF;
END //
DELIMITER ;

SET FOREIGN_KEY_CHECKS=1;

