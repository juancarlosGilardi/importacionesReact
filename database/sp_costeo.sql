-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Costeo
-- Gastos de Importacion, Prorrateo, Liquidacion Final
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- GASTOS DE IMPORTACION
-- ============================================================================

CREATE PROCEDURE sp_gasto_listar(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_oc_id INT,
    IN p_tipo_gasto VARCHAR(50),
    IN p_estado VARCHAR(20)
)
BEGIN
    SELECT
        g.id, g.tipo_gasto_codigo, tg.nombre AS tipo_gasto_nombre,
        tg.color_ui, tg.icono_ui,
        g.descripcion, g.proveedor_nombre, g.proveedor_ruc,
        g.monto, g.monto_pen, g.tipo_cambio,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        g.numero_comprobante, g.fecha_gasto,
        g.prorrateado, g.estado,
        g.notas, g.created_at,
        i.numero_importacion,
        oc.numero_oc
    FROM gastos_importacion g
    JOIN tipos_gasto tg ON g.tipo_gasto_codigo = tg.codigo
    JOIN monedas m ON g.moneda_id = m.id
    LEFT JOIN importaciones i ON g.importacion_id = i.id
    LEFT JOIN ordenes_compra oc ON g.oc_id = oc.id
    WHERE g.empresa_id = p_empresa_id
      AND (p_importacion_id IS NULL OR g.importacion_id = p_importacion_id)
      AND (p_oc_id IS NULL OR g.oc_id = p_oc_id)
      AND (p_tipo_gasto IS NULL OR g.tipo_gasto_codigo = p_tipo_gasto)
      AND (p_estado IS NULL OR g.estado = p_estado)
    ORDER BY tg.orden, g.fecha_gasto DESC;
END //

