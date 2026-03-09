-- =============================================================================
-- Sprint 8: Toma de Inventario Fisico — Stored Procedures
-- =============================================================================

DELIMITER //

-- =============================================================================
-- 8.1 sp_toma_inventario_listar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_listar//
CREATE PROCEDURE sp_toma_inventario_listar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT (p_page - 1) * p_per_page;

    SELECT
        t.id,
        t.numero,
        t.almacen_id,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        t.fecha_inicio,
        t.fecha_fin,
        t.responsable,
        t.estado,
        t.notas,
        COUNT(ti.id) AS total_items,
        SUM(CASE WHEN ti.stock_contado IS NOT NULL THEN 1 ELSE 0 END) AS items_contados,
        SUM(CASE WHEN ti.diferencia != 0 THEN 1 ELSE 0 END) AS items_con_diferencia,
        t.created_at,
        t.updated_at
    FROM toma_inventario t
    INNER JOIN almacenes a ON a.id = t.almacen_id
    LEFT JOIN toma_inventario_items ti ON ti.toma_id = t.id
    WHERE t.empresa_id = p_empresa_id
      AND (p_almacen_id IS NULL OR t.almacen_id = p_almacen_id)
      AND (p_estado IS NULL OR t.estado = p_estado)
      AND (p_search IS NULL
           OR t.numero LIKE CONCAT('%', p_search, '%')
           OR t.responsable LIKE CONCAT('%', p_search, '%')
      )
    GROUP BY t.id
    ORDER BY t.created_at DESC
    LIMIT v_offset, p_per_page;
END//


-- =============================================================================
-- 8.1b sp_toma_inventario_contar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_contar//
CREATE PROCEDURE sp_toma_inventario_contar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_estado VARCHAR(20),
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM toma_inventario t
    WHERE t.empresa_id = p_empresa_id
      AND (p_almacen_id IS NULL OR t.almacen_id = p_almacen_id)
      AND (p_estado IS NULL OR t.estado = p_estado)
      AND (p_search IS NULL
           OR t.numero LIKE CONCAT('%', p_search, '%')
           OR t.responsable LIKE CONCAT('%', p_search, '%')
      );
END//


-- =============================================================================
-- 8.2 sp_toma_inventario_obtener (multi-resultset)
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_obtener//
CREATE PROCEDURE sp_toma_inventario_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Resultset 1: Cabecera
    SELECT
        t.id,
        t.numero,
        t.almacen_id,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        t.fecha_inicio,
        t.fecha_fin,
        t.responsable,
        t.estado,
        t.notas,
        t.created_by,
        t.created_at,
        t.updated_at
    FROM toma_inventario t
    INNER JOIN almacenes a ON a.id = t.almacen_id
    WHERE t.id = p_id AND t.empresa_id = p_empresa_id;

    -- Resultset 2: Items con producto info
    SELECT
        ti.id,
        ti.producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        ti.stock_sistema,
        ti.stock_contado,
        ti.diferencia,
        ti.observacion
    FROM toma_inventario_items ti
    INNER JOIN productos p ON p.id = ti.producto_id
    WHERE ti.toma_id = p_id
    ORDER BY p.sku;
END//


