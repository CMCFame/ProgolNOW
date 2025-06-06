import pandas as pd
import numpy as np
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
import streamlit as st

class ProgolDataLoader:
    """
    Carga y procesa datos históricos de Progol para calibración
    """
    
    @staticmethod
    def load_historical_data(file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Carga datos históricos de Progol
        Si no se proporciona archivo, usa datos sintéticos para demostración
        """
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    return pd.read_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    return pd.read_excel(file_path)
                else:
                    st.error("Formato de archivo no soportado. Use CSV o XLSX.")
                    return pd.DataFrame()
            except Exception as e:
                st.error(f"Error cargando archivo: {str(e)}")
                return pd.DataFrame()
        else:
            # Generar datos sintéticos para demostración
            return ProgolDataLoader._generate_synthetic_data()
    
    @staticmethod
    def _generate_synthetic_data() -> pd.DataFrame:
        """
        Genera datos sintéticos basados en distribuciones históricas conocidas
        """
        np.random.seed(42)
        
        # Simular 100 concursos históricos
        concursos = []
        
        for concurso_id in range(2180, 2280):
            for partido_num in range(1, 15):
                # Distribución basada en metodología: 38% L, 29% E, 33% V
                resultado = np.random.choice(['L', 'E', 'V'], p=[0.38, 0.29, 0.33])
                
                concursos.append({
                    'concurso_id': concurso_id,
                    'partido_num': partido_num,
                    'resultado': resultado,
                    'fecha': f"2024-{(concurso_id % 12) + 1:02d}-{(partido_num % 28) + 1:02d}"
                })
        
        return pd.DataFrame(concursos)
    
    @staticmethod
    def calculate_historical_stats(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calcula estadísticas históricas del DataFrame
        """
        if df.empty:
            return {}
        
        stats = {}
        
        # Distribución general
        if 'resultado' in df.columns:
            dist = df['resultado'].value_counts(normalize=True)
            stats['distribucion_general'] = {
                'L': dist.get('L', 0),
                'E': dist.get('E', 0),
                'V': dist.get('V', 0)
            }
        
        # Empates por concurso
        if 'concurso_id' in df.columns and 'resultado' in df.columns:
            empates_por_concurso = df[df['resultado'] == 'E'].groupby('concurso_id').size()
            stats['empates_promedio'] = empates_por_concurso.mean()
            stats['empates_std'] = empates_por_concurso.std()
        
        # Tendencias por posición de partido
        if 'partido_num' in df.columns and 'resultado' in df.columns:
            tendencias_posicion = df.groupby('partido_num')['resultado'].value_counts(normalize=True).unstack(fill_value=0)
            stats['tendencias_por_posicion'] = tendencias_posicion.to_dict()
        
        return stats

class ProgolExporter:
    """
    Exporta quinielas en diferentes formatos
    """
    
    @staticmethod
    def export_to_csv(quinielas: List[Dict], partidos: List[Dict]) -> str:
        """
        Exporta quinielas a formato CSV
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Encabezados
        headers = ['Quiniela']
        for i in range(14):
            headers.append(f'Partido_{i+1}')
        headers.extend(['Empates', 'Prob_11_Plus', 'Tipo'])
        
        writer.writerow(headers)
        
        # Datos
        for i, quiniela in enumerate(quinielas):
            row = [f"Q-{i+1}"]
            row.extend(quiniela['resultados'])
            row.extend([
                quiniela.get('empates', quiniela['resultados'].count('E')),
                f"{quiniela.get('prob_11_plus', 0):.3f}",
                quiniela.get('tipo', 'Desconocido')
            ])
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_progol_format(quinielas: List[Dict], partidos: List[Dict]) -> str:
        """
        Exporta en formato específico para Progol (texto plano)
        """
        lines = []
        lines.append("PROGOL OPTIMIZER - QUINIELAS OPTIMIZADAS")
        lines.append("=" * 50)
        lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total quinielas: {len(quinielas)}")
        lines.append("")
        
        # Información de partidos
        lines.append("PARTIDOS:")
        for i, partido in enumerate(partidos[:14]):
            lines.append(f"{i+1:2d}. {partido['local']} vs {partido['visitante']}")
        lines.append("")
        
        # Quinielas
        lines.append("QUINIELAS:")
        for i, quiniela in enumerate(quinielas):
            resultados_str = ' '.join(quiniela['resultados'])
            prob_str = f"{quiniela.get('prob_11_plus', 0):.1%}"
            lines.append(f"Q-{i+1:2d}: {resultados_str} | Empates: {quiniela.get('empates', 0)} | Pr[≥11]: {prob_str}")
        
        lines.append("")
        
        # Estadísticas
        if quinielas:
            lines.append("ESTADÍSTICAS:")
            empates_promedio = np.mean([q.get('empates', q['resultados'].count('E')) for q in quinielas])
            prob_promedio = np.mean([q.get('prob_11_plus', 0) for q in quinielas])
            
            lines.append(f"Empates promedio: {empates_promedio:.2f}")
            lines.append(f"Pr[≥11] promedio: {prob_promedio:.1%}")
            
            # Distribución
            total_predicciones = len(quinielas) * 14
            conteos = {'L': 0, 'E': 0, 'V': 0}
            for q in quinielas:
                for r in q['resultados']:
                    conteos[r] += 1
            
            lines.append(f"Distribución: L={conteos['L']/total_predicciones:.1%}, "
                        f"E={conteos['E']/total_predicciones:.1%}, "
                        f"V={conteos['V']/total_predicciones:.1%}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def export_to_json(quinielas: List[Dict], partidos: List[Dict], 
                      validacion: Optional[Dict] = None) -> str:
        """
        Exporta todo a formato JSON estructurado
        """
        export_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'total_quinielas': len(quinielas),
                'metodologia': 'Core + Satélites con optimización GRASP-Annealing'
            },
            'partidos': partidos,
            'quinielas': quinielas,
            'validacion': validacion or {},
            'estadisticas': ProgolExporter._calculate_export_stats(quinielas)
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _calculate_export_stats(quinielas: List[Dict]) -> Dict[str, Any]:
        """
        Calcula estadísticas para exportación
        """
        if not quinielas:
            return {}
        
        # Distribución
        total_predicciones = len(quinielas) * 14
        conteos = {'L': 0, 'E': 0, 'V': 0}
        for q in quinielas:
            for r in q['resultados']:
                conteos[r] += 1
        
        distribucion = {k: v/total_predicciones for k, v in conteos.items()}
        
        # Empates
        empates_por_quiniela = [q.get('empates', q['resultados'].count('E')) for q in quinielas]
        
        # Probabilidades
        probs_11_plus = [q.get('prob_11_plus', 0) for q in quinielas]
        
        return {
            'distribucion': distribucion,
            'empates': {
                'promedio': np.mean(empates_por_quiniela),
                'minimo': min(empates_por_quiniela),
                'maximo': max(empates_por_quiniela),
                'desviacion': np.std(empates_por_quiniela)
            },
            'probabilidades_11_plus': {
                'promedio': np.mean(probs_11_plus),
                'minimo': min(probs_11_plus),
                'maximo': max(probs_11_plus),
                'portafolio': 1 - np.prod([1 - p for p in probs_11_plus])
            }
        }

class ProgolAnalyzer:
    """
    Herramientas de análisis para quinielas
    """
    
    @staticmethod
    def analyze_concentration_risk(quinielas: List[Dict]) -> Dict[str, Any]:
        """
        Analiza riesgo de concentración en el portafolio
        """
        if not quinielas:
            return {}
        
        concentraciones = []
        
        for partido_idx in range(14):
            conteos = {'L': 0, 'E': 0, 'V': 0}
            
            for quiniela in quinielas:
                if partido_idx < len(quiniela['resultados']):
                    resultado = quiniela['resultados'][partido_idx]
                    conteos[resultado] += 1
            
            total = sum(conteos.values())
            if total > 0:
                max_concentracion = max(conteos.values()) / total
                resultado_dominante = max(conteos, key=conteos.get)
                
                concentraciones.append({
                    'partido': partido_idx + 1,
                    'concentracion': max_concentracion,
                    'resultado_dominante': resultado_dominante,
                    'distribucion': {k: v/total for k, v in conteos.items()}
                })
        
        # Estadísticas de concentración
        concentraciones_valores = [c['concentracion'] for c in concentraciones]
        
        return {
            'concentraciones_por_partido': concentraciones,
            'concentracion_promedio': np.mean(concentraciones_valores),
            'concentracion_maxima': max(concentraciones_valores),
            'partidos_riesgo_alto': [c for c in concentraciones if c['concentracion'] > 0.7],
            'riesgo_general': 'Alto' if max(concentraciones_valores) > 0.8 else 'Medio' if max(concentraciones_valores) > 0.7 else 'Bajo'
        }
    
    @staticmethod
    def simulate_outcomes(quinielas: List[Dict], partidos_clasificados: List[Dict], 
                         num_simulaciones: int = 1000) -> Dict[str, Any]:
        """
        Simula resultados del portafolio usando Monte Carlo
        """
        resultados_simulacion = []
        
        for _ in range(num_simulaciones):
            # Simular resultados reales de los 14 partidos
            resultados_reales = []
            for partido in partidos_clasificados:
                prob_l = partido['prob_local']
                prob_e = partido['prob_empate']
                prob_v = partido['prob_visitante']
                
                resultado = np.random.choice(['L', 'E', 'V'], p=[prob_l, prob_e, prob_v])
                resultados_reales.append(resultado)
            
            # Evaluar cada quiniela contra resultados reales
            aciertos_por_quiniela = []
            for quiniela in quinielas:
                aciertos = sum(1 for pred, real in zip(quiniela['resultados'], resultados_reales) 
                             if pred == real)
                aciertos_por_quiniela.append(aciertos)
            
            # Estadísticas de la simulación
            max_aciertos = max(aciertos_por_quiniela)
            quinielas_11_plus = sum(1 for a in aciertos_por_quiniela if a >= 11)
            quinielas_10_plus = sum(1 for a in aciertos_por_quiniela if a >= 10)
            
            resultados_simulacion.append({
                'max_aciertos': max_aciertos,
                'quinielas_11_plus': quinielas_11_plus,
                'quinielas_10_plus': quinielas_10_plus,
                'aciertos_promedio': np.mean(aciertos_por_quiniela)
            })
        
        # Estadísticas finales
        max_aciertos_dist = [r['max_aciertos'] for r in resultados_simulacion]
        prob_11_plus = sum(1 for r in resultados_simulacion if r['quinielas_11_plus'] > 0) / num_simulaciones
        prob_10_plus = sum(1 for r in resultados_simulacion if r['quinielas_10_plus'] > 0) / num_simulaciones
        
        return {
            'probabilidad_11_plus': prob_11_plus,
            'probabilidad_10_plus': prob_10_plus,
            'aciertos_maximos_promedio': np.mean(max_aciertos_dist),
            'distribucion_max_aciertos': np.histogram(max_aciertos_dist, bins=range(0, 15))[0].tolist(),
            'estadisticas_detalladas': {
                'percentil_25': np.percentile(max_aciertos_dist, 25),
                'percentil_50': np.percentile(max_aciertos_dist, 50),
                'percentil_75': np.percentile(max_aciertos_dist, 75),
                'percentil_90': np.percentile(max_aciertos_dist, 90)
            }
        }
    
    @staticmethod
    def compare_strategies(quinielas_core: List[Dict], quinielas_optimizadas: List[Dict],
                          partidos_clasificados: List[Dict]) -> Dict[str, Any]:
        """
        Compara estrategia Core vs optimizada
        """
        comparison = {}
        
        # Simulación para ambas estrategias
        sim_core = ProgolAnalyzer.simulate_outcomes(quinielas_core, partidos_clasificados, 500)
        sim_optimizada = ProgolAnalyzer.simulate_outcomes(quinielas_optimizadas, partidos_clasificados, 500)
        
        comparison['core'] = {
            'prob_11_plus': sim_core['probabilidad_11_plus'],
            'aciertos_max_promedio': sim_core['aciertos_maximos_promedio'],
            'num_quinielas': len(quinielas_core)
        }
        
        comparison['optimizada'] = {
            'prob_11_plus': sim_optimizada['probabilidad_11_plus'],
            'aciertos_max_promedio': sim_optimizada['aciertos_maximos_promedio'],
            'num_quinielas': len(quinielas_optimizadas)
        }
        
        # Mejoras
        mejora_prob = sim_optimizada['probabilidad_11_plus'] - sim_core['probabilidad_11_plus']
        mejora_aciertos = sim_optimizada['aciertos_maximos_promedio'] - sim_core['aciertos_maximos_promedio']
        
        comparison['mejoras'] = {
            'probabilidad_11_plus': mejora_prob,
            'aciertos_promedio': mejora_aciertos,
            'lift_porcentual': mejora_prob / max(sim_core['probabilidad_11_plus'], 0.01) * 100
        }
        
        return comparison

# ============================================================================
# NUEVAS FUNCIONES PARA SOLUCIONAR ERROR JSON Y CARGA CSV
# ============================================================================

def clean_for_json(obj):
    """
    Limpia objetos para serialización JSON, convirtiendo tipos numpy a tipos nativos de Python
    """
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(clean_for_json(item) for item in obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif pd.isna(obj):
        return None
    else:
        return obj

def safe_json_dumps(obj, **kwargs):
    """
    JSON dumps seguro que limpia automáticamente los tipos numpy
    """
    cleaned_obj = clean_for_json(obj)
    return json.dumps(cleaned_obj, **kwargs)

def load_partidos_from_csv(file_path_or_buffer, tipo='regular'):
    """
    Carga partidos desde archivo CSV
    
    Args:
        file_path_or_buffer: Ruta al archivo CSV o buffer de datos
        tipo: 'regular' para 14 partidos o 'revancha' para 7 partidos
    
    Returns:
        List[Dict]: Lista de partidos cargados
    """
    try:
        # Leer CSV
        if hasattr(file_path_or_buffer, 'read'):
            # Es un buffer (archivo subido en Streamlit)
            df = pd.read_csv(file_path_or_buffer)
        else:
            # Es una ruta de archivo
            df = pd.read_csv(file_path_or_buffer)
        
        # Validar columnas requeridas
        columnas_requeridas = ['local', 'visitante', 'prob_local', 'prob_empate', 'prob_visitante']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            raise ValueError(f"Columnas faltantes en CSV: {columnas_faltantes}")
        
        # Validar número de filas
        max_partidos = 14 if tipo == 'regular' else 7
        if len(df) > max_partidos:
            st.warning(f"CSV tiene {len(df)} filas, se tomarán las primeras {max_partidos}")
            df = df.head(max_partidos)
        
        # Convertir a lista de diccionarios
        partidos = []
        for _, row in df.iterrows():
            # Normalizar probabilidades
            prob_total = row['prob_local'] + row['prob_empate'] + row['prob_visitante']
            
            if prob_total <= 0:
                raise ValueError(f"Probabilidades inválidas en fila {row.name + 1}")
            
            partido = {
                'local': str(row['local']).strip(),
                'visitante': str(row['visitante']).strip(),
                'prob_local': float(row['prob_local']) / prob_total,
                'prob_empate': float(row['prob_empate']) / prob_total,
                'prob_visitante': float(row['prob_visitante']) / prob_total,
                'es_final': bool(row.get('es_final', False)),
                'forma_diferencia': int(row.get('forma_diferencia', 0)),
                'lesiones_impact': int(row.get('lesiones_impact', 0))
            }
            
            # Validar datos del partido
            errores = validate_partido_data(partido)
            if errores:
                raise ValueError(f"Errores en fila {row.name + 1}: {'; '.join(errores)}")
            
            partidos.append(partido)
        
        return partidos
        
    except Exception as e:
        raise ValueError(f"Error cargando CSV: {str(e)}")

def generate_csv_template(tipo='regular'):
    """
    Genera template CSV para cargar partidos
    
    Args:
        tipo: 'regular' para 14 partidos o 'revancha' para 7 partidos
    
    Returns:
        str: Contenido CSV como string
    """
    num_partidos = 14 if tipo == 'regular' else 7
    
    # Crear datos de ejemplo
    data = []
    equipos_ejemplo = [
        ('Real Madrid', 'Barcelona'), ('Manchester United', 'Liverpool'),
        ('PSG', 'Bayern Munich'), ('Chelsea', 'Arsenal'),
        ('Juventus', 'Inter Milan'), ('Atletico Madrid', 'Sevilla'),
        ('Borussia Dortmund', 'Bayern Leverkusen'), ('AC Milan', 'Napoli'),
        ('Ajax', 'PSV'), ('Porto', 'Benfica'),
        ('Lyon', 'Marseille'), ('Valencia', 'Athletic Bilbao'),
        ('Roma', 'Lazio'), ('Tottenham', 'West Ham')
    ]
    
    # Para revancha, usar equipos latinoamericanos
    if tipo == 'revancha':
        equipos_ejemplo = [
            ('Flamengo', 'Palmeiras'), ('Boca Juniors', 'River Plate'),
            ('America', 'Chivas'), ('São Paulo', 'Corinthians'),
            ('Cruz Azul', 'Pumas'), ('Santos', 'Fluminense'),
            ('Monterrey', 'Tigres')
        ]
    
    for i in range(num_partidos):
        if i < len(equipos_ejemplo):
            local, visitante = equipos_ejemplo[i]
        else:
            local, visitante = f'Equipo_{i*2+1}', f'Equipo_{i*2+2}'
        
        # Generar probabilidades de ejemplo
        import random
        random.seed(42 + i)  # Semilla fija para consistencia
        
        # Distribución realista: favorito local ligeramente
        prob_local = random.uniform(0.30, 0.50)
        prob_empate = random.uniform(0.20, 0.35)
        prob_visitante = 1.0 - prob_local - prob_empate
        
        if prob_visitante < 0.15:  # Ajustar si muy bajo
            prob_visitante = 0.15
            total = prob_local + prob_empate + prob_visitante
            prob_local /= total
            prob_empate /= total
            prob_visitante /= total
        
        data.append({
            'local': local,
            'visitante': visitante,
            'prob_local': round(prob_local, 3),
            'prob_empate': round(prob_empate, 3),
            'prob_visitante': round(prob_visitante, 3),
            'es_final': 'FALSE' if i > 0 else 'TRUE',  # Primer partido como final de ejemplo
            'forma_diferencia': random.randint(-2, 2),
            'lesiones_impact': random.randint(-1, 1)
        })
    
    # Convertir a CSV
    output = io.StringIO()
    if data:
        fieldnames = ['local', 'visitante', 'prob_local', 'prob_empate', 'prob_visitante', 
                     'es_final', 'forma_diferencia', 'lesiones_impact']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    return output.getvalue()

# ============================================================================
# FUNCIONES AUXILIARES ORIGINALES
# ============================================================================

def load_historical_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Función auxiliar para cargar datos históricos
    """
    return ProgolDataLoader.load_historical_data(file_path)

def export_quinielas(quinielas: List[Dict], partidos: List[Dict], 
                    formato: str = 'csv') -> str:
    """
    Función auxiliar para exportar quinielas
    """
    if formato.lower() == 'csv':
        return ProgolExporter.export_to_csv(quinielas, partidos)
    elif formato.lower() == 'json':
        return ProgolExporter.export_to_json(quinielas, partidos)
    elif formato.lower() == 'progol':
        return ProgolExporter.export_to_progol_format(quinielas, partidos)
    else:
        raise ValueError(f"Formato no soportado: {formato}")

def validate_partido_data(partido: Dict) -> List[str]:
    """
    Valida datos de un partido individual
    """
    errores = []
    
    # Campos requeridos
    campos_requeridos = ['local', 'visitante', 'prob_local', 'prob_empate', 'prob_visitante']
    for campo in campos_requeridos:
        if campo not in partido:
            errores.append(f"Campo requerido faltante: {campo}")
    
    # Validar probabilidades
    if all(campo in partido for campo in ['prob_local', 'prob_empate', 'prob_visitante']):
        probs = [partido['prob_local'], partido['prob_empate'], partido['prob_visitante']]
        
        # Verificar que son números
        if not all(isinstance(p, (int, float)) for p in probs):
            errores.append("Las probabilidades deben ser números")
        
        # Verificar rango
        if not all(0 <= p <= 1 for p in probs):
            errores.append("Las probabilidades deben estar entre 0 y 1")
        
        # Verificar suma aproximada a 1
        suma = sum(probs)
        if abs(suma - 1.0) > 0.05:
            errores.append(f"Las probabilidades deben sumar ~1.0 (suma actual: {suma:.3f})")
    
    # Validar nombres de equipos
    if 'local' in partido and not partido['local'].strip():
        errores.append("Nombre del equipo local no puede estar vacío")
    
    if 'visitante' in partido and not partido['visitante'].strip():
        errores.append("Nombre del equipo visitante no puede estar vacío")
    
    return errores

def create_sample_data() -> Dict[str, Any]:
    """
    Crea datos de muestra para demostración
    """
    sample_partidos = [
        {
            'local': 'Real Madrid', 'visitante': 'Barcelona',
            'prob_local': 0.35, 'prob_empate': 0.30, 'prob_visitante': 0.35,
            'es_final': True, 'forma_diferencia': 0, 'lesiones_impact': 0
        },
        {
            'local': 'Manchester United', 'visitante': 'Liverpool',
            'prob_local': 0.40, 'prob_empate': 0.25, 'prob_visitante': 0.35,
            'es_final': False, 'forma_diferencia': 1, 'lesiones_impact': -1
        },
        {
            'local': 'PSG', 'visitante': 'Bayern Munich',
            'prob_local': 0.30, 'prob_empate': 0.35, 'prob_visitante': 0.35,
            'es_final': True, 'forma_diferencia': -1, 'lesiones_impact': 0
        }
    ]
    
    # Generar más partidos de muestra
    equipos_muestra = [
        ('Chelsea', 'Arsenal'), ('Juventus', 'Inter Milan'), ('Atletico Madrid', 'Sevilla'),
        ('Borussia Dortmund', 'Bayern Leverkusen'), ('AC Milan', 'Napoli'),
        ('Ajax', 'PSV'), ('Porto', 'Benfica'), ('Lyon', 'Marseille'),
        ('Valencia', 'Athletic Bilbao'), ('Roma', 'Lazio'), ('Tottenham', 'West Ham')
    ]
    
    np.random.seed(42)
    
    for local, visitante in equipos_muestra:
        # Generar probabilidades aleatorias pero realistas
        prob_base = np.random.dirichlet([4, 3, 3])  # Sesgo hacia local
        
        sample_partidos.append({
            'local': local, 'visitante': visitante,
            'prob_local': prob_base[0], 'prob_empate': prob_base[1], 'prob_visitante': prob_base[2],
            'es_final': np.random.choice([True, False], p=[0.1, 0.9]),
            'forma_diferencia': np.random.randint(-2, 3),
            'lesiones_impact': np.random.randint(-1, 2)
        })
    
    return {
        'partidos_regular': sample_partidos,
        'partidos_revancha': sample_partidos[:7]  # Primeros 7 para revancha
    }