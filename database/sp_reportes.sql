-- =============================================================================
-- Sprint 9: Reportes Avanzados — Stored Procedures
-- =============================================================================

DELIMITER //

-- =============================================================================
-- 9.1 sp_reporte_inventario_resumen
-- Totales generales, top 10 por valor, productos sin stock
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_inventario_resumen//
CREATE PROCEDURE sp_reporte_inventario_resumen(
    IN p_empresa_id INT
)
BEGIN
    -- Resultset 1: Resumen general
    SELECT
        (SELECT COUNT(*) FROM productos WHERE empresa_id = p_empresa_id AND status = 'active') AS total_productos,
        (SELECT COUNT(DISTINCT i.producto_id) FROM inventario i WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0) AS productos_con_stock,
        (SELECT COUNT(*)
         FROM productos p
         WHERE p.empresa_id = p_empresa_id AND p.status = 'active'
           AND p.id NOT IN (SELECT DISTINCT producto_id FROM inventario WHERE empresa_id = p_empresa_id AND cantidad > 0)
        ) AS productos_sin_stock,
        (SELECT COUNT(DISTINCT i.almacen_id) FROM inventario i WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0) AS almacenes_con_stock,
        COALESCE((SELECT SUM(i.cantidad * i.costo_unitario) FROM inventario i WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0), 0) AS valor_total_inventario,
        COALESCE((SELECT SUM(i.cantidad) FROM inventario i WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0), 0) AS total_unidades;

    -- Resultset 2: Top 10 productos por valor
    SELECT
        p.id AS producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        COALESCE(cp.nombre, 'Sin categoria') AS categoria_nombre,
        SUM(i.cantidad) AS stock_total,
        ROUND(AVG(i.costo_unitario), 4) AS costo_promedio,
        SUM(i.cantidad * i.costo_unitario) AS valor_total
    FROM inventario i
    INNER JOIN productos p ON p.id = i.producto_id
    LEFT JOIN categorias_producto cp ON cp.id = p.categoria_id
    WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0
    GROUP BY p.id, p.sku, p.nombre, p.unidad_medida, cp.nombre
    ORDER BY valor_total DESC
    LIMIT 10;

    -- Resultset 3: Resumen por familia/categoria
    SELECT
        COALESCE(cp.id, 0) AS categoria_id,
        COALESCE(cp.nombre, 'Sin categoria') AS categoria_nombre,
        COUNT(DISTINCT i.producto_id) AS total_productos,
        SUM(i.cantidad) AS total_cantidad,
        SUM(i.cantidad * i.costo_unitario) AS valor_total,
        ROUND(
            SUM(i.cantidad * i.costo_unitario) * 100.0 /
            NULLIF((SELECT SUM(i2.cantidad * i2.costo_unitario) FROM inventario i2 WHERE i2.empresa_id = p_empresa_id AND i2.cantidad > 0), 0),
            2
        ) AS porcentaje
    FROM inventario i
    INNER JOIN productos p ON p.id = i.producto_id
    LEFT JOIN categorias_producto cp ON cp.id = p.categoria_id
    WHERE i.empresa_id = p_empresa_id AND i.cantidad > 0
    GROUP BY cp.id, cp.nombre
    ORDER BY valor_total DESC;
END//


-- =============================================================================
-- 9.2 sp_reporte_inventario_movimientos
-- Movimientos por rango fecha con desglose almacen
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_inventario_movimientos//
CREATE PROCEDURE sp_reporte_inventario_movimientos(
    IN p_empresa_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE,
    IN p_almacen_id INT
)
BEGIN
    -- Resultset 1: Resumen de movimientos
    SELECT
        COUNT(*) AS total_movimientos,
        SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN 1 ELSE 0 END) AS total_ingresos,
        SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN 1 ELSE 0 END) AS total_salidas,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN m.valor_total ELSE 0 END), 0) AS valor_ingresos,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN m.valor_total ELSE 0 END), 0) AS valor_salidas,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN m.valor_total ELSE 0 END), 0)
        - COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN m.valor_total ELSE 0 END), 0) AS balance_neto
    FROM movimientos_almacen m
    WHERE m.empresa_id = p_empresa_id
      AND m.estado IN ('completado', 'confirmado')
      AND (p_fecha_desde IS NULL OR m.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR m.fecha_movimiento <= p_fecha_hasta)
      AND (p_almacen_id IS NULL OR m.almacen_id = p_almacen_id);

    -- Resultset 2: Detalle de movimientos
    SELECT
        m.id,
        m.numero_movimiento,
        m.tipo_movimiento,
        m.fecha_movimiento,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        COALESCE(ca.nombre, m.documento_referencia) AS concepto,
        m.total_productos,
        m.valor_total,
        m.estado,
        m.notas
    FROM movimientos_almacen m
    LEFT JOIN almacenes a ON a.id = m.almacen_id
    LEFT JOIN conceptos_almacen ca ON ca.id = m.concepto_id
    WHERE m.empresa_id = p_empresa_id
      AND m.estado IN ('completado', 'confirmado')
      AND (p_fecha_desde IS NULL OR m.fecha_movimiento >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR m.fecha_movimiento <= p_fecha_hasta)
      AND (p_almacen_id IS NULL OR m.almacen_id = p_almacen_id)
    ORDER BY m.fecha_movimiento DESC, m.id DESC
    LIMIT 200;
