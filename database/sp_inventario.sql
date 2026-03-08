-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Inventario
-- Movimientos, Stock, Kardex SUNAT
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- MOVIMIENTOS DE ALMACEN
-- ============================================================================

CREATE PROCEDURE sp_movimiento_listar(
    IN p_empresa_id INT,
    IN p_tipo VARCHAR(20),
    IN p_almacen_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE,
    IN p_estado VARCHAR(20),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    SET v_offset = (COALESCE(p_page, 1) - 1) * COALESCE(p_per_page, 20);

    SELECT
        ma.id, ma.numero_movimiento, ma.tipo_movimiento,
        ma.fecha_movimiento, ma.documento_referencia,
        ma.total_productos, ma.valor_total, ma.estado,
        a.nombre AS almacen, a.codigo AS almacen_codigo,
        ad.nombre AS almacen_destino, ad.codigo AS almacen_destino_codigo,
        oc.numero_oc,
        ma.notas, ma.created_at
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN almacenes ad ON ma.almacen_destino_id = ad.id
    LEFT JOIN ordenes_compra oc ON ma.oc_id = oc.id
    WHERE ma.empresa_id = p_empresa_id
      AND (p_tipo IS NULL OR ma.tipo_movimiento = p_tipo)
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id OR ma.almacen_destino_id = p_almacen_id)
      AND (p_fecha_desde IS NULL OR ma.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR ma.fecha_movimiento <= p_fecha_hasta)
      AND (p_estado IS NULL OR ma.estado = p_estado)
    ORDER BY ma.fecha_movimiento DESC, ma.id DESC
    LIMIT v_offset, COALESCE(p_per_page, 20);
END //

CREATE PROCEDURE sp_movimiento_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT
        ma.*,
        a.nombre AS almacen, a.codigo AS almacen_codigo,
        ad.nombre AS almacen_destino,
        oc.numero_oc
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN almacenes ad ON ma.almacen_destino_id = ad.id
    LEFT JOIN ordenes_compra oc ON ma.oc_id = oc.id
    WHERE ma.id = p_id AND ma.empresa_id = p_empresa_id;

    -- Detalle
    SELECT
        md.*, pr.sku, pr.nombre AS producto_nombre,
        pr.unidad_medida, pr.codigo_hs
    FROM movimiento_detalle md
    JOIN productos pr ON md.producto_id = pr.id
    WHERE md.movimiento_id = p_id
    ORDER BY pr.sku;
END //

-- Crear movimiento de ingreso por importacion
CREATE PROCEDURE sp_movimiento_ingreso_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_oc_id INT,
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_mov_id INT;
    DECLARE v_num VARCHAR(50);
    DECLARE v_sig INT;

    -- Generar numero de movimiento: ING-YYYY-NNN
    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_movimiento, 10) AS UNSIGNED)), 0) + 1
    INTO v_sig
    FROM movimientos_almacen
    WHERE empresa_id = p_empresa_id
      AND numero_movimiento LIKE CONCAT('ING-', YEAR(CURDATE()), '-%');

    SET v_num = CONCAT('ING-', YEAR(CURDATE()), '-', LPAD(v_sig, 4, '0'));

    INSERT INTO movimientos_almacen (
        empresa_id, numero_movimiento, tipo_movimiento,
        fecha_movimiento, almacen_id, oc_id,
        documento_referencia, estado, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, v_num, 'ingreso',
        COALESCE(p_fecha, CURDATE()), p_almacen_id, p_oc_id,
        p_documento_referencia, 'borrador', p_notas,
        p_usuario_id, p_usuario_id
    );

    SET v_mov_id = LAST_INSERT_ID();

    -- Auto-llenar con items de la OC si se proporciona
    IF p_oc_id IS NOT NULL THEN
        INSERT INTO movimiento_detalle (
            movimiento_id, producto_id, oc_item_id,
            cantidad, costo_unitario, costo_total,
            lote
        )
        SELECT
            v_mov_id, oci.producto_id, oci.id,
            oci.cantidad,
            IF(oci.costo_unitario_landed > 0, oci.costo_unitario_landed, oci.precio_unitario),
            IF(oci.costo_unitario_landed > 0, oci.cantidad * oci.costo_unitario_landed, oci.valor_fob),
            oci.lote_ingreso
        FROM orden_compra_items oci
        WHERE oci.oc_id = p_oc_id;

        -- Actualizar totales del movimiento
        UPDATE movimientos_almacen SET
            total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = v_mov_id),
            valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = v_mov_id)
        WHERE id = v_mov_id;
    END IF;

    SELECT v_mov_id AS id, v_num AS numero_movimiento;
