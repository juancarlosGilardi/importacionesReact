-- =============================================================================
-- Sprint 6: Requerimientos Internos — Stored Procedures
-- =============================================================================

DELIMITER //

-- =============================================================================
-- 6.1 sp_requerimiento_listar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_listar//
CREATE PROCEDURE sp_requerimiento_listar(
    IN p_empresa_id INT,
    IN p_estado VARCHAR(20),
    IN p_prioridad VARCHAR(10),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT (p_page - 1) * p_per_page;

    SELECT
        r.id,
        r.numero,
        r.fecha,
        r.solicitante,
        r.prioridad,
        r.estado,
        r.centro_costo,
        a.nombre AS almacen_nombre,
        a.codigo AS almacen_codigo,
        prov.razon_social AS proveedor_nombre,
        r.firmado_por,
        r.fecha_firma,
        COUNT(ri.id) AS total_items,
        COALESCE(SUM(ri.total), 0) AS valor_total,
        r.notas,
        r.created_at,
        r.updated_at
    FROM requerimientos r
    LEFT JOIN almacenes a ON a.id = r.almacen_id
    LEFT JOIN proveedores prov ON prov.id = r.proveedor_sugerido_id
    LEFT JOIN requerimiento_items ri ON ri.requerimiento_id = r.id
    WHERE r.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR r.estado = p_estado)
      AND (p_prioridad IS NULL OR r.prioridad = p_prioridad)
      AND (p_search IS NULL
           OR r.numero LIKE CONCAT('%', p_search, '%')
           OR r.solicitante LIKE CONCAT('%', p_search, '%')
           OR r.centro_costo LIKE CONCAT('%', p_search, '%')
      )
    GROUP BY r.id
    ORDER BY r.created_at DESC
    LIMIT v_offset, p_per_page;
END//


-- =============================================================================
-- 6.2 sp_requerimiento_contar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_contar//
CREATE PROCEDURE sp_requerimiento_contar(
    IN p_empresa_id INT,
    IN p_estado VARCHAR(20),
    IN p_prioridad VARCHAR(10),
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM requerimientos r
    WHERE r.empresa_id = p_empresa_id
      AND (p_estado IS NULL OR r.estado = p_estado)
      AND (p_prioridad IS NULL OR r.prioridad = p_prioridad)
      AND (p_search IS NULL
           OR r.numero LIKE CONCAT('%', p_search, '%')
           OR r.solicitante LIKE CONCAT('%', p_search, '%')
           OR r.centro_costo LIKE CONCAT('%', p_search, '%')
      );
END//


-- =============================================================================
-- 6.3 sp_requerimiento_obtener (multi-resultset: cabecera + items)
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_obtener//
CREATE PROCEDURE sp_requerimiento_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    -- Resultset 1: Cabecera
    SELECT
        r.id,
        r.numero,
        r.fecha,
        r.solicitante,
        r.prioridad,
        r.estado,
        r.centro_costo,
        r.almacen_id,
        a.nombre AS almacen_nombre,
        a.codigo AS almacen_codigo,
        r.proveedor_sugerido_id,
        prov.razon_social AS proveedor_nombre,
        r.moneda_id,
        r.tipo_cambio,
        r.firmado_por,
        r.fecha_firma,
        r.notas,
        r.created_by,
        r.created_at,
        r.updated_at
    FROM requerimientos r
    LEFT JOIN almacenes a ON a.id = r.almacen_id
    LEFT JOIN proveedores prov ON prov.id = r.proveedor_sugerido_id
    WHERE r.id = p_id AND r.empresa_id = p_empresa_id;

    -- Resultset 2: Items
    SELECT
        ri.id,
        ri.producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        ri.cantidad,
        ri.precio_estimado,
        ri.total,
        ri.notas
    FROM requerimiento_items ri
    INNER JOIN productos p ON p.id = ri.producto_id
    WHERE ri.requerimiento_id = p_id
    ORDER BY ri.id;
END//


-- =============================================================================
-- 6.4 sp_requerimiento_crear
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_crear//
CREATE PROCEDURE sp_requerimiento_crear(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_centro_costo VARCHAR(50),
    IN p_prioridad VARCHAR(10),
    IN p_proveedor_sugerido_id INT,
    IN p_solicitante VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT,
    IN p_created_by INT
)
BEGIN
    DECLARE v_numero VARCHAR(20);
    DECLARE v_nuevo_id INT;
    DECLARE v_ultimo INT;
    DECLARE v_anio INT DEFAULT YEAR(COALESCE(p_fecha, CURDATE()));

    -- Obtener siguiente correlativo
    SELECT ultimo_numero INTO v_ultimo
    FROM correlativos
    WHERE empresa_id = p_empresa_id AND tipo = 'requerimiento' AND anio = v_anio
    FOR UPDATE;

    IF v_ultimo IS NULL THEN
        INSERT INTO correlativos (empresa_id, tipo, prefijo, ultimo_numero, anio)
        VALUES (p_empresa_id, 'requerimiento', 'REQ', 1, v_anio);
        SET v_ultimo = 1;
    ELSE
        SET v_ultimo = v_ultimo + 1;
        UPDATE correlativos
        SET ultimo_numero = v_ultimo
        WHERE empresa_id = p_empresa_id AND tipo = 'requerimiento' AND anio = v_anio;
    END IF;

    SET v_numero = CONCAT('REQ-', v_anio, '-', LPAD(v_ultimo, 4, '0'));

    INSERT INTO requerimientos (
        empresa_id, numero, fecha, almacen_id, centro_costo,
        prioridad, proveedor_sugerido_id, solicitante, notas, created_by
    ) VALUES (
        p_empresa_id, v_numero, COALESCE(p_fecha, CURDATE()), p_almacen_id, p_centro_costo,
        COALESCE(p_prioridad, 'media'), p_proveedor_sugerido_id, p_solicitante, p_notas, p_created_by
    );

    SET v_nuevo_id = LAST_INSERT_ID();

    SELECT v_nuevo_id AS id, v_numero AS numero;
END//


-- =============================================================================
-- 6.5 sp_requerimiento_actualizar (solo estado abierto)
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_actualizar//
CREATE PROCEDURE sp_requerimiento_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_centro_costo VARCHAR(50),
    IN p_prioridad VARCHAR(10),
    IN p_proveedor_sugerido_id INT,
    IN p_solicitante VARCHAR(100),
    IN p_fecha DATE,
    IN p_notas TEXT
)
BEGIN
    DECLARE v_estado VARCHAR(20);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado != 'abierto' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden editar requerimientos en estado abierto';
    END IF;

    UPDATE requerimientos SET
        almacen_id = p_almacen_id,
        centro_costo = p_centro_costo,
        prioridad = COALESCE(p_prioridad, prioridad),
        proveedor_sugerido_id = p_proveedor_sugerido_id,
        solicitante = COALESCE(p_solicitante, solicitante),
        fecha = COALESCE(p_fecha, fecha),
        notas = p_notas
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'actualizado' AS status;
END//


