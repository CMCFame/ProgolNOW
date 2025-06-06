import numpy as np
from typing import List, Dict, Any
from collections import Counter

class PortfolioValidator:
    """
    Valida que el portafolio cumple con todas las reglas de la metodología definitiva:
    - Distribución histórica: 35-41% L, 25-33% E, 30-36% V
    - Empates por quiniela: 4-6
    - Concentración máxima: ≤70% (≤60% en partidos 1-3)
    - Unicidad: sin quinielas repetidas
    - Hiperdiversificación: cumplir reglas de anticorrelación
    """
    
    def __init__(self):
        # Rangos históricos válidos
        self.rangos_historicos = {
            'L': (0.35, 0.41),
            'E': (0.25, 0.33),
            'V': (0.30, 0.36)
        }
        
        # Límites de empates
        self.empates_min = 4
        self.empates_max = 6
        
        # Límites de concentración
        self.concentracion_max_general = 0.70
        self.concentracion_max_inicial = 0.60  # Partidos 1-3
        
        # Límites para correlación negativa
        self.correlacion_min = -0.50
        self.correlacion_max = -0.20
    
    def validate_portfolio(self, quinielas: List[Dict]) -> Dict[str, Any]:
        """
        Valida todo el portafolio y retorna reporte completo
        """
        validacion = {
            'es_valido': True,
            'warnings': [],
            'errores': [],
            'metricas': {},
            'detalles': {}
        }
        
        if not quinielas:
            validacion['es_valido'] = False
            validacion['errores'].append("No hay quinielas en el portafolio")
            return validacion
        
        # 1. Validar distribución histórica global
        self._validar_distribucion_global(quinielas, validacion)
        
        # 2. Validar empates por quiniela
        self._validar_empates_individuales(quinielas, validacion)
        
        # 3. Validar concentración por partido
        self._validar_concentracion(quinielas, validacion)
        
        # 4. Validar unicidad
        self._validar_unicidad(quinielas, validacion)
        
        # 5. Validar hiperdiversificación
        self._validar_hiperdiversificacion(quinielas, validacion)
        
        # 6. Validar estructura Core + Satélites
        self._validar_estructura_core_satelites(quinielas, validacion)
        
        # 7. Calcular métricas adicionales
        self._calcular_metricas_adicionales(quinielas, validacion)
        
        # Determinar validez final
        if validacion['errores']:
            validacion['es_valido'] = False
        elif len(validacion['warnings']) > 3:  # Muchas advertencias también pueden ser problemáticas
            validacion['es_valido'] = False
            validacion['errores'].append("Demasiadas advertencias en la validación")
        
        return validacion
    
    def _validar_distribucion_global(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida que la distribución global esté dentro de rangos históricos
        """
        total_predicciones = len(quinielas) * 14
        conteos = {'L': 0, 'E': 0, 'V': 0}
        
        for quiniela in quinielas:
            for resultado in quiniela['resultados']:
                conteos[resultado] += 1
        
        distribucion_global = {k: v/total_predicciones for k, v in conteos.items()}
        validacion['metricas']['distribucion_global'] = distribucion_global
        
        for resultado, proporcion in distribucion_global.items():
            min_val, max_val = self.rangos_historicos[resultado]
            
            if proporcion < min_val:
                diferencia = min_val - proporcion
                if diferencia > 0.03:  # Diferencia significativa
                    validacion['errores'].append(
                        f"Distribución {resultado}: {proporcion:.3f} muy por debajo del mínimo {min_val}"
                    )
                else:
                    validacion['warnings'].append(
                        f"Distribución {resultado}: {proporcion:.3f} ligeramente bajo (mín: {min_val})"
                    )
            
            elif proporcion > max_val:
                diferencia = proporcion - max_val
                if diferencia > 0.03:
                    validacion['errores'].append(
                        f"Distribución {resultado}: {proporcion:.3f} muy por encima del máximo {max_val}"
                    )
                else:
                    validacion['warnings'].append(
                        f"Distribución {resultado}: {proporcion:.3f} ligeramente alto (máx: {max_val})"
                    )
    
    def _validar_empates_individuales(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida que cada quiniela tenga entre 4-6 empates
        """
        empates_por_quiniela = []
        quinielas_problematicas = []
        
        for i, quiniela in enumerate(quinielas):
            empates = quiniela['resultados'].count('E')
            empates_por_quiniela.append(empates)
            
            if empates < self.empates_min:
                quinielas_problematicas.append(f"Q-{i+1}: {empates} empates (mínimo {self.empates_min})")
            elif empates > self.empates_max:
                quinielas_problematicas.append(f"Q-{i+1}: {empates} empates (máximo {self.empates_max})")
        
        validacion['metricas']['empates_promedio'] = np.mean(empates_por_quiniela)
        validacion['metricas']['empates_rango'] = (min(empates_por_quiniela), max(empates_por_quiniela))
        
        if quinielas_problematicas:
            if len(quinielas_problematicas) > len(quinielas) * 0.1:  # Más del 10%
                validacion['errores'].append(f"Muchas quinielas fuera del rango de empates: {quinielas_problematicas[:5]}")
            else:
                validacion['warnings'].extend(quinielas_problematicas)
    
    def _validar_concentracion(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida límites de concentración por partido
        """
        num_quinielas = len(quinielas)
        if num_quinielas == 0:
            return
        
        concentraciones_problematicas = []
        
        for partido_idx in range(14):  # Asumiendo 14 partidos
            # Contar resultados para este partido
            conteos_partido = {'L': 0, 'E': 0, 'V': 0}
            
            for quiniela in quinielas:
                if partido_idx < len(quiniela['resultados']):
                    resultado = quiniela['resultados'][partido_idx]
                    conteos_partido[resultado] += 1
            
            # Calcular concentración máxima
            max_concentracion = max(conteos_partido.values()) / num_quinielas
            
            # Aplicar límite según posición del partido
            if partido_idx < 3:  # Partidos 1-3
                limite_aplicable = self.concentracion_max_inicial
                tipo_limite = "inicial"
            else:
                limite_aplicable = self.concentracion_max_general
                tipo_limite = "general"
            
            if max_concentracion > limite_aplicable:
                resultado_concentrado = max(conteos_partido, key=conteos_partido.get)
                concentraciones_problematicas.append(
                    f"Partido {partido_idx+1}: {max_concentracion:.1%} en '{resultado_concentrado}' "
                    f"(límite {tipo_limite}: {limite_aplicable:.1%})"
                )
        
        validacion['detalles']['concentraciones_partido'] = self._calcular_concentraciones_detalle(quinielas)
        
        if concentraciones_problematicas:
            if len(concentraciones_problematicas) > 3:
                validacion['errores'].append(f"Múltiples violaciones de concentración: {concentraciones_problematicas[:3]}")
            else:
                validacion['warnings'].extend(concentraciones_problematicas)
    
    def _validar_unicidad(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida que no haya quinielas exactamente repetidas
        """
        quinielas_vistas = set()
        duplicadas = []
        
        for i, quiniela in enumerate(quinielas):
            quiniela_str = ''.join(quiniela['resultados'])
            
            if quiniela_str in quinielas_vistas:
                duplicadas.append(f"Q-{i+1}")
            else:
                quinielas_vistas.add(quiniela_str)
        
        if duplicadas:
            validacion['errores'].append(f"Quinielas duplicadas encontradas: {duplicadas}")
        
        # Calcular similitud promedio (distancia de Hamming)
        similitudes = self._calcular_similitudes_promedio(quinielas)
        validacion['metricas']['similitud_promedio'] = similitudes['promedio']
        validacion['metricas']['similitud_minima'] = similitudes['minima']
        
        if similitudes['minima'] > 0.85:  # Muy similares
            validacion['warnings'].append(f"Algunas quinielas son muy similares (similitud mín: {similitudes['minima']:.3f})")
    
    def _validar_hiperdiversificacion(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida reglas de hiperdiversificación y correlación negativa
        """
        # 1. Validar que pares satélites tengan correlación negativa
        correlaciones_satelites = self._calcular_correlaciones_satelites(quinielas)
        
        correlaciones_problematicas = []
        for par_info in correlaciones_satelites:
            if par_info['correlacion'] > self.correlacion_max:
                correlaciones_problematicas.append(
                    f"Par {par_info['par_id']}: correlación {par_info['correlacion']:.3f} "
                    f"(debe ser < {self.correlacion_max})"
                )
        
        if correlaciones_problematicas:
            validacion['warnings'].extend(correlaciones_problematicas)
        
        validacion['metricas']['correlaciones_satelites'] = correlaciones_satelites
        
        # 2. Validar diversificación cronológica (primeros 3-4 partidos)
        diversificacion_inicial = self._calcular_diversificacion_inicial(quinielas)
        validacion['metricas']['diversificacion_inicial'] = diversificacion_inicial
        
        if diversificacion_inicial < 0.4:
            validacion['warnings'].append(
                f"Baja diversificación en partidos iniciales: {diversificacion_inicial:.3f}"
            )
    
    def _validar_estructura_core_satelites(self, quinielas: List[Dict], validacion: Dict):
        """
        Valida que se mantenga la estructura Core + Satélites
        """
        tipos_quiniela = [q.get('tipo', 'Desconocido') for q in quinielas]
        conteo_tipos = Counter(tipos_quiniela)
        
        validacion['metricas']['estructura'] = dict(conteo_tipos)
        
        # Verificar que hay exactamente 4 Core
        if conteo_tipos.get('Core', 0) != 4:
            validacion['warnings'].append(f"Se esperan 4 quinielas Core, encontradas: {conteo_tipos.get('Core', 0)}")
        
        # Verificar que hay satélites en pares (número par)
        num_satelites = conteo_tipos.get('Satelite', 0)
        if num_satelites > 0 and num_satelites % 2 != 0:
            validacion['warnings'].append(f"Número impar de satélites: {num_satelites} (se recomienda número par)")
    
    def _calcular_metricas_adicionales(self, quinielas: List[Dict], validacion: Dict):
        """
        Calcula métricas adicionales para análisis
        """
        if not quinielas:
            return
        
        # Probabilidad promedio de 11+ aciertos
        probs_11_plus = [q.get('prob_11_plus', 0) for q in quinielas]
        validacion['metricas']['prob_11_plus_promedio'] = np.mean(probs_11_plus)
        validacion['metricas']['prob_11_plus_max'] = max(probs_11_plus)
        validacion['metricas']['prob_11_plus_min'] = min(probs_11_plus)
        
        # Probabilidad del portafolio (al menos una quiniela con 11+)
        prob_portafolio = 1 - np.prod([1 - p for p in probs_11_plus])
        validacion['metricas']['prob_portafolio_11_plus'] = prob_portafolio
        
        # Entropía del portafolio (medida de diversidad)
        entropia = self._calcular_entropia_portafolio(quinielas)
        validacion['metricas']['entropia_diversidad'] = entropia
        
        # Eficiencia (relación beneficio/costo)
        costo_total = len(quinielas) * 15  # MXN 15 por boleto
        validacion['metricas']['costo_total'] = costo_total
        validacion['metricas']['eficiencia'] = prob_portafolio / (costo_total / 1000)  # Normalizado
    
    def _calcular_concentraciones_detalle(self, quinielas: List[Dict]) -> List[Dict]:
        """
        Calcula concentraciones detalladas por partido
        """
        concentraciones = []
        num_quinielas = len(quinielas)
        
        for partido_idx in range(14):
            conteos = {'L': 0, 'E': 0, 'V': 0}
            
            for quiniela in quinielas:
                if partido_idx < len(quiniela['resultados']):
                    resultado = quiniela['resultados'][partido_idx]
                    conteos[resultado] += 1
            
            proporciones = {k: v/num_quinielas for k, v in conteos.items()}
            max_concentracion = max(proporciones.values())
            resultado_dominante = max(proporciones, key=proporciones.get)
            
            concentraciones.append({
                'partido': partido_idx + 1,
                'proporciones': proporciones,
                'max_concentracion': max_concentracion,
                'resultado_dominante': resultado_dominante
            })
        
        return concentraciones
    
    def _calcular_similitudes_promedio(self, quinielas: List[Dict]) -> Dict[str, float]:
        """
        Calcula similitudes promedio entre quinielas usando distancia de Hamming
        """
        if len(quinielas) < 2:
            return {'promedio': 0.0, 'minima': 0.0}
        
        similitudes = []
        
        for i in range(len(quinielas)):
            for j in range(i + 1, len(quinielas)):
                # Calcular distancia de Hamming
                distancia = sum(1 for a, b in zip(quinielas[i]['resultados'], quinielas[j]['resultados']) if a != b)
                similitud = 1 - (distancia / 14)  # Convertir a similitud
                similitudes.append(similitud)
        
        return {
            'promedio': np.mean(similitudes),
            'minima': min(similitudes)
        }
    
    def _calcular_correlaciones_satelites(self, quinielas: List[Dict]) -> List[Dict]:
        """
        Calcula correlaciones entre pares de satélites
        """
        satelites = [q for q in quinielas if q.get('tipo') == 'Satelite']
        
        # Agrupar por par_id
        pares = {}
        for satelite in satelites:
            par_id = satelite.get('par_id')
            if par_id is not None:
                if par_id not in pares:
                    pares[par_id] = []
                pares[par_id].append(satelite)
        
        correlaciones = []
        
        for par_id, quinielas_par in pares.items():
            if len(quinielas_par) == 2:
                # Convertir resultados a números para correlación
                resultados1 = self._convertir_resultados_numericos(quinielas_par[0]['resultados'])
                resultados2 = self._convertir_resultados_numericos(quinielas_par[1]['resultados'])
                
                # Calcular correlación de Pearson
                correlacion = np.corrcoef(resultados1, resultados2)[0, 1]
                
                correlaciones.append({
                    'par_id': par_id,
                    'correlacion': correlacion,
                    'quiniela_a': quinielas_par[0]['id'],
                    'quiniela_b': quinielas_par[1]['id']
                })
        
        return correlaciones
    
    def _convertir_resultados_numericos(self, resultados: List[str]) -> List[int]:
        """
        Convierte resultados L/E/V a números para cálculo de correlación
        """
        conversion = {'L': 1, 'E': 0, 'V': -1}
        return [conversion[r] for r in resultados]
    
    def _calcular_diversificacion_inicial(self, quinielas: List[Dict]) -> float:
        """
        Calcula diversificación en los primeros 3-4 partidos
        """
        if not quinielas:
            return 0.0
        
        # Analizar primeros 3 partidos
        diversidades_partido = []
        
        for partido_idx in range(min(3, 14)):
            conteos = {'L': 0, 'E': 0, 'V': 0}
            
            for quiniela in quinielas:
                if partido_idx < len(quiniela['resultados']):
                    resultado = quiniela['resultados'][partido_idx]
                    conteos[resultado] += 1
            
            # Calcular entropía de Shannon para este partido
            total = sum(conteos.values())
            if total > 0:
                proporciones = [count/total for count in conteos.values() if count > 0]
                entropia = -sum(p * np.log(p) for p in proporciones)
                entropia_normalizada = entropia / np.log(3)  # Normalizar por máxima entropía
                diversidades_partido.append(entropia_normalizada)
        
        return np.mean(diversidades_partido)
    
    def _calcular_entropia_portafolio(self, quinielas: List[Dict]) -> float:
        """
        Calcula entropía promedio del portafolio como medida de diversidad
        """
        if not quinielas:
            return 0.0
        
        entropias_partido = []
        
        for partido_idx in range(14):
            conteos = {'L': 0, 'E': 0, 'V': 0}
            
            for quiniela in quinielas:
                if partido_idx < len(quiniela['resultados']):
                    resultado = quiniela['resultados'][partido_idx]
                    conteos[resultado] += 1
            
            # Calcular entropía
            total = sum(conteos.values())
            if total > 0:
                proporciones = [count/total for count in conteos.values() if count > 0]
                entropia = -sum(p * np.log(p) for p in proporciones)
                entropia_normalizada = entropia / np.log(3)
                entropias_partido.append(entropia_normalizada)
        
        return np.mean(entropias_partido)
    
    def generar_reporte_validacion(self, validacion: Dict) -> str:
        """
        Genera reporte textual de la validación
        """
        lineas = []
        lineas.append("=" * 60)
        lineas.append("REPORTE DE VALIDACIÓN DEL PORTAFOLIO")
        lineas.append("=" * 60)
        
        # Estado general
        estado = "✅ VÁLIDO" if validacion['es_valido'] else "❌ INVÁLIDO"
        lineas.append(f"Estado: {estado}")
        lineas.append("")
        
        # Errores
        if validacion['errores']:
            lineas.append("🚨 ERRORES:")
            for error in validacion['errores']:
                lineas.append(f"  • {error}")
            lineas.append("")
        
        # Advertencias
        if validacion['warnings']:
            lineas.append("⚠️  ADVERTENCIAS:")
            for warning in validacion['warnings']:
                lineas.append(f"  • {warning}")
            lineas.append("")
        
        # Métricas principales
        if 'metricas' in validacion:
            lineas.append("📊 MÉTRICAS PRINCIPALES:")
            metricas = validacion['metricas']
            
            if 'distribucion_global' in metricas:
                dist = metricas['distribucion_global']
                lineas.append(f"  • Distribución: L={dist['L']:.1%}, E={dist['E']:.1%}, V={dist['V']:.1%}")
            
            if 'empates_promedio' in metricas:
                lineas.append(f"  • Empates promedio: {metricas['empates_promedio']:.2f}")
            
            if 'prob_11_plus_promedio' in metricas:
                lineas.append(f"  • Pr[≥11] promedio: {metricas['prob_11_plus_promedio']:.1%}")
            
            if 'prob_portafolio_11_plus' in metricas:
                lineas.append(f"  • Pr[≥11] portafolio: {metricas['prob_portafolio_11_plus']:.1%}")
            
            if 'costo_total' in metricas:
                lineas.append(f"  • Costo total: ${metricas['costo_total']} MXN")
        
        return "\n".join(lineas)