CREATE PROCEDURE sp_gasto_crear(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_oc_id INT,
    IN p_tipo_gasto_codigo VARCHAR(50),
    IN p_descripcion VARCHAR(200),
    IN p_proveedor_ruc VARCHAR(20),
    IN p_proveedor_nombre VARCHAR(150),
    IN p_moneda_id INT,
    IN p_monto DECIMAL(15,2),
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_numero_comprobante VARCHAR(100),
    IN p_fecha_gasto DATE,
    IN p_comprobante_path VARCHAR(500),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    INSERT INTO gastos_importacion (
        empresa_id, importacion_id, oc_id, tipo_gasto_codigo,
        descripcion, proveedor_ruc, proveedor_nombre,
        moneda_id, monto, tipo_cambio,
        numero_comprobante, fecha_gasto,
        comprobante_path, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, p_importacion_id, p_oc_id, p_tipo_gasto_codigo,
        p_descripcion, p_proveedor_ruc, p_proveedor_nombre,
        COALESCE(p_moneda_id, 1), p_monto, COALESCE(p_tipo_cambio, 1.0000),
        p_numero_comprobante, COALESCE(p_fecha_gasto, CURDATE()),
        p_comprobante_path, p_notas,
        p_usuario_id, p_usuario_id
    );
    SELECT LAST_INSERT_ID() AS id;
END //

CREATE PROCEDURE sp_gasto_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_tipo_gasto_codigo VARCHAR(50),
    IN p_descripcion VARCHAR(200),
    IN p_proveedor_ruc VARCHAR(20),
    IN p_proveedor_nombre VARCHAR(150),
    IN p_moneda_id INT,
    IN p_monto DECIMAL(15,2),
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_numero_comprobante VARCHAR(100),
    IN p_fecha_gasto DATE,
    IN p_estado VARCHAR(20),
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    UPDATE gastos_importacion SET
        tipo_gasto_codigo = COALESCE(p_tipo_gasto_codigo, tipo_gasto_codigo),
        descripcion = COALESCE(p_descripcion, descripcion),
        proveedor_ruc = COALESCE(p_proveedor_ruc, proveedor_ruc),
        proveedor_nombre = COALESCE(p_proveedor_nombre, proveedor_nombre),
        moneda_id = COALESCE(p_moneda_id, moneda_id),
        monto = COALESCE(p_monto, monto),
        tipo_cambio = COALESCE(p_tipo_cambio, tipo_cambio),
        numero_comprobante = COALESCE(p_numero_comprobante, numero_comprobante),
        fecha_gasto = COALESCE(p_fecha_gasto, fecha_gasto),
        estado = COALESCE(p_estado, estado),
        notas = COALESCE(p_notas, notas),
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;
    SELECT ROW_COUNT() AS affected;
END //

CREATE PROCEDURE sp_gasto_eliminar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_prorrateado TINYINT;
    SELECT prorrateado INTO v_prorrateado FROM gastos_importacion WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_prorrateado = 1 THEN
        SELECT 'error' AS result, 'No se puede eliminar un gasto ya prorrateado' AS message;
    ELSE
        DELETE FROM gastos_importacion WHERE id = p_id AND empresa_id = p_empresa_id;
        SELECT 'deleted' AS result, '' AS message;
    END IF;
END //

-- Resumen de gastos por tipo para una importacion
CREATE PROCEDURE sp_gasto_resumen_por_tipo(
    IN p_empresa_id INT,
    IN p_importacion_id INT
)
BEGIN
    SELECT
        tg.codigo, tg.nombre, tg.color_ui, tg.icono_ui,
        COUNT(g.id) AS cantidad_gastos,
        COALESCE(SUM(g.monto_pen), 0) AS total_pen,
        COALESCE(SUM(g.monto), 0) AS total_moneda_origen
    FROM tipos_gasto tg
    LEFT JOIN gastos_importacion g ON g.tipo_gasto_codigo = tg.codigo
        AND g.importacion_id = p_importacion_id
        AND g.empresa_id = p_empresa_id
    GROUP BY tg.codigo, tg.nombre, tg.color_ui, tg.icono_ui, tg.orden
    ORDER BY tg.orden;
END //

-- ============================================================================
-- PRORRATEO DE COSTOS
-- ============================================================================

-- Calcular prorrateo para una OC dentro de una importacion
CREATE PROCEDURE sp_prorrateo_calcular(
    IN p_empresa_id INT,
    IN p_importacion_id INT,
    IN p_oc_id INT,
    IN p_metodo VARCHAR(20),
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_prorrateo_id INT;
    DECLARE v_total_fob DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_flete DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_seguro DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_tributos DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_gastos DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_cif DECIMAL(15,2) DEFAULT 0;
    DECLARE v_total_peso DECIMAL(10,3) DEFAULT 0;
    DECLARE v_total_volumen DECIMAL(10,6) DEFAULT 0;
    DECLARE v_total_cantidad DECIMAL(10,2) DEFAULT 0;
    DECLARE v_metodo VARCHAR(20);

    SET v_metodo = COALESCE(p_metodo, 'valor_fob');

    -- 1. Obtener total FOB de la OC
    SELECT COALESCE(SUM(valor_fob), 0), COALESCE(SUM(peso_kg), 0),
           COALESCE(SUM(volumen_m3), 0), COALESCE(SUM(cantidad), 0)
    INTO v_total_fob, v_total_peso, v_total_volumen, v_total_cantidad
    FROM orden_compra_items WHERE oc_id = p_oc_id;

    -- 2. Obtener totales de gastos por categoria
    -- Flete (international_freight)
    SELECT COALESCE(SUM(monto_pen), 0) INTO v_total_flete
    FROM gastos_importacion
    WHERE (importacion_id = p_importacion_id OR oc_id = p_oc_id)
      AND tipo_gasto_codigo = 'flete_internacional'
      AND empresa_id = p_empresa_id;

    -- Seguro
    SELECT COALESCE(SUM(monto_pen), 0) INTO v_total_seguro
    FROM gastos_importacion
    WHERE (importacion_id = p_importacion_id OR oc_id = p_oc_id)
      AND tipo_gasto_codigo = 'seguro'
      AND empresa_id = p_empresa_id;

    -- Tributos (de la DUA)
    SELECT COALESCE(SUM(total_tributos * tipo_cambio), 0) INTO v_total_tributos
    FROM dua_documentos
    WHERE importacion_id = p_importacion_id
      AND empresa_id = p_empresa_id
      AND estado != 'cancelada';

    -- Otros gastos (todos excepto flete y seguro)
    SELECT COALESCE(SUM(monto_pen), 0) INTO v_total_gastos
    FROM gastos_importacion
    WHERE (importacion_id = p_importacion_id OR oc_id = p_oc_id)
      AND tipo_gasto_codigo NOT IN ('flete_internacional', 'seguro')
      AND empresa_id = p_empresa_id;

    SET v_total_cif = v_total_fob + v_total_flete + v_total_seguro;

    -- 3. Crear cabecera de prorrateo
    INSERT INTO prorrateos (
        empresa_id, importacion_id, oc_id, fecha_prorrateo, metodo_prorrateo,
        total_fob, total_flete, total_seguro, total_tributos, total_gastos,
        total_cif, total_landed_cost,
        factor_flete, factor_seguro, factor_tributos, factor_gastos,
        estado, created_by, updated_by
    ) VALUES (
        p_empresa_id, p_importacion_id, p_oc_id, CURDATE(), v_metodo,
        v_total_fob, v_total_flete, v_total_seguro, v_total_tributos, v_total_gastos,
        v_total_cif, v_total_fob + v_total_flete + v_total_seguro + v_total_tributos + v_total_gastos,
        IF(v_total_fob > 0, v_total_flete / v_total_fob, 0),
        IF(v_total_fob > 0, v_total_seguro / v_total_fob, 0),
        IF(v_total_fob > 0, v_total_tributos / v_total_fob, 0),
        IF(v_total_fob > 0, v_total_gastos / v_total_fob, 0),
        'calculado', p_usuario_id, p_usuario_id
    );
    SET v_prorrateo_id = LAST_INSERT_ID();

    -- 4. Calcular detalle por item segun metodo
    INSERT INTO prorrateo_detalle (
        prorrateo_id, oc_item_id, producto_id, cantidad, valor_fob,
        peso_kg, volumen_m3, factor_item,
        flete_prorrateado, seguro_prorrateado, tributos_prorrateados, gastos_prorrateados,
        costo_total, costo_unitario
    )
    SELECT
        v_prorrateo_id,
        oci.id,
        oci.producto_id,
        oci.cantidad,
        oci.valor_fob,
        oci.peso_kg,
        oci.volumen_m3,
        -- Factor segun metodo
        CASE v_metodo
            WHEN 'valor_fob' THEN IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
            WHEN 'peso' THEN IF(v_total_peso > 0, COALESCE(oci.peso_kg, 0) / v_total_peso, 0)
            WHEN 'volumen' THEN IF(v_total_volumen > 0, COALESCE(oci.volumen_m3, 0) / v_total_volumen, 0)
            WHEN 'cantidad' THEN IF(v_total_cantidad > 0, oci.cantidad / v_total_cantidad, 0)
            ELSE IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
        END AS factor,
        -- Montos prorrateados
        ROUND(v_total_flete * CASE v_metodo
            WHEN 'valor_fob' THEN IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
            WHEN 'peso' THEN IF(v_total_peso > 0, COALESCE(oci.peso_kg, 0) / v_total_peso, 0)
            WHEN 'volumen' THEN IF(v_total_volumen > 0, COALESCE(oci.volumen_m3, 0) / v_total_volumen, 0)
            WHEN 'cantidad' THEN IF(v_total_cantidad > 0, oci.cantidad / v_total_cantidad, 0)
            ELSE IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
        END, 2),
        ROUND(v_total_seguro * CASE v_metodo
            WHEN 'valor_fob' THEN IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
            WHEN 'peso' THEN IF(v_total_peso > 0, COALESCE(oci.peso_kg, 0) / v_total_peso, 0)
            WHEN 'volumen' THEN IF(v_total_volumen > 0, COALESCE(oci.volumen_m3, 0) / v_total_volumen, 0)
            WHEN 'cantidad' THEN IF(v_total_cantidad > 0, oci.cantidad / v_total_cantidad, 0)
            ELSE IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
        END, 2),
        ROUND(v_total_tributos * CASE v_metodo
            WHEN 'valor_fob' THEN IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
            WHEN 'peso' THEN IF(v_total_peso > 0, COALESCE(oci.peso_kg, 0) / v_total_peso, 0)
            WHEN 'volumen' THEN IF(v_total_volumen > 0, COALESCE(oci.volumen_m3, 0) / v_total_volumen, 0)
            WHEN 'cantidad' THEN IF(v_total_cantidad > 0, oci.cantidad / v_total_cantidad, 0)
            ELSE IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
        END, 2),
        ROUND(v_total_gastos * CASE v_metodo
            WHEN 'valor_fob' THEN IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
            WHEN 'peso' THEN IF(v_total_peso > 0, COALESCE(oci.peso_kg, 0) / v_total_peso, 0)
            WHEN 'volumen' THEN IF(v_total_volumen > 0, COALESCE(oci.volumen_m3, 0) / v_total_volumen, 0)
            WHEN 'cantidad' THEN IF(v_total_cantidad > 0, oci.cantidad / v_total_cantidad, 0)
            ELSE IF(v_total_fob > 0, oci.valor_fob / v_total_fob, 0)
        END, 2),
        -- Costo total y unitario se calculan abajo
        0, 0
    FROM orden_compra_items oci
    WHERE oci.oc_id = p_oc_id;

    -- 5. Actualizar costo total y unitario en detalle
    UPDATE prorrateo_detalle SET
        costo_total = valor_fob + flete_prorrateado + seguro_prorrateado + tributos_prorrateados + gastos_prorrateados,
        costo_unitario = IF(cantidad > 0,
            (valor_fob + flete_prorrateado + seguro_prorrateado + tributos_prorrateados + gastos_prorrateados) / cantidad,
            0)
    WHERE prorrateo_id = v_prorrateo_id;

    -- Devolver resultado
    SELECT v_prorrateo_id AS prorrateo_id, v_metodo AS metodo,
           v_total_fob AS total_fob, v_total_flete AS total_flete,
           v_total_seguro AS total_seguro, v_total_tributos AS total_tributos,
           v_total_gastos AS total_gastos,
           (v_total_fob + v_total_flete + v_total_seguro + v_total_tributos + v_total_gastos) AS total_landed_cost;
END //

-- Aplicar prorrateo (escribe los costos en los items de la OC)
CREATE PROCEDURE sp_prorrateo_aplicar(
    IN p_prorrateo_id INT,
    IN p_empresa_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_oc_id INT;
    DECLARE v_importacion_id INT;

    SELECT oc_id, importacion_id INTO v_oc_id, v_importacion_id
    FROM prorrateos WHERE id = p_prorrateo_id AND empresa_id = p_empresa_id;

    -- Actualizar items de OC con costos prorrateados
    UPDATE orden_compra_items oci
    JOIN prorrateo_detalle pd ON pd.oc_item_id = oci.id AND pd.prorrateo_id = p_prorrateo_id
    SET
        oci.prorrateo_flete = pd.flete_prorrateado,
        oci.prorrateo_seguro = pd.seguro_prorrateado,
        oci.prorrateo_tributos = pd.tributos_prorrateados,
        oci.prorrateo_gastos = pd.gastos_prorrateados,
        oci.costo_total = pd.costo_total,
        oci.costo_unitario_landed = pd.costo_unitario,
        oci.updated_by = p_usuario_id;

    -- Marcar prorrateo como aplicado
    UPDATE prorrateos SET
        estado = 'aplicado', fecha_aplicacion = CURDATE(), updated_by = p_usuario_id
    WHERE id = p_prorrateo_id;

    -- Marcar gastos como prorrateados
    UPDATE gastos_importacion SET prorrateado = 1
    WHERE (importacion_id = v_importacion_id OR oc_id = v_oc_id)
      AND empresa_id = p_empresa_id;

    -- Actualizar totales de la OC
    UPDATE ordenes_compra SET
        total_flete = (SELECT COALESCE(SUM(prorrateo_flete), 0) FROM orden_compra_items WHERE oc_id = v_oc_id),
        total_seguro = (SELECT COALESCE(SUM(prorrateo_seguro), 0) FROM orden_compra_items WHERE oc_id = v_oc_id),
        total_cif = total_fob + (SELECT COALESCE(SUM(prorrateo_flete), 0) FROM orden_compra_items WHERE oc_id = v_oc_id)
                    + (SELECT COALESCE(SUM(prorrateo_seguro), 0) FROM orden_compra_items WHERE oc_id = v_oc_id),
        total_costo_importacion = (SELECT COALESCE(SUM(costo_total), 0) FROM orden_compra_items WHERE oc_id = v_oc_id),
        estado = 'prorrateado',
        updated_by = p_usuario_id
    WHERE id = v_oc_id;

    -- Actualizar totales de la importacion
    IF v_importacion_id IS NOT NULL THEN
        UPDATE importaciones SET
            total_gastos_importacion = (
                SELECT COALESCE(SUM(monto_pen), 0) FROM gastos_importacion
                WHERE importacion_id = v_importacion_id AND empresa_id = p_empresa_id
            ),
            total_costo_importacion = total_fob_importacion + (
                SELECT COALESCE(SUM(monto_pen), 0) FROM gastos_importacion
                WHERE importacion_id = v_importacion_id AND empresa_id = p_empresa_id
            )
        WHERE id = v_importacion_id;
    END IF;

    SELECT 'applied' AS result, v_oc_id AS oc_id;
END //

-- Obtener detalle de prorrateo
CREATE PROCEDURE sp_prorrateo_obtener(
    IN p_prorrateo_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT p.*, oc.numero_oc, i.numero_importacion
    FROM prorrateos p
    LEFT JOIN ordenes_compra oc ON p.oc_id = oc.id
    LEFT JOIN importaciones i ON p.importacion_id = i.id
    WHERE p.id = p_prorrateo_id AND p.empresa_id = p_empresa_id;

    -- Detalle por item
    SELECT
        pd.*,
        pr.sku, pr.nombre AS producto_nombre,
        pr.codigo_hs
    FROM prorrateo_detalle pd
    JOIN productos pr ON pd.producto_id = pr.id
    WHERE pd.prorrateo_id = p_prorrateo_id
    ORDER BY pr.sku;
END //

-- Ficha de costeo de una OC (para exportar a PDF/Excel)
CREATE PROCEDURE sp_ficha_costeo_oc(
    IN p_oc_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera OC
    SELECT
        oc.*, p.razon_social AS proveedor, p.ruc AS proveedor_ruc,
        pa.nombre AS pais_origen,
        m.codigo AS moneda, m.simbolo AS moneda_simbolo,
        e.razon_social AS empresa, e.ruc AS empresa_ruc
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    LEFT JOIN paises pa ON p.pais_id = pa.id
    JOIN monedas m ON oc.moneda_id = m.id
    JOIN empresas e ON oc.empresa_id = e.id
    WHERE oc.id = p_oc_id AND oc.empresa_id = p_empresa_id;

    -- Items con costeo
    SELECT
        oci.id, pr.sku, pr.nombre AS producto, pr.codigo_hs,
        oci.cantidad, oci.precio_unitario, oci.unidad_medida,
        oci.valor_fob, oci.peso_kg, oci.volumen_m3,
        oci.prorrateo_flete, oci.prorrateo_seguro,
        oci.prorrateo_tributos, oci.prorrateo_gastos,
        oci.costo_total, oci.costo_unitario_landed,
        IF(oci.precio_unitario > 0,
           ROUND(((oci.costo_unitario_landed - oci.precio_unitario) / oci.precio_unitario) * 100, 2),
           0) AS incremento_pct
    FROM orden_compra_items oci
    JOIN productos pr ON oci.producto_id = pr.id
    WHERE oci.oc_id = p_oc_id
    ORDER BY pr.sku;

    -- Gastos asociados
    SELECT
        tg.nombre AS tipo_gasto, g.descripcion, g.proveedor_nombre,
        g.monto, m.simbolo AS moneda_simbolo, g.monto_pen
    FROM gastos_importacion g
    JOIN tipos_gasto tg ON g.tipo_gasto_codigo = tg.codigo
    JOIN monedas m ON g.moneda_id = m.id
    WHERE g.oc_id = p_oc_id AND g.empresa_id = p_empresa_id
    ORDER BY tg.orden;
END //

DELIMITER ;