END //

-- Agregar item a movimiento
CREATE PROCEDURE sp_movimiento_item_agregar(
    IN p_movimiento_id INT,
    IN p_producto_id INT,
    IN p_oc_item_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_costo_unitario DECIMAL(15,4),
    IN p_lote VARCHAR(50),
    IN p_fecha_vencimiento DATE,
    IN p_ubicacion VARCHAR(50)
)
BEGIN
    INSERT INTO movimiento_detalle (
        movimiento_id, producto_id, oc_item_id,
        cantidad, costo_unitario, costo_total,
        lote, fecha_vencimiento, ubicacion
    ) VALUES (
        p_movimiento_id, p_producto_id, p_oc_item_id,
        p_cantidad, p_costo_unitario, ROUND(p_cantidad * p_costo_unitario, 2),
        p_lote, p_fecha_vencimiento, p_ubicacion
    );

    -- Actualizar totales del movimiento
    UPDATE movimientos_almacen SET
        total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = p_movimiento_id),
        valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_movimiento_id)
    WHERE id = p_movimiento_id;

    SELECT LAST_INSERT_ID() AS id;
END //

-- Confirmar/completar movimiento (afecta inventario)
CREATE PROCEDURE sp_movimiento_completar(
    IN p_movimiento_id INT,
    IN p_empresa_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_tipo VARCHAR(20);
    DECLARE v_almacen_id INT;
    DECLARE v_almacen_dest_id INT;
    DECLARE v_oc_id INT;
    DECLARE done INT DEFAULT 0;
    DECLARE v_prod_id INT;
    DECLARE v_cantidad DECIMAL(10,2);
    DECLARE v_costo DECIMAL(15,4);
    DECLARE v_lote VARCHAR(50);

    DECLARE cur CURSOR FOR
        SELECT producto_id, cantidad, costo_unitario, lote
        FROM movimiento_detalle WHERE movimiento_id = p_movimiento_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    SELECT tipo_movimiento, almacen_id, almacen_destino_id, oc_id
    INTO v_tipo, v_almacen_id, v_almacen_dest_id, v_oc_id
    FROM movimientos_almacen
    WHERE id = p_movimiento_id AND empresa_id = p_empresa_id;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_prod_id, v_cantidad, v_costo, v_lote;
        IF done THEN LEAVE read_loop; END IF;

        CASE v_tipo
            WHEN 'ingreso' THEN
                -- Sumar al inventario
                INSERT INTO inventario (empresa_id, producto_id, almacen_id, lote, cantidad, costo_unitario)
                VALUES (p_empresa_id, v_prod_id, v_almacen_id, COALESCE(v_lote, 'DEFAULT'), v_cantidad, v_costo)
                ON DUPLICATE KEY UPDATE
                    cantidad = cantidad + v_cantidad,
                    costo_unitario = (costo_unitario * cantidad + v_costo * v_cantidad) / (cantidad + v_cantidad);

            WHEN 'salida' THEN
                -- Restar del inventario
                UPDATE inventario SET cantidad = cantidad - v_cantidad
                WHERE empresa_id = p_empresa_id AND producto_id = v_prod_id
                  AND almacen_id = v_almacen_id AND lote = COALESCE(v_lote, 'DEFAULT');

            WHEN 'transferencia' THEN
                -- Restar origen
                UPDATE inventario SET cantidad = cantidad - v_cantidad
                WHERE empresa_id = p_empresa_id AND producto_id = v_prod_id
                  AND almacen_id = v_almacen_id AND lote = COALESCE(v_lote, 'DEFAULT');
                -- Sumar destino
                INSERT INTO inventario (empresa_id, producto_id, almacen_id, lote, cantidad, costo_unitario)
                VALUES (p_empresa_id, v_prod_id, v_almacen_dest_id, COALESCE(v_lote, 'DEFAULT'), v_cantidad, v_costo)
                ON DUPLICATE KEY UPDATE
                    cantidad = cantidad + v_cantidad;

            WHEN 'ajuste' THEN
                -- Ajuste directo (puede ser + o -)
                INSERT INTO inventario (empresa_id, producto_id, almacen_id, lote, cantidad, costo_unitario)
                VALUES (p_empresa_id, v_prod_id, v_almacen_id, COALESCE(v_lote, 'DEFAULT'), v_cantidad, v_costo)
                ON DUPLICATE KEY UPDATE
                    cantidad = cantidad + v_cantidad;
        END CASE;
    END LOOP;
    CLOSE cur;

    -- Marcar movimiento como completado
    UPDATE movimientos_almacen SET
        estado = 'completado', updated_by = p_usuario_id
    WHERE id = p_movimiento_id;

    -- Si es ingreso por OC, actualizar estado de la OC
    IF v_tipo = 'ingreso' AND v_oc_id IS NOT NULL THEN
        UPDATE ordenes_compra SET estado = 'en_almacen', updated_by = p_usuario_id
        WHERE id = v_oc_id;
    END IF;

    SELECT 'completed' AS result;
END //

-- Crear transferencia entre almacenes
CREATE PROCEDURE sp_movimiento_transferencia_crear(
    IN p_empresa_id INT,
    IN p_almacen_origen_id INT,
    IN p_almacen_destino_id INT,
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_num VARCHAR(50);
    DECLARE v_sig INT;

    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_movimiento, 10) AS UNSIGNED)), 0) + 1
    INTO v_sig
    FROM movimientos_almacen
    WHERE empresa_id = p_empresa_id
      AND numero_movimiento LIKE CONCAT('TRF-', YEAR(CURDATE()), '-%');

    SET v_num = CONCAT('TRF-', YEAR(CURDATE()), '-', LPAD(v_sig, 4, '0'));

    INSERT INTO movimientos_almacen (
        empresa_id, numero_movimiento, tipo_movimiento,
        fecha_movimiento, almacen_id, almacen_destino_id,
        documento_referencia, estado, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, v_num, 'transferencia',
        COALESCE(p_fecha, CURDATE()), p_almacen_origen_id, p_almacen_destino_id,
        p_documento_referencia, 'borrador', p_notas,
        p_usuario_id, p_usuario_id
    );

    SELECT LAST_INSERT_ID() AS id, v_num AS numero_movimiento;