-- =============================================================================
-- 6.6 sp_requerimiento_item_agregar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_item_agregar//
CREATE PROCEDURE sp_requerimiento_item_agregar(
    IN p_requerimiento_id INT,
    IN p_empresa_id INT,
    IN p_producto_id INT,
    IN p_cantidad DECIMAL(15,4),
    IN p_precio_estimado DECIMAL(15,4),
    IN p_notas VARCHAR(255)
)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_total DECIMAL(15,4);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_requerimiento_id AND empresa_id = p_empresa_id;

    IF v_estado != 'abierto' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden agregar items a requerimientos abiertos';
    END IF;

    SET v_total = p_cantidad * COALESCE(p_precio_estimado, 0);

    INSERT INTO requerimiento_items (requerimiento_id, producto_id, cantidad, precio_estimado, total, notas)
    VALUES (p_requerimiento_id, p_producto_id, p_cantidad, COALESCE(p_precio_estimado, 0), v_total, p_notas);

    SELECT LAST_INSERT_ID() AS id, v_total AS total;
END//


-- =============================================================================
-- 6.7 sp_requerimiento_item_eliminar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_item_eliminar//
CREATE PROCEDURE sp_requerimiento_item_eliminar(
    IN p_requerimiento_id INT,
    IN p_item_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_requerimiento_id AND empresa_id = p_empresa_id;

    IF v_estado != 'abierto' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden eliminar items de requerimientos abiertos';
    END IF;

    DELETE FROM requerimiento_items WHERE id = p_item_id AND requerimiento_id = p_requerimiento_id;

    SELECT p_item_id AS id, 'eliminado' AS status;
END//


-- =============================================================================
-- 6.8 sp_requerimiento_firmar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_firmar//
CREATE PROCEDURE sp_requerimiento_firmar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_firmado_por VARCHAR(100)
)
BEGIN
    DECLARE v_estado VARCHAR(20);
    DECLARE v_items INT;

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado != 'abierto' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden firmar requerimientos en estado abierto';
    END IF;

    SELECT COUNT(*) INTO v_items FROM requerimiento_items WHERE requerimiento_id = p_id;

    IF v_items = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No se puede firmar un requerimiento sin items';
    END IF;

    UPDATE requerimientos SET
        estado = 'firmado',
        firmado_por = p_firmado_por,
        fecha_firma = NOW()
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'firmado' AS status;
END//


-- =============================================================================
-- 6.9 sp_requerimiento_derivar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_derivar//
CREATE PROCEDURE sp_requerimiento_derivar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado != 'firmado' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden derivar requerimientos firmados';
    END IF;

    UPDATE requerimientos SET estado = 'derivado'
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'derivado' AS status;
END//


-- =============================================================================
-- 6.10 sp_requerimiento_cerrar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_cerrar//
CREATE PROCEDURE sp_requerimiento_cerrar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado NOT IN ('firmado', 'derivado') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden cerrar requerimientos firmados o derivados';
    END IF;

    UPDATE requerimientos SET estado = 'cerrado'
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'cerrado' AS status;
END//


-- =============================================================================
-- 6.11 sp_requerimiento_eliminar (solo abierto)
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_requerimiento_eliminar//
CREATE PROCEDURE sp_requerimiento_eliminar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    DECLARE v_estado VARCHAR(20);

    SELECT estado INTO v_estado FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    IF v_estado != 'abierto' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Solo se pueden eliminar requerimientos en estado abierto';
    END IF;

    -- Items se eliminan por CASCADE
    DELETE FROM requerimientos WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'eliminado' AS status;
END//

DELIMITER ;