END//


-- =============================================================================
-- 9.3 sp_reporte_inventario_rotacion
-- Indice de rotacion por producto
-- Rotacion = Cantidad salidas (periodo) / Stock promedio
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_inventario_rotacion//
CREATE PROCEDURE sp_reporte_inventario_rotacion(
    IN p_empresa_id INT,
    IN p_meses INT
)
BEGIN
    DECLARE v_fecha_desde DATE;
    SET v_fecha_desde = DATE_SUB(CURDATE(), INTERVAL COALESCE(p_meses, 12) MONTH);

    SELECT
        p.id AS producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        p.unidad_medida,
        COALESCE(cp.nombre, 'Sin categoria') AS categoria_nombre,
        -- Stock actual
        COALESCE(inv.stock_actual, 0) AS stock_actual,
        COALESCE(inv.valor_stock, 0) AS valor_stock,
        -- Salidas en periodo
        COALESCE(sal.total_salidas, 0) AS total_salidas,
        COALESCE(sal.valor_salidas, 0) AS valor_salidas,
        -- Ingresos en periodo
        COALESCE(ing.total_ingresos, 0) AS total_ingresos,
        -- Indice de rotacion
        CASE
            WHEN COALESCE(inv.stock_actual, 0) > 0
            THEN ROUND(COALESCE(sal.total_salidas, 0) / inv.stock_actual, 2)
            ELSE 0
        END AS indice_rotacion,
        -- Clasificacion
        CASE
            WHEN COALESCE(inv.stock_actual, 0) = 0 THEN 'sin_stock'
            WHEN COALESCE(sal.total_salidas, 0) = 0 THEN 'sin_movimiento'
            WHEN (COALESCE(sal.total_salidas, 0) / inv.stock_actual) < 1.0 THEN 'lenta'
            WHEN (COALESCE(sal.total_salidas, 0) / inv.stock_actual) < 3.0 THEN 'media'
            ELSE 'alta'
        END AS clasificacion
    FROM productos p
    LEFT JOIN categorias_producto cp ON cp.id = p.categoria_id
    LEFT JOIN (
        SELECT producto_id, SUM(cantidad) AS stock_actual, SUM(cantidad * costo_unitario) AS valor_stock
        FROM inventario WHERE empresa_id = p_empresa_id AND cantidad > 0
        GROUP BY producto_id
    ) inv ON inv.producto_id = p.id
    LEFT JOIN (
        SELECT md.producto_id, SUM(md.cantidad) AS total_salidas, SUM(md.costo_total) AS valor_salidas
        FROM movimiento_detalle md
        INNER JOIN movimientos_almacen m ON m.id = md.movimiento_id
        WHERE m.empresa_id = p_empresa_id
          AND m.tipo_movimiento = 'salida'
          AND m.estado IN ('completado', 'confirmado')
          AND m.fecha_movimiento >= v_fecha_desde
        GROUP BY md.producto_id
    ) sal ON sal.producto_id = p.id
    LEFT JOIN (
        SELECT md.producto_id, SUM(md.cantidad) AS total_ingresos
        FROM movimiento_detalle md
        INNER JOIN movimientos_almacen m ON m.id = md.movimiento_id
        WHERE m.empresa_id = p_empresa_id
          AND m.tipo_movimiento = 'ingreso'
          AND m.estado IN ('completado', 'confirmado')
          AND m.fecha_movimiento >= v_fecha_desde
        GROUP BY md.producto_id
    ) ing ON ing.producto_id = p.id
    WHERE p.empresa_id = p_empresa_id AND p.status = 'active'
    ORDER BY indice_rotacion ASC, p.sku;
