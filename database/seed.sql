-- ============================================================================
-- IMPORTCOST PRO - Data Inicial (Seed)
-- Paises, Monedas, Estados, Tipos de Gasto, Partidas Arancelarias base
-- ============================================================================

USE importcost_pro;

-- ============================================================================
-- PAISES (principales socios comerciales de Peru)
-- ============================================================================
INSERT INTO paises (codigo, nombre, region, tiene_tlc_peru) VALUES
('PE', 'Perú', 'Sudamérica', 0),
('US', 'Estados Unidos', 'Norteamérica', 1),
('CN', 'China', 'Asia', 1),
('DE', 'Alemania', 'Europa', 1),
('JP', 'Japón', 'Asia', 1),
('MX', 'México', 'Norteamérica', 1),
('BR', 'Brasil', 'Sudamérica', 1),
('CL', 'Chile', 'Sudamérica', 1),
('CO', 'Colombia', 'Sudamérica', 1),
('KR', 'Corea del Sur', 'Asia', 1),
('CA', 'Canadá', 'Norteamérica', 1),
('ES', 'España', 'Europa', 1),
('IT', 'Italia', 'Europa', 1),
('FR', 'Francia', 'Europa', 1),
('GB', 'Reino Unido', 'Europa', 1),
('IN', 'India', 'Asia', 0),
('TW', 'Taiwán', 'Asia', 0),
('TH', 'Tailandia', 'Asia', 1),
('VN', 'Vietnam', 'Asia', 0),
('EC', 'Ecuador', 'Sudamérica', 1),
('AR', 'Argentina', 'Sudamérica', 1),
('PA', 'Panamá', 'Centroamérica', 1),
('CR', 'Costa Rica', 'Centroamérica', 1),
('SG', 'Singapur', 'Asia', 1),
('AU', 'Australia', 'Oceanía', 1),
('NZ', 'Nueva Zelanda', 'Oceanía', 0),
('HK', 'Hong Kong', 'Asia', 1),
('TR', 'Turquía', 'Europa', 0),
('PL', 'Polonia', 'Europa', 1),
('NL', 'Países Bajos', 'Europa', 1);

-- ============================================================================
-- MONEDAS
-- ============================================================================
INSERT INTO monedas (codigo, nombre, simbolo) VALUES
('PEN', 'Nuevo Sol', 'S/'),
('USD', 'Dólar Americano', '$'),
('EUR', 'Euro', '€'),
('CNY', 'Yuan Chino', '¥'),
('GBP', 'Libra Esterlina', '£'),
('JPY', 'Yen Japonés', '¥'),
('BRL', 'Real Brasileño', 'R$'),
('MXN', 'Peso Mexicano', '$'),
('CLP', 'Peso Chileno', '$'),
('COP', 'Peso Colombiano', '$'),
('CAD', 'Dólar Canadiense', 'C$'),
('KRW', 'Won Coreano', '₩');

-- Tipos de cambio iniciales (referencia marzo 2026)
INSERT INTO tipos_cambio (moneda_id, fecha, tc_compra, tc_venta, fuente) VALUES
((SELECT id FROM monedas WHERE codigo = 'USD'), '2026-03-07', 3.7200, 3.7500, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'EUR'), '2026-03-07', 4.0500, 4.1000, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'CNY'), '2026-03-07', 0.5100, 0.5300, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'GBP'), '2026-03-07', 4.7000, 4.7500, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'JPY'), '2026-03-07', 0.0248, 0.0252, 'sunat'),
((SELECT id FROM monedas WHERE codigo = 'BRL'), '2026-03-07', 0.6400, 0.6600, 'sunat');

-- ============================================================================
-- ESTADOS DE IMPORTACION
-- ============================================================================
INSERT INTO estados_importacion (codigo, nombre, descripcion, orden, color_ui, icono_ui, es_final) VALUES
('borrador',    'Borrador',     'Orden de compra en preparación',     1, '#94A3B8', 'edit',              0),
('confirmada',  'Confirmada',   'OC confirmada con proveedor',        2, '#3B82F6', 'check_circle',      0),
('en_transito', 'En Tránsito',  'Mercancía en camino',                3, '#F59E0B', 'local_shipping',    0),
('en_aduana',   'En Aduana',    'Proceso de desaduanaje',             4, '#EF4444', 'gavel',             0),
('prorrateado', 'Prorrateado',  'Costos calculados y distribuidos',   5, '#8B5CF6', 'calculate',         0),
('en_almacen',  'En Almacén',   'Mercancía recibida en almacén',      6, '#10B981', 'inventory',         0),
('completada',  'Completada',   'Importación finalizada',             7, '#059669', 'done_all',          1),
('cancelada',   'Cancelada',    'Importación cancelada',              8, '#DC2626', 'cancel',            1);