END //

-- Crear salida de almacen
CREATE PROCEDURE sp_movimiento_salida_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_num VARCHAR(50);
    DECLARE v_sig INT;

    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_movimiento, 10) AS UNSIGNED)), 0) + 1
    INTO v_sig
    FROM movimientos_almacen
    WHERE empresa_id = p_empresa_id
      AND numero_movimiento LIKE CONCAT('SAL-', YEAR(CURDATE()), '-%');

    SET v_num = CONCAT('SAL-', YEAR(CURDATE()), '-', LPAD(v_sig, 4, '0'));

    INSERT INTO movimientos_almacen (
        empresa_id, numero_movimiento, tipo_movimiento,
        fecha_movimiento, almacen_id,
        documento_referencia, estado, notas,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, v_num, 'salida',
        COALESCE(p_fecha, CURDATE()), p_almacen_id,
        p_documento_referencia, 'borrador', p_notas,
        p_usuario_id, p_usuario_id
    );

    SELECT LAST_INSERT_ID() AS id, v_num AS numero_movimiento;
END //

-- ============================================================================
-- INVENTARIO / STOCK
-- ============================================================================

CREATE PROCEDURE sp_inventario_stock(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_search VARCHAR(100),
    IN p_solo_con_stock TINYINT
)
BEGIN
    SELECT
        inv.id, inv.cantidad, inv.costo_unitario, inv.valor_total, inv.lote,
        inv.fecha_ultimo_movimiento,
        pr.sku, pr.nombre AS producto, pr.unidad_medida, pr.codigo_hs,
        pr.color_ui, pr.icono_ui,
        a.nombre AS almacen, a.codigo AS almacen_codigo
    FROM inventario inv
    JOIN productos pr ON inv.producto_id = pr.id
    JOIN almacenes a ON inv.almacen_id = a.id
    WHERE inv.empresa_id = p_empresa_id
      AND (p_almacen_id IS NULL OR inv.almacen_id = p_almacen_id)
      AND (p_solo_con_stock IS NULL OR p_solo_con_stock = 0 OR inv.cantidad > 0)
      AND (p_search IS NULL OR p_search = ''
           OR pr.sku LIKE CONCAT('%', p_search, '%')
           OR pr.nombre LIKE CONCAT('%', p_search, '%'))
    ORDER BY pr.sku, a.nombre;
