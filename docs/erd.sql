-- HealthShield AI - Enterprise Relational Schema
-- PostgreSQL 16+ | MySQL 8.0+
-- Last Updated: May 2026

-- ═══════════════════════════════════════════════════════════════════════════
-- 1. AUTHENTICATION MODULE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE usuarios_clinicos (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) CHECK (rol IN ('administrador', 'medico', 'analista')) DEFAULT 'analista',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_rol (rol)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- 2. ETL & CLINICAL DATA MODULE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE pacientes (
    id SERIAL PRIMARY KEY,
    id_paciente_original INT UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    edad SMALLINT CHECK (edad >= 0 AND edad <= 120),
    sexo CHAR(1) CHECK (sexo IN ('M', 'F')),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_nombres (nombres),
    INDEX idx_edad (edad),
    INDEX idx_fecha (fecha_registro)
);

CREATE TABLE registros_clinicos (
    id SERIAL PRIMARY KEY,
    paciente_id INT NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    fuente_etl INT NULL REFERENCES ejecuciones_etl(id) ON DELETE SET NULL,
    fecha_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Vital Signs
    peso DECIMAL(5, 2),  -- kg
    altura DECIMAL(4, 2),  -- m
    imc DECIMAL(5, 2),  -- calculated
    presion_sistolica INT CHECK (presion_sistolica BETWEEN 0 AND 300),
    presion_diastolica INT CHECK (presion_diastolica BETWEEN 0 AND 300),
    frecuencia_cardiaca INT CHECK (frecuencia_cardiaca BETWEEN 30 AND 200),
    temperatura DECIMAL(4, 1) CHECK (temperatura BETWEEN 35 AND 43),
    saturacion_oxigeno DECIMAL(5, 2) CHECK (saturacion_oxigeno BETWEEN 0 AND 100),
    
    -- Laboratory
    glucosa DECIMAL(7, 2),
    colesterol DECIMAL(7, 2),
    
    -- Medical History
    antecedentes_familiares BOOLEAN DEFAULT FALSE,
    fumador BOOLEAN DEFAULT FALSE,
    consumo_alcohol BOOLEAN DEFAULT FALSE,
    actividad_fisica VARCHAR(50),
    diagnostico_preliminar VARCHAR(255),
    
    -- Risk Classification
    riesgo_enfermedad VARCHAR(20) CHECK (riesgo_enfermedad IN ('Bajo', 'Medio', 'Alto', 'Crítico')),
    clasificacion_imc VARCHAR(30),
    
    INDEX idx_paciente (paciente_id),
    INDEX idx_riesgo (riesgo_enfermedad),
    INDEX idx_fecha (fecha_consulta),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
);

CREATE TABLE ejecuciones_etl (
    id SERIAL PRIMARY KEY,
    usuario_id INT NULL REFERENCES usuarios_clinicos(id) ON DELETE SET NULL,
    archivo_fuente VARCHAR(255),
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL,
    duracion_segundos DECIMAL(8, 3),
    
    registros_extraidos INT DEFAULT 0,
    registros_procesados INT DEFAULT 0,
    registros_rechazados INT DEFAULT 0,
    duplicados_eliminados INT DEFAULT 0,
    nulos_imputados INT DEFAULT 0,
    
    estado VARCHAR(20) CHECK (estado IN ('en_proceso', 'completado', 'fallido')) DEFAULT 'en_proceso',
    tipo VARCHAR(20) CHECK (tipo IN ('manual', 'simulacion', 'importacion')),
    calidad_score DECIMAL(5, 2) CHECK (calidad_score BETWEEN 0 AND 100),
    
    INDEX idx_usuario (usuario_id),
    INDEX idx_estado (estado),
    INDEX idx_fecha (fecha_inicio)
);

