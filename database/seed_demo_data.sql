-- ============================================================================
-- IMPORTCOST PRO - Datos Demo Completos
-- Ejecutar DESPUES de: schema.sql, seed.sql, todas las migrations y SPs
-- ============================================================================

USE importcost_pro;

SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================================
-- 1. ALMACENES ADICIONALES
-- ============================================================================
INSERT INTO almacenes (empresa_id, codigo, nombre, responsable, direccion, status) VALUES
(1, 'ALM-02', 'Almacén Secundario', 'Carlos Mendoza', 'Jr. Huancavelica 456, Lima', 'active'),
(1, 'ALM-03', 'Depósito Callao', 'Pedro Ramirez', 'Av. Gambetta 789, Callao', 'active');

-- ============================================================================
-- 2. USUARIOS ADICIONALES
-- ============================================================================
-- password para todos: admin123 (mismo hash)
INSERT INTO usuarios (empresa_id, email, password_hash, nombre, apellido, rol, status, ultimo_login) VALUES
(1, 'carlos@importdemo.pe', '$2b$12$U3JJR./ZVlzYXMQitz5VBOEWXVb5/95muORQIqFxZyG7dBFvryI6y',
 'Carlos', 'Mendoza', 'usuario', 'active', '2026-03-08 14:30:00'),
(1, 'maria@importdemo.pe', '$2b$12$U3JJR./ZVlzYXMQitz5VBOEWXVb5/95muORQIqFxZyG7dBFvryI6y',
 'Maria', 'Gutierrez', 'usuario', 'active', '2026-03-07 09:15:00'),
(1, 'jose@importdemo.pe', '$2b$12$U3JJR./ZVlzYXMQitz5VBOEWXVb5/95muORQIqFxZyG7dBFvryI6y',
 'Jose', 'Paredes', 'readonly', 'active', '2026-03-05 16:45:00'),
(1, 'ana@importdemo.pe', '$2b$12$U3JJR./ZVlzYXMQitz5VBOEWXVb5/95muORQIqFxZyG7dBFvryI6y',
 'Ana', 'Quispe', 'usuario', 'inactive', NULL);

-- Update admin ultimo_login
UPDATE usuarios SET ultimo_login = '2026-03-09 08:00:00' WHERE email = 'admin@importdemo.pe';

-- ============================================================================
-- 3. CATEGORIAS DE PRODUCTO
-- ============================================================================
INSERT INTO categorias_producto (empresa_id, nombre, descripcion, color_ui) VALUES
(1, 'Electrónica', 'Equipos electrónicos y tecnología', '#3B82F6'),
(1, 'Textiles', 'Prendas de vestir y telas', '#EF4444'),
(1, 'Maquinaria', 'Maquinaria industrial y equipos', '#F59E0B'),
(1, 'Alimentos', 'Productos alimenticios importados', '#10B981'),
(1, 'Plásticos', 'Envases y productos plásticos', '#8B5CF6'),
(1, 'Autopartes', 'Repuestos y accesorios vehiculares', '#0891B2');

-- ============================================================================
-- 4. PROVEEDORES
-- ============================================================================
INSERT INTO proveedores (empresa_id, ruc, razon_social, nombre_comercial, pais_id, email, telefono, contacto_nombre, moneda_id, incoterm_default, es_extranjero) VALUES
(1, 'CN-SH-88001', 'Shanghai Electronics Co Ltd', 'Shanghai Electronics',
 (SELECT id FROM paises WHERE codigo='CN'), 'sales@shanghaielectro.cn', '+86-21-5555-0100', 'Li Wei', 2, 'FOB', 1),
(1, 'CN-GZ-88002', 'Guangzhou Textiles Group', 'GZ Textiles',
 (SELECT id FROM paises WHERE codigo='CN'), 'export@gztextiles.cn', '+86-20-5555-0200', 'Zhang Min', 2, 'FOB', 1),
(1, 'US-CA-88003', 'California Industrial Supply', 'CalIndustrial',
 (SELECT id FROM paises WHERE codigo='US'), 'orders@calindustrial.com', '+1-310-555-0300', 'John Smith', 2, 'CIF', 1),
(1, 'DE-HH-88004', 'Hamburg Maschinen GmbH', 'Hamburg Maschinen',
 (SELECT id FROM paises WHERE codigo='DE'), 'verkauf@hamburgmaschinen.de', '+49-40-5555-0400', 'Klaus Mueller', 3, 'CIF', 1),
(1, 'BR-SP-88005', 'Sao Paulo Alimentos SA', 'SP Alimentos',
 (SELECT id FROM paises WHERE codigo='BR'), 'ventas@spalimentos.com.br', '+55-11-5555-0500', 'Roberto Silva', 2, 'FOB', 1),
(1, 'KR-SE-88006', 'Seoul Tech Components', 'Seoul Tech',
 (SELECT id FROM paises WHERE codigo='KR'), 'export@seoultech.kr', '+82-2-5555-0600', 'Park Ji-Sung', 2, 'FOB', 1),
(1, '20456789012', 'Distribuidora Nacional SAC', 'DistriNacional',
 (SELECT id FROM paises WHERE codigo='PE'), 'ventas@distrinacional.pe', '+51-1-555-0700', 'Luis Torres', 1, 'FOB', 0);

