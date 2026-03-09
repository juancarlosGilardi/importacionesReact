-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Vales de Ingreso/Salida
-- Sprint 5: Sistema formal de vales con IGV, conceptos, correlativos
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- HELPER: Obtener siguiente correlativo
-- ============================================================================
CREATE PROCEDURE sp_correlativo_siguiente(
    IN p_empresa_id INT,
    IN p_tipo VARCHAR(50),
    OUT p_numero VARCHAR(20)
)
BEGIN
    DECLARE v_prefijo VARCHAR(20);
    DECLARE v_ultimo INT;
    DECLARE v_anio INT;

    SET v_anio = YEAR(CURDATE());

    SELECT prefijo, ultimo_numero INTO v_prefijo, v_ultimo
    FROM correlativos
    WHERE empresa_id = p_empresa_id AND tipo = p_tipo AND anio = v_anio
    FOR UPDATE;

    IF v_prefijo IS NULL THEN
        -- Crear correlativo si no existe para este año
        SELECT prefijo INTO v_prefijo FROM correlativos
        WHERE empresa_id = p_empresa_id AND tipo = p_tipo
        LIMIT 1;

        IF v_prefijo IS NULL THEN
            SET v_prefijo = UPPER(LEFT(p_tipo, 3));
        END IF;

        INSERT INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio)
        VALUES (p_empresa_id, p_tipo, v_prefijo, 1, v_anio);
        SET v_ultimo = 1;
    ELSE
        SET v_ultimo = v_ultimo + 1;
        UPDATE correlativos SET ultimo_numero = v_ultimo
        WHERE empresa_id = p_empresa_id AND tipo = p_tipo AND anio = v_anio;
    END IF;

    SET p_numero = CONCAT(v_prefijo, '-', v_anio, '-', LPAD(v_ultimo, 4, '0'));
END //


-- ============================================================================
-- CONCEPTOS DE ALMACEN
-- ============================================================================

CREATE PROCEDURE sp_concepto_almacen_listar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_tipo VARCHAR(10)
)
BEGIN
    SELECT
        ca.id, ca.codigo, ca.nombre, ca.tipo, ca.afecta_costo, ca.activo,
        COALESCE(cac.habilitado, 1) AS habilitado
    FROM conceptos_almacen ca
    LEFT JOIN concepto_almacen_config cac
        ON ca.id = cac.concepto_id AND cac.almacen_id = p_almacen_id
    WHERE ca.empresa_id = p_empresa_id
      AND ca.activo = 1
      AND (p_tipo IS NULL OR ca.tipo = p_tipo)
    ORDER BY ca.tipo, ca.codigo;
END //


CREATE PROCEDURE sp_concepto_almacen_toggle(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_habilitado TINYINT
)
BEGIN
    INSERT INTO concepto_almacen_config (empresa_id, almacen_id, concepto_id, habilitado)
    VALUES (p_empresa_id, p_almacen_id, p_concepto_id, p_habilitado)
    ON DUPLICATE KEY UPDATE habilitado = p_habilitado;

    SELECT 'ok' AS result;
END //


-- ============================================================================
-- VALES DE INGRESO
-- ============================================================================

CREATE PROCEDURE sp_vale_ingreso_listar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    DECLARE v_limit INT DEFAULT 20;
    SET v_limit = IFNULL(p_per_page, 20);
    SET v_offset = (IFNULL(p_page, 1) - 1) * v_limit;

    SELECT
        ma.id, ma.numero_movimiento, ma.fecha_movimiento,
        ma.documento_referencia, ma.total_productos,
        ma.subtotal, ma.igv, ma.total, ma.estado, ma.notas,
        a.nombre AS almacen_nombre, a.codigo AS almacen_codigo,
        ca.nombre AS concepto_nombre, ca.codigo AS concepto_codigo,
        p.razon_social AS proveedor_nombre,
        ma.created_at
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN conceptos_almacen ca ON ma.concepto_id = ca.id
    LEFT JOIN proveedores p ON ma.proveedor_id = p.id
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'ingreso'
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_concepto_id IS NULL OR ma.concepto_id = p_concepto_id)
      AND (p_estado IS NULL OR ma.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.documento_referencia LIKE CONCAT('%', p_search, '%'))
    ORDER BY ma.fecha_movimiento DESC, ma.id DESC
    LIMIT v_offset, v_limit;
