-- ============================================================================
-- IMPORTCOST PRO - Vistas SQL
-- Dashboard, Pipeline, Kardex SUNAT, Resumen de costos
-- ============================================================================

USE importcost_pro;

-- ============================================================================
-- Vista: Metricas de Dashboard (conteo por estado)
-- ============================================================================
CREATE OR REPLACE VIEW vw_dashboard_metricas AS
SELECT
    oc.empresa_id,
    SUM(IF(oc.estado = 'borrador', 1, 0)) AS borradores,
    SUM(IF(oc.estado = 'confirmada', 1, 0)) AS confirmadas,
    SUM(IF(oc.estado = 'en_transito', 1, 0)) AS en_transito,
    SUM(IF(oc.estado = 'en_aduana', 1, 0)) AS en_aduana,
    SUM(IF(oc.estado = 'prorrateado', 1, 0)) AS prorrateadas,
    SUM(IF(oc.estado = 'en_almacen', 1, 0)) AS en_almacen,
    SUM(IF(oc.estado = 'completada', 1, 0)) AS completadas,
    SUM(IF(oc.estado = 'cancelada', 1, 0)) AS canceladas,
    COALESCE(SUM(IF(oc.estado = 'completada'
        AND MONTH(oc.fecha_orden) = MONTH(CURDATE())
        AND YEAR(oc.fecha_orden) = YEAR(CURDATE()),
        oc.total_costo_importacion, 0)), 0) AS costo_mes_actual,
    COALESCE(SUM(IF(oc.estado = 'completada'
        AND MONTH(oc.fecha_orden) = MONTH(DATE_SUB(CURDATE(), INTERVAL 1 MONTH))
        AND YEAR(oc.fecha_orden) = YEAR(DATE_SUB(CURDATE(), INTERVAL 1 MONTH)),
        oc.total_costo_importacion, 0)), 0) AS costo_mes_anterior
FROM ordenes_compra oc
GROUP BY oc.empresa_id;

