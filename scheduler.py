"""
Programador de tareas para la aplicación de quinielas.
Gestiona la actualización periódica de datos de partidos.
"""
import time
import threading
import queue
import logging
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("QuinielaScheduler")

class UpdateEvent:
    """Clase para representar un evento de actualización."""
    
    def __init__(self, 
                 event_type: str, 
                 data: Any = None, 
                 timestamp: Optional[datetime] = None):
        """
        Inicializa un evento de actualización.
        
        Args:
            event_type: Tipo de evento (ej: 'match_update', 'score_change')
            data: Datos asociados al evento
            timestamp: Momento en que ocurrió el evento
        """
        self.event_type = event_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
    
    def __str__(self) -> str:
        return f"{self.event_type} at {self.timestamp.isoformat()}"


class QuinielaScheduler:
    """Programador de tareas para la aplicación de quinielas."""
    
    def __init__(self, 
                 update_interval: int = 30, 
                 max_events: int = 100):
        """
        Inicializa el programador de tareas.
        
        Args:
            update_interval: Intervalo en segundos entre actualizaciones
            max_events: Número máximo de eventos en la cola
        """
        self.update_interval = update_interval
        self.running = False
        self.thread = None
        self.last_update = None
        self.event_queue = queue.Queue(maxsize=max_events)
        self.event_listeners = []
        self.data_service = None
        self.quiniela_manager = None
    
    def set_data_service(self, data_service) -> None:
        """
        Establece el servicio de datos que se utilizará.
        
        Args:
            data_service: Instancia del servicio de datos
        """
        self.data_service = data_service
    
    def set_quiniela_manager(self, quiniela_manager) -> None:
        """
        Establece el gestor de quinielas que se utilizará.
        
        Args:
            quiniela_manager: Instancia del gestor de quinielas
        """
        self.quiniela_manager = quiniela_manager
    
    def add_event_listener(self, listener: Callable[[UpdateEvent], None]) -> None:
        """
        Añade un listener para eventos.
        
        Args:
            listener: Función que será llamada cuando ocurra un evento
        """
        if listener not in self.event_listeners:
            self.event_listeners.append(listener)
    
    def remove_event_listener(self, listener: Callable[[UpdateEvent], None]) -> None:
        """
        Elimina un listener de eventos.
        
        Args:
            listener: Función a eliminar
        """
        if listener in self.event_listeners:
            self.event_listeners.remove(listener)
    
    def _notify_listeners(self, event: UpdateEvent) -> None:
        """
        Notifica a todos los listeners sobre un evento.
        
        Args:
            event: Evento a notificar
        """
        for listener in self.event_listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Error en listener: {e}")
    
    def start(self) -> None:
        """Inicia el programador de tareas."""
        if self.running:
            logger.warning("El programador ya está en ejecución")
            return
        
        if not self.data_service:
            raise ValueError("No se ha establecido el servicio de datos")
        
        if not self.quiniela_manager:
            raise ValueError("No se ha establecido el gestor de quinielas")
        
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Programador iniciado (intervalo: {self.update_interval}s)")
    
    def stop(self) -> None:
        """Detiene el programador de tareas."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.update_interval + 5)
            self.thread = None
        logger.info("Programador detenido")
    
    def _update_loop(self) -> None:
        """Bucle principal de actualización."""
        while self.running:
            try:
                self._update_data()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error en bucle de actualización: {e}")
                # Dormir un poco para evitar ciclos de error rápidos
                time.sleep(5)
    
    def _update_data(self) -> None:
        """Realiza una actualización de datos."""
        if not self.data_service or not self.quiniela_manager:
            logger.error("No se puede actualizar: falta servicio de datos o gestor de quinielas")
            return
        
        try:
            # Obtener partidos activos
            active_matches = self.data_service.get_active_matches()
            
            # Actualizar partidos en el gestor de quinielas y detectar cambios
            changes = self.quiniela_manager.actualizar_partidos_activos(active_matches)
            
            # Si hay cambios, generar eventos
            if changes:
                relevant_changes = self.quiniela_manager.obtener_cambios_relevantes(changes)
                
                for change in relevant_changes:
                    # Crear evento de cambio de resultado
                    event = UpdateEvent(
                        event_type="score_change",
                        data=change
                    )
                    
                    # Añadir a la cola de eventos
                    try:
                        self.event_queue.put_nowait(event)
                    except queue.Full:
                        # Si la cola está llena, quitar un evento antiguo
                        try:
                            self.event_queue.get_nowait()
                            self.event_queue.put_nowait(event)
                        except:
                            logger.warning("No se pudo añadir evento a la cola")
                    
                    # Notificar a los listeners
                    self._notify_listeners(event)
            
            # Registrar actualización
            self.last_update = datetime.now()
            
            # Generar evento de actualización periódica
            update_event = UpdateEvent(
                event_type="periodic_update",
                data={
                    "active_matches": len(active_matches),
                    "changes_detected": len(changes)
                }
            )
            self._notify_listeners(update_event)
            
            logger.debug(f"Actualización completada: {len(active_matches)} partidos activos, {len(changes)} cambios")
        
        except Exception as e:
            logger.error(f"Error en actualización de datos: {e}")
            
            # Notificar error a los listeners
            error_event = UpdateEvent(
                event_type="update_error",
                data=str(e)
            )
            self._notify_listeners(error_event)
    
    def force_update(self) -> None:
        """Fuerza una actualización inmediata de datos."""
        if not self.running:
            logger.warning("El programador no está en ejecución, no se puede forzar actualización")
            return
        
        # Crear un hilo separado para no bloquear
        update_thread = threading.Thread(target=self._update_data)
        update_thread.daemon = True
        update_thread.start()
        logger.info("Actualización forzada iniciada")
    
    def get_latest_events(self, limit: int = 10) -> List[UpdateEvent]:
        """
        Obtiene los eventos más recientes.
        
        Args:
            limit: Número máximo de eventos a obtener
            
        Returns:
            Lista de eventos más recientes
        """
        events = []
        temp_queue = queue.Queue()
        
        # Extraer eventos de la cola original
        try:
            while not self.event_queue.empty() and len(events) < limit:
                event = self.event_queue.get_nowait()
                events.append(event)
                temp_queue.put(event)
        except:
            pass
        
        # Restaurar eventos a la cola original
        try:
            while not temp_queue.empty():
                self.event_queue.put(temp_queue.get_nowait())
        except:
            pass
        
        # Ordenar por timestamp (más reciente primero)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return events[:limit]

# Función de prueba
def test_scheduler():
    """Función para probar el programador de tareas."""
    from data_service import SofascoreDataService
    from quiniela_manager import QuinielaManager
    
    # Crear servicios
    data_service = SofascoreDataService()
    quiniela_manager = QuinielaManager()
    
    # Crear programador
    scheduler = QuinielaScheduler(update_interval=10)  # 10 segundos para prueba
    scheduler.set_data_service(data_service)
    scheduler.set_quiniela_manager(quiniela_manager)
    
    # Añadir listener de eventos
    def event_listener(event):
        print(f"Evento recibido: {event}")
        print(f"Datos: {event.data}")
    
    scheduler.add_event_listener(event_listener)
    
    # Iniciar programador
    scheduler.start()
    
    try:
        print("Programador en ejecución. Presiona Ctrl+C para detener...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        print("Programador detenido")

if __name__ == "__main__":
    test_scheduler()