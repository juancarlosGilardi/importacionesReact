-- =============================================================================
-- Sprint 7: Stock Avanzado + Alertas + Inventario Valorizado
-- =============================================================================

DELIMITER //

-- =============================================================================
-- 7.1 sp_stock_resumen
-- Resumen general: total productos, items inventario, valor total, almacenes
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_stock_resumen//
CREATE PROCEDURE sp_stock_resumen(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        (SELECT COUNT(*) FROM productos WHERE empresa_id = p_empresa_id AND status = 'active') AS total_productos,
        (SELECT COUNT(*) FROM inventario WHERE empresa_id = p_empresa_id AND cantidad > 0) AS items_con_stock,
        (SELECT COALESCE(SUM(cantidad * costo_unitario), 0) FROM inventario WHERE empresa_id = p_empresa_id AND cantidad > 0) AS valor_total_inventario,
        (SELECT COUNT(*) FROM almacenes WHERE empresa_id = p_empresa_id AND status = 'active') AS almacenes_activos,
        (SELECT COUNT(DISTINCT producto_id) FROM inventario WHERE empresa_id = p_empresa_id AND cantidad > 0) AS productos_con_stock,
        (SELECT COUNT(*) FROM productos p WHERE p.empresa_id = p_empresa_id AND p.status = 'active'
            AND NOT EXISTS (SELECT 1 FROM inventario i WHERE i.producto_id = p.id AND i.empresa_id = p_empresa_id AND i.cantidad > 0)
        ) AS productos_sin_stock;
END//


-- =============================================================================
-- 7.2 sp_stock_por_almacen
-- Stock agrupado por almacen con valor total
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_stock_por_almacen//
CREATE PROCEDURE sp_stock_por_almacen(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        a.id AS almacen_id,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        a.responsable,
        COUNT(DISTINCT i.producto_id) AS total_productos,
        COALESCE(SUM(i.cantidad), 0) AS total_cantidad,
        COALESCE(SUM(i.cantidad * i.costo_unitario), 0) AS valor_total
    FROM almacenes a
    LEFT JOIN inventario i ON i.almacen_id = a.id AND i.empresa_id = a.empresa_id AND i.cantidad > 0
    WHERE a.empresa_id = p_empresa_id
      AND a.status = 'active'
    GROUP BY a.id, a.codigo, a.nombre, a.responsable
    ORDER BY valor_total DESC;
END//


-- =============================================================================
-- 7.3 sp_alertas_stock
-- Productos bajo punto_reposicion con nivel de criticidad
-- Critico: cantidad <= stock_minimo (o 0)
-- Bajo: cantidad > stock_minimo AND cantidad <= punto_reposicion
-- Normal: cantidad > punto_reposicion
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_alertas_stock//
CREATE PROCEDURE sp_alertas_stock(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_nivel VARCHAR(20),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT (p_page - 1) * p_per_page;

    SELECT
        p.id AS producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        cat.nombre AS categoria_nombre,
        COALESCE(p.stock_minimo, 0) AS stock_minimo,
        COALESCE(p.punto_reposicion, 0) AS punto_reposicion,
        COALESCE(stock_calc.stock_actual, 0) AS stock_actual,
        COALESCE(stock_calc.valor_stock, 0) AS valor_stock,
        CASE
            WHEN COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.stock_minimo, 0) THEN 'critico'
            WHEN COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.punto_reposicion, 0) THEN 'bajo'
            ELSE 'normal'
        END AS nivel_alerta,
        COALESCE(p.punto_reposicion, 0) - COALESCE(stock_calc.stock_actual, 0) AS cantidad_reponer
    FROM productos p
    LEFT JOIN categorias_producto cat ON cat.id = p.categoria_id
    LEFT JOIN (
        SELECT
            producto_id,
            SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad ELSE 0 END) AS stock_actual,
            SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad * costo_unitario ELSE 0 END) AS valor_stock
        FROM inventario
        WHERE empresa_id = p_empresa_id
        GROUP BY producto_id
    ) stock_calc ON stock_calc.producto_id = p.id
    WHERE p.empresa_id = p_empresa_id
      AND p.status = 'active'
      AND COALESCE(p.punto_reposicion, 0) > 0
      AND COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.punto_reposicion, 0)
      AND (p_nivel IS NULL
           OR (p_nivel = 'critico' AND COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.stock_minimo, 0))
           OR (p_nivel = 'bajo' AND COALESCE(stock_calc.stock_actual, 0) > COALESCE(p.stock_minimo, 0)
                                 AND COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.punto_reposicion, 0))
      )
      AND (p_search IS NULL
           OR p.sku LIKE CONCAT('%', p_search, '%')
           OR p.nombre LIKE CONCAT('%', p_search, '%')
      )
    ORDER BY
        CASE
            WHEN COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.stock_minimo, 0) THEN 1
            ELSE 2
        END,
        stock_calc.stock_actual ASC
    LIMIT v_offset, p_per_page;