END //


CREATE PROCEDURE sp_vale_ingreso_contar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM movimientos_almacen ma
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'ingreso'
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_concepto_id IS NULL OR ma.concepto_id = p_concepto_id)
      AND (p_estado IS NULL OR ma.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.documento_referencia LIKE CONCAT('%', p_search, '%'));
END //


CREATE PROCEDURE sp_vale_ingreso_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT
        ma.*, a.nombre AS almacen_nombre, a.codigo AS almacen_codigo,
        ca.nombre AS concepto_nombre, ca.codigo AS concepto_codigo,
        p.razon_social AS proveedor_nombre,
        u.nombre AS creado_por_nombre
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN conceptos_almacen ca ON ma.concepto_id = ca.id
    LEFT JOIN proveedores p ON ma.proveedor_id = p.id
    LEFT JOIN usuarios u ON ma.created_by = u.id
    WHERE ma.id = p_id AND ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'ingreso';

    -- Detalle
    SELECT
        md.id, md.producto_id, md.cantidad, md.costo_unitario, md.costo_total,
        md.lote, md.fecha_vencimiento, md.ubicacion,
        pr.sku, pr.nombre AS producto_nombre, pr.unidad_medida
    FROM movimiento_detalle md
    JOIN productos pr ON md.producto_id = pr.id
    WHERE md.movimiento_id = p_id
    ORDER BY md.id;
END //


CREATE PROCEDURE sp_vale_ingreso_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_proveedor_id INT,
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_numero VARCHAR(20);
    DECLARE v_mov_id INT;

    CALL sp_correlativo_siguiente(p_empresa_id, 'vale_ingreso', v_numero);

    INSERT INTO movimientos_almacen (
        empresa_id, numero_movimiento, tipo_movimiento,
        fecha_movimiento, almacen_id, concepto_id, proveedor_id,
        documento_referencia, estado, notas,
        subtotal, igv, total,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, v_numero, 'ingreso',
        COALESCE(p_fecha, CURDATE()), p_almacen_id, p_concepto_id, p_proveedor_id,
        p_documento_referencia, 'borrador', p_notas,
        0, 0, 0,
        p_usuario_id, p_usuario_id
    );

    SET v_mov_id = LAST_INSERT_ID();
    SELECT v_mov_id AS id, v_numero AS numero_movimiento;
END //


CREATE PROCEDURE sp_vale_ingreso_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_proveedor_id INT,
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);

    SELECT estado INTO v_estado FROM movimientos_almacen
    WHERE id = p_id AND empresa_id = p_empresa_id AND tipo_movimiento = 'ingreso';

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden editar vales en estado borrador';
    END IF;

    UPDATE movimientos_almacen SET
        almacen_id = COALESCE(p_almacen_id, almacen_id),
        concepto_id = COALESCE(p_concepto_id, concepto_id),
        proveedor_id = p_proveedor_id,
        documento_referencia = COALESCE(p_documento_referencia, documento_referencia),
        fecha_movimiento = COALESCE(p_fecha, fecha_movimiento),
        notas = p_notas,
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'updated' AS result;
END //


CREATE PROCEDURE sp_vale_ingreso_item_agregar(
    IN p_vale_id INT,
    IN p_empresa_id INT,
    IN p_producto_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_costo_unitario DECIMAL(15,4),
    IN p_lote VARCHAR(50),
    IN p_fecha_vencimiento DATE,
    IN p_ubicacion VARCHAR(50)
)
BEGIN
    DECLARE v_costo_total DECIMAL(15,2);
    DECLARE v_item_id INT;

    SET v_costo_total = ROUND(p_cantidad * p_costo_unitario, 2);

    INSERT INTO movimiento_detalle (
        movimiento_id, producto_id, cantidad, costo_unitario, costo_total,
        lote, fecha_vencimiento, ubicacion
    ) VALUES (
        p_vale_id, p_producto_id, p_cantidad, p_costo_unitario, v_costo_total,
        p_lote, p_fecha_vencimiento, p_ubicacion
    );

    SET v_item_id = LAST_INSERT_ID();

    -- Recalcular totales del vale (subtotal + IGV 18%)
    UPDATE movimientos_almacen SET
        total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        subtotal = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        igv = ROUND((SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id) * 0.18, 2),
        total = ROUND((SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id) * 1.18, 2)
    WHERE id = p_vale_id;

    SELECT v_item_id AS id;