-- =============================================================================
-- 8.3 sp_toma_inventario_crear
-- Genera items automaticamente desde el inventario actual del almacen
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_crear//
CREATE PROCEDURE sp_toma_inventario_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_responsable VARCHAR(100),
    IN p_fecha_inicio DATE,
    IN p_notas TEXT,
    IN p_created_by INT
)
BEGIN
    DECLARE v_numero VARCHAR(20);
    DECLARE v_nuevo_id INT;
    DECLARE v_ultimo INT;
    DECLARE v_anio INT DEFAULT YEAR(COALESCE(p_fecha_inicio, CURDATE()));
    DECLARE v_items_count INT;

    -- Obtener siguiente correlativo
    SELECT ultimo_numero INTO v_ultimo
    FROM correlativos
    WHERE empresa_id = p_empresa_id AND tipo = 'toma_inventario' AND anio = v_anio
    FOR UPDATE;

    IF v_ultimo IS NULL THEN
        INSERT INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio)
        VALUES (p_empresa_id, 'toma_inventario', 'TIF', 1, v_anio);
        SET v_ultimo = 1;
    ELSE
        SET v_ultimo = v_ultimo + 1;
        UPDATE correlativos
        SET ultimo_numero = v_ultimo
        WHERE empresa_id = p_empresa_id AND tipo = 'toma_inventario' AND anio = v_anio;
    END IF;

    SET v_numero = CONCAT('TIF-', v_anio, '-', LPAD(v_ultimo, 4, '0'));

    -- Crear cabecera
    INSERT INTO toma_inventario (
        empresa_id, numero, almacen_id, fecha_inicio, responsable, notas, created_by
    ) VALUES (
        p_empresa_id, v_numero, p_almacen_id,
        COALESCE(p_fecha_inicio, CURDATE()), p_responsable, p_notas, p_created_by
    );

    SET v_nuevo_id = LAST_INSERT_ID();

    -- Generar items desde inventario actual del almacen
    INSERT INTO toma_inventario_items (toma_id, producto_id, stock_sistema, stock_contado, diferencia)
    SELECT
        v_nuevo_id,
        i.producto_id,
        SUM(i.cantidad),
        NULL,
        0
    FROM inventario i
    WHERE i.empresa_id = p_empresa_id
      AND i.almacen_id = p_almacen_id
      AND i.cantidad > 0
    GROUP BY i.producto_id;

    SELECT COUNT(*) INTO v_items_count FROM toma_inventario_items WHERE toma_id = v_nuevo_id;

    -- Si no hay stock, agregar todos los productos activos con stock_sistema = 0
    IF v_items_count = 0 THEN
        INSERT INTO toma_inventario_items (toma_id, producto_id, stock_sistema, stock_contado, diferencia)
        SELECT
            v_nuevo_id,
            p.id,
            0,
            NULL,
            0
        FROM productos p
        WHERE p.empresa_id = p_empresa_id AND p.status = 'active';

        SELECT COUNT(*) INTO v_items_count FROM toma_inventario_items WHERE toma_id = v_nuevo_id;
    END IF;

    SELECT v_nuevo_id AS id, v_numero AS numero, v_items_count AS total_items;
END//


-- =============================================================================
-- 8.4 sp_toma_inventario_actualizar_items
-- Actualiza stock_contado y calcula diferencia para un item
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_actualizar_item//
CREATE PROCEDURE sp_toma_inventario_actualizar_item(
    IN p_toma_id INT,
    IN p_item_id INT,
    IN p_empresa_id INT,
    IN p_stock_contado DECIMAL(15,4),
    IN p_observacion VARCHAR(255)
)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_stock_sistema DECIMAL(15,4);

    SELECT estado INTO v_estado FROM toma_inventario WHERE id = p_toma_id AND empresa_id = p_empresa_id;

    IF v_estado NOT IN ('pendiente', 'en_proceso') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden actualizar tomas pendientes o en proceso';
    END IF;

    -- Cambiar a en_proceso si esta pendiente
    IF v_estado = 'pendiente' THEN
        UPDATE toma_inventario SET estado = 'en_proceso' WHERE id = p_toma_id;
    END IF;

    -- Obtener stock_sistema
    SELECT stock_sistema INTO v_stock_sistema
    FROM toma_inventario_items WHERE id = p_item_id AND toma_id = p_toma_id;

    -- Actualizar item
    UPDATE toma_inventario_items SET
        stock_contado = p_stock_contado,
        diferencia = p_stock_contado - v_stock_sistema,
        observacion = p_observacion
    WHERE id = p_item_id AND toma_id = p_toma_id;

    SELECT p_item_id AS id, p_stock_contado AS stock_contado, (p_stock_contado - v_stock_sistema) AS diferencia;
END//


-- =============================================================================
-- 8.5 sp_toma_inventario_completar
-- Valida que todos los items esten contados
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_completar//
CREATE PROCEDURE sp_toma_inventario_completar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_sin_contar INT;

    SELECT estado INTO v_estado FROM toma_inventario WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado NOT IN ('pendiente', 'en_proceso') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden completar tomas pendientes o en proceso';
    END IF;

    -- Verificar que todos los items fueron contados
    SELECT COUNT(*) INTO v_sin_contar
    FROM toma_inventario_items
    WHERE toma_id = p_id AND stock_contado IS NULL;

    IF v_sin_contar > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Hay items sin contar. Complete todos los conteos antes de finalizar.';
    END IF;

    UPDATE toma_inventario SET
        estado = 'completado',
        fecha_fin = CURDATE()
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'completado' AS status;
END//


