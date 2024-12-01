import threading
import time
from collections import defaultdict

from dma.bus import BusInteligente

class DMA:

    """
    Implementación del Acceso Directo a Memoria (DMA) para la transferencia eficiente de datos.

    Esta clase gestiona la transferencia de datos entre dispositivos y memoria principal,
    implementando un sistema de buffer y caché para optimizar el rendimiento.

    Attributes:
        buffer (list): Cola de solicitudes pendientes
        buffer_size (int): Tamaño máximo del buffer
        cache_size (int): Tamaño máximo de la caché
        lock (threading.Lock): Lock principal para sincronización
        buffer_not_full (Condition): Condición para control de buffer lleno
        buffer_not_empty (Condition): Condición para control de buffer vacío
        bus (BusInteligente): Instancia del bus para transferencia de datos
        is_running (bool): Estado de ejecución del DMA
        cache (dict): Caché de solicitudes procesadas
        cache_hits (int): Contador de aciertos en caché
        cache_misses (int): Contador de fallos en caché
        buffer_usage_history (list): Historial de uso del buffer
        cache_hits_history (list): Historial de rendimiento de la caché
    """
     
    def __init__(self, buffer_size=5, cache_size=100):
        # Inicialización de estructuras básicas
        self.buffer = []  # Buffer principal de solicitudes
        self.buffer_size = buffer_size  # Tamaño configurable del buffer
        self.cache_size = cache_size  # Tamaño configurable de la caché
        
        # Mecanismos de sincronización
        self.lock = threading.Lock()  # Lock principal
        self.buffer_not_full = threading.Condition(self.lock)  # Control de buffer lleno
        self.buffer_not_empty = threading.Condition(self.lock)  # Control de buffer vacío
        
        # Componentes del sistema
        self.bus = BusInteligente()  # Bus para transferencia de datos
        self.is_running = True  # Estado de ejecución
        
        # Sistema de caché y métricas
        self.cache = {}  # Caché de solicitudes
        self.cache_hits = 0  # Contador de aciertos
        self.cache_misses = 0  # Contador de fallos
        self.transferencia_total = 0  # Total de transferencias
        self.buffer_usage_history = []  # Historial de uso
        self.cache_hits_history = []  # Historial de rendimiento
        
        # Inicialización de hilos
        self.processing_thread = threading.Thread(target=self.procesar_buffer)
        self.monitor_thread = threading.Thread(target=self.monitor_rendimiento)
        self.processing_thread.daemon = True
        self.monitor_thread.daemon = True
        self.processing_thread.start()
        self.monitor_thread.start()

    def procesar_buffer(self):
        """
        Procesa continuamente las solicitudes del buffer.
        
        Este método se ejecuta en un hilo separado y maneja la transferencia
        de solicitudes desde el buffer hacia el bus inteligente.
        """
        while self.is_running:
            with self.buffer_not_empty:
                # Esperar si el buffer está vacío
                while not self.buffer and self.is_running:
                    self.buffer_not_empty.wait(timeout=1.0)
                
                if not self.is_running:
                    break
                    
                # Procesar siguiente solicitud si hay disponible
                if self.buffer:
                    solicitud = self.buffer.pop(0)
                    self.buffer_not_full.notify()
                    self.bus.agregar_solicitud(solicitud)

    def transferir(self, solicitud):
        """
        Transfiere una solicitud al buffer del DMA.
        
        Este método implementa la lógica de caché y control de buffer,
        optimizando el rendimiento de las transferencias.

        Args:
            solicitud (Solicitud): La solicitud a transferir
        """
        with self.buffer_not_full:
            # Esperar si el buffer está lleno
            while len(self.buffer) >= self.buffer_size and self.is_running:
                print(f"DMA: Buffer lleno ({len(self.buffer)}/{self.buffer_size}). Esperando...")
                self.buffer_not_full.wait(timeout=1.0)
            
            if not self.is_running:
                return
            
            # Verificar caché antes de transferir
            cache_key = (solicitud.id_dispositivo, solicitud.posicion, solicitud.tipo)
            if cache_key in self.cache:
                self.cache_hits += 1
                return self.cache[cache_key]
            
            # Procesar nueva solicitud
            self.cache_misses += 1
            self.buffer.append(solicitud)
            self.transferencia_total += 1
            
            # Actualizar caché con política LRU
            self.cache[cache_key] = solicitud
            if len(self.cache) > self.cache_size:
                self.cache.pop(next(iter(self.cache)))
            
            self.buffer_not_empty.notify()

    def monitor_rendimiento(self):
        """
        Monitorea y registra estadísticas de rendimiento del DMA.
        
        Mantiene un registro histórico del uso del buffer y rendimiento
        de la caché para análisis y optimización.
        """
        while self.is_running:
            with self.lock:
                # Registrar uso del buffer
                self.buffer_usage_history.append({
                    'timestamp': time.time(),
                    'usage': len(self.buffer)
                })
                
                # Registrar hit rate de cache
                total_accesos = self.cache_hits + self.cache_misses
                hit_rate = (self.cache_hits / total_accesos * 100) if total_accesos > 0 else 0
                self.cache_hits_history.append({
                    'timestamp': time.time(),
                    'hit_rate': hit_rate
                })
                
                # Limitar histórico
                if len(self.buffer_usage_history) > 1000:
                    self.buffer_usage_history = self.buffer_usage_history[-1000:]
                if len(self.cache_hits_history) > 1000:
                    self.cache_hits_history = self.cache_hits_history[-1000:]
            
            time.sleep(0.1)

    def get_status(self):
        """
        Obtiene el estado actual del DMA.
        
        Returns:
            dict: Diccionario con métricas actuales incluyendo:
                - Uso del buffer
                - Estadísticas de caché
                - Historial de rendimiento
        """
        with self.lock:
            total_accesos = self.cache_hits + self.cache_misses
            hit_rate = (self.cache_hits / total_accesos * 100) if total_accesos > 0 else 0
            
            return {
                'buffer_size': self.buffer_size,
                'buffer_used': len(self.buffer),
                'buffer_usage_percent': (len(self.buffer) / self.buffer_size) * 100,
                'cache_size': self.cache_size,
                'cache_used': len(self.cache),
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate': hit_rate,
                'transferencias_totales': self.transferencia_total,
                'buffer_history': self.buffer_usage_history[-50:],
                'cache_history': self.cache_hits_history[-50:]
            }

    def set_cache_size(self, new_size):
        """
        Ajusta dinámicamente el tamaño de la caché.
        
        Args:
            new_size (int): Nuevo tamaño de caché deseado
        """
        with self.lock:
            self.cache_size = new_size
            while len(self.cache) > new_size:
                self.cache.pop(next(iter(self.cache)))

    def shutdown(self):
        """
        Detiene de manera segura todos los procesos del DMA.
        
        Asegura una terminación limpia de hilos y liberación de recursos.
        """
        self.is_running = False
        with self.buffer_not_empty:
            self.buffer_not_empty.notify_all()
        with self.buffer_not_full:
            self.buffer_not_full.notify_all()
        self.processing_thread.join()
        self.monitor_thread.join()