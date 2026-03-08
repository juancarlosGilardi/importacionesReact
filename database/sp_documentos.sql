-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Documentos
-- DUA, Documentos de Transporte, Facturas de Proveedor
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- DUA (Declaracion Aduanera de Mercancias)
-- ============================================================================

CREATE PROCEDURE sp_dua_listar(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_estado VARCHAR(20),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    SET v_offset = (COALESCE(p_page, 1) - 1) * COALESCE(p_per_page, 20);

    SELECT
        d.id, d.numero_dua, d.fecha_registro, d.fecha_levante,
        d.agencia_aduanas, d.numero_operacion,
        d.valor_fob_usd, d.flete_usd, d.seguro_usd, d.valor_cif_usd,
        d.total_tributos, d.total_gastos_aduana,
        d.estado, d.tipo_cambio,
        i.numero_importacion, i.descripcion AS importacion_desc,
        (SELECT COUNT(*) FROM dua_items di WHERE di.dua_id = d.id) AS total_series
    FROM dua_documentos d
    JOIN importaciones i ON d.importacion_id = i.id
    WHERE d.empresa_id = p_empresa_id
      AND (p_importacion_id IS NULL OR d.importacion_id = p_importacion_id)
      AND (p_estado IS NULL OR d.estado = p_estado)
    ORDER BY d.fecha_registro DESC
    LIMIT v_offset, COALESCE(p_per_page, 20);
END //

CREATE PROCEDURE sp_dua_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera DUA
    SELECT d.*, i.numero_importacion, i.descripcion AS importacion_desc
    FROM dua_documentos d
    JOIN importaciones i ON d.importacion_id = i.id
    WHERE d.id = p_id AND d.empresa_id = p_empresa_id;

    -- Series/Items de la DUA
    SELECT
        di.*,
        pr.sku, pr.nombre AS producto_nombre
    FROM dua_items di
    LEFT JOIN productos pr ON di.producto_id = pr.id
    WHERE di.dua_id = p_id
    ORDER BY di.numero_serie;
END //

CREATE PROCEDURE sp_dua_crear(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_numero_dua VARCHAR(50),
    IN p_fecha_registro DATE,
    IN p_fecha_levante DATE,
    IN p_agencia_aduanas VARCHAR(150),
    IN p_ruc_agente VARCHAR(11),
    IN p_numero_operacion VARCHAR(50),
    IN p_valor_fob_usd DECIMAL(15,2),
    IN p_flete_usd DECIMAL(15,2),
    IN p_seguro_usd DECIMAL(15,2),
    IN p_tasa_ad_valorem DECIMAL(5,2),
    IN p_tasa_igv DECIMAL(5,2),
    IN p_tasa_ipm DECIMAL(5,2),
    IN p_monto_isc DECIMAL(15,2),
    IN p_monto_antidumping DECIMAL(15,2),
    IN p_tasa_percepcion DECIMAL(5,2),
    IN p_gastos_despacho DECIMAL(15,2),
    IN p_honorarios_agente DECIMAL(15,2),
    IN p_almacenaje DECIMAL(15,2),
    IN p_otros_gastos DECIMAL(15,2),
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_archivo_pdf VARCHAR(500),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_cif DECIMAL(15,2);
    DECLARE v_ad_valorem DECIMAL(15,2);
    DECLARE v_base_igv DECIMAL(15,2);
    DECLARE v_igv DECIMAL(15,2);
    DECLARE v_ipm DECIMAL(15,2);
    DECLARE v_percepcion DECIMAL(15,2);
    DECLARE v_total_tributos DECIMAL(15,2);
    DECLARE v_total_gastos DECIMAL(15,2);

    -- Calcular CIF
    SET v_cif = COALESCE(p_valor_fob_usd, 0) + COALESCE(p_flete_usd, 0) + COALESCE(p_seguro_usd, 0);

    -- Calcular tributos
    SET v_ad_valorem = ROUND(v_cif * COALESCE(p_tasa_ad_valorem, 0) / 100, 2);
    SET v_base_igv = v_cif + v_ad_valorem + COALESCE(p_monto_isc, 0);
    SET v_igv = ROUND(v_base_igv * COALESCE(p_tasa_igv, 18) / 100, 2);
    SET v_ipm = ROUND(v_base_igv * COALESCE(p_tasa_ipm, 0) / 100, 2);

    -- Percepcion sobre CIF + todos los tributos
    SET v_percepcion = ROUND((v_cif + v_ad_valorem + COALESCE(p_monto_isc, 0) + v_igv + v_ipm)
                             * COALESCE(p_tasa_percepcion, 3.5) / 100, 2);

    SET v_total_tributos = v_ad_valorem + v_igv + v_ipm + COALESCE(p_monto_isc, 0)
                           + COALESCE(p_monto_antidumping, 0) + v_percepcion;

    SET v_total_gastos = COALESCE(p_gastos_despacho, 0) + COALESCE(p_honorarios_agente, 0)
                         + COALESCE(p_almacenaje, 0) + COALESCE(p_otros_gastos, 0);

    INSERT INTO dua_documentos (
        empresa_id, importacion_id, numero_dua, fecha_registro, fecha_levante,
        agencia_aduanas, ruc_agente, numero_operacion,
        valor_fob_usd, flete_usd, seguro_usd, valor_cif_usd,
        tasa_ad_valorem, monto_ad_valorem,
        tasa_igv, monto_igv, tasa_ipm, monto_ipm,
        monto_isc, monto_antidumping,
        monto_percepcion, tasa_percepcion,
        gastos_despacho, honorarios_agente, almacenaje, otros_gastos_aduana,
        total_tributos, total_gastos_aduana,
        tipo_cambio, archivo_pdf, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_importacion_id, p_numero_dua, p_fecha_registro, p_fecha_levante,
        p_agencia_aduanas, p_ruc_agente, p_numero_operacion,
        p_valor_fob_usd, p_flete_usd, p_seguro_usd, v_cif,
        COALESCE(p_tasa_ad_valorem, 0), v_ad_valorem,
        COALESCE(p_tasa_igv, 18), v_igv, COALESCE(p_tasa_ipm, 0), v_ipm,
        COALESCE(p_monto_isc, 0), COALESCE(p_monto_antidumping, 0),
        v_percepcion, COALESCE(p_tasa_percepcion, 3.5),
        COALESCE(p_gastos_despacho, 0), COALESCE(p_honorarios_agente, 0),
        COALESCE(p_almacenaje, 0), COALESCE(p_otros_gastos, 0),
        v_total_tributos, v_total_gastos,
        COALESCE(p_tipo_cambio, 1.0000), p_archivo_pdf, p_notas,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id, v_cif AS cif_calculado,
           v_ad_valorem AS ad_valorem, v_igv AS igv, v_ipm AS ipm,
           v_percepcion AS percepcion, v_total_tributos AS total_tributos;
END //

CREATE PROCEDURE sp_dua_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_fecha_levante DATE,
    IN p_valor_fob_usd DECIMAL(15,2),
    IN p_flete_usd DECIMAL(15,2),
    IN p_seguro_usd DECIMAL(15,2),
    IN p_tasa_ad_valorem DECIMAL(5,2),
    IN p_tasa_igv DECIMAL(5,2),
    IN p_tasa_ipm DECIMAL(5,2),
    IN p_monto_isc DECIMAL(15,2),
    IN p_monto_antidumping DECIMAL(15,2),
    IN p_tasa_percepcion DECIMAL(5,2),
    IN p_gastos_despacho DECIMAL(15,2),
    IN p_honorarios_agente DECIMAL(15,2),
    IN p_almacenaje DECIMAL(15,2),
    IN p_otros_gastos DECIMAL(15,2),
    IN p_estado VARCHAR(20),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_cif DECIMAL(15,2);
    DECLARE v_ad_valorem DECIMAL(15,2);
    DECLARE v_base_igv DECIMAL(15,2);
    DECLARE v_igv DECIMAL(15,2);
    DECLARE v_ipm DECIMAL(15,2);
    DECLARE v_percepcion DECIMAL(15,2);

    -- Recalcular si cambian valores
    SET v_cif = COALESCE(p_valor_fob_usd, 0) + COALESCE(p_flete_usd, 0) + COALESCE(p_seguro_usd, 0);
    SET v_ad_valorem = ROUND(v_cif * COALESCE(p_tasa_ad_valorem, 0) / 100, 2);
    SET v_base_igv = v_cif + v_ad_valorem + COALESCE(p_monto_isc, 0);
    SET v_igv = ROUND(v_base_igv * COALESCE(p_tasa_igv, 18) / 100, 2);
    SET v_ipm = ROUND(v_base_igv * COALESCE(p_tasa_ipm, 0) / 100, 2);
    SET v_percepcion = ROUND((v_cif + v_ad_valorem + COALESCE(p_monto_isc, 0) + v_igv + v_ipm)
                             * COALESCE(p_tasa_percepcion, 3.5) / 100, 2);

    UPDATE dua_documentos SET
        fecha_levante = COALESCE(p_fecha_levante, fecha_levante),
        valor_fob_usd = COALESCE(p_valor_fob_usd, valor_fob_usd),
        flete_usd = COALESCE(p_flete_usd, flete_usd),
        seguro_usd = COALESCE(p_seguro_usd, seguro_usd),
        valor_cif_usd = v_cif,
        tasa_ad_valorem = COALESCE(p_tasa_ad_valorem, tasa_ad_valorem),
        monto_ad_valorem = v_ad_valorem,
        tasa_igv = COALESCE(p_tasa_igv, tasa_igv),
        monto_igv = v_igv,
        tasa_ipm = COALESCE(p_tasa_ipm, tasa_ipm),
        monto_ipm = v_ipm,
        monto_isc = COALESCE(p_monto_isc, monto_isc),
        monto_antidumping = COALESCE(p_monto_antidumping, monto_antidumping),
        monto_percepcion = v_percepcion,
        tasa_percepcion = COALESCE(p_tasa_percepcion, tasa_percepcion),
        gastos_despacho = COALESCE(p_gastos_despacho, gastos_despacho),
        honorarios_agente = COALESCE(p_honorarios_agente, honorarios_agente),
        almacenaje = COALESCE(p_almacenaje, almacenaje),
        otros_gastos_aduana = COALESCE(p_otros_gastos, otros_gastos_aduana),
        total_tributos = v_ad_valorem + v_igv + v_ipm + COALESCE(p_monto_isc, 0)
                         + COALESCE(p_monto_antidumping, 0) + v_percepcion,
        total_gastos_aduana = COALESCE(p_gastos_despacho, 0) + COALESCE(p_honorarios_agente, 0)
                              + COALESCE(p_almacenaje, 0) + COALESCE(p_otros_gastos, 0),
        estado = COALESCE(p_estado, estado),
        notas = COALESCE(p_notas, notas),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

-- Agregar serie/item a DUA
CREATE PROCEDURE sp_dua_item_agregar(
    IN p_dua_id INT,
    IN p_numero_serie INT,
    IN p_producto_id INT,
    IN p_codigo_hs VARCHAR(12),
    IN p_descripcion VARCHAR(500),
    IN p_cantidad DECIMAL(10,2),
    IN p_unidad_medida VARCHAR(10),
    IN p_valor_fob_usd DECIMAL(15,2),
    IN p_peso_kg DECIMAL(10,3),
    IN p_tasa_ad_valorem DECIMAL(5,2)
)
BEGIN
    DECLARE v_ad_valorem DECIMAL(15,2);
    DECLARE v_igv DECIMAL(15,2);
    DECLARE v_ipm DECIMAL(15,2);

    SET v_ad_valorem = ROUND(p_valor_fob_usd * COALESCE(p_tasa_ad_valorem, 0) / 100, 2);
    SET v_igv = ROUND((p_valor_fob_usd + v_ad_valorem) * 0.18, 2);
    SET v_ipm = 0;

    INSERT INTO dua_items (
        dua_id, numero_serie, producto_id, codigo_hs, descripcion,
        cantidad, unidad_medida, valor_fob_usd, peso_kg,
        tasa_ad_valorem, monto_ad_valorem, monto_igv, monto_ipm
    ) VALUES (
        p_dua_id, p_numero_serie, p_producto_id, p_codigo_hs, p_descripcion,
        p_cantidad, p_unidad_medida, p_valor_fob_usd, p_peso_kg,
        COALESCE(p_tasa_ad_valorem, 0), v_ad_valorem, v_igv, v_ipm
    );
    SELECT LAST_INSERT_ID() AS id;
END //

-- ============================================================================
-- DOCUMENTOS DE TRANSPORTE (BL / AWB)
-- ============================================================================

CREATE PROCEDURE sp_doc_transporte_listar(
    IN p_empresa_id INT,
    IN p_importacion_id INT
)
BEGIN
    SELECT
        dt.*, i.numero_importacion
    FROM documentos_transporte dt
    JOIN importaciones i ON dt.importacion_id = i.id
    WHERE dt.empresa_id = p_empresa_id
      AND (p_importacion_id IS NULL OR dt.importacion_id = p_importacion_id)
    ORDER BY dt.created_at DESC;
END //

CREATE PROCEDURE sp_doc_transporte_crear(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_tipo_documento VARCHAR(20),
    IN p_numero_documento VARCHAR(100),
    IN p_transportista VARCHAR(150),
    IN p_nombre_nave VARCHAR(100),
    IN p_numero_viaje VARCHAR(50),
    IN p_fecha_etd DATE,
    IN p_fecha_eta DATE,
    IN p_total_bultos INT,
    IN p_peso_bruto_kg DECIMAL(10,2),
    IN p_volumen_m3 DECIMAL(10,3),
    IN p_archivo_path VARCHAR(500),
    IN p_tracking_url VARCHAR(500),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO documentos_transporte (
        empresa_id, importacion_id, tipo_documento, numero_documento,
        transportista, nombre_nave, numero_viaje,
        fecha_etd, fecha_eta, total_bultos, peso_bruto_kg, volumen_m3,
        archivo_path, tracking_url, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_importacion_id, p_tipo_documento, p_numero_documento,
        p_transportista, p_nombre_nave, p_numero_viaje,
        p_fecha_etd, p_fecha_eta, p_total_bultos, p_peso_bruto_kg, p_volumen_m3,
        p_archivo_path, p_tracking_url, p_notas,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_doc_transporte_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_numero_documento VARCHAR(100),
    IN p_transportista VARCHAR(150),
    IN p_nombre_nave VARCHAR(100),
    IN p_numero_viaje VARCHAR(50),
    IN p_fecha_etd DATE,
    IN p_fecha_eta DATE,
    IN p_fecha_arribo_real DATE,
    IN p_total_bultos INT,
    IN p_peso_bruto_kg DECIMAL(10,2),
    IN p_volumen_m3 DECIMAL(10,3),
    IN p_tracking_url VARCHAR(500),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    UPDATE documentos_transporte SET
        numero_documento = COALESCE(p_numero_documento, numero_documento),
        transportista = COALESCE(p_transportista, transportista),
        nombre_nave = COALESCE(p_nombre_nave, nombre_nave),
        numero_viaje = COALESCE(p_numero_viaje, numero_viaje),
        fecha_etd = COALESCE(p_fecha_etd, fecha_etd),
        fecha_eta = COALESCE(p_fecha_eta, fecha_eta),
        fecha_arribo_real = COALESCE(p_fecha_arribo_real, fecha_arribo_real),
        total_bultos = COALESCE(p_total_bultos, total_bultos),
        peso_bruto_kg = COALESCE(p_peso_bruto_kg, peso_bruto_kg),
        volumen_m3 = COALESCE(p_volumen_m3, volumen_m3),
        tracking_url = COALESCE(p_tracking_url, tracking_url),
        notas = COALESCE(p_notas, notas),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

-- ============================================================================
-- FACTURAS DE PROVEEDOR
-- ============================================================================

CREATE PROCEDURE sp_factura_listar(
    IN p_empresa_id INT,
    IN p_oc_id INT,
    IN p_proveedor_id INT,
    IN p_estado VARCHAR(20),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    SET v_offset = (COALESCE(p_page, 1) - 1) * COALESCE(p_per_page, 20);

    SELECT
        f.id, f.numero_factura, f.fecha_factura,
        f.subtotal, f.impuesto, f.total, f.estado,
        p.razon_social AS proveedor,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        f.tipo_cambio,
        oc.numero_oc,
        (SELECT COUNT(*) FROM factura_items fi WHERE fi.factura_id = f.id) AS total_items
    FROM facturas_proveedor f
    JOIN proveedores p ON f.proveedor_id = p.id
    JOIN monedas m ON f.moneda_id = m.id
    LEFT JOIN ordenes_compra oc ON f.oc_id = oc.id
    WHERE f.empresa_id = p_empresa_id
      AND (p_oc_id IS NULL OR f.oc_id = p_oc_id)
      AND (p_proveedor_id IS NULL OR f.proveedor_id = p_proveedor_id)
      AND (p_estado IS NULL OR f.estado = p_estado)
    ORDER BY f.fecha_factura DESC
    LIMIT v_offset, COALESCE(p_per_page, 20);
END //

CREATE PROCEDURE sp_factura_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    SELECT
        f.*, p.razon_social AS proveedor, p.ruc AS proveedor_ruc,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        oc.numero_oc
    FROM facturas_proveedor f
    JOIN proveedores p ON f.proveedor_id = p.id
    JOIN monedas m ON f.moneda_id = m.id
    LEFT JOIN ordenes_compra oc ON f.oc_id = oc.id
    WHERE f.id = p_id AND f.empresa_id = p_empresa_id;

    -- Items
    SELECT fi.*, pr.sku, pr.nombre AS producto_nombre
    FROM factura_items fi
    JOIN productos pr ON fi.producto_id = pr.id
    WHERE fi.factura_id = p_id
    ORDER BY fi.id;
END //

CREATE PROCEDURE sp_factura_crear(
    IN p_empresa_id INT,
    IN p_numero_factura VARCHAR(100),
    IN p_oc_id INT,
    IN p_proveedor_id INT,
    IN p_fecha_factura DATE,
    IN p_moneda_id INT,
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_subtotal DECIMAL(15,2),
    IN p_impuesto DECIMAL(15,2),
    IN p_total DECIMAL(15,2),
    IN p_xml_file_path VARCHAR(500),
    IN p_xml_hash VARCHAR(64),
    IN p_archivo_pdf VARCHAR(500),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO facturas_proveedor (
        empresa_id, numero_factura, oc_id, proveedor_id,
        fecha_factura, moneda_id, tipo_cambio,
        subtotal, impuesto, total,
        xml_file_path, xml_hash, archivo_pdf, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_numero_factura, p_oc_id, p_proveedor_id,
        p_fecha_factura, p_moneda_id, COALESCE(p_tipo_cambio, 1.0000),
        p_subtotal, COALESCE(p_impuesto, 0), p_total,
        p_xml_file_path, p_xml_hash, p_archivo_pdf, p_notas,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_factura_item_agregar(
    IN p_factura_id INT,
    IN p_producto_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_precio_unitario DECIMAL(15,4),
    IN p_precio_total DECIMAL(15,2)
)
BEGIN
    INSERT INTO factura_items (factura_id, producto_id, cantidad, precio_unitario, precio_total)
    VALUES (p_factura_id, p_producto_id, p_cantidad, p_precio_unitario,
            COALESCE(p_precio_total, p_cantidad * p_precio_unitario));
    SELECT LAST_INSERT_ID() AS id;
END //

DELIMITER ;
