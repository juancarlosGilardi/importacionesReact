-- ============================================================================
-- IMPORTCOST PRO - Stored Procedures: Dashboard y Reportes
-- Metricas, Pipeline, Reportes de costeo
-- ============================================================================

USE importcost_pro;
DELIMITER //

-- ============================================================================
-- DASHBOARD - METRICAS PRINCIPALES
-- ============================================================================

CREATE PROCEDURE sp_dashboard_metricas(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        -- Contadores por estado
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'borrador') AS ocs_borrador,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'confirmada') AS ocs_confirmadas,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'en_transito') AS ocs_en_transito,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'en_aduana') AS ocs_en_aduana,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'prorrateado') AS ocs_prorrateadas,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'en_almacen') AS ocs_en_almacen,
        (SELECT COUNT(*) FROM ordenes_compra WHERE empresa_id = p_empresa_id AND estado = 'completada') AS ocs_completadas,
        -- Importaciones activas
        (SELECT COUNT(*) FROM importaciones WHERE empresa_id = p_empresa_id AND estado NOT IN ('completada', 'cancelada')) AS importaciones_activas,
        -- Totales del mes actual
        (SELECT COALESCE(SUM(total_fob), 0) FROM ordenes_compra
         WHERE empresa_id = p_empresa_id AND MONTH(fecha_orden) = MONTH(CURDATE()) AND YEAR(fecha_orden) = YEAR(CURDATE())
        ) AS fob_mes_actual,
        (SELECT COALESCE(SUM(total_costo_importacion), 0) FROM ordenes_compra
         WHERE empresa_id = p_empresa_id AND estado = 'completada'
         AND MONTH(fecha_orden) = MONTH(CURDATE()) AND YEAR(fecha_orden) = YEAR(CURDATE())
        ) AS costo_total_mes_actual,
        -- Totales del mes anterior
        (SELECT COALESCE(SUM(total_costo_importacion), 0) FROM ordenes_compra
         WHERE empresa_id = p_empresa_id AND estado = 'completada'
         AND MONTH(fecha_orden) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
         AND YEAR(fecha_orden) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        ) AS costo_total_mes_anterior,
        -- Productos y proveedores
        (SELECT COUNT(*) FROM productos WHERE empresa_id = p_empresa_id AND status = 'active') AS total_productos,
        (SELECT COUNT(*) FROM proveedores WHERE empresa_id = p_empresa_id AND status = 'active') AS total_proveedores,
        -- Valor total inventario
        (SELECT COALESCE(SUM(cantidad * costo_unitario), 0) FROM inventario
         WHERE empresa_id = p_empresa_id AND cantidad > 0) AS valor_inventario;
END //

-- ============================================================================
-- PIPELINE KANBAN
-- ============================================================================