END//


-- =============================================================================
-- 7.4 sp_alertas_stock_resumen
-- Conteo de alertas por nivel + valor en riesgo
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_alertas_stock_resumen//
CREATE PROCEDURE sp_alertas_stock_resumen(
    IN p_empresa_id INT,
    IN p_almacen_id INT
)
BEGIN
    SELECT
        COUNT(*) AS total_alertas,
        SUM(CASE
            WHEN COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.stock_minimo, 0) THEN 1
            ELSE 0
        END) AS alertas_criticas,
        SUM(CASE
            WHEN COALESCE(stock_calc.stock_actual, 0) > COALESCE(p.stock_minimo, 0)
             AND COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.punto_reposicion, 0) THEN 1
            ELSE 0
        END) AS alertas_bajas,
        COALESCE(SUM(
            (COALESCE(p.punto_reposicion, 0) - COALESCE(stock_calc.stock_actual, 0))
            * COALESCE(stock_calc.costo_promedio, 0)
        ), 0) AS valor_reposicion_estimado
    FROM productos p
    LEFT JOIN (
        SELECT
            producto_id,
            SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad ELSE 0 END) AS stock_actual,
            CASE
                WHEN SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad ELSE 0 END) > 0
                THEN SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad * costo_unitario ELSE 0 END)
                     / SUM(CASE WHEN (p_almacen_id IS NULL OR almacen_id = p_almacen_id) THEN cantidad ELSE 0 END)
                ELSE 0
            END AS costo_promedio
        FROM inventario
        WHERE empresa_id = p_empresa_id
        GROUP BY producto_id
    ) stock_calc ON stock_calc.producto_id = p.id
    WHERE p.empresa_id = p_empresa_id
      AND p.status = 'active'
      AND COALESCE(p.punto_reposicion, 0) > 0
      AND COALESCE(stock_calc.stock_actual, 0) <= COALESCE(p.punto_reposicion, 0);
END//


-- =============================================================================
-- 7.5 sp_inventario_valorizado
-- Inventario valorizado completo con conversion de moneda
-- p_moneda: 'PEN' o 'USD'
-- p_tipo_cambio: tipo de cambio PEN/USD (ej: 3.75)
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_inventario_valorizado//
CREATE PROCEDURE sp_inventario_valorizado(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_categoria_id INT,
    IN p_moneda VARCHAR(3),
    IN p_tipo_cambio DECIMAL(10,4),
    IN p_search VARCHAR(100),
    IN p_page INT,
    IN p_per_page INT
)
BEGIN
    DECLARE v_offset INT DEFAULT (p_page - 1) * p_per_page;
    DECLARE v_tc DECIMAL(10,4) DEFAULT COALESCE(p_tipo_cambio, 3.7500);

    SELECT
        p.id AS producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        cat.nombre AS categoria_nombre,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        i.cantidad,
        i.costo_unitario AS costo_unitario_pen,
        i.cantidad * i.costo_unitario AS valor_total_pen,
        CASE
            WHEN p_moneda = 'USD' THEN ROUND(i.costo_unitario / v_tc, 4)
            ELSE i.costo_unitario
        END AS costo_unitario_moneda,
        CASE
            WHEN p_moneda = 'USD' THEN ROUND(i.cantidad * i.costo_unitario / v_tc, 2)
            ELSE i.cantidad * i.costo_unitario
        END AS valor_total_moneda,
        p_moneda AS moneda,
        i.lote,
        i.fecha_ultimo_movimiento
    FROM inventario i
    INNER JOIN productos p ON p.id = i.producto_id
    LEFT JOIN categorias_producto cat ON cat.id = p.categoria_id
    INNER JOIN almacenes a ON a.id = i.almacen_id
    WHERE i.empresa_id = p_empresa_id
      AND i.cantidad > 0
      AND (p_almacen_id IS NULL OR i.almacen_id = p_almacen_id)
      AND (p_categoria_id IS NULL OR p.categoria_id = p_categoria_id)
      AND (p_search IS NULL
           OR p.sku LIKE CONCAT('%', p_search, '%')
           OR p.nombre LIKE CONCAT('%', p_search, '%')
      )
    ORDER BY valor_total_pen DESC
    LIMIT v_offset, p_per_page;