-- =============================================================================
-- 8.6 sp_toma_inventario_regularizar
-- Genera vales de ajuste automaticos:
--   - Sobrantes (diferencia > 0) → vale ingreso con concepto "Sobrantes"
--   - Faltantes (diferencia < 0) → vale salida con concepto "Faltantes"
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_toma_inventario_regularizar//
CREATE PROCEDURE sp_toma_inventario_regularizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_user_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_almacen_id INT;
    DECLARE v_concepto_sobrantes INT;
    DECLARE v_concepto_faltantes INT;
    DECLARE v_sobrantes_count INT DEFAULT 0;
    DECLARE v_faltantes_count INT DEFAULT 0;
    DECLARE v_vale_ingreso_id INT DEFAULT NULL;
    DECLARE v_vale_salida_id INT DEFAULT NULL;

    SELECT estado, almacen_id INTO v_estado, v_almacen_id
    FROM toma_inventario WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado != 'completado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden regularizar tomas completadas';
    END IF;

    -- Buscar conceptos de sobrantes y faltantes
    SELECT id INTO v_concepto_sobrantes
    FROM conceptos_almacen
    WHERE empresa_id = p_empresa_id AND codigo = 'ING-SOB' AND tipo = 'ingreso'
    LIMIT 1;

    SELECT id INTO v_concepto_faltantes
    FROM conceptos_almacen
    WHERE empresa_id = p_empresa_id AND codigo = 'SAL-FAL' AND tipo = 'salida'
    LIMIT 1;

    -- Contar sobrantes y faltantes
    SELECT COUNT(*) INTO v_sobrantes_count
    FROM toma_inventario_items WHERE toma_id = p_id AND diferencia > 0;

    SELECT COUNT(*) INTO v_faltantes_count
    FROM toma_inventario_items WHERE toma_id = p_id AND diferencia < 0;

    -- Crear vale de ingreso para sobrantes
    IF v_sobrantes_count > 0 AND v_concepto_sobrantes IS NOT NULL THEN
        INSERT INTO movimientos_almacen (
            empresa_id, tipo_movimiento, almacen_id, concepto_id,
            documento_referencia, fecha_movimiento, notas, estado, created_by
        ) VALUES (
            p_empresa_id, 'ingreso', v_almacen_id, v_concepto_sobrantes,
            CONCAT('Regularizacion TIF #', p_id), CURDATE(),
            CONCAT('Ajuste por sobrantes - Toma de inventario #', p_id),
            'borrador', p_user_id
        );
        SET v_vale_ingreso_id = LAST_INSERT_ID();

        -- Agregar items sobrantes
        INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total)
        SELECT
            v_vale_ingreso_id,
            ti.producto_id,
            ti.diferencia,
            COALESCE(
                (SELECT i.costo_unitario FROM inventario i
                 WHERE i.producto_id = ti.producto_id AND i.almacen_id = v_almacen_id AND i.empresa_id = p_empresa_id
                 LIMIT 1),
                0
            ),
            ti.diferencia * COALESCE(
                (SELECT i.costo_unitario FROM inventario i
                 WHERE i.producto_id = ti.producto_id AND i.almacen_id = v_almacen_id AND i.empresa_id = p_empresa_id
                 LIMIT 1),
                0
            )
        FROM toma_inventario_items ti
        WHERE ti.toma_id = p_id AND ti.diferencia > 0;
    END IF;

    -- Crear vale de salida para faltantes
    IF v_faltantes_count > 0 AND v_concepto_faltantes IS NOT NULL THEN
        INSERT INTO movimientos_almacen (
            empresa_id, tipo_movimiento, almacen_id, concepto_id,
            documento_referencia, fecha_movimiento, notas, estado, created_by
        ) VALUES (
            p_empresa_id, 'salida', v_almacen_id, v_concepto_faltantes,
            CONCAT('Regularizacion TIF #', p_id), CURDATE(),
            CONCAT('Ajuste por faltantes - Toma de inventario #', p_id),
            'borrador', p_user_id
        );
        SET v_vale_salida_id = LAST_INSERT_ID();

        -- Agregar items faltantes (cantidad positiva, la diferencia es negativa)
        INSERT INTO movimiento_detalle (movimiento_id, producto_id, cantidad, costo_unitario, costo_total)
        SELECT
            v_vale_salida_id,
            ti.producto_id,
            ABS(ti.diferencia),
            COALESCE(
                (SELECT i.costo_unitario FROM inventario i
                 WHERE i.producto_id = ti.producto_id AND i.almacen_id = v_almacen_id AND i.empresa_id = p_empresa_id
                 LIMIT 1),
                0
            ),
            ABS(ti.diferencia) * COALESCE(
                (SELECT i.costo_unitario FROM inventario i
                 WHERE i.producto_id = ti.producto_id AND i.almacen_id = v_almacen_id AND i.empresa_id = p_empresa_id
                 LIMIT 1),
                0
            )
        FROM toma_inventario_items ti
        WHERE ti.toma_id = p_id AND ti.diferencia < 0;
    END IF;

    -- Marcar toma como regularizada
    UPDATE toma_inventario SET estado = 'regularizado'
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT
        p_id AS id,
        'regularizado' AS status,
        v_sobrantes_count AS sobrantes,
        v_faltantes_count AS faltantes,
        v_vale_ingreso_id AS vale_ingreso_id,
        v_vale_salida_id AS vale_salida_id;
END//

DELIMITER ;