-- ============================================================================
-- TIPOS DE GASTO
-- ============================================================================
INSERT INTO tipos_gasto (codigo, nombre, descripcion, color_ui, icono_ui, requiere_proveedor, afecta_cif, orden) VALUES
('flete_internacional', 'Flete Internacional',  'Transporte internacional marítimo/aéreo',   '#3B82F6', 'flight',           1, 1, 1),
('seguro',              'Seguro',               'Seguro de transporte internacional',        '#10B981', 'security',         1, 1, 2),
('flete_local',         'Flete Local',          'Transporte nacional puerto-almacén',        '#F59E0B', 'local_shipping',   1, 0, 3),
('gastos_aduaneros',    'Gastos Aduaneros',     'Derechos y tasas de aduana',                '#EF4444', 'gavel',            0, 0, 4),
('honorarios_agente',   'Honorarios Agente',    'Honorarios de agente de aduanas',           '#8B5CF6', 'badge',            1, 0, 5),
('almacenaje',          'Almacenaje',           'Almacenamiento temporal en depósito',       '#6366F1', 'warehouse',        1, 0, 6),
('gastos_bancarios',    'Gastos Bancarios',     'Comisiones y gastos bancarios',             '#059669', 'account_balance',  0, 0, 7),
('handling',            'Handling Portuario',   'Gastos de manipulación en puerto',          '#D97706', 'forklift',         1, 0, 8),
('inspeccion',          'Inspección',           'Gastos de inspección y control',            '#0891B2', 'search',           1, 0, 9),
('descarga',            'Descarga',             'Gastos de descarga de mercancía',           '#BE185D', 'download',         1, 0, 10),
('otros',               'Otros Gastos',         'Otros gastos varios de importación',        '#94A3B8', 'payments',         0, 0, 99);

-- ============================================================================
-- TLC ACUERDOS (principales tratados comerciales de Peru)
-- ============================================================================
INSERT INTO tlc_acuerdos (pais_id, nombre_acuerdo, fecha_vigencia, tasa_preferencial, requisitos, status) VALUES
((SELECT id FROM paises WHERE codigo = 'US'), 'TLC Perú - Estados Unidos', '2009-02-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'CN'), 'TLC Perú - China', '2010-03-01', 0.00, 'Certificado de origen Form E', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'CL'), 'TLC Perú - Chile', '2009-03-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'CA'), 'TLC Perú - Canadá', '2009-08-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'KR'), 'TLC Perú - Corea del Sur', '2011-08-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'JP'), 'AAE Perú - Japón', '2012-03-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'MX'), 'Alianza del Pacífico', '2016-05-01', 0.00, 'Certificado de origen AP', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'CO'), 'CAN - Comunidad Andina', '1993-01-01', 0.00, 'Certificado de origen CAN', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'DE'), 'TLC Perú - Unión Europea', '2013-03-01', 0.00, 'EUR.1 o declaración en factura', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'GB'), 'TLC Perú - Reino Unido', '2021-01-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'AU'), 'CPTPP', '2021-09-19', 0.00, 'Certificado de origen CPTPP', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'SG'), 'TLC Perú - Singapur', '2009-08-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'TH'), 'TLC Perú - Tailandia', '2011-12-31', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'PA'), 'TLC Perú - Panamá', '2012-05-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'CR'), 'TLC Perú - Costa Rica', '2013-06-01', 0.00, 'Certificado de origen', 'vigente'),
((SELECT id FROM paises WHERE codigo = 'HK'), 'TLC Perú - Hong Kong', '2024-01-01', 0.00, 'Certificado de origen', 'vigente');

