"""
Gestor de quinielas para la aplicación de pronósticos de fútbol.
Maneja la creación, actualización y seguimiento de quinielas de usuarios.
"""
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

class ProgolQuiniela:
    """Clase para representar una quiniela de Progol."""
    
    def __init__(self, nombre: str, partidos_regulares: List[Dict[str, Any]], 
                partidos_revancha: List[Dict[str, Any]] = None, 
                selecciones: Dict[int, str] = None,
                selecciones_revancha: Dict[int, str] = None):
        """
        Inicializa una quiniela de Progol.
        
        Args:
            nombre: Nombre identificativo de la quiniela
            partidos_regulares: Lista de 14 partidos regulares
            partidos_revancha: Lista de hasta 7 partidos de revancha (opcional)
            selecciones: Diccionario con las selecciones del usuario para partidos regulares (match_id -> resultado)
            selecciones_revancha: Diccionario con las selecciones para partidos de revancha
        """
        self.nombre = nombre
        self.partidos_regulares = partidos_regulares
        self.partidos_revancha = partidos_revancha or []
        self.selecciones = selecciones or {}
        self.selecciones_revancha = selecciones_revancha or {}
        self.fecha_creacion = datetime.now().isoformat()
        self.ultima_actualizacion = self.fecha_creacion
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la quiniela a un diccionario para almacenamiento."""
        return {
            'nombre': self.nombre,
            'partidos_regulares': self.partidos_regulares,
            'partidos_revancha': self.partidos_revancha,
            'selecciones': self.selecciones,
            'selecciones_revancha': self.selecciones_revancha,
            'fecha_creacion': self.fecha_creacion,
            'ultima_actualizacion': self.ultima_actualizacion
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgolQuiniela':
        """Crea una quiniela a partir de un diccionario."""
        quiniela = cls(
            nombre=data['nombre'],
            partidos_regulares=data.get('partidos_regulares', []),
            partidos_revancha=data.get('partidos_revancha', []),
            selecciones=data.get('selecciones', {}),
            selecciones_revancha=data.get('selecciones_revancha', {})
        )
        quiniela.fecha_creacion = data['fecha_creacion']
        quiniela.ultima_actualizacion = data['ultima_actualizacion']
        return quiniela
    
    def establecer_pronostico(self, match_id: int, resultado: str, es_revancha: bool = False) -> None:
        """
        Establece un pronóstico para un partido.
        
        Args:
            match_id: ID del partido
            resultado: Resultado pronosticado ('L', 'E', 'V')
            es_revancha: Indica si es un partido de revancha
        """
        if resultado not in ['L', 'E', 'V']:
            raise ValueError("El resultado debe ser 'L', 'E' o 'V'")
        
        # Verificar que el partido está en la quiniela
        if es_revancha:
            match_ids = [p['match_id'] for p in self.partidos_revancha]
            if match_id not in match_ids:
                raise ValueError(f"El partido con ID {match_id} no está en esta quiniela (revancha)")
            self.selecciones_revancha[match_id] = resultado
        else:
            match_ids = [p['match_id'] for p in self.partidos_regulares]
            if match_id not in match_ids:
                raise ValueError(f"El partido con ID {match_id} no está en esta quiniela (regular)")
            self.selecciones[match_id] = resultado
        
        self.ultima_actualizacion = datetime.now().isoformat()
    
    def obtener_pronostico(self, match_id: int, es_revancha: bool = False) -> Optional[str]:
        """
        Obtiene el pronóstico para un partido específico.
        
        Args:
            match_id: ID del partido
            es_revancha: Indica si es un partido de revancha
            
        Returns:
            Resultado pronosticado ('L', 'E', 'V') o None si no hay pronóstico
        """
        if es_revancha:
            return self.selecciones_revancha.get(match_id)
        else:
            return self.selecciones.get(match_id)
    
    def calcular_aciertos(self, resultados_actuales: Dict[int, str], 
                          resultados_revancha: Dict[int, str] = None) -> Dict[str, Any]:
        """
        Calcula los aciertos en la quiniela según los resultados actuales.
        
        Args:
            resultados_actuales: Diccionario con los resultados actuales (match_id -> resultado)
            resultados_revancha: Diccionario con los resultados de revancha
            
        Returns:
            Diccionario con estadísticas de aciertos
        """
        resultados_revancha = resultados_revancha or {}
        
        # Estadísticas para partidos regulares
        total_regulares = len(self.partidos_regulares)
        regulares_con_pronostico = len(self.selecciones)
        regulares_con_resultado = sum(1 for match_id in self.selecciones if match_id in resultados_actuales)
        
        aciertos_regulares = 0
        for match_id, pronostico in self.selecciones.items():
            if match_id in resultados_actuales and pronostico == resultados_actuales[match_id]:
                aciertos_regulares += 1
        
        # Estadísticas para partidos de revancha
        total_revancha = len(self.partidos_revancha)
        revancha_con_pronostico = len(self.selecciones_revancha)
        revancha_con_resultado = sum(1 for match_id in self.selecciones_revancha if match_id in resultados_revancha)
        
        aciertos_revancha = 0
        for match_id, pronostico in self.selecciones_revancha.items():
            if match_id in resultados_revancha and pronostico == resultados_revancha[match_id]:
                aciertos_revancha += 1
        
        # Totales
        total_partidos = total_regulares + total_revancha
        partidos_con_pronostico = regulares_con_pronostico + revancha_con_pronostico
        partidos_con_resultado = regulares_con_resultado + revancha_con_resultado
        aciertos_totales = aciertos_regulares + aciertos_revancha
        
        # Porcentajes
        porcentaje_aciertos_regulares = (aciertos_regulares / regulares_con_resultado * 100) if regulares_con_resultado > 0 else 0
        porcentaje_aciertos_revancha = (aciertos_revancha / revancha_con_resultado * 100) if revancha_con_resultado > 0 else 0
        porcentaje_aciertos_totales = (aciertos_totales / partidos_con_resultado * 100) if partidos_con_resultado > 0 else 0
        
        return {
            # Regulares
            'total_regulares': total_regulares,
            'regulares_con_pronostico': regulares_con_pronostico,
            'regulares_con_resultado': regulares_con_resultado,
            'aciertos_regulares': aciertos_regulares,
            'porcentaje_aciertos_regulares': porcentaje_aciertos_regulares,
            
            # Revancha
            'total_revancha': total_revancha,
            'revancha_con_pronostico': revancha_con_pronostico,
            'revancha_con_resultado': revancha_con_resultado,
            'aciertos_revancha': aciertos_revancha,
            'porcentaje_aciertos_revancha': porcentaje_aciertos_revancha,
            
            # Totales
            'total_partidos': total_partidos,
            'partidos_con_pronostico': partidos_con_pronostico,
            'partidos_con_resultado': partidos_con_resultado,
            'aciertos_totales': aciertos_totales,
            'porcentaje_aciertos_totales': porcentaje_aciertos_totales
        }


class QuinielaManager:
    """Gestor para administrar múltiples quinielas de usuarios."""
    
    def __init__(self, ruta_almacenamiento: str = "data"):
        """
        Inicializa el gestor de quinielas.
        
        Args:
            ruta_almacenamiento: Ruta donde se almacenarán los datos de quinielas
        """
        self.ruta_almacenamiento = ruta_almacenamiento
        self.quinielas = {}
        self.partidos_activos = {}
        self.partidos_revancha_activos = {}
        
        # Crear directorio de almacenamiento si no existe
        if not os.path.exists(ruta_almacenamiento):
            os.makedirs(ruta_almacenamiento)
        
        # Cargar quinielas guardadas
        self._cargar_quinielas()
    
    def _cargar_quinielas(self) -> None:
        """Carga las quinielas desde el almacenamiento."""
        ruta_archivo = os.path.join(self.ruta_almacenamiento, "quinielas.json")
        if os.path.exists(ruta_archivo):
            try:
                with open(ruta_archivo, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for nombre, quiniela_data in data.items():
                        self.quinielas[nombre] = ProgolQuiniela.from_dict(quiniela_data)
                print(f"Cargadas {len(self.quinielas)} quinielas")
            except Exception as e:
                print(f"Error al cargar quinielas: {e}")
                self.quinielas = {}
    
    def _guardar_quinielas(self) -> None:
        """Guarda las quinielas en el almacenamiento."""
        ruta_archivo = os.path.join(self.ruta_almacenamiento, "quinielas.json")
        try:
            data = {nombre: quiniela.to_dict() for nombre, quiniela in self.quinielas.items()}
            with open(ruta_archivo, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error al guardar quinielas: {e}")
    
    def crear_quiniela(self, nombre: str, partidos_regulares: List[Dict[str, Any]], 
                      partidos_revancha: List[Dict[str, Any]] = None) -> ProgolQuiniela:
        """
        Crea una nueva quiniela.
        
        Args:
            nombre: Nombre identificativo de la quiniela
            partidos_regulares: Lista de 14 partidos regulares
            partidos_revancha: Lista de hasta 7 partidos de revancha (opcional)
            
        Returns:
            La quiniela creada
        """
        if nombre in self.quinielas:
            raise ValueError(f"Ya existe una quiniela con el nombre '{nombre}'")
        
        # Verificar número de partidos
        if len(partidos_regulares) != 14:
            raise ValueError(f"Se requieren exactamente 14 partidos regulares, se proporcionaron {len(partidos_regulares)}")
        
        if partidos_revancha and len(partidos_revancha) > 7:
            raise ValueError(f"Se permiten máximo 7 partidos de revancha, se proporcionaron {len(partidos_revancha)}")
        
        quiniela = ProgolQuiniela(
            nombre=nombre, 
            partidos_regulares=partidos_regulares,
            partidos_revancha=partidos_revancha or []
        )
        self.quinielas[nombre] = quiniela
        self._guardar_quinielas()
        return quiniela
    
    def eliminar_quiniela(self, nombre: str) -> None:
        """
        Elimina una quiniela existente.
        
        Args:
            nombre: Nombre de la quiniela a eliminar
        """
        if nombre not in self.quinielas:
            raise ValueError(f"No existe una quiniela con el nombre '{nombre}'")
        
        del self.quinielas[nombre]
        self._guardar_quinielas()
    
    def obtener_quiniela(self, nombre: str) -> ProgolQuiniela:
        """
        Obtiene una quiniela por su nombre.
        
        Args:
            nombre: Nombre de la quiniela
            
        Returns:
            La quiniela solicitada
        """
        if nombre not in self.quinielas:
            raise ValueError(f"No existe una quiniela con el nombre '{nombre}'")
        
        return self.quinielas[nombre]
    
    def listar_quinielas(self) -> List[str]:
        """
        Lista los nombres de todas las quinielas disponibles.
        
        Returns:
            Lista de nombres de quinielas
        """
        return list(self.quinielas.keys())
    
    def actualizar_partidos_activos(self, partidos: List[Dict[str, Any]]) -> List[Tuple[int, str, str]]:
        """
        Actualiza la lista de partidos activos y detecta cambios.
        
        Args:
            partidos: Lista de diccionarios con información de partidos activos
            
        Returns:
            Lista de tuplas (match_id, resultado_anterior, resultado_nuevo) con cambios detectados
        """
        cambios = []
        
        # Dividir en regulares y revancha
        partidos_regulares = []
        partidos_revancha = []
        
        for partido in partidos:
            if partido.get('is_revancha', False):
                partidos_revancha.append(partido)
            else:
                partidos_regulares.append(partido)
        
        # Crear nuevos diccionarios de partidos activos
        nuevos_partidos = {p['match_id']: p for p in partidos_regulares}
        nuevos_partidos_revancha = {p['match_id']: p for p in partidos_revancha}
        
        # Detectar cambios en resultados (regulares)
        for match_id, partido in nuevos_partidos.items():
            resultado_nuevo = partido.get('result', '')
            resultado_anterior = self.partidos_activos.get(match_id, {}).get('result', '')
            
            if match_id in self.partidos_activos and resultado_anterior != resultado_nuevo:
                cambios.append((match_id, resultado_anterior, resultado_nuevo, False))
        
        # Detectar cambios en resultados (revancha)
        for match_id, partido in nuevos_partidos_revancha.items():
            resultado_nuevo = partido.get('result', '')
            resultado_anterior = self.partidos_revancha_activos.get(match_id, {}).get('result', '')
            
            if match_id in self.partidos_revancha_activos and resultado_anterior != resultado_nuevo:
                cambios.append((match_id, resultado_anterior, resultado_nuevo, True))
        
        # Actualizar partidos activos
        self.partidos_activos = nuevos_partidos
        self.partidos_revancha_activos = nuevos_partidos_revancha
        
        return cambios
    
    def obtener_resultados_actuales(self, solo_revancha: bool = False) -> Dict[int, str]:
        """
        Obtiene un diccionario con los resultados actuales de los partidos.
        
        Args:
            solo_revancha: Si es True, devuelve sólo resultados de partidos de revancha
            
        Returns:
            Diccionario con los resultados (match_id -> resultado)
        """
        if solo_revancha:
            return {match_id: partido.get('result', '') 
                    for match_id, partido in self.partidos_revancha_activos.items()
                    if partido.get('result', '') in ['L', 'E', 'V']}
        else:
            return {match_id: partido.get('result', '') 
                    for match_id, partido in self.partidos_activos.items()
                    if partido.get('result', '') in ['L', 'E', 'V']}
    
    def obtener_cambios_relevantes(self, cambios: List[Tuple[int, str, str, bool]]) -> List[Dict[str, Any]]:
        """
        Filtra los cambios relevantes para las quinielas existentes.
        
        Args:
            cambios: Lista de tuplas (match_id, resultado_anterior, resultado_nuevo, es_revancha)
            
        Returns:
            Lista de diccionarios con información de cambios relevantes
        """
        cambios_relevantes = []
        
        # Buscar match_ids en todas las quinielas
        match_ids_regulares = set()
        match_ids_revancha = set()
        
        for quiniela in self.quinielas.values():
            for partido in quiniela.partidos_regulares:
                match_ids_regulares.add(partido.get('match_id'))
            
            for partido in quiniela.partidos_revancha:
                match_ids_revancha.add(partido.get('match_id'))
        
        # Filtrar cambios relevantes
        for match_id, resultado_anterior, resultado_nuevo, es_revancha in cambios:
            relevant_ids = match_ids_revancha if es_revancha else match_ids_regulares
            
            if match_id in relevant_ids:
                # Obtener información adicional del partido
                partidos_activos = self.partidos_revancha_activos if es_revancha else self.partidos_activos
                partido = partidos_activos.get(match_id, {})
                
                cambio = {
                    'match_id': match_id,
                    'home_team': partido.get('home_team', ''),
                    'away_team': partido.get('away_team', ''),
                    'home_score': partido.get('home_score', 0),
                    'away_score': partido.get('away_score', 0),
                    'resultado_anterior': resultado_anterior,
                    'resultado_nuevo': resultado_nuevo,
                    'es_revancha': es_revancha,
                    'timestamp': datetime.now().isoformat()
                }
                cambios_relevantes.append(cambio)
        
        return cambios_relevantes

# Función de prueba
def test_quiniela_manager():
    """Función para probar el gestor de quinielas."""
    # Crear algunos partidos de ejemplo
    partidos_regulares = [
        {
            'match_id': 1000001,
            'home_team': 'Equipo A',
            'away_team': 'Equipo B',
            'scheduled_time': datetime.now().isoformat(),
            'league': 'Liga MX',
            'is_revancha': False
        },
        # ... 13 partidos más
    ]
    
    partidos_revancha = [
        {
            'match_id': 2000001,
            'home_team': 'Equipo C',
            'away_team': 'Equipo D',
            'scheduled_time': datetime.now().isoformat(),
            'league': 'EPL',
            'is_revancha': True
        },
        # ... hasta 6 partidos más
    ]
    
    # Crear gestor de quinielas
    manager = QuinielaManager(ruta_almacenamiento="test_data")
    
    # Crear quiniela
    quiniela = manager.crear_quiniela("Mi Quiniela", partidos_regulares, partidos_revancha)
    
    # Establecer pronósticos
    quiniela.establecer_pronostico(1000001, 'L')
    quiniela.establecer_pronostico(2000001, 'E', es_revancha=True)
    
    # Guardar y recargar
    manager._guardar_quinielas()
    manager = QuinielaManager(ruta_almacenamiento="test_data")
    
    # Verificar que la quiniela se cargó correctamente
    quiniela_cargada = manager.obtener_quiniela("Mi Quiniela")
    print(f"Pronóstico para partido regular: {quiniela_cargada.obtener_pronostico(1000001)}")
    print(f"Pronóstico para partido revancha: {quiniela_cargada.obtener_pronostico(2000001, es_revancha=True)}")
    
    # Simular actualización de partidos activos
    partidos_activos = [
        {
            'match_id': 1000001,
            'home_team': 'Equipo A',
            'away_team': 'Equipo B',
            'home_score': 2,
            'away_score': 0,
            'result': 'L',
            'is_live': True,
            'is_revancha': False
        },
        {
            'match_id': 2000001,
            'home_team': 'Equipo C',
            'away_team': 'Equipo D',
            'home_score': 1,
            'away_score': 1,
            'result': 'E',
            'is_live': True,
            'is_revancha': True
        }
    ]
    
    cambios = manager.actualizar_partidos_activos(partidos_activos)
    print(f"Cambios detectados: {cambios}")
    
    # Calcular aciertos
    resultados_actuales = manager.obtener_resultados_actuales()
    resultados_revancha = manager.obtener_resultados_actuales(solo_revancha=True)
    aciertos = quiniela_cargada.calcular_aciertos(resultados_actuales, resultados_revancha)
    print(f"Aciertos: {aciertos}")
    
    # Simular cambio en resultado
    partidos_activos[1]['home_score'] = 2
    partidos_activos[1]['result'] = 'L'
    
    cambios = manager.actualizar_partidos_activos(partidos_activos)
    print(f"Nuevos cambios detectados: {cambios}")
    
    cambios_relevantes = manager.obtener_cambios_relevantes(cambios)
    print(f"Cambios relevantes: {cambios_relevantes}")
    
    # Actualizar aciertos
        resultados_actuales = manager.obtener_resultados_actuales()
        resultados_revancha = manager.obtener_resultados_actuales(solo_revancha=True)
        aciertos = quiniela_cargada.calcular_aciertos(resultados_actuales, resultados_revancha)
        print(f"Aciertos actualizados: {aciertos}")

    if __name__ == "__main__":
        test_quiniela_manager()