-- ============================================================================
-- 5. PRODUCTOS (20 productos variados)
-- ============================================================================
INSERT INTO productos (empresa_id, sku, nombre, descripcion, categoria_id, partida_id, unidad_medida, peso_kg, stock_minimo, punto_reposicion) VALUES
-- Electrónica (cat 1)
(1, 'ELEC-001', 'Laptop HP ProBook 450', 'Laptop empresarial 15.6" i5 16GB', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8471.30.00'), 'NIU', 2.100, 10, 15),
(1, 'ELEC-002', 'Monitor Samsung 27" 4K', 'Monitor LED 27 pulgadas UHD', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8528.52.10'), 'NIU', 5.500, 8, 12),
(1, 'ELEC-003', 'Impresora Epson L3250', 'Impresora multifunción tinta continua', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8443.31.10'), 'NIU', 4.200, 5, 8),
(1, 'ELEC-004', 'Cable HDMI 2m', 'Cable HDMI 2.1 alta velocidad', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8544.42.00'), 'NIU', 0.150, 50, 80),
-- Textiles (cat 2)
(1, 'TEXT-001', 'Polo algodón premium', 'Polo 100% algodón pima talla variada', 2,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='6109.10.00'), 'NIU', 0.250, 100, 150),
(1, 'TEXT-002', 'Chompa lana merino', 'Chompa tejida lana merino importada', 2,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='6110.20.00'), 'NIU', 0.450, 30, 50),
(1, 'TEXT-003', 'Zapatillas deportivas', 'Zapatillas running suela caucho', 2,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='6403.99.00'), 'PAR', 0.800, 40, 60),
-- Maquinaria (cat 3)
(1, 'MAQ-001', 'Selladora de bolsas industrial', 'Selladora automatica 220V', 3,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8422.30.00'), 'NIU', 45.000, 2, 3),
(1, 'MAQ-002', 'Horno industrial panadería', 'Horno rotativo 10 bandejas', 3,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8438.10.00'), 'NIU', 350.000, 1, 2),
(1, 'MAQ-003', 'Lavadora industrial 15kg', 'Lavadora centrifuga industrial', 3,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8450.20.00'), 'NIU', 68.000, 2, 3),
-- Alimentos (cat 4)
(1, 'ALIM-001', 'Café gourmet colombiano 1kg', 'Café tostado grano entero premium', 4,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='0901.21.10'), 'KGM', 1.000, 200, 300),
(1, 'ALIM-002', 'Chocolate belga tableta', 'Chocolate negro 70% cacao 100g', 4,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='1806.32.00'), 'KGM', 0.100, 500, 750),
(1, 'ALIM-003', 'Vino tinto reserva', 'Vino Cabernet Sauvignon 750ml', 4,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='2204.21.00'), 'NIU', 1.200, 100, 150),
-- Plásticos (cat 5)
(1, 'PLAS-001', 'Envases PET 500ml', 'Botellas PET transparentes lote 1000', 5,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='3923.30.00'), 'KGM', 0.025, 5000, 8000),
(1, 'PLAS-002', 'Contenedores plásticos', 'Contenedores apilables 20L', 5,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='3926.90.00'), 'NIU', 1.500, 100, 150),
-- Autopartes (cat 6)
(1, 'AUTO-001', 'Pastillas de freno', 'Juego pastillas freno delantero', 6,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8708.29.00'), 'NIU', 0.800, 30, 50),
(1, 'AUTO-002', 'Neumáticos 195/65R15', 'Neumáticos para sedán', 6,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='4011.10.00'), 'NIU', 8.500, 20, 30),
-- Más electrónica
(1, 'ELEC-005', 'Teclado mecánico RGB', 'Teclado gaming mecánico switches blue', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8471.41.00'), 'NIU', 0.900, 20, 35),
(1, 'ELEC-006', 'Mouse inalámbrico', 'Mouse ergonómico bluetooth', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8471.41.00'), 'NIU', 0.120, 30, 50),
(1, 'ELEC-007', 'Webcam HD 1080p', 'Cámara web con micrófono integrado', 1,
 (SELECT id FROM partidas_arancelarias WHERE codigo_hs='8528.52.10'), 'NIU', 0.200, 15, 25);

-- ============================================================================
-- 6. ORDENES DE COMPRA (8 ordenes en varios estados)
-- ============================================================================
INSERT INTO ordenes_compra (empresa_id, numero_oc, proveedor_id, fecha_orden, fecha_llegada_est, incoterm, moneda_id, tipo_cambio, puerto_embarque, puerto_destino, estado, total_flete, total_seguro, notas, created_by) VALUES
-- OC-001: China Electrónica (completada)
(1, 'OC-2026-001',
 (SELECT id FROM proveedores WHERE ruc='CN-SH-88001'), '2025-11-15', '2025-12-20',
 'FOB', 2, 3.7200, 'Shanghai', 'Callao', 'completada', 2500.00, 350.00, 'Primer pedido laptops y monitores', 1),
-- OC-002: China Textiles (en_almacen)
(1, 'OC-2026-002',
 (SELECT id FROM proveedores WHERE ruc='CN-GZ-88002'), '2025-12-01', '2026-01-15',
 'FOB', 2, 3.7300, 'Guangzhou', 'Callao', 'en_almacen', 1800.00, 250.00, 'Textiles temporada verano', 1),
-- OC-003: USA Maquinaria (prorrateado)
(1, 'OC-2026-003',
 (SELECT id FROM proveedores WHERE ruc='US-CA-88003'), '2026-01-10', '2026-02-15',
 'CIF', 2, 3.7400, 'Los Angeles', 'Callao', 'prorrateado', 3200.00, 480.00, 'Maquinaria industrial', 1),
-- OC-004: Alemania (en_transito)
(1, 'OC-2026-004',
 (SELECT id FROM proveedores WHERE ruc='DE-HH-88004'), '2026-02-01', '2026-03-20',
 'CIF', 3, 4.0500, 'Hamburg', 'Callao', 'en_transito', 4100.00, 620.00, 'Horno industrial y selladora', 1),
-- OC-005: Brasil Alimentos (en_aduana)
(1, 'OC-2026-005',
 (SELECT id FROM proveedores WHERE ruc='BR-SP-88005'), '2026-01-20', '2026-02-28',
 'FOB', 2, 3.7500, 'Santos', 'Callao', 'en_aduana', 1200.00, 180.00, 'Café y chocolate', 1),
-- OC-006: Corea (confirmada)
(1, 'OC-2026-006',
 (SELECT id FROM proveedores WHERE ruc='KR-SE-88006'), '2026-02-15', '2026-04-01',
 'FOB', 2, 3.7200, 'Busan', 'Callao', 'confirmada', 0, 0, 'Componentes electrónicos', 1),
-- OC-007: China Electrónica 2 (borrador)
(1, 'OC-2026-007',
 (SELECT id FROM proveedores WHERE ruc='CN-SH-88001'), '2026-03-05', '2026-04-15',
 'FOB', 2, 3.7500, 'Shanghai', 'Callao', 'borrador', 0, 0, 'Reposición periféricos', 1),
-- OC-008: China Plásticos (completada)
(1, 'OC-2026-008',
 (SELECT id FROM proveedores WHERE ruc='CN-GZ-88002'), '2025-10-20', '2025-11-25',
 'FOB', 2, 3.7100, 'Ningbo', 'Callao', 'completada', 900.00, 120.00, 'Envases y contenedores', 1);

-- ============================================================================
-- 7. ITEMS DE ORDENES DE COMPRA
-- ============================================================================

-- OC-001 items (laptops, monitores, impresoras)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'),
 (SELECT id FROM productos WHERE sku='ELEC-001'), 25, 485.00, 'NIU', 52.50, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'),
 (SELECT id FROM productos WHERE sku='ELEC-002'), 20, 290.00, 'NIU', 110.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'),
 (SELECT id FROM productos WHERE sku='ELEC-003'), 15, 165.00, 'NIU', 63.00, 1);

-- OC-002 items (textiles)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'),
 (SELECT id FROM productos WHERE sku='TEXT-001'), 500, 4.80, 'NIU', 125.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'),
 (SELECT id FROM productos WHERE sku='TEXT-002'), 200, 18.50, 'NIU', 90.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'),
 (SELECT id FROM productos WHERE sku='TEXT-003'), 300, 12.00, 'PAR', 240.00, 1);