END//


-- =============================================================================
-- 7.5b sp_inventario_valorizado_contar
-- COUNT para paginacion del valorizado
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_inventario_valorizado_contar//
CREATE PROCEDURE sp_inventario_valorizado_contar(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_categoria_id INT,
    IN p_search VARCHAR(100)
)
BEGIN
    SELECT COUNT(*) AS total
    FROM inventario i
    INNER JOIN productos p ON p.id = i.producto_id
    WHERE i.empresa_id = p_empresa_id
      AND i.cantidad > 0
      AND (p_almacen_id IS NULL OR i.almacen_id = p_almacen_id)
      AND (p_categoria_id IS NULL OR p.categoria_id = p_categoria_id)
      AND (p_search IS NULL
           OR p.sku LIKE CONCAT('%', p_search, '%')
           OR p.nombre LIKE CONCAT('%', p_search, '%')
      );
END//


-- =============================================================================
-- 7.6 sp_inventario_valorizado_por_familia
-- Agrupado por categoria con porcentajes
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_inventario_valorizado_por_familia//
CREATE PROCEDURE sp_inventario_valorizado_por_familia(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_moneda VARCHAR(3),
    IN p_tipo_cambio DECIMAL(10,4)
)
BEGIN
    DECLARE v_tc DECIMAL(10,4) DEFAULT COALESCE(p_tipo_cambio, 3.7500);
    DECLARE v_total_general DECIMAL(15,2);

    -- Calcular total general
    SELECT COALESCE(SUM(i.cantidad * i.costo_unitario), 0) INTO v_total_general
    FROM inventario i
    WHERE i.empresa_id = p_empresa_id
      AND i.cantidad > 0
      AND (p_almacen_id IS NULL OR i.almacen_id = p_almacen_id);

    -- Retornar por familia/categoria
    SELECT
        COALESCE(cat.id, 0) AS categoria_id,
        COALESCE(cat.nombre, 'Sin Categoria') AS categoria_nombre,
        COUNT(DISTINCT i.producto_id) AS total_productos,
        SUM(i.cantidad) AS total_cantidad,
        SUM(i.cantidad * i.costo_unitario) AS valor_total_pen,
        CASE
            WHEN p_moneda = 'USD' THEN ROUND(SUM(i.cantidad * i.costo_unitario) / v_tc, 2)
            ELSE SUM(i.cantidad * i.costo_unitario)
        END AS valor_total_moneda,
        CASE
            WHEN v_total_general > 0
            THEN ROUND(SUM(i.cantidad * i.costo_unitario) / v_total_general * 100, 2)
            ELSE 0
        END AS porcentaje,
        p_moneda AS moneda,
        v_total_general AS total_general_pen,
        CASE
            WHEN p_moneda = 'USD' THEN ROUND(v_total_general / v_tc, 2)
            ELSE v_total_general
        END AS total_general_moneda
    FROM inventario i
    INNER JOIN productos p ON p.id = i.producto_id
    LEFT JOIN categorias_producto cat ON cat.id = p.categoria_id
    WHERE i.empresa_id = p_empresa_id
      AND i.cantidad > 0
      AND (p_almacen_id IS NULL OR i.almacen_id = p_almacen_id)
    GROUP BY COALESCE(cat.id, 0), COALESCE(cat.nombre, 'Sin Categoria')
    ORDER BY valor_total_pen DESC;
END//

DELIMITER ;
