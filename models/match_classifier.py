import numpy as np
from typing import List, Dict, Any

class MatchClassifier:
    """
    Clasifica partidos según la metodología definitiva Progol:
    - Ancla: >60% confianza en un resultado
    - Divisor: Alta incertidumbre (40-60% máxima probabilidad)
    - Tendencia Empate: >30% probabilidad de empate y condiciones específicas
    - Neutro: El resto
    """
    
    def __init__(self, 
                 umbral_ancla: float = 0.60,
                 umbral_divisor_min: float = 0.40,
                 umbral_divisor_max: float = 0.60,
                 umbral_empate: float = 0.30):
        
        self.umbral_ancla = umbral_ancla
        self.umbral_divisor_min = umbral_divisor_min
        self.umbral_divisor_max = umbral_divisor_max
        self.umbral_empate = umbral_empate
        
    def classify_matches(self, partidos: List[Dict]) -> List[Dict]:
        """
        Clasifica cada partido y aplica calibración bayesiana simplificada
        """
        partidos_clasificados = []
        
        for i, partido in enumerate(partidos):
            # Aplicar calibración bayesiana
            partido_calibrado = self._aplicar_calibracion_bayesiana(partido)
            
            # Clasificar según probabilidades calibradas
            clasificacion = self._clasificar_partido(partido_calibrado)
            
            # Crear objeto partido clasificado
            partido_procesado = {
                'id': i,
                'local': partido['local'],
                'visitante': partido['visitante'],
                'prob_local': partido_calibrado['prob_local'],
                'prob_empate': partido_calibrado['prob_empate'],
                'prob_visitante': partido_calibrado['prob_visitante'],
                'clasificacion': clasificacion,
                'resultado_sugerido': self._get_resultado_sugerido(partido_calibrado),
                'confianza': self._calcular_confianza(partido_calibrado),
                'factores_contextuales': self._extraer_factores_contextuales(partido)
            }
            
            partidos_clasificados.append(partido_procesado)
        
        return partidos_clasificados
    
    def _aplicar_calibracion_bayesiana(self, partido: Dict) -> Dict:
        """
        Aplica calibración bayesiana simplificada usando factores contextuales
        Basado en la ecuación del documento: p_final = p_raw * (1 + k1*ΔForma + k2*Lesiones + k3*Contexto) / Z
        """
        # Coeficientes calibrados empíricamente (simplificados)
        k1 = 0.15  # Factor forma
        k2 = 0.10  # Factor lesiones
        k3 = 0.20  # Factor contexto (finales, derbis)
        
        # Extraer factores
        delta_forma = partido.get('forma_diferencia', 0)
        lesiones_impact = partido.get('lesiones_impact', 0)
        contexto = 1.0 if partido.get('es_final', False) else 0.0
        
        # Calcular factor de ajuste
        factor_ajuste = 1 + k1 * delta_forma + k2 * lesiones_impact + k3 * contexto
        
        # Aplicar ajuste a probabilidades
        prob_local_ajustada = partido['prob_local'] * factor_ajuste
        prob_empate_ajustada = partido['prob_empate']  # Los empates se ajustan diferente
        prob_visitante_ajustada = partido['prob_visitante'] / factor_ajuste if factor_ajuste > 0 else partido['prob_visitante']
        
        # Aplicar regla de draw-propensity
        prob_empate_ajustada = self._aplicar_draw_propensity(
            prob_local_ajustada, prob_empate_ajustada, prob_visitante_ajustada
        )
        
        # Renormalizar
        total = prob_local_ajustada + prob_empate_ajustada + prob_visitante_ajustada
        
        if total > 0:
            return {
                'prob_local': prob_local_ajustada / total,
                'prob_empate': prob_empate_ajustada / total,
                'prob_visitante': prob_visitante_ajustada / total
            }
        else:
            return partido  # Devolver original si hay error
    
    def _aplicar_draw_propensity(self, prob_l: float, prob_e: float, prob_v: float) -> float:
        """
        Aplica la regla de draw-propensity del documento:
        Si |p_L - p_V| < 0.08 y p_E > max(p_L, p_V), entonces p_E += 0.06
        """
        if abs(prob_l - prob_v) < 0.08 and prob_e > max(prob_l, prob_v):
            return min(prob_e + 0.06, 0.95)  # Cap para evitar probabilidades extremas
        return prob_e
    
    def _clasificar_partido(self, partido: Dict) -> str:
        """
        Clasifica el partido según los umbrales definidos
        """
        probs = [partido['prob_local'], partido['prob_empate'], partido['prob_visitante']]
        max_prob = max(probs)
        
        # Regla para Ancla
        if max_prob > self.umbral_ancla:
            return 'Ancla'
        
        # Regla para Tendencia Empate
        if (partido['prob_empate'] > self.umbral_empate and 
            partido['prob_empate'] >= max(partido['prob_local'], partido['prob_visitante'])):
            return 'TendenciaEmpate'
        
        # Regla para Divisor
        if self.umbral_divisor_min < max_prob < self.umbral_divisor_max:
            return 'Divisor'
        
        # Por defecto
        return 'Neutro'
    
    def _get_resultado_sugerido(self, partido: Dict) -> str:
        """
        Obtiene el resultado sugerido basado en máxima probabilidad
        """
        probs = {
            'L': partido['prob_local'],
            'E': partido['prob_empate'],
            'V': partido['prob_visitante']
        }
        return max(probs, key=probs.get)
    
    def _calcular_confianza(self, partido: Dict) -> float:
        """
        Calcula nivel de confianza como la diferencia entre primera y segunda opción
        """
        probs = [partido['prob_local'], partido['prob_empate'], partido['prob_visitante']]
        probs_sorted = sorted(probs, reverse=True)
        return probs_sorted[0] - probs_sorted[1]
    
    def _extraer_factores_contextuales(self, partido: Dict) -> Dict:
        """
        Extrae y estructura los factores contextuales
        """
        return {
            'es_final': partido.get('es_final', False),
            'forma_diferencia': partido.get('forma_diferencia', 0),
            'lesiones_impact': partido.get('lesiones_impact', 0),
            'volatilidad': self._calcular_volatilidad(partido)
        }
    
    def _calcular_volatilidad(self, partido: Dict) -> float:
        """
        Calcula volatilidad basada en la distribución de probabilidades
        Entropía de Shannon normalizada
        """
        probs = [partido['prob_local'], partido['prob_empate'], partido['prob_visitante']]
        # Evitar log(0)
        probs = [max(p, 1e-10) for p in probs]
        
        entropia = -sum(p * np.log(p) for p in probs)
        # Normalizar por máxima entropía posible (log(3))
        return entropia / np.log(3)
    
    def get_clasificacion_stats(self, partidos_clasificados: List[Dict]) -> Dict:
        """
        Obtiene estadísticas de la clasificación
        """
        clasificaciones = [p['clasificacion'] for p in partidos_clasificados]
        
        stats = {
            'total': len(partidos_clasificados),
            'ancla': clasificaciones.count('Ancla'),
            'divisor': clasificaciones.count('Divisor'),
            'tendencia_empate': clasificaciones.count('TendenciaEmpate'),
            'neutro': clasificaciones.count('Neutro')
        }
        
        # Agregar porcentajes
        total = stats['total']
        if total > 0:
            for key in ['ancla', 'divisor', 'tendencia_empate', 'neutro']:
                stats[f'{key}_pct'] = stats[key] / total
        
        return stats
    
    def aplicar_regularizacion_global(self, partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Aplica regularización global para mantener rangos históricos:
        - 35-41% locales, 25-33% empates, 30-36% visitantes
        """
        # Calcular distribución actual
        resultados_sugeridos = [p['resultado_sugerido'] for p in partidos_clasificados]
        total = len(resultados_sugeridos)
        
        if total == 0:
            return partidos_clasificados
        
        dist_actual = {
            'L': resultados_sugeridos.count('L') / total,
            'E': resultados_sugeridos.count('E') / total,
            'V': resultados_sugeridos.count('V') / total
        }
        
        # Rangos objetivo
        rangos_objetivo = {
            'L': (0.35, 0.41),
            'E': (0.25, 0.33),
            'V': (0.30, 0.36)
        }
        
        # Verificar si necesita ajuste
        necesita_ajuste = False
        for resultado, (min_val, max_val) in rangos_objetivo.items():
            if not (min_val <= dist_actual[resultado] <= max_val):
                necesita_ajuste = True
                break
        
        if not necesita_ajuste:
            return partidos_clasificados
        
        # Aplicar ajuste suave a partidos neutros y de baja confianza
        partidos_ajustados = partidos_clasificados.copy()
        
        for partido in partidos_ajustados:
            if partido['clasificacion'] in ['Neutro', 'Divisor'] and partido['confianza'] < 0.15:
                # Ajustar hacia resultado que necesite más representación
                self._ajustar_resultado_partido(partido, dist_actual, rangos_objetivo)
        
        return partidos_ajustados
    
    def _ajustar_resultado_partido(self, partido: Dict, dist_actual: Dict, rangos_objetivo: Dict):
        """
        Ajusta el resultado sugerido de un partido específico
        """
        # Encontrar qué resultado está más por debajo del rango objetivo
        deficits = {}
        for resultado, (min_val, max_val) in rangos_objetivo.items():
            if dist_actual[resultado] < min_val:
                deficits[resultado] = min_val - dist_actual[resultado]
        
        if deficits:
            # Cambiar al resultado con mayor déficit, si tiene probabilidad razonable
            resultado_objetivo = max(deficits, key=deficits.get)
            prob_key = f'prob_{resultado_objetivo.lower()}' if resultado_objetivo != 'L' else 'prob_local'
            if resultado_objetivo == 'E':
                prob_key = 'prob_empate'
            elif resultado_objetivo == 'V':
                prob_key = 'prob_visitante'
            
            if partido[prob_key] > 0.20:  # Solo si tiene probabilidad mínima razonable
                partido['resultado_sugerido'] = resultado_objetivo