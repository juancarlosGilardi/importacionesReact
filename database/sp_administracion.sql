-- =============================================================================
-- Sprint 10: Administracion — Stored Procedures
-- =============================================================================

DELIMITER //

-- =============================================================================
-- 10.1 sp_usuario_listar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_listar//
CREATE PROCEDURE sp_usuario_listar(
    IN p_empresa_id INT,
    IN p_search VARCHAR(100),
    IN p_rol VARCHAR(20),
    IN p_status VARCHAR(20)
)
BEGIN
    SELECT
        u.id,
        u.email,
        u.nombre,
        u.apellido,
        u.rol,
        u.status,
        u.almacen_default_id,
        a.nombre AS almacen_nombre,
        a.codigo AS almacen_codigo,
        u.ultimo_login,
        u.created_at,
        u.updated_at
    FROM usuarios u
    LEFT JOIN almacenes a ON a.id = u.almacen_default_id
    WHERE u.empresa_id = p_empresa_id
      AND (p_search IS NULL
           OR u.nombre LIKE CONCAT('%', p_search, '%')
           OR u.apellido LIKE CONCAT('%', p_search, '%')
           OR u.email LIKE CONCAT('%', p_search, '%')
      )
      AND (p_rol IS NULL OR u.rol = p_rol)
      AND (p_status IS NULL OR u.status = p_status)
    ORDER BY u.nombre, u.apellido;
END//


-- =============================================================================
-- 10.2 sp_usuario_obtener
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_obtener//
CREATE PROCEDURE sp_usuario_obtener(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    SELECT
        u.id,
        u.email,
        u.nombre,
        u.apellido,
        u.rol,
        u.status,
        u.almacen_default_id,
        a.nombre AS almacen_nombre,
        a.codigo AS almacen_codigo,
        u.ultimo_login,
        u.created_at,
        u.updated_at
    FROM usuarios u
    LEFT JOIN almacenes a ON a.id = u.almacen_default_id
    WHERE u.id = p_id AND u.empresa_id = p_empresa_id;
END//


-- =============================================================================
-- 10.3 sp_usuario_crear
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_crear//
CREATE PROCEDURE sp_usuario_crear(
    IN p_empresa_id INT,
    IN p_email VARCHAR(100),
    IN p_password_hash VARCHAR(255),
    IN p_nombre VARCHAR(100),
    IN p_apellido VARCHAR(100),
    IN p_rol VARCHAR(20),
    IN p_almacen_default_id INT
)
BEGIN
    DECLARE v_exists INT;

    SELECT COUNT(*) INTO v_exists FROM usuarios WHERE email = p_email;
    IF v_exists > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El email ya esta registrado';
    END IF;

    INSERT INTO usuarios (empresa_id, email, password_hash, nombre, apellido, rol, almacen_default_id)
    VALUES (p_empresa_id, p_email, p_password_hash, p_nombre, p_apellido,
            COALESCE(p_rol, 'usuario'), p_almacen_default_id);

    SELECT LAST_INSERT_ID() AS id, p_email AS email, p_nombre AS nombre;
END//


-- =============================================================================
-- 10.4 sp_usuario_actualizar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_actualizar//
CREATE PROCEDURE sp_usuario_actualizar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_nombre VARCHAR(100),
    IN p_apellido VARCHAR(100),
    IN p_rol VARCHAR(20),
    IN p_status VARCHAR(20),
    IN p_almacen_default_id INT
)
BEGIN
    UPDATE usuarios SET
        nombre = COALESCE(p_nombre, nombre),
        apellido = COALESCE(p_apellido, apellido),
        rol = COALESCE(p_rol, rol),
        status = COALESCE(p_status, status),
        almacen_default_id = p_almacen_default_id
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'actualizado' AS status;
END//


-- =============================================================================
-- 10.5 sp_usuario_reset_password
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_reset_password//
CREATE PROCEDURE sp_usuario_reset_password(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_new_password_hash VARCHAR(255)
)
BEGIN
    UPDATE usuarios SET
        password_hash = p_new_password_hash
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'password_actualizado' AS status;
END//


-- =============================================================================
-- 10.6 sp_usuario_desactivar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_desactivar//
CREATE PROCEDURE sp_usuario_desactivar(
    IN p_id INT,
    IN p_empresa_id INT,
    IN p_current_user_id INT
)
BEGIN
    IF p_id = p_current_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No puede desactivar su propia cuenta';
    END IF;

    UPDATE usuarios SET status = 'inactive'
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'desactivado' AS status;
END//


-- =============================================================================
-- 10.7 sp_usuario_activar
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_usuario_activar//
CREATE PROCEDURE sp_usuario_activar(
    IN p_id INT,
    IN p_empresa_id INT
)
BEGIN
    UPDATE usuarios SET status = 'active'
    WHERE id = p_id AND empresa_id = p_empresa_id;

    SELECT p_id AS id, 'activado' AS status;
END//


-- =============================================================================
-- 10.8 sp_configuracion_obtener
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_configuracion_obtener//
CREATE PROCEDURE sp_configuracion_obtener(
    IN p_empresa_id INT,
    IN p_seccion VARCHAR(50)
)
BEGIN
    SELECT
        id,
        seccion,
        clave,
        valor,
        tipo_dato,
        descripcion,
        updated_at
    FROM configuracion_sistema
    WHERE empresa_id = p_empresa_id
      AND (p_seccion IS NULL OR seccion = p_seccion)
    ORDER BY seccion, clave;
END//


-- =============================================================================
-- 10.9 sp_configuracion_actualizar
-- Recibe seccion + clave + valor, upsert
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_configuracion_actualizar//
CREATE PROCEDURE sp_configuracion_actualizar(
    IN p_empresa_id INT,
    IN p_seccion VARCHAR(50),
    IN p_clave VARCHAR(100),
    IN p_valor TEXT
)
BEGIN
    INSERT INTO configuracion_sistema (empresa_id, seccion, clave, valor)
    VALUES (p_empresa_id, p_seccion, p_clave, p_valor)
    ON DUPLICATE KEY UPDATE valor = p_valor;

    SELECT p_seccion AS seccion, p_clave AS clave, 'actualizado' AS status;
END//


-- =============================================================================
-- 10.10 sp_configuracion_obtener_secciones
-- Lista secciones distintas
-- =============================================================================
DROP PROCEDURE IF EXISTS sp_configuracion_obtener_secciones//
CREATE PROCEDURE sp_configuracion_obtener_secciones(
    IN p_empresa_id INT
)
BEGIN
    SELECT DISTINCT seccion,
        COUNT(*) AS total_claves
    FROM configuracion_sistema
    WHERE empresa_id = p_empresa_id
    GROUP BY seccion
    ORDER BY seccion;
END//

DELIMITER ;
