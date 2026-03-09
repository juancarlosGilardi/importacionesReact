-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Catalogos
-- Proveedores, Productos, Almacenes, Categorias
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- PROVEEDORES
-- ============================================================================

CREATE PROCEDURE sp_proveedor_listar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_status VARCHAR(10),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    DECLARE v_limit INT DEFAULT 20;
    SET v_limit = IFNULL(p_per_page, 20);
    SET v_offset = (IFNULL(p_page, 1) - 1) * v_limit;

    SELECT
        p.id, p.ruc, p.razon_social, p.nombre_comercial,
        pa.nombre AS pais, pa.codigo AS pais_codigo,
        m.codigo AS moneda, p.incoterm_default,
        p.es_extranjero, p.email, p.telefono,
        p.contacto_nombre, p.status,
        p.created_at, p.updated_at,
        (SELECT COUNT(*) FROM ordenes_compra oc WHERE oc.proveedor_id = p.id) AS total_ocs
    FROM proveedores p
    LEFT JOIN paises pa ON p.pais_id = pa.id
    LEFT JOIN monedas m ON p.moneda_id = m.id
    WHERE p.empresa_id = p_empresa_id
      AND (p_status IS NULL OR p.status = p_status)
      AND (p_search IS NULL OR p_search = ''
           OR p.razon_social LIKE CONCAT('%', p_search, '%')
           OR p.nombre_comercial LIKE CONCAT('%', p_search, '%')
           OR p.ruc LIKE CONCAT('%', p_search, '%'))
    ORDER BY p.razon_social
    LIMIT v_offset, v_limit;
END //

CREATE PROCEDURE sp_proveedor_contar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_status VARCHAR(10)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM proveedores p
    WHERE p.empresa_id = p_empresa_id
      AND (p_status IS NULL OR p.status = p_status)
      AND (p_search IS NULL OR p_search = ''
           OR p.razon_social LIKE CONCAT('%', p_search, '%')
           OR p.nombre_comercial LIKE CONCAT('%', p_search, '%')
           OR p.ruc LIKE CONCAT('%', p_search, '%'));
END //

CREATE PROCEDURE sp_proveedor_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    SELECT
        p.*, pa.nombre AS pais, pa.codigo AS pais_codigo,
        m.codigo AS moneda_codigo, m.simbolo AS moneda_simbolo
    FROM proveedores p
    LEFT JOIN paises pa ON p.pais_id = pa.id
    LEFT JOIN monedas m ON p.moneda_id = m.id
    WHERE p.id = p_id AND p.empresa_id = p_empresa_id;
END //

