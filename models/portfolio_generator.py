import numpy as np
import random
from typing import List, Dict, Any, Tuple
from itertools import combinations
import copy

class PortfolioGenerator:
    """
    Implementa la metodología Core + Satélites con optimización GRASP-Annealing
    según el documento de metodología definitiva Progol
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Parámetros de la metodología
        self.empates_min = 4
        self.empates_max = 6
        self.concentracion_max = 0.70
        self.concentracion_inicial_max = 0.60  # Para partidos 1-3
        self.correlacion_objetivo = -0.35
        
    def generate_core_quinielas(self, partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Genera 4 quinielas Core según la metodología
        """
        core_quinielas = []
        
        for i in range(4):
            quiniela = self._crear_quiniela_core_base(partidos_clasificados)
            
            # Aplicar variación por rotación de empates
            if i > 0:
                quiniela = self._aplicar_rotacion_empates(quiniela, partidos_clasificados, i)
            
            # Validar y ajustar empates
            quiniela = self._ajustar_empates_quiniela(quiniela, partidos_clasificados)
            
            # Calcular probabilidad de 11+ aciertos
            prob_11_plus = self._calcular_prob_11_plus(quiniela, partidos_clasificados)
            
            quiniela_obj = {
                'id': f'Core-{i+1}',
                'tipo': 'Core',
                'resultados': quiniela,
                'empates': quiniela.count('E'),
                'prob_11_plus': prob_11_plus,
                'distribucion': self._calcular_distribucion(quiniela)
            }
            
            core_quinielas.append(quiniela_obj)
        
        return core_quinielas
    
    def _crear_quiniela_core_base(self, partidos_clasificados: List[Dict]) -> List[str]:
        """
        Crea quiniela base siguiendo reglas Core:
        - Ancla: fijar resultado de máxima probabilidad
        - TendenciaEmpate: asignar E si empates < 6
        - Otros: argmax probabilidad
        """
        quiniela = []
        empates_actuales = 0
        
        for partido in partidos_clasificados:
            if partido['clasificacion'] == 'Ancla':
                # Fijar resultado de máxima probabilidad
                resultado = partido['resultado_sugerido']
            elif partido['clasificacion'] == 'TendenciaEmpate':
                # Asignar empate si no excede límite
                if empates_actuales < self.empates_max:
                    resultado = 'E'
                    empates_actuales += 1
                else:
                    resultado = partido['resultado_sugerido']
            else:
                # Usar resultado sugerido
                resultado = partido['resultado_sugerido']
            
            if resultado == 'E':
                empates_actuales += 1
                
            quiniela.append(resultado)
        
        return quiniela
    
    def _aplicar_rotacion_empates(self, quiniela: List[str], 
                                 partidos_clasificados: List[Dict], 
                                 variacion: int) -> List[str]:
        """
        Aplica rotación de empates para crear variaciones en las quinielas Core
        """
        quiniela_variada = quiniela.copy()
        
        # Encontrar partidos que pueden cambiar (no Ancla)
        candidatos_cambio = []
        for i, partido in enumerate(partidos_clasificados):
            if partido['clasificacion'] != 'Ancla':
                candidatos_cambio.append(i)
        
        # Aplicar cambios según variación
        num_cambios = min(2 + variacion, len(candidatos_cambio))
        indices_cambio = random.sample(candidatos_cambio, num_cambios)
        
        for idx in indices_cambio:
            partido = partidos_clasificados[idx]
            # Alternar entre las dos probabilidades más altas
            probs = {
                'L': partido['prob_local'],
                'E': partido['prob_empate'],
                'V': partido['prob_visitante']
            }
            probs_ordenadas = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            
            # Usar segunda opción más probable
            if len(probs_ordenadas) > 1:
                quiniela_variada[idx] = probs_ordenadas[1][0]
        
        return quiniela_variada
    
    def generate_satellite_quinielas(self, partidos_clasificados: List[Dict],
                                    quinielas_core: List[Dict],
                                    num_satelites: int) -> List[Dict]:
        """
        Genera quinielas satélites en pares con correlación negativa
        """
        satelites = []
        num_pares = num_satelites // 2
        
        # Identificar partidos Divisor para anticorrelación
        partidos_divisor = [i for i, p in enumerate(partidos_clasificados) 
                          if p['clasificacion'] == 'Divisor']
        
        for par in range(num_pares):
            # Crear par de satélites
            sat_a, sat_b = self._crear_par_satelites(
                partidos_clasificados, 
                partidos_divisor,
                par
            )
            
            satelites.extend([sat_a, sat_b])
        
        # Si número impar, crear uno adicional
        if num_satelites % 2 == 1:
            sat_extra = self._crear_satelite_individual(partidos_clasificados, len(satelites))
            satelites.append(sat_extra)
        
        return satelites
    
    def _crear_par_satelites(self, partidos_clasificados: List[Dict],
                           partidos_divisor: List[int],
                           par_id: int) -> Tuple[Dict, Dict]:
        """
        Crea par de satélites con correlación negativa
        """
        # Seleccionar partidos divisor para anticorrelación
        if len(partidos_divisor) > par_id:
            partido_principal = partidos_divisor[par_id]
        else:
            # Si no hay suficientes divisores, usar cualquier partido no-Ancla
            partidos_no_ancla = [i for i, p in enumerate(partidos_clasificados)
                                if p['clasificacion'] != 'Ancla']
            partido_principal = partidos_no_ancla[par_id % len(partidos_no_ancla)]
        
        # Crear satélite A (sigue probabilidad máxima en partido principal)
        quiniela_a = []
        quiniela_b = []
        
        for i, partido in enumerate(partidos_clasificados):
            if i == partido_principal:
                # Anticorrelación en este partido
                resultado_a = partido['resultado_sugerido']
                resultado_b = self._get_resultado_alternativo(partido)
            else:
                # Mantener misma lógica que Core pero con variación
                if partido['clasificacion'] == 'Ancla':
                    resultado = partido['resultado_sugerido']
                    resultado_a = resultado_b = resultado
                else:
                    # Pequeña variación aleatoria
                    if random.random() < 0.3:  # 30% chance de variación
                        resultado_alt = self._get_resultado_alternativo(partido)
                        resultado_a = partido['resultado_sugerido']
                        resultado_b = resultado_alt
                    else:
                        resultado = partido['resultado_sugerido']
                        resultado_a = resultado_b = resultado
            
            quiniela_a.append(resultado_a)
            quiniela_b.append(resultado_b)
        
        # Ajustar empates
        quiniela_a = self._ajustar_empates_quiniela(quiniela_a, partidos_clasificados)
        quiniela_b = self._ajustar_empates_quiniela(quiniela_b, partidos_clasificados)
        
        # Crear objetos satélite
        sat_a = {
            'id': f'Sat-{par_id*2+1}A',
            'tipo': 'Satelite',
            'resultados': quiniela_a,
            'empates': quiniela_a.count('E'),
            'prob_11_plus': self._calcular_prob_11_plus(quiniela_a, partidos_clasificados),
            'distribucion': self._calcular_distribucion(quiniela_a),
            'par_id': par_id
        }
        
        sat_b = {
            'id': f'Sat-{par_id*2+1}B',
            'tipo': 'Satelite',
            'resultados': quiniela_b,
            'empates': quiniela_b.count('E'),
            'prob_11_plus': self._calcular_prob_11_plus(quiniela_b, partidos_clasificados),
            'distribucion': self._calcular_distribucion(quiniela_b),
            'par_id': par_id
        }
        
        return sat_a, sat_b
    
    def _crear_satelite_individual(self, partidos_clasificados: List[Dict], satelite_id: int) -> Dict:
        """
        Crea satélite individual (cuando número es impar)
        """
        quiniela = self._crear_quiniela_core_base(partidos_clasificados)
        
        # Aplicar variación aleatoria
        for i, partido in enumerate(partidos_clasificados):
            if partido['clasificacion'] not in ['Ancla'] and random.random() < 0.4:
                quiniela[i] = self._get_resultado_alternativo(partido)
        
        quiniela = self._ajustar_empates_quiniela(quiniela, partidos_clasificados)
        
        return {
            'id': f'Sat-{satelite_id+1}',
            'tipo': 'Satelite',
            'resultados': quiniela,
            'empates': quiniela.count('E'),
            'prob_11_plus': self._calcular_prob_11_plus(quiniela, partidos_clasificados),
            'distribucion': self._calcular_distribucion(quiniela),
            'par_id': None
        }
    
    def optimize_portfolio_grasp(self, quinielas_candidatas: List[Dict],
                               partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Optimiza el portafolio usando GRASP-Annealing
        """
        # Fase GRASP: construcción golosa con aleatorización
        mejor_portafolio = self._grasp_construction(quinielas_candidatas, partidos_clasificados)
        
        # Fase Annealing: mejora local
        mejor_portafolio = self._simulated_annealing(mejor_portafolio, partidos_clasificados)
        
        return mejor_portafolio
    
    def _grasp_construction(self, candidatas: List[Dict], 
                          partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Construcción GRASP: selección golosa con aleatorización
        """
        portafolio = []
        candidatas_disponibles = candidatas.copy()
        
        # Siempre incluir las 4 Core primero
        cores = [q for q in candidatas if q['tipo'] == 'Core'][:4]
        portafolio.extend(cores)
        
        # Remover cores de candidatas disponibles
        candidatas_disponibles = [q for q in candidatas_disponibles if q['tipo'] != 'Core']
        
        # Completar con satélites usando criterio goloso aleatorizado
        while len(portafolio) < 20 and candidatas_disponibles:  # Limitamos a 20 para eficiencia
            # Calcular valor marginal de cada candidata
            valores_marginales = []
            
            for candidata in candidatas_disponibles:
                valor = self._calcular_valor_marginal(candidata, portafolio, partidos_clasificados)
                valores_marginales.append((candidata, valor))
            
            # Ordenar por valor marginal
            valores_marginales.sort(key=lambda x: x[1], reverse=True)
            
            # Seleccionar del top 15% (aleatorización GRASP)
            alpha = 0.15
            top_size = max(1, int(len(valores_marginales) * alpha))
            top_candidatas = valores_marginales[:top_size]
            
            # Selección aleatoria del top
            seleccionada, _ = random.choice(top_candidatas)
            portafolio.append(seleccionada)
            candidatas_disponibles.remove(seleccionada)
        
        return portafolio
    
    def _simulated_annealing(self, portafolio_inicial: List[Dict],
                           partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Mejora local con enfriamiento simulado
        """
        portafolio_actual = copy.deepcopy(portafolio_inicial)
        mejor_portafolio = copy.deepcopy(portafolio_inicial)
        
        # Parámetros de annealing
        temperatura_inicial = 0.05
        factor_enfriamiento = 0.92
        iteraciones_max = 200
        
        temperatura = temperatura_inicial
        mejor_valor = self._evaluar_portafolio(mejor_portafolio, partidos_clasificados)
        
        for iteracion in range(iteraciones_max):
            # Generar vecino (swap de 1-3 signos en una quiniela)
            vecino = self._generar_vecino(portafolio_actual, partidos_clasificados)
            
            if vecino is None:
                continue
            
            # Evaluar vecino
            valor_actual = self._evaluar_portafolio(portafolio_actual, partidos_clasificados)
            valor_vecino = self._evaluar_portafolio(vecino, partidos_clasificados)
            
            delta = valor_vecino - valor_actual
            
            # Criterio de aceptación
            if delta > 0 or random.random() < np.exp(delta / temperatura):
                portafolio_actual = vecino
                
                # Actualizar mejor si es necesario
                if valor_vecino > mejor_valor:
                    mejor_portafolio = copy.deepcopy(vecino)
                    mejor_valor = valor_vecino
            
            # Enfriar
            if iteracion % 10 == 0:
                temperatura *= factor_enfriamiento
        
        return mejor_portafolio
    
    def _generar_vecino(self, portafolio: List[Dict], 
                       partidos_clasificados: List[Dict]) -> List[Dict]:
        """
        Genera portafolio vecino cambiando 1-3 signos en una quiniela aleatoria
        """
        vecino = copy.deepcopy(portafolio)
        
        # Seleccionar quiniela aleatoria (excluir Core para preservar estructura)
        satelites = [i for i, q in enumerate(vecino) if q['tipo'] == 'Satelite']
        if not satelites:
            return None
        
        idx_quiniela = random.choice(satelites)
        quiniela = vecino[idx_quiniela]
        
        # Seleccionar 1-3 partidos para cambiar
        num_cambios = random.randint(1, 3)
        
        # Solo cambiar partidos no-Ancla
        partidos_cambiables = [i for i, p in enumerate(partidos_clasificados)
                             if p['clasificacion'] != 'Ancla']
        
        if len(partidos_cambiables) < num_cambios:
            return None
        
        indices_cambio = random.sample(partidos_cambiables, num_cambios)
        
        # Aplicar cambios
        for idx in indices_cambio:
            partido = partidos_clasificados[idx]
            resultado_alternativo = self._get_resultado_alternativo(partido)
            quiniela['resultados'][idx] = resultado_alternativo
        
        # Reajustar empates
        quiniela['resultados'] = self._ajustar_empates_quiniela(
            quiniela['resultados'], partidos_clasificados
        )
        
        # Recalcular métricas
        quiniela['empates'] = quiniela['resultados'].count('E')
        quiniela['prob_11_plus'] = self._calcular_prob_11_plus(
            quiniela['resultados'], partidos_clasificados
        )
        quiniela['distribucion'] = self._calcular_distribucion(quiniela['resultados'])
        
        return vecino
    
    def _get_resultado_alternativo(self, partido: Dict) -> str:
        """
        Obtiene resultado alternativo basado en segunda mayor probabilidad
        """
        probs = {
            'L': partido['prob_local'],
            'E': partido['prob_empate'],
            'V': partido['prob_visitante']
        }
        
        # Ordenar por probabilidad
        probs_ordenadas = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        
        # Devolver segunda opción más probable
        if len(probs_ordenadas) > 1:
            return probs_ordenadas[1][0]
        else:
            return probs_ordenadas[0][0]
    
    def _ajustar_empates_quiniela(self, quiniela: List[str], 
                                partidos_clasificados: List[Dict]) -> List[str]:
        """
        Ajusta empates para cumplir rango 4-6 empates por quiniela
        """
        empates_actuales = quiniela.count('E')
        quiniela_ajustada = quiniela.copy()
        
        if empates_actuales < self.empates_min:
            # Necesitamos más empates
            empates_necesarios = self.empates_min - empates_actuales
            
            # Candidatos para convertir a empate (partidos con prob_empate razonable)
            candidatos = []
            for i, (resultado, partido) in enumerate(zip(quiniela_ajustada, partidos_clasificados)):
                if resultado != 'E' and partido['prob_empate'] > 0.20:
                    candidatos.append((i, partido['prob_empate']))
            
            # Ordenar por probabilidad de empate
            candidatos.sort(key=lambda x: x[1], reverse=True)
            
            # Convertir los mejores candidatos
            for i, _ in candidatos[:empates_necesarios]:
                quiniela_ajustada[i] = 'E'
        
        elif empates_actuales > self.empates_max:
            # Demasiados empates, convertir algunos
            empates_exceso = empates_actuales - self.empates_max
            
            # Encontrar empates con menor probabilidad
            candidatos_empate = []
            for i, (resultado, partido) in enumerate(zip(quiniela_ajustada, partidos_clasificados)):
                if resultado == 'E':
                    candidatos_empate.append((i, partido['prob_empate']))
            
            # Ordenar por menor probabilidad de empate
            candidatos_empate.sort(key=lambda x: x[1])
            
            # Convertir los empates más débiles
            for i, _ in candidatos_empate[:empates_exceso]:
                partido = partidos_clasificados[i]
                quiniela_ajustada[i] = partido['resultado_sugerido']
        
        return quiniela_ajustada
    
    def _calcular_prob_11_plus(self, quiniela: List[str], 
                             partidos_clasificados: List[Dict]) -> float:
        """
        Calcula probabilidad de 11+ aciertos usando aproximación Monte Carlo
        """
        # Probabilidades individuales de acierto
        probs_acierto = []
        
        for resultado, partido in zip(quiniela, partidos_clasificados):
            if resultado == 'L':
                prob = partido['prob_local']
            elif resultado == 'E':
                prob = partido['prob_empate']
            else:  # 'V'
                prob = partido['prob_visitante']
            
            probs_acierto.append(prob)
        
        # Simulación Monte Carlo (simplificada)
        num_simulaciones = 1000
        aciertos_11_plus = 0
        
        for _ in range(num_simulaciones):
            aciertos = sum(1 for prob in probs_acierto if random.random() < prob)
            if aciertos >= 11:
                aciertos_11_plus += 1
        
        return aciertos_11_plus / num_simulaciones
    
    def _calcular_distribucion(self, quiniela: List[str]) -> Dict[str, float]:
        """
        Calcula distribución de resultados en la quiniela
        """
        total = len(quiniela)
        return {
            'L': quiniela.count('L') / total,
            'E': quiniela.count('E') / total,
            'V': quiniela.count('V') / total
        }
    
    def _calcular_valor_marginal(self, candidata: Dict, portafolio_actual: List[Dict],
                               partidos_clasificados: List[Dict]) -> float:
        """
        Calcula valor marginal de agregar una candidata al portafolio
        """
        # Factores que contribuyen al valor:
        # 1. Probabilidad de 11+ aciertos
        # 2. Diversificación (diferencia con quinielas existentes)
        # 3. Balance de distribución
        
        valor_prob = candidata['prob_11_plus']
        
        # Diversificación (promedio de distancia Hamming con portafolio)
        if portafolio_actual:
            distancias = []
            for q in portafolio_actual:
                distancia = self._calcular_distancia_hamming(
                    candidata['resultados'], q['resultados']
                )
                distancias.append(distancia)
            valor_diversificacion = np.mean(distancias) / 14  # Normalizar
        else:
            valor_diversificacion = 1.0
        
        # Balance de distribución (penalizar si se aleja mucho del histórico)
        dist_objetivo = {'L': 0.38, 'E': 0.29, 'V': 0.33}
        penalizacion_balance = 0
        
        for resultado, prop_objetivo in dist_objetivo.items():
            diferencia = abs(candidata['distribucion'][resultado] - prop_objetivo)
            penalizacion_balance += diferencia
        
        valor_balance = max(0, 1 - penalizacion_balance)
        
        # Combinar factores
        valor_total = (0.5 * valor_prob + 
                      0.3 * valor_diversificacion + 
                      0.2 * valor_balance)
        
        return valor_total
    
    def _calcular_distancia_hamming(self, quiniela1: List[str], quiniela2: List[str]) -> int:
        """
        Calcula distancia de Hamming entre dos quinielas
        """
        return sum(1 for a, b in zip(quiniela1, quiniela2) if a != b)
    
    def _evaluar_portafolio(self, portafolio: List[Dict], 
                          partidos_clasificados: List[Dict]) -> float:
        """
        Evalúa calidad del portafolio completo
        Implementa F = 1 - ∏(1 - Pr_q[≥11])
        """
        if not portafolio:
            return 0.0
        
        # Probabilidad de que al menos una quiniela tenga 11+ aciertos
        prob_complementaria = 1.0
        for quiniela in portafolio:
            prob_complementaria *= (1 - quiniela['prob_11_plus'])
        
        return 1 - prob_complementaria