-- ============================================================================
-- Vista: Pipeline de OCs (para Kanban)
-- ============================================================================
CREATE OR REPLACE VIEW vw_oc_pipeline AS
SELECT
    oc.id,
    oc.empresa_id,
    oc.numero_oc,
    oc.fecha_orden,
    p.razon_social AS proveedor,
    p.nombre_comercial AS proveedor_comercial,
    pa.nombre AS pais_origen,
    pa.codigo AS pais_codigo,
    oc.incoterm,
    m.simbolo AS moneda_simbolo,
    oc.total_fob,
    oc.total_costo_importacion,
    oc.estado,
    ei.nombre AS estado_nombre,
    ei.color_ui AS estado_color,
    ei.icono_ui AS estado_icono,
    ei.orden AS estado_orden,
    (SELECT COUNT(*) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS items_count,
    (SELECT COALESCE(SUM(oci.cantidad), 0) FROM orden_compra_items oci WHERE oci.oc_id = oc.id) AS total_cantidad,
    DATEDIFF(CURDATE(), oc.fecha_orden) AS dias_transcurridos
FROM ordenes_compra oc
JOIN proveedores p ON oc.proveedor_id = p.id
LEFT JOIN paises pa ON p.pais_id = pa.id
JOIN monedas m ON oc.moneda_id = m.id
LEFT JOIN estados_importacion ei ON oc.estado = ei.codigo;

-- ============================================================================
-- Vista: Resumen de costos por producto (historico)
-- ============================================================================
CREATE OR REPLACE VIEW vw_producto_costo_resumen AS
SELECT
    pr.empresa_id,
    pr.id AS producto_id,
    pr.sku,
    pr.nombre AS producto,
    pr.codigo_hs,
    COUNT(DISTINCT oc.id) AS total_importaciones,
    COALESCE(SUM(oci.cantidad), 0) AS cantidad_total_importada,
    COALESCE(AVG(oci.precio_unitario), 0) AS precio_fob_promedio,
    COALESCE(AVG(IF(oci.costo_unitario_landed > 0, oci.costo_unitario_landed, NULL)), 0) AS costo_unitario_promedio,
    COALESCE(MIN(oci.costo_unitario_landed), 0) AS costo_unitario_min,
    COALESCE(MAX(oci.costo_unitario_landed), 0) AS costo_unitario_max,
    MAX(oc.fecha_orden) AS ultima_importacion,
    COALESCE(AVG(IF(oci.precio_unitario > 0 AND oci.costo_unitario_landed > 0,
        ((oci.costo_unitario_landed - oci.precio_unitario) / oci.precio_unitario) * 100,
        NULL)), 0) AS incremento_promedio_pct
FROM productos pr
JOIN orden_compra_items oci ON pr.id = oci.producto_id
JOIN ordenes_compra oc ON oci.oc_id = oc.id AND oc.estado IN ('prorrateado', 'en_almacen', 'completada')
GROUP BY pr.id;

-- ============================================================================
-- Vista: Kardex SUNAT (formato oficial)
-- ============================================================================
CREATE OR REPLACE VIEW vw_kardex_sunat AS
SELECT
    ma.empresa_id,
    md.id AS detalle_id,
    pr.id AS producto_id,
    pr.sku AS producto_codigo,
    pr.nombre AS producto_descripcion,
    pr.unidad_medida AS unidad,
    ma.fecha_movimiento AS fecha,
    ma.created_at,
    -- Tipo de operacion SUNAT
    CASE
        WHEN ma.tipo_movimiento = 'ingreso' AND ma.oc_id IS NOT NULL THEN '02'  -- Compra
        WHEN ma.tipo_movimiento = 'ingreso' AND ma.oc_id IS NULL THEN '16'      -- Saldo Inicial
        WHEN ma.tipo_movimiento = 'salida' THEN '01'                            -- Venta
        WHEN ma.tipo_movimiento = 'transferencia' THEN '11'                     -- Transferencia
        ELSE '99'                                                               -- Otros
    END AS operacion_tipo,
    '09' AS doc_tipo,
    IF(LOCATE('-', ma.documento_referencia) > 0,
       SUBSTRING_INDEX(ma.documento_referencia, '-', 1), '001') AS doc_serie,
    IF(LOCATE('-', ma.documento_referencia) > 0,
       SUBSTRING_INDEX(ma.documento_referencia, '-', -1), ma.documento_referencia) AS doc_numero,
    ma.tipo_movimiento,
    md.cantidad,
    md.costo_unitario,
    md.costo_total,
    a.nombre AS almacen,
    a.codigo AS almacen_codigo
FROM movimiento_detalle md
JOIN movimientos_almacen ma ON md.movimiento_id = ma.id
JOIN productos pr ON md.producto_id = pr.id
JOIN almacenes a ON ma.almacen_id = a.id
WHERE ma.estado = 'completado';

-- ============================================================================
-- Vista: Gastos por importacion consolidado
-- ============================================================================
CREATE OR REPLACE VIEW vw_gastos_importacion_resumen AS
SELECT
    g.empresa_id,
    g.importacion_id,
    i.numero_importacion,
    tg.codigo AS tipo_gasto_codigo,
    tg.nombre AS tipo_gasto,
    tg.color_ui,
    tg.icono_ui,
    COUNT(g.id) AS cantidad_gastos,
    COALESCE(SUM(g.monto_pen), 0) AS total_pen,
    SUM(IF(g.prorrateado = 1, 1, 0)) AS gastos_prorrateados,
    SUM(IF(g.prorrateado = 0, 1, 0)) AS gastos_pendientes
FROM gastos_importacion g
JOIN tipos_gasto tg ON g.tipo_gasto_codigo = tg.codigo
LEFT JOIN importaciones i ON g.importacion_id = i.id
GROUP BY g.empresa_id, g.importacion_id, tg.codigo;

-- ============================================================================
-- Vista: Inventario valorizado por almacen
-- ============================================================================
CREATE OR REPLACE VIEW vw_inventario_valorizado AS
SELECT
    inv.empresa_id,
    a.id AS almacen_id,
    a.nombre AS almacen,
    a.codigo AS almacen_codigo,
    COUNT(DISTINCT inv.producto_id) AS productos_distintos,
    COALESCE(SUM(inv.cantidad), 0) AS unidades_totales,
    COALESCE(SUM(inv.cantidad * inv.costo_unitario), 0) AS valor_total
FROM inventario inv
JOIN almacenes a ON inv.almacen_id = a.id
WHERE inv.cantidad > 0
GROUP BY inv.empresa_id, a.id;
