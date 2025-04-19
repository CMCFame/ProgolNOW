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
    
    def __init__(self, nombre: str, partidos: List[Dict[str, Any]], selecciones: Dict[int, str] = None):
        """
        Inicializa una quiniela de Progol.
        
        Args:
            nombre: Nombre identificativo de la quiniela
            partidos: Lista de diccionarios con información de los partidos
            selecciones: Diccionario con las selecciones del usuario (match_id -> resultado)
        """
        self.nombre = nombre
        self.partidos = partidos
        self.selecciones = selecciones or {}
        self.fecha_creacion = datetime.now().isoformat()
        self.ultima_actualizacion = self.fecha_creacion
        
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la quiniela a un diccionario para almacenamiento."""
        return {
            'nombre': self.nombre,
            'partidos': self.partidos,
            'selecciones': self.selecciones,
            'fecha_creacion': self.fecha_creacion,
            'ultima_actualizacion': self.ultima_actualizacion
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgolQuiniela':
        """Crea una quiniela a partir de un diccionario."""
        quiniela = cls(
            nombre=data['nombre'],
            partidos=data['partidos'],
            selecciones=data['selecciones']
        )
        quiniela.fecha_creacion = data['fecha_creacion']
        quiniela.ultima_actualizacion = data['ultima_actualizacion']
        return quiniela
    
    def establecer_pronostico(self, match_id: int, resultado: str) -> None:
        """
        Establece un pronóstico para un partido.
        
        Args:
            match_id: ID del partido
            resultado: Resultado pronosticado ('L', 'E', 'V')
        """
        if resultado not in ['L', 'E', 'V']:
            raise ValueError("El resultado debe ser 'L', 'E' o 'V'")
        
        # Verificar que el partido está en la quiniela
        match_ids = [p['match_id'] for p in self.partidos]
        if match_id not in match_ids:
            raise ValueError(f"El partido con ID {match_id} no está en esta quiniela")
        
        self.selecciones[match_id] = resultado
        self.ultima_actualizacion = datetime.now().isoformat()
    
    def obtener_pronostico(self, match_id: int) -> Optional[str]:
        """
        Obtiene el pronóstico para un partido específico.
        
        Args:
            match_id: ID del partido
            
        Returns:
            Resultado pronosticado ('L', 'E', 'V') o None si no hay pronóstico
        """
        return self.selecciones.get(match_id)
    
    def calcular_aciertos(self, resultados_actuales: Dict[int, str]) -> Dict[str, Any]:
        """
        Calcula los aciertos en la quiniela según los resultados actuales.
        
        Args:
            resultados_actuales: Diccionario con los resultados actuales (match_id -> resultado)
            
        Returns:
            Diccionario con estadísticas de aciertos
        """
        total_partidos = len(self.partidos)
        partidos_con_pronostico = len(self.selecciones)
        partidos_con_resultado = sum(1 for match_id in self.selecciones if match_id in resultados_actuales)
        
        aciertos = 0
        for match_id, pronostico in self.selecciones.items():
            if match_id in resultados_actuales and pronostico == resultados_actuales[match_id]:
                aciertos += 1
        
        return {
            'total_partidos': total_partidos,
            'partidos_con_pronostico': partidos_con_pronostico,
            'partidos_con_resultado': partidos_con_resultado,
            'aciertos': aciertos,
            'porcentaje_aciertos': (aciertos / partidos_con_resultado) * 100 if partidos_con_resultado > 0 else 0
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
    
    def crear_quiniela(self, nombre: str, partidos: List[Dict[str, Any]]) -> ProgolQuiniela:
        """
        Crea una nueva quiniela.
        
        Args:
            nombre: Nombre identificativo de la quiniela
            partidos: Lista de diccionarios con información de los partidos
            
        Returns:
            La quiniela creada
        """
        if nombre in self.quinielas:
            raise ValueError(f"Ya existe una quiniela con el nombre '{nombre}'")
        
        quiniela = ProgolQuiniela(nombre=nombre, partidos=partidos)
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
        
        # Crear nuevo diccionario de partidos activos
        nuevos_partidos = {p['match_id']: p for p in partidos}
        
        # Detectar cambios en resultados
        for match_id, partido in nuevos_partidos.items():
            resultado_nuevo = partido.get('result', '')
            resultado_anterior = self.partidos_activos.get(match_id, {}).get('result', '')
            
            if match_id in self.partidos_activos and resultado_anterior != resultado_nuevo:
                cambios.append((match_id, resultado_anterior, resultado_nuevo))
        
        # Actualizar partidos activos
        self.partidos_activos = nuevos_partidos
        
        return cambios
    
    def obtener_resultados_actuales(self) -> Dict[int, str]:
        """
        Obtiene un diccionario con los resultados actuales de los partidos.
        
        Returns:
            Diccionario con los resultados (match_id -> resultado)
        """
        return {match_id: partido.get('result', '') 
                for match_id, partido in self.partidos_activos.items()
                if partido.get('result', '') in ['L', 'E', 'V']}
    
    def obtener_cambios_relevantes(self, cambios: List[Tuple[int, str, str]]) -> List[Dict[str, Any]]:
        """
        Filtra los cambios relevantes para las quinielas existentes.
        
        Args:
            cambios: Lista de tuplas (match_id, resultado_anterior, resultado_nuevo)
            
        Returns:
            Lista de diccionarios con información de cambios relevantes
        """
        cambios_relevantes = []
        
        # Buscar match_ids en todas las quinielas
        match_ids_en_quinielas = set()
        for quiniela in self.quinielas.values():
            for partido in quiniela.partidos:
                match_ids_en_quinielas.add(partido.get('match_id'))
        
        # Filtrar cambios relevantes
        for match_id, resultado_anterior, resultado_nuevo in cambios:
            if match_id in match_ids_en_quinielas:
                # Obtener información adicional del partido
                partido = self.partidos_activos.get(match_id, {})
                
                cambio = {
                    'match_id': match_id,
                    'home_team': partido.get('home_team', ''),
                    'away_team': partido.get('away_team', ''),
                    'home_score': partido.get('home_score', 0),
                    'away_score': partido.get('away_score', 0),
                    'resultado_anterior': resultado_anterior,
                    'resultado_nuevo': resultado_nuevo,
                    'timestamp': datetime.now().isoformat()
                }
                cambios_relevantes.append(cambio)
        
        return cambios_relevantes

# Función de prueba
def test_quiniela_manager():
    """Función para probar el gestor de quinielas."""
    # Crear algunos partidos de ejemplo
    partidos_ejemplo = [
        {
            'match_id': 1,
            'home_team': 'Equipo A',
            'away_team': 'Equipo B',
            'scheduled_time': datetime.now().isoformat(),
            'league': 'Liga MX'
        },
        {
            'match_id': 2,
            'home_team': 'Equipo C',
            'away_team': 'Equipo D',
            'scheduled_time': datetime.now().isoformat(),
            'league': 'EPL'
        }
    ]
    
    # Crear gestor de quinielas
    manager = QuinielaManager(ruta_almacenamiento="test_data")
    
    # Crear quiniela
    quiniela = manager.crear_quiniela("Mi Quiniela", partidos_ejemplo)
    
    # Establecer pronósticos
    quiniela.establecer_pronostico(1, 'L')
    quiniela.establecer_pronostico(2, 'E')
    
    # Guardar y recargar
    manager._guardar_quinielas()
    manager = QuinielaManager(ruta_almacenamiento="test_data")
    
    # Verificar que la quiniela se cargó correctamente
    quiniela_cargada = manager.obtener_quiniela("Mi Quiniela")
    print(f"Pronóstico para partido 1: {quiniela_cargada.obtener_pronostico(1)}")
    print(f"Pronóstico para partido 2: {quiniela_cargada.obtener_pronostico(2)}")
    
    # Simular actualización de partidos activos
    partidos_activos = [
        {
            'match_id': 1,
            'home_team': 'Equipo A',
            'away_team': 'Equipo B',
            'home_score': 2,
            'away_score': 0,
            'result': 'L',
            'is_live': True
        },
        {
            'match_id': 2,
            'home_team': 'Equipo C',
            'away_team': 'Equipo D',
            'home_score': 1,
            'away_score': 1,
            'result': 'E',
            'is_live': True
        }
    ]
    
    cambios = manager.actualizar_partidos_activos(partidos_activos)
    print(f"Cambios detectados: {cambios}")
    
    # Calcular aciertos
    resultados_actuales = manager.obtener_resultados_actuales()
    aciertos = quiniela_cargada.calcular_aciertos(resultados_actuales)
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
    aciertos = quiniela_cargada.calcular_aciertos(resultados_actuales)
    print(f"Aciertos actualizados: {aciertos}")

if __name__ == "__main__":
    test_quiniela_manager()