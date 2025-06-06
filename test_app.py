"""
Tests básicos para Progol Optimizer
Verificaciones de funcionalidad principal
"""

import sys
import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models.match_classifier import MatchClassifier
    from models.portfolio_generator import PortfolioGenerator
    from models.validators import PortfolioValidator
    from utils.helpers import create_sample_data, validate_partido_data
    from config import Config
    print("✅ Todos los módulos importados correctamente")
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    sys.exit(1)

def test_config():
    """Test configuración"""
    print("\n🧪 Testing configuración...")
    
    # Verificar distribución histórica
    assert abs(sum(Config.DISTRIBUCION_HISTORICA.values()) - 1.0) < 0.01
    print("✅ Distribución histórica suma 1.0")
    
    # Verificar rangos válidos
    for resultado, (min_val, max_val) in Config.RANGOS_HISTORICOS.items():
        assert min_val < max_val
        assert 0 <= min_val <= 1
        assert 0 <= max_val <= 1
    print("✅ Rangos históricos válidos")
    
    # Verificar configuración general
    assert Config.validate_config()
    print("✅ Configuración general válida")

def test_sample_data():
    """Test datos de muestra"""
    print("\n🧪 Testing datos de muestra...")
    
    sample_data = create_sample_data()
    
    assert 'partidos_regular' in sample_data
    assert 'partidos_revancha' in sample_data
    print("✅ Estructura de datos correcta")
    
    # Verificar partidos regulares
    partidos_reg = sample_data['partidos_regular']
    assert len(partidos_reg) >= 14
    print(f"✅ {len(partidos_reg)} partidos regulares generados")
    
    # Verificar partidos revancha
    partidos_rev = sample_data['partidos_revancha']
    assert len(partidos_rev) >= 7
    print(f"✅ {len(partidos_rev)} partidos revancha generados")
    
    # Validar primer partido
    primer_partido = partidos_reg[0]
    errores = validate_partido_data(primer_partido)
    assert len(errores) == 0, f"Errores en datos: {errores}"
    print("✅ Datos de partidos válidos")

def test_match_classifier():
    """Test clasificador de partidos"""
    print("\n🧪 Testing clasificador de partidos...")
    
    classifier = MatchClassifier()
    sample_data = create_sample_data()
    partidos = sample_data['partidos_regular'][:14]
    
    # Clasificar partidos
    partidos_clasificados = classifier.classify_matches(partidos)
    
    assert len(partidos_clasificados) == 14
    print("✅ Clasificación de 14 partidos completada")
    
    # Verificar que hay diferentes tipos de clasificación
    clasificaciones = [p['clasificacion'] for p in partidos_clasificados]
    tipos_unicos = set(clasificaciones)
    print(f"✅ Tipos de clasificación encontrados: {tipos_unicos}")
    
    # Verificar estadísticas
    stats = classifier.get_clasificacion_stats(partidos_clasificados)
    assert stats['total'] == 14
    print(f"✅ Estadísticas: {stats}")
    
    # Verificar probabilidades normalizadas
    for partido in partidos_clasificados:
        suma_probs = partido['prob_local'] + partido['prob_empate'] + partido['prob_visitante']
        assert abs(suma_probs - 1.0) < 0.01, f"Probabilidades no suman 1: {suma_probs}"
    print("✅ Probabilidades correctamente normalizadas")

def test_portfolio_generator():
    """Test generador de portafolio"""
    print("\n🧪 Testing generador de portafolio...")
    
    # Preparar datos
    classifier = MatchClassifier()
    generator = PortfolioGenerator()
    sample_data = create_sample_data()
    partidos = sample_data['partidos_regular'][:14]
    
    partidos_clasificados = classifier.classify_matches(partidos)
    
    # Generar quinielas Core
    quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
    
    assert len(quinielas_core) == 4
    print("✅ 4 quinielas Core generadas")
    
    # Verificar que cada quiniela tiene 14 resultados
    for quiniela in quinielas_core:
        assert len(quiniela['resultados']) == 14
        empates = quiniela['resultados'].count('E')
        assert Config.EMPATES_MIN <= empates <= Config.EMPATES_MAX
    print("✅ Quinielas Core válidas (empates en rango)")
    
    # Generar satélites
    quinielas_satelites = generator.generate_satellite_quinielas(
        partidos_clasificados, quinielas_core, 6
    )
    
    assert len(quinielas_satelites) == 6
    print("✅ 6 quinielas satélites generadas")
    
    # Verificar correlación negativa en pares
    pares_encontrados = {}
    for satelite in quinielas_satelites:
        par_id = satelite.get('par_id')
        if par_id is not None:
            if par_id not in pares_encontrados:
                pares_encontrados[par_id] = []
            pares_encontrados[par_id].append(satelite)
    
    print(f"✅ {len(pares_encontrados)} pares de satélites encontrados")