END//


-- =============================================================================
-- 9.4 sp_reporte_almacen_ocupacion
-- Ocupacion por almacen: productos, unidades, valor
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_almacen_ocupacion//
CREATE PROCEDURE sp_reporte_almacen_ocupacion(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        a.id AS almacen_id,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        a.responsable,
        a.status,
        COUNT(DISTINCT i.producto_id) AS total_productos,
        COALESCE(SUM(i.cantidad), 0) AS total_unidades,
        COALESCE(SUM(i.cantidad * i.costo_unitario), 0) AS valor_total,
        -- Porcentaje del valor total
        ROUND(
            COALESCE(SUM(i.cantidad * i.costo_unitario), 0) * 100.0 /
            NULLIF((SELECT SUM(i2.cantidad * i2.costo_unitario) FROM inventario i2 WHERE i2.empresa_id = p_empresa_id AND i2.cantidad > 0), 0),
            2
        ) AS porcentaje_valor,
        -- Movimientos ultimos 30 dias
        (SELECT COUNT(*) FROM movimientos_almacen m
         WHERE m.empresa_id = p_empresa_id AND m.almacen_id = a.id
           AND m.estado IN ('completado', 'confirmado')
           AND m.fecha_movimiento >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ) AS movimientos_30d
    FROM almacenes a
    LEFT JOIN inventario i ON i.almacen_id = a.id AND i.empresa_id = p_empresa_id AND i.cantidad > 0
    WHERE a.empresa_id = p_empresa_id AND a.status = 'active'
    GROUP BY a.id, a.codigo, a.nombre, a.responsable, a.status
    ORDER BY valor_total DESC;
END//


-- =============================================================================
-- 9.5 sp_reporte_almacen_movimientos
-- Movimientos por almacen con resumen mensual
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_almacen_movimientos//
CREATE PROCEDURE sp_reporte_almacen_movimientos(
    IN p_empresa_id INT,
    IN p_almacen_id INT,
    IN p_meses INT
)
BEGIN
    DECLARE v_fecha_desde DATE;
    SET v_fecha_desde = DATE_SUB(CURDATE(), INTERVAL COALESCE(p_meses, 6) MONTH);

    -- Resultset 1: Resumen mensual
    SELECT
        YEAR(m.fecha_movimiento) AS anio,
        MONTH(m.fecha_movimiento) AS mes,
        SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN 1 ELSE 0 END) AS ingresos_count,
        SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN 1 ELSE 0 END) AS salidas_count,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN m.valor_total ELSE 0 END), 0) AS valor_ingresos,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN m.valor_total ELSE 0 END), 0) AS valor_salidas,
        COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN m.valor_total ELSE 0 END), 0)
        - COALESCE(SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN m.valor_total ELSE 0 END), 0) AS balance
    FROM movimientos_almacen m
    WHERE m.empresa_id = p_empresa_id
      AND (p_almacen_id IS NULL OR m.almacen_id = p_almacen_id)
      AND m.estado IN ('completado', 'confirmado')
      AND m.fecha_movimiento >= v_fecha_desde
    GROUP BY YEAR(m.fecha_movimiento), MONTH(m.fecha_movimiento)
    ORDER BY anio DESC, mes DESC;

    -- Resultset 2: Top productos movidos
    SELECT
        p.id AS producto_id,
        p.sku,
        p.nombre AS producto_nombre,
        SUM(CASE WHEN m.tipo_movimiento = 'ingreso' THEN md.cantidad ELSE 0 END) AS cantidad_ingresada,
        SUM(CASE WHEN m.tipo_movimiento = 'salida' THEN md.cantidad ELSE 0 END) AS cantidad_salida,
        COUNT(DISTINCT m.id) AS total_movimientos
    FROM movimiento_detalle md
    INNER JOIN movimientos_almacen m ON m.id = md.movimiento_id
    INNER JOIN productos p ON p.id = md.producto_id
    WHERE m.empresa_id = p_empresa_id
      AND (p_almacen_id IS NULL OR m.almacen_id = p_almacen_id)
      AND m.estado IN ('completado', 'confirmado')
      AND m.fecha_movimiento >= v_fecha_desde
    GROUP BY p.id, p.sku, p.nombre
    ORDER BY total_movimientos DESC
    LIMIT 20;