CREATE PROCEDURE sp_proveedor_crear(
    IN p_empresa_id INT,
    IN p_ruc VARCHAR(20),
    IN p_razon_social VARCHAR(200),
    IN p_nombre_comercial VARCHAR(200),
    IN p_pais_id INT,
    IN p_direccion TEXT,
    IN p_email VARCHAR(100),
    IN p_telefono VARCHAR(30),
    IN p_contacto_nombre VARCHAR(100),
    IN p_moneda_id INT,
    IN p_incoterm_default VARCHAR(10),
    IN p_es_extranjero TINYINT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO proveedores (
        empresa_id, ruc, razon_social, nombre_comercial,
        pais_id, direccion, email, telefono, contacto_nombre,
        moneda_id, incoterm_default, es_extranjero,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_ruc, p_razon_social, p_nombre_comercial,
        p_pais_id, p_direccion, p_email, p_telefono, p_contacto_nombre,
        COALESCE(p_moneda_id, 1), COALESCE(p_incoterm_default, 'FOB'), COALESCE(p_es_extranjero, 1),
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_proveedor_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_ruc VARCHAR(20),
    IN p_razon_social VARCHAR(200),
    IN p_nombre_comercial VARCHAR(200),
    IN p_pais_id INT,
    IN p_direccion TEXT,
    IN p_email VARCHAR(100),
    IN p_telefono VARCHAR(30),
    IN p_contacto_nombre VARCHAR(100),
    IN p_moneda_id INT,
    IN p_incoterm_default VARCHAR(10),
    IN p_es_extranjero TINYINT,
    IN p_status VARCHAR(10),
    IN p_usuario_id INT
)
BEGIN
    UPDATE proveedores SET
        ruc = COALESCE(p_ruc, ruc),
        razon_social = COALESCE(p_razon_social, razon_social),
        nombre_comercial = COALESCE(p_nombre_comercial, nombre_comercial),
        pais_id = COALESCE(p_pais_id, pais_id),
        direccion = COALESCE(p_direccion, direccion),
        email = COALESCE(p_email, email),
        telefono = COALESCE(p_telefono, telefono),
        contacto_nombre = COALESCE(p_contacto_nombre, contacto_nombre),
        moneda_id = COALESCE(p_moneda_id, moneda_id),
        incoterm_default = COALESCE(p_incoterm_default, incoterm_default),
        es_extranjero = COALESCE(p_es_extranjero, es_extranjero),
        status = COALESCE(p_status, status),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_proveedor_eliminar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_ocs INT DEFAULT 0;
    SELECT COUNT(*) INTO v_ocs FROM ordenes_compra WHERE proveedor_id = p_id;
    IF v_ocs > 0 THEN
        UPDATE proveedores SET status = 'inactive' WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'inactivated' AS result, v_ocs AS ordenes_asociadas;
    ELSE
        DELETE FROM proveedores WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'deleted' AS result, 0 AS ordenes_asociadas;
    END IF;
END //

-- ============================================================================
-- PRODUCTOS
-- ============================================================================

CREATE PROCEDURE sp_producto_listar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_categoria_id INT,
    IN p_status VARCHAR(10),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    DECLARE v_limit INT DEFAULT 20;
    SET v_limit = IFNULL(p_per_page, 20);
    SET v_offset = (IFNULL(p_page, 1) - 1) * v_limit;

    SELECT
        pr.id, pr.sku, pr.nombre, pr.descripcion,
        pr.codigo_hs, pr.unidad_medida, pr.peso_kg, pr.volumen_m3,
        pr.color_ui, pr.icono_ui, pr.status,
        cp.nombre AS categoria,
        pa.descripcion AS partida_descripcion,
        pa.tasa_ad_valorem,
        prov.razon_social AS proveedor_default,
        pr.created_at,
        (SELECT COALESCE(SUM(inv.cantidad), 0) FROM inventario inv WHERE inv.producto_id = pr.id) AS stock_total
    FROM productos pr
    LEFT JOIN categorias_producto cp ON pr.categoria_id = cp.id
    LEFT JOIN partidas_arancelarias pa ON pr.partida_id = pa.id
    LEFT JOIN proveedores prov ON pr.proveedor_default_id = prov.id
    WHERE pr.empresa_id = p_empresa_id
      AND (p_status IS NULL OR pr.status = p_status)
      AND (p_categoria_id IS NULL OR pr.categoria_id = p_categoria_id)
      AND (p_search IS NULL OR p_search = ''
           OR pr.sku LIKE CONCAT('%', p_search, '%')
           OR pr.nombre LIKE CONCAT('%', p_search, '%')
           OR pr.codigo_hs LIKE CONCAT('%', p_search, '%'))
    ORDER BY pr.nombre
    LIMIT v_offset, v_limit;
END //

CREATE PROCEDURE sp_producto_contar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_categoria_id INT,
    IN p_status VARCHAR(10)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM productos pr
    WHERE pr.empresa_id = p_empresa_id
      AND (p_status IS NULL OR pr.status = p_status)
      AND (p_categoria_id IS NULL OR pr.categoria_id = p_categoria_id)
      AND (p_search IS NULL OR p_search = ''
           OR pr.sku LIKE CONCAT('%', p_search, '%')
           OR pr.nombre LIKE CONCAT('%', p_search, '%')
           OR pr.codigo_hs LIKE CONCAT('%', p_search, '%'));
END //

CREATE PROCEDURE sp_producto_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    SELECT
        pr.*, cp.nombre AS categoria,
        pa.descripcion AS partida_descripcion,
        pa.tasa_ad_valorem, pa.tasa_igv, pa.tasa_ipm, pa.tasa_isc,
        prov.razon_social AS proveedor_default_nombre
    FROM productos pr
    LEFT JOIN categorias_producto cp ON pr.categoria_id = cp.id
    LEFT JOIN partidas_arancelarias pa ON pr.partida_id = pa.id
    LEFT JOIN proveedores prov ON pr.proveedor_default_id = prov.id
    WHERE pr.id = p_id AND pr.empresa_id = p_empresa_id;
END //

CREATE PROCEDURE sp_producto_crear(
    IN p_empresa_id INT,
    IN p_sku VARCHAR(50),
    IN p_nombre VARCHAR(200),
    IN p_descripcion TEXT,
    IN p_codigo_hs VARCHAR(12),
    IN p_categoria_id INT,
    IN p_unidad_medida VARCHAR(20),
    IN p_peso_kg DECIMAL(10,3),
    IN p_volumen_m3 DECIMAL(10,6),
    IN p_proveedor_default_id INT,
    IN p_color_ui VARCHAR(7),
    IN p_icono_ui VARCHAR(50),
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_partida_id INT DEFAULT NULL;

    -- Buscar partida arancelaria si se proporciona hs_code
    IF p_codigo_hs IS NOT NULL AND p_codigo_hs != '' THEN
        SELECT id INTO v_partida_id
        FROM partidas_arancelarias
        WHERE codigo_hs = p_codigo_hs
        LIMIT 1;
    END IF;

    INSERT INTO productos (
        empresa_id, sku, nombre, descripcion, codigo_hs, partida_id,
        categoria_id, unidad_medida, peso_kg, volumen_m3,
        proveedor_default_id, color_ui, icono_ui,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_sku, p_nombre, p_descripcion, p_codigo_hs, v_partida_id,
        p_categoria_id, COALESCE(p_unidad_medida, 'NIU'), p_peso_kg, p_volumen_m3,
        p_proveedor_default_id,
        COALESCE(p_color_ui, '#3B82F6'), COALESCE(p_icono_ui, 'inventory_2'),
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_producto_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_sku VARCHAR(50),
    IN p_nombre VARCHAR(200),
    IN p_descripcion TEXT,
    IN p_codigo_hs VARCHAR(12),
    IN p_categoria_id INT,
    IN p_unidad_medida VARCHAR(20),
    IN p_peso_kg DECIMAL(10,3),
    IN p_volumen_m3 DECIMAL(10,6),
    IN p_proveedor_default_id INT,
    IN p_color_ui VARCHAR(7),
    IN p_icono_ui VARCHAR(50),
    IN p_status VARCHAR(10),
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_partida_id INT DEFAULT NULL;

    IF p_codigo_hs IS NOT NULL AND p_codigo_hs != '' THEN
        SELECT id INTO v_partida_id
        FROM partidas_arancelarias
        WHERE codigo_hs = p_codigo_hs
        LIMIT 1;
    END IF;

    UPDATE productos SET
        sku = COALESCE(p_sku, sku),
        nombre = COALESCE(p_nombre, nombre),
        descripcion = COALESCE(p_descripcion, descripcion),
        codigo_hs = COALESCE(p_codigo_hs, codigo_hs),
        partida_id = COALESCE(v_partida_id, partida_id),
        categoria_id = COALESCE(p_categoria_id, categoria_id),
        unidad_medida = COALESCE(p_unidad_medida, unidad_medida),
        peso_kg = COALESCE(p_peso_kg, peso_kg),
        volumen_m3 = COALESCE(p_volumen_m3, volumen_m3),
        proveedor_default_id = COALESCE(p_proveedor_default_id, proveedor_default_id),
        color_ui = COALESCE(p_color_ui, color_ui),
        icono_ui = COALESCE(p_icono_ui, icono_ui),
        status = COALESCE(p_status, status),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_producto_eliminar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_items INT DEFAULT 0;
    SELECT COUNT(*) INTO v_items FROM orden_compra_items WHERE producto_id = p_id;
    IF v_items > 0 THEN
        UPDATE productos SET status = 'inactive' WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'inactivated' AS result;
    ELSE
        DELETE FROM productos WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'deleted' AS result;
    END IF;
END //

-- ============================================================================
-- ALMACENES
-- ============================================================================

CREATE PROCEDURE sp_almacen_listar(
    IN p_empresa_id INT,
    IN p_status VARCHAR(10)
)
BEGIN
    SELECT
        a.*,
        (SELECT COUNT(DISTINCT inv.producto_id) FROM inventario inv WHERE inv.almacen_id = a.id AND inv.cantidad > 0) AS total_productos,
        (SELECT COALESCE(SUM(inv.cantidad * inv.costo_unitario), 0) FROM inventario inv WHERE inv.almacen_id = a.id AND inv.cantidad > 0) AS valor_total
    FROM almacenes a
    WHERE a.empresa_id = p_empresa_id
      AND (p_status IS NULL OR a.status = p_status)
    ORDER BY a.nombre;
END //

CREATE PROCEDURE sp_almacen_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    SELECT a.*
    FROM almacenes a
    WHERE a.id = p_id AND a.empresa_id = p_empresa_id;
END //

CREATE PROCEDURE sp_almacen_crear(
    IN p_empresa_id INT,
    IN p_codigo VARCHAR(10),
    IN p_nombre VARCHAR(100),
    IN p_responsable VARCHAR(100),
    IN p_direccion TEXT,
    IN p_notas TEXT
)
BEGIN
    INSERT INTO almacenes (empresa_id, codigo, nombre, responsable, direccion, notas)
    VALUES (p_empresa_id, p_codigo, p_nombre, p_responsable, p_direccion, p_notas);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_almacen_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_codigo VARCHAR(10),
    IN p_nombre VARCHAR(100),
    IN p_responsable VARCHAR(100),
    IN p_direccion TEXT,
    IN p_notas TEXT,
    IN p_status VARCHAR(10)
)
BEGIN
    UPDATE almacenes SET
        codigo = COALESCE(p_codigo, codigo),
        nombre = COALESCE(p_nombre, nombre),
        responsable = COALESCE(p_responsable, responsable),
        direccion = COALESCE(p_direccion, direccion),
        notas = COALESCE(p_notas, notas),
        status = COALESCE(p_status, status)
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

-- ============================================================================
-- CATEGORIAS DE PRODUCTO
-- ============================================================================

CREATE PROCEDURE sp_categoria_listar(
    IN p_empresa_id INT
)
BEGIN
    SELECT cp.*,
        (SELECT COUNT(*) FROM productos pr WHERE pr.categoria_id = cp.id AND pr.status = 'active') AS total_productos
    FROM categorias_producto cp
    WHERE cp.empresa_id = p_empresa_id AND cp.status = 'active'
    ORDER BY cp.nombre;
END //

CREATE PROCEDURE sp_categoria_crear(
    IN p_empresa_id INT,
    IN p_nombre VARCHAR(100),
    IN p_descripcion TEXT,
    IN p_color_ui VARCHAR(7),
    IN p_icono_ui VARCHAR(50)
)
BEGIN
    INSERT INTO categorias_producto (empresa_id, nombre, descripcion, color_ui, icono_ui)
    VALUES (p_empresa_id, p_nombre, p_descripcion,
            COALESCE(p_color_ui, '#3B82F6'), COALESCE(p_icono_ui, 'category'));
    SELECT LAST_INSERT_ID() AS id;
END //

-- ============================================================================
-- PAISES y MONEDAS (consulta)
-- ============================================================================

CREATE PROCEDURE sp_pais_listar()
BEGIN
    SELECT id, codigo, nombre, region, tiene_tlc_peru FROM paises ORDER BY nombre;
END //

CREATE PROCEDURE sp_moneda_listar()
BEGIN
    SELECT id, codigo, nombre, simbolo FROM monedas ORDER BY codigo;
END //

CREATE PROCEDURE sp_tipo_cambio_obtener(
    IN p_moneda_codigo VARCHAR(3),
    IN p_fecha DATE
)
BEGIN
    SELECT tc.tc_compra, tc.tc_venta, tc.fecha, tc.fuente
    FROM tipos_cambio tc
    JOIN monedas m ON tc.moneda_id = m.id
    WHERE m.codigo = p_moneda_codigo
      AND tc.fecha <= COALESCE(p_fecha, CURDATE())
    ORDER BY tc.fecha DESC
    LIMIT 1;
END //

CREATE PROCEDURE sp_tipo_cambio_registrar(
    IN p_moneda_codigo VARCHAR(3),
    IN p_fecha DATE,
    IN p_tc_compra DECIMAL(10,4),
    IN p_tc_venta DECIMAL(10,4),
    IN p_fuente VARCHAR(10)
)
BEGIN
    DECLARE v_moneda_id INT;
    SELECT id INTO v_moneda_id FROM monedas WHERE codigo = p_moneda_codigo;

    INSERT INTO tipos_cambio (moneda_id, fecha, tc_compra, tc_venta, fuente)
    VALUES (v_moneda_id, p_fecha, p_tc_compra, p_tc_venta, COALESCE(p_fuente, 'manual'))
    ON DUPLICATE KEY UPDATE
        tc_compra = p_tc_compra,
        tc_venta = p_tc_venta,
        fuente = COALESCE(p_fuente, fuente);
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_partida_arancelaria_buscar(
    IN p_codigo VARCHAR(12)
)
BEGIN
    SELECT * FROM partidas_arancelarias
    WHERE codigo_hs LIKE CONCAT(p_codigo, '%')
    ORDER BY codigo_hs
    LIMIT 20;
END //

DELIMITER ;
