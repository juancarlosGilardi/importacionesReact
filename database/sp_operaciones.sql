-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Operaciones
-- Ordenes de Compra, Items OC, Importaciones, Importacion-OC
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- ORDENES DE COMPRA
-- ============================================================================

CREATE PROCEDURE sp_oc_listar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_estado VARCHAR(30),
    IN p_proveedor_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE,
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    SET v_offset = (COALESCE(p_page, 1) - 1) * COALESCE(p_per_page, 20);

    SELECT
        oc.id, oc.numero_oc, oc.fecha_orden, oc.fecha_llegada_est,
        oc.incoterm, oc.estado,
        oc.total_fob, oc.total_cif, oc.total_costo_importacion,
        p.razon_social AS proveedor, p.nombre_comercial AS proveedor_comercial,
        pa.nombre AS pais_origen, pa.codigo AS pais_codigo,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        oc.tipo_cambio,
        ei.nombre AS estado_nombre, ei.color_ui AS estado_color, ei.icono_ui AS estado_icono,
        (SELECT COUNT(*) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS total_items,
        (SELECT SUM(oci.cantidad) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS total_cantidad,
        oc.created_at, oc.updated_at
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    LEFT JOIN paises pa ON p.pais_id = pa.id
    JOIN monedas m ON oc.moneda_id = m.id
    LEFT JOIN estados_importacion ei ON oc.estado = ei.codigo
    WHERE oc.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR oc.estado = p_estado)
      AND (p_proveedor_id IS NULL OR oc.proveedor_id = p_proveedor_id)
      AND (p_fecha_desde IS NULL OR oc.fecha_orden >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR oc.fecha_orden <= p_fecha_hasta)
      AND (p_search IS NULL OR p_search = ''
           OR oc.numero_oc LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%'))
    ORDER BY ei.orden, oc.fecha_orden DESC
    LIMIT v_offset, COALESCE(p_per_page, 20);
END //

CREATE PROCEDURE sp_oc_contar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_estado VARCHAR(30),
    IN p_proveedor_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE
)
BEGIN
    SELECT COUNT(*) AS total
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    WHERE oc.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR oc.estado = p_estado)
      AND (p_proveedor_id IS NULL OR oc.proveedor_id = p_proveedor_id)
      AND (p_fecha_desde IS NULL OR oc.fecha_orden >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR oc.fecha_orden <= p_fecha_hasta)
      AND (p_search IS NULL OR p_search = ''
           OR oc.numero_oc LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%'));
END //

CREATE PROCEDURE sp_oc_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT
        oc.*,
        p.razon_social AS proveedor, p.nombre_comercial AS proveedor_comercial,
        p.ruc AS proveedor_ruc, p.email AS proveedor_email,
        pa.nombre AS pais_origen, pa.codigo AS pais_codigo, pa.tiene_tlc_peru,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        ei.nombre AS estado_nombre, ei.color_ui AS estado_color, ei.icono_ui AS estado_icono
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    LEFT JOIN paises pa ON p.pais_id = pa.id
    JOIN monedas m ON oc.moneda_id = m.id
    LEFT JOIN estados_importacion ei ON oc.estado = ei.codigo
    WHERE oc.id = p_id AND oc.empresa_id = p_empresa_id;

    -- Items
    SELECT
        oci.*,
        pr.sku, pr.nombre AS producto_nombre, pr.codigo_hs,
        pr.color_ui, pr.icono_ui
    FROM orden_compra_items oci
    JOIN productos pr ON oci.producto_id = pr.id
    WHERE oci.oc_id = p_id
    ORDER BY oci.id;
END //

CREATE PROCEDURE sp_oc_crear(
    IN p_empresa_id INT,
    IN p_numero_oc VARCHAR(50),
    IN p_proveedor_id INT,
    IN p_fecha_orden DATE,
    IN p_fecha_llegada_est DATE,
    IN p_incoterm VARCHAR(10),
    IN p_moneda_id INT,
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_puerto_embarque VARCHAR(100),
    IN p_puerto_destino VARCHAR(100),
    IN p_agente_aduanero VARCHAR(150),
    IN p_agente_carga VARCHAR(150),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO ordenes_compra (
        empresa_id, numero_oc, proveedor_id, fecha_orden, fecha_llegada_est,
        incoterm, moneda_id, tipo_cambio, puerto_embarque, puerto_destino,
        agente_aduanero, agente_carga, notas, estado,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_numero_oc, p_proveedor_id,
        COALESCE(p_fecha_orden, CURDATE()), p_fecha_llegada_est,
        COALESCE(p_incoterm, 'FOB'), COALESCE(p_moneda_id, 1),
        COALESCE(p_tipo_cambio, 1.0000),
        p_puerto_embarque, p_puerto_destino,
        p_agente_aduanero, p_agente_carga, p_notas, 'borrador',
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_oc_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_numero_oc VARCHAR(50),
    IN p_proveedor_id INT,
    IN p_fecha_orden DATE,
    IN p_fecha_llegada_est DATE,
    IN p_incoterm VARCHAR(10),
    IN p_moneda_id INT,
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_puerto_embarque VARCHAR(100),
    IN p_puerto_destino VARCHAR(100),
    IN p_agente_aduanero VARCHAR(150),
    IN p_agente_carga VARCHAR(150),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    UPDATE ordenes_compra SET
        numero_oc = COALESCE(p_numero_oc, numero_oc),
        proveedor_id = COALESCE(p_proveedor_id, proveedor_id),
        fecha_orden = COALESCE(p_fecha_orden, fecha_orden),
        fecha_llegada_est = COALESCE(p_fecha_llegada_est, fecha_llegada_est),
        incoterm = COALESCE(p_incoterm, incoterm),
        moneda_id = COALESCE(p_moneda_id, moneda_id),
        tipo_cambio = COALESCE(p_tipo_cambio, tipo_cambio),
        puerto_embarque = COALESCE(p_puerto_embarque, puerto_embarque),
        puerto_destino = COALESCE(p_puerto_destino, puerto_destino),
        agente_aduanero = COALESCE(p_agente_aduanero, agente_aduanero),
        agente_carga = COALESCE(p_agente_carga, agente_carga),
        notas = COALESCE(p_notas, notas),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_oc_cambiar_estado(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_nuevo_estado VARCHAR(30),
    IN p_usuario_id INT
)
BEGIN
    UPDATE ordenes_compra
    SET estado = p_nuevo_estado, updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_oc_eliminar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);
    SELECT estado INTO v_estado FROM ordenes_compra WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado = 'borrador' THEN
        DELETE FROM ordenes_compra WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'deleted' AS result;
    ELSE
        SELECT 'error' AS result, 'Solo se pueden eliminar OC en estado borrador' AS message;
    END IF;
END //

-- ============================================================================
-- ITEMS DE ORDEN DE COMPRA
-- ============================================================================

CREATE PROCEDURE sp_oc_item_agregar(
    IN p_oc_id INT,
    IN p_producto_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_precio_unitario DECIMAL(15,4),
    IN p_unidad_medida VARCHAR(20),
    IN p_peso_kg DECIMAL(10,3),
    IN p_volumen_m3 DECIMAL(10,6),
    IN p_usuario_id INT
)
BEGIN
    -- Si no se pasa peso/volumen, tomar del producto
    DECLARE v_peso DECIMAL(10,3);
    DECLARE v_volumen DECIMAL(10,6);
    DECLARE v_unidad VARCHAR(20);

    SELECT
        COALESCE(p_peso_kg, peso_kg * p_cantidad),
        COALESCE(p_volumen_m3, volumen_m3 * p_cantidad),
        COALESCE(p_unidad_medida, unidad_medida)
    INTO v_peso, v_volumen, v_unidad
    FROM productos WHERE id = p_producto_id;

    INSERT INTO orden_compra_items (
        oc_id, producto_id, cantidad, precio_unitario,
        unidad_medida, peso_kg, volumen_m3,
        created_by, updated_by
    ) VALUES (
        p_oc_id, p_producto_id, p_cantidad, p_precio_unitario,
        COALESCE(v_unidad, 'NIU'), v_peso, v_volumen,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_oc_item_actualizar(
    IN p_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_precio_unitario DECIMAL(15,4),
    IN p_peso_kg DECIMAL(10,3),
    IN p_volumen_m3 DECIMAL(10,6),
    IN p_usuario_id INT
)
BEGIN
    UPDATE orden_compra_items SET
        cantidad = COALESCE(p_cantidad, cantidad),
        precio_unitario = COALESCE(p_precio_unitario, precio_unitario),
        peso_kg = COALESCE(p_peso_kg, peso_kg),
        volumen_m3 = COALESCE(p_volumen_m3, volumen_m3),
        updated_by = p_usuario_id
    WHERE id = p_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_oc_item_eliminar(
    IN p_id INT
)
BEGIN
    DELETE FROM orden_compra_items WHERE id = p_id;
    SELECT ROW_COUNT() AS affected;
END //

-- ============================================================================
-- IMPORTACIONES
-- ============================================================================

CREATE PROCEDURE sp_importacion_listar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_estado VARCHAR(30),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    SET v_offset = (COALESCE(p_page, 1) - 1) * COALESCE(p_per_page, 20);

    SELECT
        i.id, i.numero_importacion, i.descripcion, i.fecha_creacion,
        i.bl_number, i.container_number, i.via_transporte,
        i.fecha_embarque, i.fecha_arribo_estimada, i.fecha_arribo_real,
        i.estado,
        i.total_fob_importacion, i.total_gastos_importacion, i.total_costo_importacion,
        i.agente_aduanero,
        (SELECT COUNT(*) FROM importacion_ocs io WHERE io.importacion_id = i.id) AS total_ocs,
        (SELECT GROUP_CONCAT(oc.numero_oc SEPARATOR ', ')
         FROM importacion_ocs io JOIN ordenes_compra oc ON io.oc_id = oc.id
         WHERE io.importacion_id = i.id) AS ocs_asociadas,
        i.created_at
    FROM importaciones i
    WHERE i.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR i.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR i.numero_importacion LIKE CONCAT('%', p_search, '%')
           OR i.descripcion LIKE CONCAT('%', p_search, '%')
           OR i.bl_number LIKE CONCAT('%', p_search, '%'))
    ORDER BY i.fecha_creacion DESC
    LIMIT v_offset, COALESCE(p_per_page, 20);
END //

CREATE PROCEDURE sp_importacion_contar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_estado VARCHAR(30)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM importaciones i
    WHERE i.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR i.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR i.numero_importacion LIKE CONCAT('%', p_search, '%')
           OR i.descripcion LIKE CONCAT('%', p_search, '%')
           OR i.bl_number LIKE CONCAT('%', p_search, '%'));
END //

CREATE PROCEDURE sp_importacion_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT i.*
    FROM importaciones i
    WHERE i.id = p_id AND i.empresa_id = p_empresa_id;

    -- OCs asociadas
    SELECT
        io.id AS relacion_id, io.porcentaje_participacion,
        oc.id AS oc_id, oc.numero_oc, oc.fecha_orden, oc.incoterm,
        oc.total_fob, oc.estado,
        p.razon_social AS proveedor,
        m.simbolo AS moneda_simbolo
    FROM importacion_ocs io
    JOIN ordenes_compra oc ON io.oc_id = oc.id
    JOIN proveedores p ON oc.proveedor_id = p.id
    JOIN monedas m ON oc.moneda_id = m.id
    WHERE io.importacion_id = p_id
    ORDER BY oc.numero_oc;

    -- DUAs
    SELECT d.id, d.numero_dua, d.fecha_registro, d.estado,
           d.valor_cif_usd, d.total_tributos
    FROM dua_documentos d
    WHERE d.importacion_id = p_id;

    -- Gastos
    SELECT g.id, g.tipo_gasto_codigo, tg.nombre AS tipo_gasto_nombre,
           g.descripcion, g.monto, g.monto_pen,
           m.simbolo AS moneda_simbolo, g.estado, g.prorrateado
    FROM gastos_importacion g
    JOIN tipos_gasto tg ON g.tipo_gasto_codigo = tg.codigo
    JOIN monedas m ON g.moneda_id = m.id
    WHERE g.importacion_id = p_id
    ORDER BY tg.orden;
END //

CREATE PROCEDURE sp_importacion_crear(
    IN p_empresa_id INT,
    IN p_numero_importacion VARCHAR(20),
    IN p_descripcion VARCHAR(200),
    IN p_via_transporte VARCHAR(20),
    IN p_bl_number VARCHAR(100),
    IN p_container_number VARCHAR(50),
    IN p_nombre_nave VARCHAR(100),
    IN p_numero_viaje VARCHAR(50),
    IN p_fecha_embarque DATE,
    IN p_fecha_arribo_estimada DATE,
    IN p_agente_aduanero VARCHAR(150),
    IN p_agente_carga VARCHAR(150),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO importaciones (
        empresa_id, numero_importacion, descripcion, via_transporte,
        bl_number, container_number, nombre_nave, numero_viaje,
        fecha_embarque, fecha_arribo_estimada,
        agente_aduanero, agente_carga, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_numero_importacion, p_descripcion,
        COALESCE(p_via_transporte, 'maritimo'),
        p_bl_number, p_container_number, p_nombre_nave, p_numero_viaje,
        p_fecha_embarque, p_fecha_arribo_estimada,
        p_agente_aduanero, p_agente_carga, p_notas,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_importacion_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_descripcion VARCHAR(200),
    IN p_via_transporte VARCHAR(20),
    IN p_bl_number VARCHAR(100),
    IN p_container_number VARCHAR(50),
    IN p_nombre_nave VARCHAR(100),
    IN p_numero_viaje VARCHAR(50),
    IN p_fecha_embarque DATE,
    IN p_fecha_arribo_estimada DATE,
    IN p_fecha_arribo_real DATE,
    IN p_fecha_desaduanaje DATE,
    IN p_agente_aduanero VARCHAR(150),
    IN p_agente_carga VARCHAR(150),
    IN p_estado VARCHAR(30),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    UPDATE importaciones SET
        descripcion = COALESCE(p_descripcion, descripcion),
        via_transporte = COALESCE(p_via_transporte, via_transporte),
        bl_number = COALESCE(p_bl_number, bl_number),
        container_number = COALESCE(p_container_number, container_number),
        nombre_nave = COALESCE(p_nombre_nave, nombre_nave),
        numero_viaje = COALESCE(p_numero_viaje, numero_viaje),
        fecha_embarque = COALESCE(p_fecha_embarque, fecha_embarque),
        fecha_arribo_estimada = COALESCE(p_fecha_arribo_estimada, fecha_arribo_estimada),
        fecha_arribo_real = COALESCE(p_fecha_arribo_real, fecha_arribo_real),
        fecha_desaduanaje = COALESCE(p_fecha_desaduanaje, fecha_desaduanaje),
        agente_aduanero = COALESCE(p_agente_aduanero, agente_aduanero),
        agente_carga = COALESCE(p_agente_carga, agente_carga),
        estado = COALESCE(p_estado, estado),
        notas = COALESCE(p_notas, notas),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

-- Asociar OC a Importacion
CREATE PROCEDURE sp_importacion_asociar_oc(
    IN p_importacion_id INT,
    IN p_oc_id INT
)
BEGIN
    DECLARE v_peso DECIMAL(10,3);
    DECLARE v_volumen DECIMAL(10,6);

    SELECT
        COALESCE(SUM(oci.peso_kg), 0),
        COALESCE(SUM(oci.volumen_m3), 0)
    INTO v_peso, v_volumen
    FROM orden_compra_items oci
    WHERE oci.oc_id = p_oc_id;

    INSERT INTO importacion_ocs (importacion_id, oc_id, peso_total, volumen_total)
    VALUES (p_importacion_id, p_oc_id, v_peso, v_volumen)
    ON DUPLICATE KEY UPDATE peso_total = v_peso, volumen_total = v_volumen;

    -- Recalcular FOB total de importacion
    UPDATE importaciones i SET
        total_fob_importacion = (
            SELECT COALESCE(SUM(oc.total_fob), 0)
            FROM importacion_ocs io
            JOIN ordenes_compra oc ON io.oc_id = oc.id
            WHERE io.importacion_id = p_importacion_id
        )
    WHERE i.id = p_importacion_id;

    -- Recalcular porcentajes de participacion
    CALL sp_importacion_recalcular_participacion(p_importacion_id);

    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_importacion_desasociar_oc(
    IN p_importacion_id INT,
    IN p_oc_id INT
)
BEGIN
    DELETE FROM importacion_ocs WHERE importacion_id = p_importacion_id AND oc_id = p_oc_id;

    UPDATE importaciones i SET
        total_fob_importacion = (
            SELECT COALESCE(SUM(oc.total_fob), 0)
            FROM importacion_ocs io
            JOIN ordenes_compra oc ON io.oc_id = oc.id
            WHERE io.importacion_id = p_importacion_id
        )
    WHERE i.id = p_importacion_id;

    CALL sp_importacion_recalcular_participacion(p_importacion_id);
    SELECT ROW_COUNT() AS affected;
END //

-- Recalcular % de participacion de cada OC en la importacion
CREATE PROCEDURE sp_importacion_recalcular_participacion(
    IN p_importacion_id INT
)
BEGIN
    DECLARE v_total_fob DECIMAL(15,2);

    SELECT COALESCE(SUM(oc.total_fob), 0) INTO v_total_fob
    FROM importacion_ocs io
    JOIN ordenes_compra oc ON io.oc_id = oc.id
    WHERE io.importacion_id = p_importacion_id;

    IF v_total_fob > 0 THEN
        UPDATE importacion_ocs io
        JOIN ordenes_compra oc ON io.oc_id = oc.id
        SET io.porcentaje_participacion = ROUND((oc.total_fob / v_total_fob) * 100, 2)
        WHERE io.importacion_id = p_importacion_id;
    END IF;
END //

DELIMITER ;