END//


-- =============================================================================
-- 9.6 sp_reporte_almacen_comparativo
-- Comparativo entre almacenes
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_almacen_comparativo//
CREATE PROCEDURE sp_reporte_almacen_comparativo(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        a.id AS almacen_id,
        a.codigo AS almacen_codigo,
        a.nombre AS almacen_nombre,
        -- Stock actual
        COUNT(DISTINCT i.producto_id) AS productos_distintos,
        COALESCE(SUM(i.cantidad), 0) AS total_unidades,
        COALESCE(SUM(i.cantidad * i.costo_unitario), 0) AS valor_inventario,
        -- Ingresos ultimos 30 dias
        COALESCE((
            SELECT SUM(m.valor_total) FROM movimientos_almacen m
            WHERE m.empresa_id = p_empresa_id AND m.almacen_id = a.id
              AND m.tipo_movimiento = 'ingreso' AND m.estado IN ('completado', 'confirmado')
              AND m.fecha_movimiento >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ), 0) AS ingresos_30d,
        -- Salidas ultimos 30 dias
        COALESCE((
            SELECT SUM(m.valor_total) FROM movimientos_almacen m
            WHERE m.empresa_id = p_empresa_id AND m.almacen_id = a.id
              AND m.tipo_movimiento = 'salida' AND m.estado IN ('completado', 'confirmado')
              AND m.fecha_movimiento >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ), 0) AS salidas_30d,
        -- Alertas stock
        (SELECT COUNT(*)
         FROM productos p
         INNER JOIN inventario i2 ON i2.producto_id = p.id AND i2.almacen_id = a.id AND i2.empresa_id = p_empresa_id
         WHERE p.empresa_id = p_empresa_id AND p.punto_reposicion > 0
         GROUP BY a.id
         HAVING SUM(i2.cantidad) < MAX(p.punto_reposicion)
        ) AS alertas_stock
    FROM almacenes a
    LEFT JOIN inventario i ON i.almacen_id = a.id AND i.empresa_id = p_empresa_id AND i.cantidad > 0
    WHERE a.empresa_id = p_empresa_id AND a.status = 'active'
    GROUP BY a.id, a.codigo, a.nombre
    ORDER BY valor_inventario DESC;
END//


-- =============================================================================
-- 9.7 sp_reporte_compras_resumen
-- Resumen de ordenes de compra: totales, por estado, tiempo entrega
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_compras_resumen//
CREATE PROCEDURE sp_reporte_compras_resumen(
    IN p_empresa_id INT,
    IN p_anio INT
)
BEGIN
    DECLARE v_anio INT;
    SET v_anio = COALESCE(p_anio, YEAR(CURDATE()));

    -- Resultset 1: Resumen general del anio
    SELECT
        COUNT(*) AS total_ordenes,
        COALESCE(SUM(oc.total_fob), 0) AS total_fob,
        COALESCE(SUM(oc.total_costo_importacion), 0) AS total_costo,
        COALESCE(AVG(oc.total_fob), 0) AS promedio_fob,
        COUNT(DISTINCT oc.proveedor_id) AS proveedores_distintos,
        COALESCE(AVG(DATEDIFF(oc.fecha_llegada_est, oc.fecha_orden)), 0) AS dias_entrega_promedio
    FROM ordenes_compra oc
    WHERE oc.empresa_id = p_empresa_id
      AND YEAR(oc.fecha_orden) = v_anio;

    -- Resultset 2: Por estado
    SELECT
        oc.estado,
        COUNT(*) AS cantidad,
        COALESCE(SUM(oc.total_fob), 0) AS total_fob,
        COALESCE(SUM(oc.total_costo_importacion), 0) AS total_costo
    FROM ordenes_compra oc
    WHERE oc.empresa_id = p_empresa_id
      AND YEAR(oc.fecha_orden) = v_anio
    GROUP BY oc.estado
    ORDER BY cantidad DESC;

    -- Resultset 3: Por mes
    SELECT
        MONTH(oc.fecha_orden) AS mes,
        COUNT(*) AS total_ordenes,
        COALESCE(SUM(oc.total_fob), 0) AS total_fob,
        COALESCE(SUM(oc.total_costo_importacion), 0) AS total_costo
    FROM ordenes_compra oc
    WHERE oc.empresa_id = p_empresa_id
      AND YEAR(oc.fecha_orden) = v_anio
    GROUP BY MONTH(oc.fecha_orden)
    ORDER BY mes;
END//


-- =============================================================================
-- 9.8 sp_reporte_compras_por_proveedor
-- Resumen de compras agrupado por proveedor
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_compras_por_proveedor//
CREATE PROCEDURE sp_reporte_compras_por_proveedor(
    IN p_empresa_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE
)
BEGIN
    SELECT
        prov.id AS proveedor_id,
        prov.razon_social AS proveedor_nombre,
        prov.ruc AS proveedor_ruc,
        COALESCE(pa.nombre, 'N/A') AS pais,
        COUNT(*) AS total_ordenes,
        COALESCE(SUM(oc.total_fob), 0) AS total_fob,
        COALESCE(SUM(oc.total_costo_importacion), 0) AS total_costo,
        COALESCE(AVG(oc.total_fob), 0) AS promedio_fob_orden,
        COALESCE(AVG(DATEDIFF(oc.fecha_llegada_est, oc.fecha_orden)), 0) AS dias_entrega_promedio,
        MAX(oc.fecha_orden) AS ultima_orden,
        -- Porcentaje del total
        ROUND(
            SUM(oc.total_fob) * 100.0 /
            NULLIF((
                SELECT SUM(oc2.total_fob) FROM ordenes_compra oc2
                WHERE oc2.empresa_id = p_empresa_id
                  AND (p_fecha_desde IS NULL OR oc2.fecha_orden >= p_fecha_desde)
                  AND (p_fecha_hasta IS NULL OR oc2.fecha_orden <= p_fecha_hasta)
            ), 0),
            2
        ) AS porcentaje_total
    FROM ordenes_compra oc
    INNER JOIN proveedores prov ON prov.id = oc.proveedor_id
    LEFT JOIN paises pa ON pa.id = prov.pais_id
    WHERE oc.empresa_id = p_empresa_id
      AND (p_fecha_desde IS NULL OR oc.fecha_orden >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR oc.fecha_orden <= p_fecha_hasta)
    GROUP BY prov.id, prov.razon_social, prov.ruc, pa.nombre
    ORDER BY total_fob DESC;
END//


-- =============================================================================
-- 9.9 sp_reporte_compras_pendientes
-- OCs pendientes con dias de espera
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_reporte_compras_pendientes//
CREATE PROCEDURE sp_reporte_compras_pendientes(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        oc.id,
        oc.numero_oc,
        prov.razon_social AS proveedor_nombre,
        prov.ruc AS proveedor_ruc,
        oc.fecha_orden,
        oc.fecha_llegada_est,
        mon.codigo AS moneda,
        oc.total_fob,
        oc.total_cif,
        oc.estado,
        DATEDIFF(CURDATE(), oc.fecha_orden) AS dias_desde_orden,
        CASE
            WHEN oc.fecha_llegada_est IS NOT NULL AND oc.fecha_llegada_est < CURDATE()
            THEN DATEDIFF(CURDATE(), oc.fecha_llegada_est)
            ELSE 0
        END AS dias_atraso,
        CASE
            WHEN oc.fecha_llegada_est IS NOT NULL AND oc.fecha_llegada_est < CURDATE() THEN 'atrasada'
            WHEN oc.fecha_llegada_est IS NOT NULL AND oc.fecha_llegada_est <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 'proxima'
            ELSE 'en_plazo'
        END AS urgencia,
        (SELECT COUNT(*) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS total_items,
        oc.notas
    FROM ordenes_compra oc
    INNER JOIN proveedores prov ON prov.id = oc.proveedor_id
    LEFT JOIN monedas mon ON mon.id = oc.moneda_id
    WHERE oc.empresa_id = p_empresa_id
      AND oc.estado NOT IN ('completada', 'cancelada', 'en_almacen')
    ORDER BY
        CASE
            WHEN oc.fecha_llegada_est IS NOT NULL AND oc.fecha_llegada_est < CURDATE() THEN 0
            WHEN oc.fecha_llegada_est IS NOT NULL AND oc.fecha_llegada_est <= DATE_ADD(CURDATE(), INTERVAL 7 DAY) THEN 1
            ELSE 2
        END,
        oc.fecha_llegada_est ASC,
        oc.fecha_orden ASC;
END//

DELIMITER ;