CREATE PROCEDURE sp_dashboard_pipeline(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        oc.id, oc.numero_oc, oc.fecha_orden, oc.incoterm,
        oc.total_fob, oc.total_costo_importacion, oc.estado,
        p.razon_social AS proveedor, p.nombre_comercial AS proveedor_comercial,
        pa.codigo AS pais_codigo,
        m.simbolo AS moneda_simbolo,
        ei.nombre AS estado_nombre, ei.color_ui AS estado_color,
        ei.icono_ui AS estado_icono, ei.orden AS estado_orden,
        (SELECT COUNT(*) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS items_count,
        DATEDIFF(CURDATE(), oc.fecha_orden) AS dias_transcurridos
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    LEFT JOIN paises pa ON p.pais_id = pa.id
    JOIN monedas m ON oc.moneda_id = m.id
    LEFT JOIN estados_importacion ei ON oc.estado = ei.codigo
    WHERE oc.empresa_id = p_empresa_id
      AND oc.estado NOT IN ('completada', 'cancelada')
    ORDER BY ei.orden, oc.fecha_orden DESC;
END //

-- ============================================================================
-- PIPELINE DE IMPORTACIONES
-- ============================================================================

CREATE PROCEDURE sp_dashboard_importaciones_pipeline(
    IN p_empresa_id INT
)
BEGIN
    SELECT
        i.id, i.numero_importacion, i.descripcion, i.fecha_creacion,
        i.via_transporte, i.bl_number, i.container_number,
        i.estado,
        i.total_fob_importacion, i.total_costo_importacion,
        i.fecha_embarque, i.fecha_arribo_estimada, i.fecha_arribo_real,
        (SELECT COUNT(*) FROM importacion_ocs io WHERE io.importacion_id = i.id) AS total_ocs,
        (SELECT GROUP_CONCAT(oc.numero_oc SEPARATOR ', ')
         FROM importacion_ocs io JOIN ordenes_compra oc ON io.oc_id = oc.id
         WHERE io.importacion_id = i.id) AS ocs,
        DATEDIFF(CURDATE(), i.fecha_creacion) AS dias_desde_creacion,
        DATEDIFF(i.fecha_arribo_estimada, CURDATE()) AS dias_para_arribo
    FROM importaciones i
    WHERE i.empresa_id = p_empresa_id
      AND i.estado NOT IN ('completada', 'cancelada')
    ORDER BY i.fecha_creacion DESC;
END //

-- ============================================================================
-- REPORTE: Costo historico por producto
-- ============================================================================

CREATE PROCEDURE sp_reporte_costo_producto(
    IN p_empresa_id INT,
    IN p_producto_id INT
)
BEGIN
    SELECT
        pr.sku, pr.nombre AS producto, pr.codigo_hs,
        oc.numero_oc, oc.fecha_orden,
        p.razon_social AS proveedor,
        oci.cantidad, oci.precio_unitario AS precio_fob,
        oci.valor_fob,
        oci.prorrateo_flete, oci.prorrateo_seguro,
        oci.prorrateo_tributos, oci.prorrateo_gastos,
        oci.costo_total, oci.costo_unitario_landed,
        IF(oci.precio_unitario > 0,
           ROUND(((oci.costo_unitario_landed - oci.precio_unitario) / oci.precio_unitario) * 100, 2),
           0) AS incremento_pct,
        m.simbolo AS moneda
    FROM orden_compra_items oci
    JOIN ordenes_compra oc ON oci.oc_id = oc.id
    JOIN productos pr ON oci.producto_id = pr.id
    JOIN proveedores p ON oc.proveedor_id = p.id
    JOIN monedas m ON oc.moneda_id = m.id
    WHERE oc.empresa_id = p_empresa_id
      AND (p_producto_id IS NULL OR oci.producto_id = p_producto_id)
      AND oc.estado IN ('prorrateado', 'en_almacen', 'completada')
    ORDER BY pr.sku, oc.fecha_orden DESC;
END //

-- ============================================================================
-- REPORTE: Comparativo por proveedor
-- ============================================================================

CREATE PROCEDURE sp_reporte_comparativo_proveedor(
    IN p_empresa_id INT,
    IN p_fecha_desde DATE,
    IN p_fecha_hasta DATE
)
BEGIN
    SELECT
        p.id AS proveedor_id,
        p.razon_social AS proveedor,
        pa.nombre AS pais,
        COUNT(DISTINCT oc.id) AS total_ocs,
        SUM(oc.total_fob) AS total_fob,
        SUM(oc.total_costo_importacion) AS total_costo,
        AVG(IF(oc.total_fob > 0,
            ((oc.total_costo_importacion - oc.total_fob) / oc.total_fob) * 100,
            0)) AS incremento_promedio_pct,
        MIN(oc.fecha_orden) AS primera_oc,
        MAX(oc.fecha_orden) AS ultima_oc
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    LEFT JOIN paises pa ON p.pais_id = pa.id
    WHERE oc.empresa_id = p_empresa_id
      AND oc.estado IN ('prorrateado', 'en_almacen', 'completada')
      AND (p_fecha_desde IS NULL OR oc.fecha_orden >= p_fecha_desde)
      AND (p_fecha_hasta IS NULL OR oc.fecha_orden <= p_fecha_hasta)
    GROUP BY p.id
    ORDER BY total_fob DESC;
END //

-- ============================================================================
-- REPORTE: Resumen mensual
-- ============================================================================

CREATE PROCEDURE sp_reporte_resumen_mensual(
    IN p_empresa_id INT,
    IN p_anio INT
)
BEGIN
    DECLARE v_anio INT;
    SET v_anio = COALESCE(p_anio, YEAR(CURDATE()));

    SELECT
        MONTH(oc.fecha_orden) AS mes,
        COUNT(DISTINCT oc.id) AS total_ocs,
        SUM(oc.total_fob) AS total_fob,
        SUM(oc.total_cif) AS total_cif,
        SUM(oc.total_costo_importacion) AS total_landed_cost,
        AVG(IF(oc.total_fob > 0,
            ((oc.total_costo_importacion - oc.total_fob) / oc.total_fob) * 100,
            0)) AS incremento_promedio_pct,
        COUNT(DISTINCT oc.proveedor_id) AS proveedores_distintos,
        SUM((SELECT COUNT(*) FROM orden_compra_items oci WHERE oci.oc_id = oc.id)) AS total_items
    FROM ordenes_compra oc
    WHERE oc.empresa_id = p_empresa_id
      AND YEAR(oc.fecha_orden) = v_anio
      AND oc.estado NOT IN ('borrador', 'cancelada')
    GROUP BY MONTH(oc.fecha_orden)
    ORDER BY mes;
END //

-- ============================================================================
-- BUSQUEDA GLOBAL
-- ============================================================================

CREATE PROCEDURE sp_busqueda_global(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100)
)
BEGIN
    -- OCs
    SELECT 'oc' AS tipo, oc.id, oc.numero_oc AS numero, oc.estado,
           CONCAT(p.razon_social, ' - ', oc.incoterm) AS detalle
    FROM ordenes_compra oc
    JOIN proveedores p ON oc.proveedor_id = p.id
    WHERE oc.empresa_id = p_empresa_id
      AND (oc.numero_oc LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%'))
    LIMIT 5;

    -- Importaciones
    SELECT 'importacion' AS tipo, i.id, i.numero_importacion AS numero, i.estado,
           i.descripcion AS detalle
    FROM importaciones i
    WHERE i.empresa_id = p_empresa_id
      AND (i.numero_importacion LIKE CONCAT('%', p_search, '%')
           OR i.descripcion LIKE CONCAT('%', p_search, '%')
           OR i.bl_number LIKE CONCAT('%', p_search, '%'))
    LIMIT 5;

    -- Productos
    SELECT 'producto' AS tipo, pr.id, pr.sku AS numero, pr.status AS estado,
           pr.nombre AS detalle
    FROM productos pr
    WHERE pr.empresa_id = p_empresa_id
      AND (pr.sku LIKE CONCAT('%', p_search, '%')
           OR pr.nombre LIKE CONCAT('%', p_search, '%'))
    LIMIT 5;

    -- Proveedores
    SELECT 'proveedor' AS tipo, p.id, p.ruc AS numero, p.status AS estado,
           p.razon_social AS detalle
    FROM proveedores p
    WHERE p.empresa_id = p_empresa_id
      AND (p.ruc LIKE CONCAT('%', p_search, '%')
           OR p.razon_social LIKE CONCAT('%', p_search, '%'))
    LIMIT 5;
END //

DELIMITER ;
