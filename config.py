"""
Configuración principal para Progol Optimizer
Parámetros centralizados de la metodología definitiva
"""

import os
from typing import Dict, Any

class ProgolConfig:
    """
    Configuración principal de la aplicación Progol Optimizer
    Basada en la metodología definitiva documentada
    """
    
    # Información de la aplicación
    APP_NAME = "Progol Optimizer"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Metodología Definitiva Core + Satélites"
    
    # Distribución histórica de Progol (1,497+ concursos)
    DISTRIBUCION_HISTORICA = {
        'L': 0.38,  # 38% victorias locales
        'E': 0.29,  # 29% empates  
        'V': 0.33   # 33% victorias visitantes
    }
    
    # Rangos válidos para validación
    RANGOS_HISTORICOS = {
        'L': (0.35, 0.41),  # Victorias locales: 35-41%
        'E': (0.25, 0.33),  # Empates: 25-33%
        'V': (0.30, 0.36)   # Victorias visitantes: 30-36%
    }
    
    # Configuración de empates
    EMPATES_PROMEDIO_HISTORICO = 4.33
    EMPATES_MIN = 4
    EMPATES_MAX = 6
    
    # Límites de concentración
    CONCENTRACION_MAX_GENERAL = 0.70  # 70% máximo en un resultado
    CONCENTRACION_MAX_INICIAL = 0.60  # 60% máximo en partidos 1-3
    
    # Calibración Bayesiana - Coeficientes
    CALIBRACION_COEFICIENTES = {
        'k1_forma': 0.15,      # Factor forma reciente
        'k2_lesiones': 0.10,   # Factor lesiones
        'k3_contexto': 0.20    # Factor contexto (finales, derbis)
    }
    
    # Regla Draw-Propensity
    DRAW_PROPENSITY = {
        'umbral_diferencia': 0.08,  # |p_L - p_V| < 0.08
        'boost_empate': 0.06        # +6 p.p. al empate
    }
    
    # Clasificación de partidos - Umbrales
    UMBRALES_CLASIFICACION = {
        'ancla_min': 0.60,          # >60% confianza = Ancla
        'divisor_min': 0.40,        # 40-60% = Divisor
        'divisor_max': 0.60,
        'empate_min': 0.30          # >30% prob empate = TendenciaEmpate
    }
    
    # Arquitectura Core + Satélites
    ARQUITECTURA = {
        'num_core': 4,              # Siempre 4 quinielas Core
        'correlacion_objetivo': -0.35,  # Correlación negativa objetivo
        'correlacion_min': -0.50,  # Rango válido de correlación
        'correlacion_max': -0.20
    }
    
    # Optimización GRASP-Annealing
    OPTIMIZACION_GRASP = {
        'alpha': 0.15,              # Top 15% para aleatorización
        'temperatura_inicial': 0.05,
        'factor_enfriamiento': 0.92,
        'iteraciones_max': 200,
        'iteraciones_sin_mejora': 50
    }
    
    # Simulación Monte Carlo
    SIMULACION = {
        'num_simulaciones_default': 1000,
        'num_simulaciones_rapida': 500,
        'num_simulaciones_detallada': 2000
    }
    
    # Validación de portafolio
    VALIDACION = {
        'max_warnings_permitidas': 3,
        'tolerancia_distribucion': 0.03,  # 3 p.p. tolerancia
        'similitud_minima_aceptable': 0.15  # Mínimo 15% diferencia entre quinielas
    }
    
    # Configuración de exportación
    EXPORTACION = {
        'formatos_soportados': ['csv', 'json', 'progol', 'xlsx'],
        'incluir_metadata': True,
        'incluir_estadisticas': True
    }
    
    # Configuración de UI/UX
    INTERFAZ = {
        'num_quinielas_default': 20,
        'num_quinielas_min': 10,
        'num_quinielas_max': 35,
        'mostrar_debug': False,
        'mostrar_advertencias_detalladas': True
    }
    
    # Paths y archivos
    PATHS = {
        'data_dir': 'data',
        'sample_data': 'data/sample_data.json',
        'exports_dir': 'exports',
        'logs_dir': 'logs'
    }
    
    # Configuración específica por liga (ejemplos)
    LIGAS_CONFIG = {
        'Liga_MX': {
            'factor_local': 0.45,
            'empates_tendencia': 0.31,
            'volatilidad_alta': True
        },
        'Premier_League': {
            'factor_local': 0.35,
            'empates_tendencia': 0.26,
            'volatilidad_alta': False
        },
        'Brasileirao': {
            'factor_local': 0.55,
            'empates_tendencia': 0.28,
            'volatilidad_alta': True
        },
        'Champions_League': {
            'factor_local': 0.25,  # Menor ventaja local
            'empates_tendencia': 0.32,
            'volatilidad_alta': True
        }
    }
    
    @classmethod
    def get_config_for_league(cls, liga: str) -> Dict[str, Any]:
        """
        Obtiene configuración específica para una liga
        """
        return cls.LIGAS_CONFIG.get(liga, {
            'factor_local': 0.40,
            'empates_tendencia': 0.29,
            'volatilidad_alta': False
        })
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Valida que la configuración sea coherente
        """
        try:
            # Verificar que distribución histórica suma 1.0
            suma_dist = sum(cls.DISTRIBUCION_HISTORICA.values())
            if abs(suma_dist - 1.0) > 0.01:
                return False
            
            # Verificar rangos históricos coherentes
            for resultado, (min_val, max_val) in cls.RANGOS_HISTORICOS.items():
                if min_val >= max_val:
                    return False
                if not (0 <= min_val <= 1 and 0 <= max_val <= 1):
                    return False
            
            # Verificar umbrales de clasificación
            umbrales = cls.UMBRALES_CLASIFICACION
            if umbrales['divisor_min'] >= umbrales['divisor_max']:
                return False
            if umbrales['ancla_min'] <= umbrales['divisor_max']:
                return False
            
            return True
        except Exception:
            return False
    
    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """
        Obtiene resumen de la configuración
        """
        return {
            'app_info': {
                'name': cls.APP_NAME,
                'version': cls.APP_VERSION,
                'description': cls.APP_DESCRIPTION
            },
            'metodologia': {
                'distribucion_objetivo': cls.DISTRIBUCION_HISTORICA,
                'empates_promedio': cls.EMPATES_PROMEDIO_HISTORICO,
                'arquitectura': f"{cls.ARQUITECTURA['num_core']} Core + Satélites",
                'optimizacion': 'GRASP-Annealing'
            },
            'validacion_ok': cls.validate_config()
        }

# Configuración para desarrollo/producción
class DevelopmentConfig(ProgolConfig):
    """Configuración para desarrollo"""
    DEBUG = True
    MOSTRAR_LOGS_DETALLADOS = True
    SIMULACION_RAPIDA = True

class ProductionConfig(ProgolConfig):
    """Configuración para producción"""
    DEBUG = False
    MOSTRAR_LOGS_DETALLADOS = False
    SIMULACION_RAPIDA = False

# Selección automática de configuración
def get_config():
    """
    Selecciona configuración según variable de entorno
    """
    env = os.getenv('PROGOL_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig
    else:
        return DevelopmentConfig

# Configuración actual
Config = get_config()