END //


CREATE PROCEDURE sp_vale_ingreso_item_eliminar(
    IN p_vale_id INT,
    IN p_item_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);

    SELECT estado INTO v_estado FROM movimientos_almacen
    WHERE id = p_vale_id AND empresa_id = p_empresa_id;

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden eliminar items de vales en borrador';
    END IF;

    DELETE FROM movimiento_detalle WHERE id = p_item_id AND movimiento_id = p_vale_id;

    -- Recalcular totales
    UPDATE movimientos_almacen SET
        total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        subtotal = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        igv = ROUND((SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id) * 0.18, 2),
        total = ROUND((SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id) * 1.18, 2)
    WHERE id = p_vale_id;

    SELECT 'deleted' AS result;
END //


CREATE PROCEDURE sp_vale_ingreso_completar(
    IN p_vale_id INT,
    IN p_empresa_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);
    DECLARE v_almacen_id INT;
    DECLARE v_items INT;
    DECLARE done INT DEFAULT 0;
    DECLARE v_prod_id INT;
    DECLARE v_cantidad DECIMAL(10,2);
    DECLARE v_costo DECIMAL(15,4);
    DECLARE v_lote VARCHAR(50);

    DECLARE cur CURSOR FOR
        SELECT producto_id, cantidad, costo_unitario, lote
        FROM movimiento_detalle WHERE movimiento_id = p_vale_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    SELECT estado, almacen_id INTO v_estado, v_almacen_id
    FROM movimientos_almacen
    WHERE id = p_vale_id AND empresa_id = p_empresa_id AND tipo_movimiento = 'ingreso';

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden completar vales en borrador';
    END IF;

    SELECT COUNT(*) INTO v_items FROM movimiento_detalle WHERE movimiento_id = p_vale_id;
    IF v_items = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El vale debe tener al menos un item';
    END IF;

    -- Actualizar inventario
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_prod_id, v_cantidad, v_costo, v_lote;
        IF done THEN LEAVE read_loop; END IF;

        INSERT INTO inventario (empresa_id, producto_id, almacen_id, lote, cantidad, costo_unitario)
        VALUES (p_empresa_id, v_prod_id, v_almacen_id, COALESCE(v_lote, 'DEFAULT'), v_cantidad, v_costo)
        ON DUPLICATE KEY UPDATE
            costo_unitario = (costo_unitario * cantidad + v_costo * v_cantidad) / (cantidad + v_cantidad),
            cantidad = cantidad + v_cantidad;
    END LOOP;
    CLOSE cur;

    -- Marcar como completado
    UPDATE movimientos_almacen SET
        estado = 'completado', updated_by = p_usuario_id
    WHERE id = p_vale_id;

    SELECT 'completed' AS result;
END //


-- ============================================================================
-- VALES DE SALIDA
-- ============================================================================

CREATE PROCEDURE sp_vale_salida_listar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    DECLARE v_limit INT DEFAULT 20;
    SET v_limit = IFNULL(p_per_page, 20);
    SET v_offset = (IFNULL(p_page, 1) - 1) * v_limit;

    SELECT
        ma.id, ma.numero_movimiento, ma.fecha_movimiento,
        ma.documento_referencia, ma.total_productos,
        ma.subtotal, ma.igv, ma.total, ma.estado,
        ma.centro_costo, ma.solicitante, ma.notas,
        a.nombre AS almacen_nombre, a.codigo AS almacen_codigo,
        ca.nombre AS concepto_nombre, ca.codigo AS concepto_codigo,
        ma.created_at
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN conceptos_almacen ca ON ma.concepto_id = ca.id
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'salida'
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_concepto_id IS NULL OR ma.concepto_id = p_concepto_id)
      AND (p_estado IS NULL OR ma.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.solicitante LIKE CONCAT('%', p_search, '%'))
    ORDER BY ma.fecha_movimiento DESC, ma.id DESC
    LIMIT v_offset, v_limit;