-- OC-003 items (maquinaria)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'),
 (SELECT id FROM productos WHERE sku='MAQ-001'), 5, 1200.00, 'NIU', 225.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'),
 (SELECT id FROM productos WHERE sku='MAQ-003'), 3, 2800.00, 'NIU', 204.00, 1);

-- OC-004 items (maquinaria alemana)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-004'),
 (SELECT id FROM productos WHERE sku='MAQ-002'), 2, 8500.00, 'NIU', 700.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-004'),
 (SELECT id FROM productos WHERE sku='MAQ-001'), 3, 1350.00, 'NIU', 135.00, 1);

-- OC-005 items (alimentos)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'),
 (SELECT id FROM productos WHERE sku='ALIM-001'), 500, 8.50, 'KGM', 500.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'),
 (SELECT id FROM productos WHERE sku='ALIM-002'), 1000, 3.20, 'KGM', 100.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'),
 (SELECT id FROM productos WHERE sku='ALIM-003'), 200, 6.80, 'NIU', 240.00, 1);

-- OC-006 items (electrónica Corea)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-006'),
 (SELECT id FROM productos WHERE sku='ELEC-005'), 100, 28.00, 'NIU', 90.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-006'),
 (SELECT id FROM productos WHERE sku='ELEC-006'), 200, 12.50, 'NIU', 24.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-006'),
 (SELECT id FROM productos WHERE sku='ELEC-007'), 80, 22.00, 'NIU', 16.00, 1);

-- OC-007 items (borrador)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-007'),
 (SELECT id FROM productos WHERE sku='ELEC-004'), 500, 3.50, 'NIU', 75.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-007'),
 (SELECT id FROM productos WHERE sku='ELEC-005'), 50, 28.00, 'NIU', 45.00, 1);

-- OC-008 items (plásticos - completada)
INSERT INTO orden_compra_items (oc_id, producto_id, cantidad, precio_unitario, unidad_medida, peso_kg, created_by) VALUES
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'),
 (SELECT id FROM productos WHERE sku='PLAS-001'), 10000, 0.45, 'KGM', 250.00, 1),
((SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'),
 (SELECT id FROM productos WHERE sku='PLAS-002'), 200, 8.50, 'NIU', 300.00, 1);

-- ============================================================================
-- 8. IMPORTACIONES
-- ============================================================================
INSERT INTO importaciones (empresa_id, numero_importacion, descripcion, fecha_creacion, bl_number, container_number, via_transporte, fecha_embarque, fecha_arribo_estimada, fecha_arribo_real, estado, agente_aduanero, agente_carga, notas, created_by) VALUES
(1, '2025-001', 'Electrónica China - Nov 2025', '2025-11-20', 'SHACAL2025001', 'MSKU1234567',
 'maritimo', '2025-11-25', '2025-12-20', '2025-12-18', 'completada',
 'Aduanas Express SAC', 'MSC Peru', 'Embarque laptops y monitores', 1),
(1, '2025-002', 'Plásticos China - Oct 2025', '2025-10-25', 'NBOCAL2025002', 'TCLU7654321',
 'maritimo', '2025-10-28', '2025-11-25', '2025-11-23', 'completada',
 'Aduanas Express SAC', 'Hapag-Lloyd', 'Envases PET y contenedores', 1),
(1, '2026-001', 'Textiles China - Dic 2025', '2025-12-05', 'GZCAL2026001', 'CMAU9876543',
 'maritimo', '2025-12-10', '2026-01-15', '2026-01-14', 'en_almacen',
 'Aduanas Express SAC', 'COSCO Peru', 'Textiles temporada verano', 1),
(1, '2026-002', 'Maquinaria USA', '2026-01-15', 'LACAL2026002', 'HLXU1122334',
 'maritimo', '2026-01-20', '2026-02-15', '2026-02-14', 'prorrateado',
 'Global Aduanas SA', 'Maersk Peru', 'Selladoras y lavadoras industriales', 1),
(1, '2026-003', 'Alimentos Brasil', '2026-01-25', 'STCAL2026003', 'MSCU4455667',
 'maritimo', '2026-01-28', '2026-02-28', '2026-03-01', 'en_aduana',
 'Aduanas Express SAC', 'Evergreen Peru', 'Café, chocolate y vino', 1),
(1, '2026-004', 'Maquinaria Alemania', '2026-02-05', 'HHCAL2026004', 'TCNU7788990',
 'maritimo', '2026-02-10', '2026-03-20', NULL, 'en_transito',
 'Global Aduanas SA', 'Hamburg Süd', 'Hornos y selladoras industriales', 1);

-- Link importaciones <-> OCs
INSERT INTO importacion_ocs (importacion_id, oc_id, peso_total) VALUES
(1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 225.50),
(2, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'), 550.00),
(3, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'), 455.00),
(4, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'), 429.00),
(5, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'), 840.00),
(6, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-004'), 835.00);

-- ============================================================================
-- 9. GASTOS DE IMPORTACION
-- ============================================================================
INSERT INTO gastos_importacion (empresa_id, importacion_id, oc_id, tipo_gasto_codigo, descripcion, moneda_id, monto, tipo_cambio, fecha_gasto, estado, created_by) VALUES
-- Importación 1 (Electrónica - completada)
(1, 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 'flete_internacional', 'Flete marítimo Shanghai-Callao', 2, 2500.00, 3.7200, '2025-11-25', 'pagado', 1),
(1, 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 'seguro', 'Seguro marítimo', 2, 350.00, 3.7200, '2025-11-25', 'pagado', 1),
(1, 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 'gastos_aduaneros', 'Derechos de aduana DUA', 1, 4250.00, 1.0000, '2025-12-20', 'pagado', 1),
(1, 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 'honorarios_agente', 'Honorarios Aduanas Express', 1, 1800.00, 1.0000, '2025-12-22', 'pagado', 1),
(1, 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'), 'flete_local', 'Transporte Callao-Almacén', 1, 950.00, 1.0000, '2025-12-23', 'pagado', 1),
-- Importación 2 (Plásticos - completada)
(1, 2, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'), 'flete_internacional', 'Flete marítimo Ningbo-Callao', 2, 900.00, 3.7100, '2025-10-28', 'pagado', 1),
(1, 2, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'), 'seguro', 'Seguro de carga', 2, 120.00, 3.7100, '2025-10-28', 'pagado', 1),
(1, 2, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'), 'gastos_aduaneros', 'Derechos de aduana', 1, 2100.00, 1.0000, '2025-11-25', 'pagado', 1),
(1, 2, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'), 'flete_local', 'Transporte local', 1, 650.00, 1.0000, '2025-11-26', 'pagado', 1),
-- Importación 3 (Textiles)
(1, 3, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'), 'flete_internacional', 'Flete COSCO Guangzhou-Callao', 2, 1800.00, 3.7300, '2025-12-10', 'pagado', 1),
(1, 3, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'), 'seguro', 'Seguro marítimo', 2, 250.00, 3.7300, '2025-12-10', 'pagado', 1),
(1, 3, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'), 'gastos_aduaneros', 'Derechos aduaneros textiles', 1, 3800.00, 1.0000, '2026-01-15', 'aprobado', 1),
(1, 3, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'), 'honorarios_agente', 'Honorarios agente', 1, 1500.00, 1.0000, '2026-01-16', 'aprobado', 1),
-- Importación 4 (Maquinaria USA)
(1, 4, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'), 'flete_internacional', 'Flete Maersk LA-Callao', 2, 3200.00, 3.7400, '2026-01-20', 'pagado', 1),
(1, 4, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'), 'seguro', 'Seguro maquinaria', 2, 480.00, 3.7400, '2026-01-20', 'pagado', 1),
(1, 4, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'), 'gastos_aduaneros', 'Impuestos importación', 1, 5200.00, 1.0000, '2026-02-16', 'aprobado', 1),
(1, 4, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'), 'handling', 'Handling portuario', 1, 2800.00, 1.0000, '2026-02-15', 'aprobado', 1),
-- Importación 5 (Alimentos)
(1, 5, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'), 'flete_internacional', 'Flete Santos-Callao', 2, 1200.00, 3.7500, '2026-01-28', 'aprobado', 1),
(1, 5, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'), 'seguro', 'Seguro alimentos', 2, 180.00, 3.7500, '2026-01-28', 'aprobado', 1),
(1, 5, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-005'), 'inspeccion', 'Inspección sanitaria SENASA', 1, 1500.00, 1.0000, '2026-03-01', 'pendiente', 1);

-- ============================================================================
-- 10. INVENTARIO (stock actual en almacenes)
-- ============================================================================
INSERT INTO inventario (empresa_id, producto_id, almacen_id, lote, cantidad, costo_unitario) VALUES
-- ALM-01 Principal
(1, (SELECT id FROM productos WHERE sku='ELEC-001'), 1, 'OC2026001-L1', 18, 625.40),
(1, (SELECT id FROM productos WHERE sku='ELEC-002'), 1, 'OC2026001-L1', 14, 378.20),
(1, (SELECT id FROM productos WHERE sku='ELEC-003'), 1, 'OC2026001-L1', 10, 225.80),
(1, (SELECT id FROM productos WHERE sku='ELEC-004'), 1, 'STOCK-INI', 120, 15.50),
(1, (SELECT id FROM productos WHERE sku='TEXT-001'), 1, 'OC2026002-L1', 380, 8.20),
(1, (SELECT id FROM productos WHERE sku='TEXT-002'), 1, 'OC2026002-L1', 160, 28.40),
(1, (SELECT id FROM productos WHERE sku='TEXT-003'), 1, 'OC2026002-L1', 220, 19.60),
(1, (SELECT id FROM productos WHERE sku='PLAS-001'), 1, 'OC2026008-L1', 7500, 2.10),
(1, (SELECT id FROM productos WHERE sku='PLAS-002'), 1, 'OC2026008-L1', 150, 14.20),
(1, (SELECT id FROM productos WHERE sku='MAQ-001'), 1, 'OC2026003-L1', 4, 1580.00),
(1, (SELECT id FROM productos WHERE sku='MAQ-003'), 1, 'OC2026003-L1', 2, 3650.00),
(1, (SELECT id FROM productos WHERE sku='ALIM-001'), 1, 'STOCK-INI', 80, 42.50),
(1, (SELECT id FROM productos WHERE sku='ALIM-002'), 1, 'STOCK-INI', 200, 18.90),
(1, (SELECT id FROM productos WHERE sku='ALIM-003'), 1, 'STOCK-INI', 45, 32.80),
(1, (SELECT id FROM productos WHERE sku='AUTO-001'), 1, 'STOCK-INI', 25, 22.50),
(1, (SELECT id FROM productos WHERE sku='AUTO-002'), 1, 'STOCK-INI', 12, 185.00),
(1, (SELECT id FROM productos WHERE sku='ELEC-005'), 1, 'STOCK-INI', 35, 42.00),
(1, (SELECT id FROM productos WHERE sku='ELEC-006'), 1, 'STOCK-INI', 45, 18.50),
(1, (SELECT id FROM productos WHERE sku='ELEC-007'), 1, 'STOCK-INI', 8, 35.00),
-- ALM-02 Secundario
(1, (SELECT id FROM productos WHERE sku='ELEC-001'), 2, 'OC2026001-L1', 5, 625.40),
(1, (SELECT id FROM productos WHERE sku='TEXT-001'), 2, 'OC2026002-L1', 100, 8.20),
(1, (SELECT id FROM productos WHERE sku='TEXT-003'), 2, 'OC2026002-L1', 60, 19.60),
(1, (SELECT id FROM productos WHERE sku='PLAS-001'), 2, 'OC2026008-L1', 2000, 2.10),
(1, (SELECT id FROM productos WHERE sku='ALIM-001'), 2, 'STOCK-INI', 120, 42.50),
-- ALM-03 Depósito Callao
(1, (SELECT id FROM productos WHERE sku='MAQ-001'), 3, 'OC2026003-L1', 1, 1580.00),
(1, (SELECT id FROM productos WHERE sku='PLAS-002'), 3, 'OC2026008-L1', 40, 14.20);

-- ============================================================================
-- 11. MOVIMIENTOS DE ALMACEN (con detalle)
-- ============================================================================

-- Movimiento 1: Ingreso Electrónica (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, oc_id, concepto_id, documento_referencia, total_productos, valor_total, estado, notas, created_by) VALUES
(1, 'VLE-2025-001', 'ingreso', '2025-12-23',
 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-001'),
 (SELECT id FROM conceptos_almacen WHERE codigo='ING-02'),
 'OC-2026-001', 3, 20575.00, 'completado', 'Ingreso importación electrónica', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(1, (SELECT id FROM productos WHERE sku='ELEC-001'), 25, 625.40, 15635.00, 'OC2026001-L1'),
(1, (SELECT id FROM productos WHERE sku='ELEC-002'), 20, 378.20, 7564.00, 'OC2026001-L1'),
(1, (SELECT id FROM productos WHERE sku='ELEC-003'), 15, 225.80, 3387.00, 'OC2026001-L1');

-- Movimiento 2: Ingreso Plásticos (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, oc_id, concepto_id, documento_referencia, total_productos, valor_total, estado, created_by) VALUES
(1, 'VLE-2025-002', 'ingreso', '2025-11-26',
 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-008'),
 (SELECT id FROM conceptos_almacen WHERE codigo='ING-02'),
 'OC-2026-008', 2, 6200.00, 'completado', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(2, (SELECT id FROM productos WHERE sku='PLAS-001'), 10000, 2.10, 21000.00, 'OC2026008-L1'),
(2, (SELECT id FROM productos WHERE sku='PLAS-002'), 200, 14.20, 2840.00, 'OC2026008-L1');

-- Movimiento 3: Ingreso Textiles (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, oc_id, concepto_id, documento_referencia, total_productos, valor_total, estado, created_by) VALUES
(1, 'VLE-2026-001', 'ingreso', '2026-01-16',
 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-002'),
 (SELECT id FROM conceptos_almacen WHERE codigo='ING-02'),
 'OC-2026-002', 3, 11216.00, 'completado', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(3, (SELECT id FROM productos WHERE sku='TEXT-001'), 500, 8.20, 4100.00, 'OC2026002-L1'),
(3, (SELECT id FROM productos WHERE sku='TEXT-002'), 200, 28.40, 5680.00, 'OC2026002-L1'),
(3, (SELECT id FROM productos WHERE sku='TEXT-003'), 300, 19.60, 5880.00, 'OC2026002-L1');

-- Movimiento 4: Ingreso Maquinaria (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, oc_id, concepto_id, documento_referencia, total_productos, valor_total, estado, created_by) VALUES
(1, 'VLE-2026-002', 'ingreso', '2026-02-16',
 1, (SELECT id FROM ordenes_compra WHERE numero_oc='OC-2026-003'),
 (SELECT id FROM conceptos_almacen WHERE codigo='ING-02'),
 'OC-2026-003', 2, 17270.00, 'completado', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(4, (SELECT id FROM productos WHERE sku='MAQ-001'), 5, 1580.00, 7900.00, 'OC2026003-L1'),
(4, (SELECT id FROM productos WHERE sku='MAQ-003'), 3, 3650.00, 10950.00, 'OC2026003-L1');

-- Movimiento 5: Salida por consumo interno (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, concepto_id, solicitante, total_productos, valor_total, estado, notas, created_by) VALUES
(1, 'VLS-2026-001', 'salida', '2026-01-20',
 1, (SELECT id FROM conceptos_almacen WHERE codigo='SAL-01'),
 'Dpto. Sistemas', 2, 2503.80, 'completado', 'Equipos para oficina nueva', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(5, (SELECT id FROM productos WHERE sku='ELEC-001'), 2, 625.40, 1250.80, 'OC2026001-L1'),
(5, (SELECT id FROM productos WHERE sku='ELEC-002'), 3, 378.20, 1134.60, 'OC2026001-L1');

-- Movimiento 6: Salida textiles (completado)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, concepto_id, solicitante, total_productos, valor_total, estado, notas, created_by) VALUES
(1, 'VLS-2026-002', 'salida', '2026-02-05',
 1, (SELECT id FROM conceptos_almacen WHERE codigo='SAL-01'),
 'Tienda Centro', 3, 2780.00, 'completado', 'Reposición tienda centro', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(6, (SELECT id FROM productos WHERE sku='TEXT-001'), 20, 8.20, 164.00, 'OC2026002-L1'),
(6, (SELECT id FROM productos WHERE sku='TEXT-002'), 40, 28.40, 1136.00, 'OC2026002-L1'),
(6, (SELECT id FROM productos WHERE sku='TEXT-003'), 20, 19.60, 392.00, 'OC2026002-L1');

-- Movimiento 7: Transferencia a ALM-02
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, almacen_destino_id, concepto_id, total_productos, valor_total, estado, notas, created_by) VALUES
(1, 'VLS-2026-003', 'transferencia', '2026-02-10',
 1, 2, (SELECT id FROM conceptos_almacen WHERE codigo='SAL-02'),
 3, 5977.00, 'completado', 'Transferencia a almacén secundario', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(7, (SELECT id FROM productos WHERE sku='ELEC-001'), 5, 625.40, 3127.00, 'OC2026001-L1'),
(7, (SELECT id FROM productos WHERE sku='TEXT-001'), 100, 8.20, 820.00, 'OC2026002-L1'),
(7, (SELECT id FROM productos WHERE sku='TEXT-003'), 60, 19.60, 1176.00, 'OC2026002-L1');

-- Movimiento 8: Salida consumo plásticos
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, concepto_id, solicitante, total_productos, valor_total, estado, created_by) VALUES
(1, 'VLS-2026-004', 'salida', '2026-02-20',
 1, (SELECT id FROM conceptos_almacen WHERE codigo='SAL-01'),
 'Producción', 1, 1050.00, 'completado', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(8, (SELECT id FROM productos WHERE sku='PLAS-001'), 500, 2.10, 1050.00, 'OC2026008-L1');

-- Movimiento 9: Salida reciente (marzo)
INSERT INTO movimientos_almacen (empresa_id, numero_movimiento, tipo_movimiento, fecha_movimiento, almacen_id, concepto_id, solicitante, total_productos, valor_total, estado, created_by) VALUES
(1, 'VLS-2026-005', 'salida', '2026-03-05',
 1, (SELECT id FROM conceptos_almacen WHERE codigo='SAL-01'),
 'Tienda San Isidro', 2, 1252.40, 'completado', 1);

INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote) VALUES
(9, (SELECT id FROM productos WHERE sku='ELEC-003'), 5, 225.80, 1129.00, 'OC2026001-L1'),
(9, (SELECT id FROM productos WHERE sku='ELEC-004'), 30, 15.50, 465.00, 'STOCK-INI');

-- Update correlativos
UPDATE correlativos SET ultimo_numero = 2 WHERE tipo = 'vale_ingreso' AND empresa_id = 1;
UPDATE correlativos SET ultimo_numero = 5 WHERE tipo = 'vale_salida' AND empresa_id = 1;

-- ============================================================================
-- 12. REQUERIMIENTOS
-- ============================================================================
INSERT INTO requerimientos (empresa_id, numero, fecha, almacen_id, prioridad, solicitante, estado, notas, created_by) VALUES
(1, 'REQ-2026-001', '2026-02-15', 1, 'alta', 'Maria Gutierrez', 'firmado',
 'Reposición urgente de laptops para proyecto', 2),
(1, 'REQ-2026-002', '2026-02-20', 1, 'media', 'Carlos Mendoza', 'derivado',
 'Envases para producción mensual', 2),
(1, 'REQ-2026-003', '2026-03-01', 2, 'baja', 'Ana Quispe', 'abierto',
 'Reponer stock mínimo autopartes', 3),
(1, 'REQ-2026-004', '2026-03-05', 1, 'alta', 'Jose Paredes', 'abierto',
 'Requerimiento maquinaria para nueva planta', 4);

INSERT INTO requerimiento_items (requerimiento_id, producto_id, cantidad, precio_estimado, total) VALUES
-- REQ-001
(1, (SELECT id FROM productos WHERE sku='ELEC-001'), 10, 625.40, 6254.00),
(1, (SELECT id FROM productos WHERE sku='ELEC-002'), 8, 378.20, 3025.60),
-- REQ-002
(2, (SELECT id FROM productos WHERE sku='PLAS-001'), 5000, 2.10, 10500.00),
(2, (SELECT id FROM productos WHERE sku='PLAS-002'), 50, 14.20, 710.00),
-- REQ-003
(3, (SELECT id FROM productos WHERE sku='AUTO-001'), 30, 22.50, 675.00),
(3, (SELECT id FROM productos WHERE sku='AUTO-002'), 20, 185.00, 3700.00),
-- REQ-004
(4, (SELECT id FROM productos WHERE sku='MAQ-002'), 1, 8500.00, 8500.00),
(4, (SELECT id FROM productos WHERE sku='MAQ-001'), 2, 1580.00, 3160.00);

UPDATE correlativos SET ultimo_numero = 4 WHERE tipo = 'requerimiento' AND empresa_id = 1;

-- ============================================================================
-- 13. TOMA DE INVENTARIO
-- ============================================================================
INSERT INTO toma_inventario (empresa_id, numero, almacen_id, fecha_inicio, fecha_fin, responsable, estado, notas, created_by) VALUES
(1, 'TIF-2026-001', 1, '2026-02-28', '2026-03-01', 'Carlos Mendoza', 'completado',
 'Toma de inventario mensual febrero', 2),
(1, 'TIF-2026-002', 2, '2026-03-07', NULL, 'Pedro Ramirez', 'en_proceso',
 'Toma inventario almacén secundario', 1);

-- Toma 1 items (completada - con algunas diferencias)
INSERT INTO toma_inventario_items (toma_id, producto_id, stock_sistema, stock_contado, diferencia, observacion) VALUES
(1, (SELECT id FROM productos WHERE sku='ELEC-001'), 20, 18, -2, 'Falta verificar despacho pendiente'),
(1, (SELECT id FROM productos WHERE sku='ELEC-002'), 17, 14, -3, 'Posible error en registro de salida'),
(1, (SELECT id FROM productos WHERE sku='ELEC-003'), 15, 15, 0, NULL),
(1, (SELECT id FROM productos WHERE sku='TEXT-001'), 400, 380, -20, 'Revisar merma'),
(1, (SELECT id FROM productos WHERE sku='TEXT-002'), 200, 200, 0, NULL),
(1, (SELECT id FROM productos WHERE sku='PLAS-001'), 9500, 9500, 0, NULL),
(1, (SELECT id FROM productos WHERE sku='MAQ-001'), 5, 5, 0, NULL);

-- Toma 2 items (en proceso)
INSERT INTO toma_inventario_items (toma_id, producto_id, stock_sistema, stock_contado, diferencia) VALUES
(2, (SELECT id FROM productos WHERE sku='ELEC-001'), 5, 5, 0),
(2, (SELECT id FROM productos WHERE sku='TEXT-001'), 100, NULL, 0),
(2, (SELECT id FROM productos WHERE sku='TEXT-003'), 60, NULL, 0),
(2, (SELECT id FROM productos WHERE sku='PLAS-001'), 2000, NULL, 0);

UPDATE correlativos SET ultimo_numero = 2 WHERE tipo = 'toma_inventario' AND empresa_id = 1;

-- ============================================================================
-- 14. CONFIGURACION DEL SISTEMA (si existe la tabla)
-- ============================================================================
INSERT IGNORE INTO configuracion_sistema (empresa_id, seccion, clave, valor, tipo_dato, descripcion) VALUES
(1, 'general', 'nombre_empresa', 'EMPRESA DEMO SAC', 'string', 'Razón social'),
(1, 'general', 'ruc', '20100000001', 'string', 'RUC de la empresa'),
(1, 'general', 'moneda_default', 'PEN', 'string', 'Moneda por defecto'),
(1, 'general', 'incoterm_default', 'FOB', 'string', 'Incoterm por defecto'),
(1, 'general', 'igv_tasa', '18', 'number', 'Tasa de IGV (%)'),
(1, 'inventario', 'metodo_costeo', 'promedio', 'string', 'Método de costeo de inventario'),
(1, 'inventario', 'stock_minimo_alerta', 'true', 'boolean', 'Activar alertas de stock mínimo'),
(1, 'inventario', 'dias_rotacion_lenta', '90', 'number', 'Días para considerar rotación lenta'),
(1, 'inventario', 'permitir_stock_negativo', 'false', 'boolean', 'Permitir stock negativo'),
(1, 'compras', 'aprobacion_requerida', 'true', 'boolean', 'Requiere aprobación para OC'),
(1, 'compras', 'monto_aprobacion', '5000', 'number', 'Monto en USD que requiere aprobación'),
(1, 'compras', 'dias_entrega_default', '30', 'number', 'Días de entrega por defecto'),
(1, 'compras', 'formato_oc', 'OC-{YYYY}-{NNN}', 'string', 'Formato de numeración OC'),
(1, 'documentos', 'prefijo_vale_ingreso', 'VLE', 'string', 'Prefijo de vales de ingreso'),
(1, 'documentos', 'prefijo_vale_salida', 'VLS', 'string', 'Prefijo de vales de salida'),
(1, 'documentos', 'prefijo_requerimiento', 'REQ', 'string', 'Prefijo de requerimientos'),
(1, 'documentos', 'prefijo_toma', 'TIF', 'string', 'Prefijo de toma de inventario');

-- ============================================================================
-- 15. TIPOS DE CAMBIO HISTORICOS (para reportes)
-- ============================================================================
INSERT INTO tipos_cambio (moneda_id, fecha, tc_compra, tc_venta, fuente) VALUES
((SELECT id FROM monedas WHERE codigo = 'USD'), '2025-10-15', 3.7050, 3.7350, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2025-11-15', 3.7100, 3.7400, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2025-12-15', 3.7150, 3.7450, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2026-01-15', 3.7200, 3.7500, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2026-02-15', 3.7300, 3.7600, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2026-03-01', 3.7250, 3.7550, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'USD'), '2026-03-08', 3.7200, 3.7500, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'EUR'), '2026-01-15', 4.0300, 4.0800, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'EUR'), '2026-02-15', 4.0400, 4.0900, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'EUR'), '2026-03-08', 4.0500, 4.1000, 'sunat');

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- VERIFICACION
-- ============================================================================
SELECT 'Almacenes' AS tabla, COUNT(*) AS registros FROM almacenes
UNION ALL SELECT 'Usuarios', COUNT(*) FROM usuarios
UNION ALL SELECT 'Categorias', COUNT(*) FROM categorias_producto
UNION ALL SELECT 'Proveedores', COUNT(*) FROM proveedores
UNION ALL SELECT 'Productos', COUNT(*) FROM productos
UNION ALL SELECT 'Ordenes Compra', COUNT(*) FROM ordenes_compra
UNION ALL SELECT 'OC Items', COUNT(*) FROM orden_compra_items
UNION ALL SELECT 'Importaciones', COUNT(*) FROM importaciones
UNION ALL SELECT 'Gastos', COUNT(*) FROM gastos_importacion
UNION ALL SELECT 'Inventario', COUNT(*) FROM inventario
UNION ALL SELECT 'Movimientos', COUNT(*) FROM movimientos_almacen
UNION ALL SELECT 'Mov Detalle', COUNT(*) FROM movimiento_detalle
UNION ALL SELECT 'Requerimientos', COUNT(*) FROM requerimientos
UNION ALL SELECT 'Tomas Inventario', COUNT(*) FROM toma_inventario;