-- ============================================================================
-- PARTIDAS ARANCELARIAS BASE (las mas comunes para Pymes importadoras)
-- ============================================================================
INSERT INTO partidas_arancelarias (codigo_hs, descripcion, tasa_ad_valorem, tasa_igv, tasa_ipm, unidad_medida) VALUES
-- Electrónica y tecnología
('8471.30.00', 'Máquinas automáticas para procesamiento de datos portátiles (laptops)', 0.00, 16.00, 2.00, 'NIU'),
('8471.41.00', 'Otras máquinas automáticas para procesamiento de datos (PCs)', 0.00, 16.00, 2.00, 'NIU'),
('8528.52.10', 'Monitores con pantalla plana LCD/LED', 0.00, 16.00, 2.00, 'NIU'),
('8517.12.00', 'Teléfonos móviles celulares y smartphones', 0.00, 16.00, 2.00, 'NIU'),
('8443.31.10', 'Impresoras multifuncionales', 6.00, 16.00, 2.00, 'NIU'),
('8542.39.00', 'Circuitos integrados y semiconductores', 0.00, 16.00, 2.00, 'KGM'),
('8544.42.00', 'Cables y conductores eléctricos', 0.00, 16.00, 2.00, 'KGM'),
-- Textiles y confecciones
('6109.10.00', 'Camisetas de punto de algodón', 11.00, 16.00, 2.00, 'NIU'),
('6110.20.00', 'Suéteres y pullovers de algodón', 11.00, 16.00, 2.00, 'NIU'),
('6204.62.00', 'Pantalones de algodón para mujeres', 11.00, 16.00, 2.00, 'NIU'),
('6403.99.00', 'Calzado con suela de caucho/plástico', 11.00, 16.00, 2.00, 'PAR'),
-- Alimentos y bebidas
('0901.21.10', 'Café tostado sin descafeinar', 6.00, 16.00, 2.00, 'KGM'),
('1806.32.00', 'Chocolate en tabletas o barras', 6.00, 16.00, 2.00, 'KGM'),
('2204.21.00', 'Vino de uvas frescas', 6.00, 16.00, 2.00, 'LTR'),
-- Maquinaria y equipos
('8422.30.00', 'Máquinas de llenar, cerrar, sellar botellas', 0.00, 16.00, 2.00, 'NIU'),
('8438.10.00', 'Máquinas para panadería y pastelería', 0.00, 16.00, 2.00, 'NIU'),
('8450.20.00', 'Lavadoras de capacidad > 10 kg', 6.00, 16.00, 2.00, 'NIU'),
-- Autopartes
('8708.29.00', 'Partes y accesorios de carrocería', 6.00, 16.00, 2.00, 'KGM'),
('4011.10.00', 'Neumáticos nuevos de caucho para automóviles', 6.00, 16.00, 2.00, 'NIU'),
-- Plásticos
('3923.30.00', 'Envases de plástico (botellas, frascos)', 6.00, 16.00, 2.00, 'KGM'),
('3926.90.00', 'Otras manufacturas de plástico', 6.00, 16.00, 2.00, 'KGM'),
-- Cosméticos y salud
('3304.99.00', 'Preparaciones de belleza y maquillaje', 6.00, 16.00, 2.00, 'KGM'),
('3401.11.00', 'Jabones y preparaciones de tocador', 6.00, 16.00, 2.00, 'KGM'),
-- Juguetes
('9503.00.00', 'Juguetes y modelos a escala', 6.00, 16.00, 2.00, 'KGM'),
-- Muebles
('9403.60.00', 'Muebles de madera', 6.00, 16.00, 2.00, 'KGM'),
('9403.20.00', 'Muebles de metal', 6.00, 16.00, 2.00, 'KGM');

-- ============================================================================
-- EMPRESA DEMO (para desarrollo)
-- ============================================================================
INSERT INTO empresas (ruc, razon_social, nombre_comercial, email, moneda_default_id)
VALUES ('20100000001', 'EMPRESA DEMO SAC', 'ImportDemo', 'admin@importdemo.pe',
        (SELECT id FROM monedas WHERE codigo = 'PEN'));

-- Usuario admin de prueba (password: admin123 - bcrypt hash)
INSERT INTO usuarios (empresa_id, email, password_hash, nombre, apellido, rol)
VALUES (1, 'admin@importdemo.pe',
        '$2b$12$U3JJR./ZVlzYXMQitz5VBOEWXVb5/95muORQIqFxZyG7dBFvryI6y',
        'Admin', 'Demo', 'admin');

-- Almacen principal de demo
INSERT INTO almacenes (empresa_id, codigo, nombre, responsable, direccion)
VALUES (1, 'ALM-01', 'Almacén Principal', 'Admin Demo', 'Av. Argentina 1234, Callao');