END //


CREATE PROCEDURE sp_vale_salida_contar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM movimientos_almacen ma
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'salida'
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_concepto_id IS NULL OR ma.concepto_id = p_concepto_id)
      AND (p_estado IS NULL OR ma.estado = p_estado)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.solicitante LIKE CONCAT('%', p_search, '%'));
END //


CREATE PROCEDURE sp_vale_salida_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Cabecera
    SELECT
        ma.*, a.nombre AS almacen_nombre, a.codigo AS almacen_codigo,
        ca.nombre AS concepto_nombre, ca.codigo AS concepto_codigo,
        u.nombre AS creado_por_nombre
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN conceptos_almacen ca ON ma.concepto_id = ca.id
    LEFT JOIN usuarios u ON ma.created_by = u.id
    WHERE ma.id = p_id AND ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento = 'salida';

    -- Detalle con stock disponible
    SELECT
        md.id, md.producto_id, md.cantidad, md.costo_unitario, md.costo_total,
        md.lote, md.ubicacion,
        pr.sku, pr.nombre AS producto_nombre, pr.unidad_medida,
        COALESCE((SELECT SUM(inv.cantidad) FROM inventario inv
                  WHERE inv.producto_id = md.producto_id
                    AND inv.almacen_id = ma.almacen_id
                    AND inv.empresa_id = p_empresa_id), 0) AS stock_disponible
    FROM movimiento_detalle md
    JOIN productos pr ON md.producto_id = pr.id
    JOIN movimientos_almacen ma ON md.movimiento_id = ma.id
    WHERE md.movimiento_id = p_id
    ORDER BY md.id;
END //


CREATE PROCEDURE sp_vale_salida_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_centro_costo VARCHAR(50),
    IN p_solicitante VARCHAR(100),
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_numero VARCHAR(20);
    DECLARE v_mov_id INT;

    CALL sp_correlativo_siguiente(p_empresa_id, 'vale_salida', v_numero);

    INSERT INTO movimientos_almacen (
        empresa_id, numero_movimiento, tipo_movimiento,
        fecha_movimiento, almacen_id, concepto_id,
        centro_costo, solicitante,
        documento_referencia, estado, notas,
        subtotal, igv, total,
        created_by, updated_by
    ) VALUES (
        p_empresa_id, v_numero, 'salida',
        COALESCE(p_fecha, CURDATE()), p_almacen_id, p_concepto_id,
        p_centro_costo, p_solicitante,
        p_documento_referencia, 'borrador', p_notas,
        0, 0, 0,
        p_usuario_id, p_usuario_id
    );

    SET v_mov_id = LAST_INSERT_ID();
    SELECT v_mov_id AS id, v_numero AS numero_movimiento;
END //


CREATE PROCEDURE sp_vale_salida_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_concepto_id INT,
    IN p_centro_costo VARCHAR(50),
    IN p_solicitante VARCHAR(100),
    IN p_documento_referencia VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);

    SELECT estado INTO v_estado FROM movimientos_almacen
    WHERE id = p_id AND empresa_id = p_empresa_id AND tipo_movimiento = 'salida';

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden editar vales en estado borrador';
    END IF;

    UPDATE movimientos_almacen SET
        almacen_id = COALESCE(p_almacen_id, almacen_id),
        concepto_id = COALESCE(p_concepto_id, concepto_id),
        centro_costo = p_centro_costo,
        solicitante = p_solicitante,
        documento_referencia = COALESCE(p_documento_referencia, documento_referencia),
        fecha_movimiento = COALESCE(p_fecha, fecha_movimiento),
        notas = p_notas,
        updated_by = p_usuario_id
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'updated' AS result;
END //