END //

-- Stock consolidado por producto (todos los almacenes)
CREATE PROCEDURE sp_inventario_stock_consolidado(
    IN p_empresa_id INT,
    IN p_producto_id INT
)
BEGIN
    SELECT
        pr.id, pr.sku, pr.nombre, pr.unidad_medida,
        COALESCE(SUM(inv.cantidad), 0) AS stock_total,
        COALESCE(AVG(inv.costo_unitario), 0) AS costo_promedio,
        COALESCE(SUM(inv.valor_total), 0) AS valor_total,
        COUNT(DISTINCT inv.almacen_id) AS almacenes_con_stock
    FROM productos pr
    LEFT JOIN inventario inv ON pr.id = inv.producto_id AND inv.cantidad > 0
    WHERE pr.empresa_id = p_empresa_id
      AND (p_producto_id IS NULL OR pr.id = p_producto_id)
      AND pr.status = 'active'
    GROUP BY pr.id
    ORDER BY pr.sku;
END //

-- ============================================================================
-- KARDEX SUNAT
-- ============================================================================

CREATE PROCEDURE sp_kardex_producto(
    IN p_empresa_id INT,
    IN p_producto_id INT,
    IN p_almacen_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE
)
BEGIN
    SELECT
        ma.fecha_movimiento AS fecha,
        ma.tipo_movimiento,
        CASE
            WHEN ma.tipo_movimiento = 'ingreso' AND ma.oc_id IS NOT NULL THEN '02'
            WHEN ma.tipo_movimiento = 'ingreso' AND ma.oc_id IS NULL THEN '16'
            WHEN ma.tipo_movimiento = 'salida' THEN '01'
            WHEN ma.tipo_movimiento = 'transferencia' THEN '11'
            WHEN ma.tipo_movimiento = 'ajuste' THEN '99'
            ELSE '99'
        END AS tipo_operacion_sunat,
        ma.documento_referencia,
        md.cantidad,
        md.costo_unitario,
        md.costo_total,
        -- Entrada
        IF(ma.tipo_movimiento IN ('ingreso', 'ajuste') AND md.cantidad > 0, md.cantidad, NULL) AS entrada_cantidad,
        IF(ma.tipo_movimiento IN ('ingreso', 'ajuste') AND md.cantidad > 0, md.costo_unitario, NULL) AS entrada_costo_unit,
        IF(ma.tipo_movimiento IN ('ingreso', 'ajuste') AND md.cantidad > 0, md.costo_total, NULL) AS entrada_costo_total,
        -- Salida
        IF(ma.tipo_movimiento IN ('salida') OR (ma.tipo_movimiento = 'transferencia' AND ma.almacen_id = p_almacen_id),
           md.cantidad, NULL) AS salida_cantidad,
        IF(ma.tipo_movimiento IN ('salida') OR (ma.tipo_movimiento = 'transferencia' AND ma.almacen_id = p_almacen_id),
           md.costo_unitario, NULL) AS salida_costo_unit,
        IF(ma.tipo_movimiento IN ('salida') OR (ma.tipo_movimiento = 'transferencia' AND ma.almacen_id = p_almacen_id),
           md.costo_total, NULL) AS salida_costo_total,
        ma.numero_movimiento,
        a.nombre AS almacen
    FROM movimiento_detalle md
    JOIN movimientos_almacen ma ON md.movimiento_id = ma.id
    JOIN almacenes a ON ma.almacen_id = a.id
    WHERE ma.empresa_id = p_empresa_id
      AND md.producto_id = p_producto_id
      AND ma.estado = 'completado'
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id OR ma.almacen_destino_id = p_almacen_id)
      AND (p_fecha_desde IS NULL OR ma.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR ma.fecha_movimiento <= p_fecha_hasta)
    ORDER BY ma.fecha_movimiento, ma.id;
END //

DELIMITER ;