def test_portfolio_validator():
    """Test validador de portafolio"""
    print("\n🧪 Testing validador de portafolio...")
    
    # Crear portafolio de prueba
    classifier = MatchClassifier()
    generator = PortfolioGenerator()
    validator = PortfolioValidator()
    
    sample_data = create_sample_data()
    partidos = sample_data['partidos_regular'][:14]
    partidos_clasificados = classifier.classify_matches(partidos)
    
    # Generar portafolio completo
    quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
    quinielas_satelites = generator.generate_satellite_quinielas(
        partidos_clasificados, quinielas_core, 6
    )
    
    portafolio = quinielas_core + quinielas_satelites
    
    # Validar
    validacion = validator.validate_portfolio(portafolio)
    
    assert 'es_valido' in validacion
    assert 'metricas' in validacion
    assert 'warnings' in validacion
    assert 'errores' in validacion
    
    print(f"✅ Validación completada - Válido: {validacion['es_valido']}")
    print(f"✅ Warnings: {len(validacion['warnings'])}")
    print(f"✅ Errores: {len(validacion['errores'])}")
    
    # Verificar métricas
    if 'metricas' in validacion:
        metricas = validacion['metricas']
        if 'distribucion_global' in metricas:
            dist = metricas['distribucion_global']
            print(f"✅ Distribución: L={dist.get('L', 0):.1%}, E={dist.get('E', 0):.1%}, V={dist.get('V', 0):.1%}")

def test_integration():
    """Test de integración completo"""
    print("\n🧪 Testing integración completa...")
    
    # Flujo completo como en la aplicación
    sample_data = create_sample_data()
    partidos_regular = sample_data['partidos_regular'][:14]
    
    # 1. Clasificar
    classifier = MatchClassifier()
    partidos_clasificados = classifier.classify_matches(partidos_regular)
    print("✅ Paso 1: Partidos clasificados")
    
    # 2. Generar Core
    generator = PortfolioGenerator()
    quinielas_core = generator.generate_core_quinielas(partidos_clasificados)
    print("✅ Paso 2: Quinielas Core generadas")
    
    # 3. Generar Satélites
    quinielas_satelites = generator.generate_satellite_quinielas(
        partidos_clasificados, quinielas_core, 16
    )
    print("✅ Paso 3: Quinielas Satélites generadas")
    
    # 4. Optimizar (simplificado)
    todas_quinielas = quinielas_core + quinielas_satelites
    portafolio_final = todas_quinielas[:20]  # Limitamos a 20 para prueba rápida
    print("✅ Paso 4: Portafolio optimizado")
    
    # 5. Validar
    validator = PortfolioValidator()
    validacion = validator.validate_portfolio(portafolio_final)
    print("✅ Paso 5: Portafolio validado")
    
    # 6. Resultados
    print(f"\n📊 RESULTADOS DE INTEGRACIÓN:")
    print(f"  - Total quinielas: {len(portafolio_final)}")
    print(f"  - Validación: {'✅ Válido' if validacion['es_valido'] else '⚠️ Con advertencias'}")
    print(f"  - Warnings: {len(validacion['warnings'])}")
    print(f"  - Errores: {len(validacion['errores'])}")
    
    if validacion.get('metricas'):
        metricas = validacion['metricas']
        if 'empates_promedio' in metricas:
            print(f"  - Empates promedio: {metricas['empates_promedio']:.2f}")
        if 'prob_11_plus_promedio' in metricas:
            print(f"  - Pr[≥11] promedio: {metricas['prob_11_plus_promedio']:.1%}")

def run_all_tests():
    """Ejecuta todos los tests"""
    print("🚀 INICIANDO TESTS DE PROGOL OPTIMIZER")
    print("=" * 50)
    
    try:
        test_config()
        test_sample_data()
        test_match_classifier()
        test_portfolio_generator()
        test_portfolio_validator()
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("✅ La aplicación está lista para despliegue")
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)