CREATE PROCEDURE sp_vale_salida_item_agregar(
    IN p_vale_id INT,
    IN p_empresa_id INT,
    IN p_producto_id INT,
    IN p_cantidad DECIMAL(10,2),
    IN p_lote VARCHAR(50)
)
BEGIN
    DECLARE v_costo_promedio DECIMAL(15,4);
    DECLARE v_costo_total DECIMAL(15,2);
    DECLARE v_almacen_id INT;
    DECLARE v_stock DECIMAL(10,2);
    DECLARE v_item_id INT;

    -- Obtener almacén del vale
    SELECT almacen_id INTO v_almacen_id
    FROM movimientos_almacen WHERE id = p_vale_id AND empresa_id = p_empresa_id;

    -- Obtener costo promedio del producto en ese almacén
    SELECT COALESCE(AVG(costo_unitario), 0), COALESCE(SUM(cantidad), 0)
    INTO v_costo_promedio, v_stock
    FROM inventario
    WHERE empresa_id = p_empresa_id AND producto_id = p_producto_id AND almacen_id = v_almacen_id;

    IF v_costo_promedio = 0 THEN
        -- Si no hay stock, buscar costo promedio global
        SELECT COALESCE(AVG(costo_unitario), 0) INTO v_costo_promedio
        FROM inventario
        WHERE empresa_id = p_empresa_id AND producto_id = p_producto_id;
    END IF;

    SET v_costo_total = ROUND(p_cantidad * v_costo_promedio, 2);

    INSERT INTO movimiento_detalle (
        movimiento_id, producto_id, cantidad, costo_unitario, costo_total, lote
    ) VALUES (
        p_vale_id, p_producto_id, p_cantidad, v_costo_promedio, v_costo_total, p_lote
    );

    SET v_item_id = LAST_INSERT_ID();

    -- Recalcular totales
    UPDATE movimientos_almacen SET
        total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        subtotal = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id)
    WHERE id = p_vale_id;

    SELECT v_item_id AS id, v_costo_promedio AS costo_unitario, v_stock AS stock_disponible;
END //


CREATE PROCEDURE sp_vale_salida_item_eliminar(
    IN p_vale_id INT,
    IN p_item_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);

    SELECT estado INTO v_estado FROM movimientos_almacen
    WHERE id = p_vale_id AND empresa_id = p_empresa_id;

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden eliminar items de vales en borrador';
    END IF;

    DELETE FROM movimiento_detalle WHERE id = p_item_id AND movimiento_id = p_vale_id;

    -- Recalcular totales
    UPDATE movimientos_almacen SET
        total_productos = (SELECT COUNT(*) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        valor_total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        subtotal = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id),
        total = (SELECT COALESCE(SUM(costo_total), 0) FROM movimiento_detalle WHERE movimiento_id = p_vale_id)
    WHERE id = p_vale_id;

    SELECT 'deleted' AS result;
END //


