import threading
import time

from collections import defaultdict


class BusInteligente:

    """
    Implementa un bus inteligente que gestiona la transferencia de datos entre dispositivos
    y la memoria principal, manejando múltiples colas de prioridad.
    
    El bus inteligente organiza las solicitudes por niveles de prioridad y las procesa
    de manera ordenada, asegurando que las solicitudes de mayor prioridad sean atendidas
    primero.

    Attributes:
        colas_prioridad (defaultdict): Diccionario que mantiene listas separadas de solicitudes por nivel de prioridad
        lock (threading.Lock): Mecanismo de sincronización para acceso seguro a recursos compartidos
        tiempo_total_procesamiento (float): Acumulador del tiempo total de procesamiento
        solicitudes_totales (int): Contador del total de solicitudes recibidas
        solicitudes_procesadas (int): Contador de solicitudes completadas
        processing_thread (Thread): Hilo dedicado al procesamiento de solicitudes
        is_running (bool): Flag que controla el estado de ejecución del bus
    """

    def __init__(self):
        self.colas_prioridad = defaultdict(list)  # Diccionario para colas por prioridad
        self.lock = threading.Lock()
        self.tiempo_total_procesamiento = 0.0
        self.solicitudes_totales = 0
        self.solicitudes_procesadas = 0
        self.processing_thread = None
        self.is_running = True

    def agregar_solicitud(self, solicitud):
        """
        Agrega una nueva solicitud a la cola correspondiente según su prioridad.
        
        Este método es thread-safe y maneja automáticamente el inicio del procesamiento
        si es necesario.

        Args:
            solicitud (Solicitud): Objeto solicitud a ser procesado
        """
        with self.lock:  # Asegura acceso exclusivo a las colas
             # Agregar solicitud a la cola de su prioridad
            self.colas_prioridad[solicitud.prioridad].append(solicitud)
            self.solicitudes_totales += 1
            # Iniciar el procesamiento si no está en curso
            if not self.processing_thread or not self.processing_thread.is_alive():
                self.processing_thread = threading.Thread(target=self.procesar_solicitudes)
                self.processing_thread.daemon = True
                self.processing_thread.start()

    def procesar_solicitudes(self):
        """
        Procesa las solicitudes pendientes respetando el orden de prioridad.
        
        Este método implementa la lógica principal de procesamiento:
        - Procesa primero las solicitudes de mayor prioridad
        - Mantiene un registro del tiempo de procesamiento
        - Garantiza el acceso thread-safe a las colas
        """
        tiempo_inicio = time.time()
        # Continúa mientras haya solicitudes en alguna cola
        while any(self.colas_prioridad.values()):
            # Procesa prioridades en orden descendente
            for prioridad in sorted(self.colas_prioridad.keys(), reverse=True):
                while self.colas_prioridad[prioridad]:
                    with self.lock:
                        # Extrae y procesa la siguiente solicitud
                        solicitud = self.colas_prioridad[prioridad].pop(0)
                        self.solicitudes_procesadas += 1
                    time.sleep(0.1)  # Simula tiempo de procesamiento
        
        # Actualiza estadísticas de tiempo
        tiempo_total = time.time() - tiempo_inicio
        self.tiempo_total_procesamiento += tiempo_total

    def get_status(self):
        """
        Proporciona información sobre el estado actual del bus.
        
        Returns:
            dict: Diccionario con estadísticas actuales:
                - solicitudes_totales: Número total de solicitudes recibidas
                - solicitudes_procesadas: Número de solicitudes completadas
                - tiempo_promedio: Tiempo promedio de procesamiento por solicitud
        """
        with self.lock:
            return {
                'solicitudes_totales': self.solicitudes_totales,
                'solicitudes_procesadas': self.solicitudes_procesadas,
                'tiempo_promedio': (self.tiempo_total_procesamiento / self.solicitudes_procesadas
                                  if self.solicitudes_procesadas > 0 else 0)
            }