CREATE TABLE logs_etl (
    id SERIAL PRIMARY KEY,
    ejecucion_id INT NOT NULL REFERENCES ejecuciones_etl(id) ON DELETE CASCADE,
    nivel VARCHAR(20) CHECK (nivel IN ('INFO', 'WARNING', 'ERROR')),
    campo_afectado VARCHAR(100),
    mensaje TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ejecucion (ejecucion_id),
    INDEX idx_nivel (nivel)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- 3. MACHINE LEARNING MODULE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE modelos_ml (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    algoritmo VARCHAR(50) CHECK (algoritmo IN ('random_forest', 'logistic_regression', 'decision_tree')),
    version VARCHAR(20),
    
    accuracy DECIMAL(5, 4),
    precision_score DECIMAL(5, 4),
    recall DECIMAL(5, 4),
    f1_score DECIMAL(5, 4),
    roc_auc DECIMAL(5, 4),
    
    entrenado_en TIMESTAMP,
    activo BOOLEAN DEFAULT FALSE,
    ruta_modelo VARCHAR(255),
    
    INDEX idx_algoritmo (algoritmo),
    INDEX idx_activo (activo)
);

CREATE TABLE predicciones (
    id SERIAL PRIMARY KEY,
    paciente_id INT NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    modelo_id INT NOT NULL REFERENCES modelos_ml(id) ON DELETE CASCADE,
    
    riesgo_predicho VARCHAR(20) CHECK (riesgo_predicho IN ('Bajo', 'Medio', 'Alto', 'Crítico')),
    probabilidad DECIMAL(5, 4) CHECK (probabilidad BETWEEN 0 AND 1),
    confianza DECIMAL(5, 4),
    
    factores_clave JSON,  -- {feature: importance}
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_paciente (paciente_id),
    INDEX idx_modelo (modelo_id),
    INDEX idx_riesgo (riesgo_predicho)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- 4. ANALYTICS MODULE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    paciente_id INT NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    tipo_alerta VARCHAR(100),
    nivel_urgencia VARCHAR(20) CHECK (nivel_urgencia IN ('bajo', 'medio', 'alto', 'crítico')),
    descripcion TEXT,
    visto_por_id INT NULL REFERENCES usuarios_clinicos(id) ON DELETE SET NULL,
    
    fecha_alerta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_vista TIMESTAMP NULL,
    resuelta BOOLEAN DEFAULT FALSE,
    
    INDEX idx_paciente (paciente_id),
    INDEX idx_urgencia (nivel_urgencia),
    INDEX idx_resuelta (resuelta)
);

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS FOR ANALYTICS
-- ═══════════════════════════════════════════════════════════════════════════

CREATE VIEW vista_pacientes_criticos AS
SELECT 
    p.id, p.nombres, p.apellidos, p.edad, p.sexo,
    rc.riesgo_enfermedad, rc.presion_sistolica, rc.glucosa,
    COUNT(*) as registros_criticos
FROM pacientes p
JOIN registros_clinicos rc ON p.id = rc.paciente_id
WHERE rc.riesgo_enfermedad = 'Crítico'
GROUP BY p.id, p.nombres, p.apellidos, p.edad, p.sexo, rc.riesgo_enfermedad, rc.presion_sistolica, rc.glucosa;

CREATE VIEW vista_distribucion_riesgo AS
SELECT 
    riesgo_enfermedad,
    COUNT(*) as cantidad,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM registros_clinicos), 2) as porcentaje
FROM registros_clinicos
GROUP BY riesgo_enfermedad;

CREATE VIEW vista_imc_por_grupo_etario AS
SELECT 
    CASE 
        WHEN p.edad < 20 THEN '10-19'
        WHEN p.edad < 30 THEN '20-29'
        WHEN p.edad < 40 THEN '30-39'
        WHEN p.edad < 50 THEN '40-49'
        WHEN p.edad < 60 THEN '50-59'
        ELSE '60+'
    END as grupo_etario,
    AVG(rc.imc) as imc_promedio,
    COUNT(*) as cantidad_pacientes
FROM pacientes p
JOIN registros_clinicos rc ON p.id = rc.paciente_id
GROUP BY grupo_etario;

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES FOR PERFORMANCE
-- ═══════════════════════════════════════════════════════════════════════════

CREATE INDEX idx_registros_paciente_fecha ON registros_clinicos(paciente_id, fecha_consulta DESC);
CREATE INDEX idx_alertas_paciente_fecha ON alertas(paciente_id, fecha_alerta DESC);
CREATE INDEX idx_predicciones_modelo_fecha ON predicciones(modelo_id, fecha DESC);