CREATE PROCEDURE sp_vale_salida_completar(
    IN p_vale_id INT,
    IN p_empresa_id INT,
    IN p_usuario_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(30);
    DECLARE v_almacen_id INT;
    DECLARE v_items INT;
    DECLARE done INT DEFAULT 0;
    DECLARE v_prod_id INT;
    DECLARE v_cantidad DECIMAL(10,2);
    DECLARE v_costo DECIMAL(15,4);
    DECLARE v_lote VARCHAR(50);
    DECLARE v_stock_actual DECIMAL(10,2);

    DECLARE cur CURSOR FOR
        SELECT producto_id, cantidad, costo_unitario, lote
        FROM movimiento_detalle WHERE movimiento_id = p_vale_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    SELECT estado, almacen_id INTO v_estado, v_almacen_id
    FROM movimientos_almacen
    WHERE id = p_vale_id AND empresa_id = p_empresa_id AND tipo_movimiento = 'salida';

    IF v_estado != 'borrador' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden completar vales en borrador';
    END IF;

    SELECT COUNT(*) INTO v_items FROM movimiento_detalle WHERE movimiento_id = p_vale_id;
    IF v_items = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El vale debe tener al menos un item';
    END IF;

    -- Validar stock y descontar
    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_prod_id, v_cantidad, v_costo, v_lote;
        IF done THEN LEAVE read_loop; END IF;

        -- Verificar stock suficiente
        SELECT COALESCE(SUM(cantidad), 0) INTO v_stock_actual
        FROM inventario
        WHERE empresa_id = p_empresa_id AND producto_id = v_prod_id AND almacen_id = v_almacen_id;

        IF v_stock_actual < v_cantidad THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Stock insuficiente para completar la salida';
        END IF;

        -- Descontar del inventario
        UPDATE inventario SET cantidad = cantidad - v_cantidad
        WHERE empresa_id = p_empresa_id AND producto_id = v_prod_id
          AND almacen_id = v_almacen_id AND lote = COALESCE(v_lote, 'DEFAULT');
    END LOOP;
    CLOSE cur;

    -- Marcar como completado
    UPDATE movimientos_almacen SET
        estado = 'completado', updated_by = p_usuario_id
    WHERE id = p_vale_id;

    SELECT 'completed' AS result;
END //


-- ============================================================================
-- LISTA UNIFICADA DE VALES
-- ============================================================================

CREATE PROCEDURE sp_vales_listar_unificado(
    IN p_empresa_id INT,
    IN p_tipo VARCHAR(10),
    IN p_almacen_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE,
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT 0;
    DECLARE v_limit INT DEFAULT 20;
    SET v_limit = IFNULL(p_per_page, 20);
    SET v_offset = (IFNULL(p_page, 1) - 1) * v_limit;

    SELECT
        ma.id, ma.numero_movimiento, ma.tipo_movimiento,
        ma.fecha_movimiento, ma.documento_referencia,
        ma.total_productos, ma.subtotal, ma.total, ma.estado,
        a.nombre AS almacen_nombre, a.codigo AS almacen_codigo,
        ca.nombre AS concepto_nombre,
        CASE
            WHEN ma.tipo_movimiento = 'ingreso' THEN p.razon_social
            ELSE ma.solicitante
        END AS proveedor_o_solicitante,
        ma.created_at
    FROM movimientos_almacen ma
    LEFT JOIN almacenes a ON ma.almacen_id = a.id
    LEFT JOIN conceptos_almacen ca ON ma.concepto_id = ca.id
    LEFT JOIN proveedores p ON ma.proveedor_id = p.id
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento IN ('ingreso', 'salida')
      AND ma.concepto_id IS NOT NULL
      AND (p_tipo IS NULL OR p_tipo = '' OR ma.tipo_movimiento = p_tipo)
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_fecha_desde IS NULL OR ma.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR ma.fecha_movimiento <= p_fecha_hasta)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.documento_referencia LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%')
           OR ma.solicitante LIKE CONCAT('%', p_search, '%'))
    ORDER BY ma.fecha_movimiento DESC, ma.id DESC
    LIMIT v_offset, v_limit;
END //


CREATE PROCEDURE sp_vales_contar_unificado(
    IN p_empresa_id INT,
    IN p_tipo VARCHAR(10),
    IN p_almacen_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE,
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM movimientos_almacen ma
    LEFT JOIN proveedores p ON ma.proveedor_id = p.id
    WHERE ma.empresa_id = p_empresa_id
      AND ma.tipo_movimiento IN ('ingreso', 'salida')
      AND ma.concepto_id IS NOT NULL
      AND (p_tipo IS NULL OR p_tipo = '' OR ma.tipo_movimiento = p_tipo)
      AND (p_almacen_id IS NULL OR ma.almacen_id = p_almacen_id)
      AND (p_fecha_desde IS NULL OR ma.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR ma.fecha_movimiento <= p_fecha_hasta)
      AND (p_search IS NULL OR p_search = ''
           OR ma.numero_movimiento LIKE CONCAT('%', p_search, '%')
           OR ma.documento_referencia LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%')
           OR ma.solicitante LIKE CONCAT('%', p_search, '%'));
END //


DELIMITER ;
