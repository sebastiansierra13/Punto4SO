import time
from dataclasses import dataclass
from typing import List

@dataclass
class MetricaAcceso:
    """
    Estructura de datos para almacenar información detallada de cada acceso al disco.
    
    Esta clase utiliza @dataclass para proporcionar una estructura eficiente
    para el almacenamiento y manejo de métricas individuales de acceso.
    
    Attributes:
        posicion (int): Posición en el disco donde se realizó el acceso
        movimientos (int): Cantidad de movimientos del cabezal realizados
        tiempo_inicio (float): Timestamp del inicio de la operación
        tiempo_fin (float): Timestamp de finalización de la operación
    """
    posicion: int
    movimientos: int
    tiempo_inicio: float
    tiempo_fin: float

    @property
    def tiempo_proceso(self):
        """
        Calcula el tiempo total de proceso para este acceso.
        
        Returns:
            float: Tiempo total en segundos que tomó el acceso
        """
        return self.tiempo_fin - self.tiempo_inicio

class Metricas:
    """
    Sistema de medición y análisis de rendimiento para el planificador de disco.
    
    Esta clase mantiene un registro detallado de todas las operaciones realizadas,
    incluyendo tiempos, movimientos y estadísticas de rendimiento.
    
    Attributes:
        movimientos_cabezal (int): Total de movimientos realizados por el cabezal
        solicitudes_procesadas (int): Número total de solicitudes completadas
        tiempo_inicio_global (float): Timestamp del inicio de la medición
        tiempos_por_solicitud (list): Lista de tiempos de proceso por solicitud
        historial_accesos (list): Lista detallada de todos los accesos realizados
        acceso_actual (dict): Información del acceso en proceso actual
    """
    def __init__(self):
        """
        Inicializa el sistema de métricas con valores por defecto.
        """
        self.movimientos_cabezal = 0  # Contador de movimientos totales
        self.solicitudes_procesadas = 0  # Contador de solicitudes procesadas
        self.tiempo_inicio_global = time.time()  # Marca de tiempo inicial
        self.tiempos_por_solicitud = []  # Registro de tiempos individuales
        self.historial_accesos: List[MetricaAcceso] = []  # Historial completo
        self.acceso_actual = None  # Acceso en proceso

    def iniciar_solicitud(self):
        """
        Marca el inicio de una nueva solicitud.
        
        Registra el timestamp de inicio para la medición precisa
        del tiempo de proceso de la solicitud actual.
        """
        self.acceso_actual = {
            'tiempo_inicio': time.time()
        }

    def registrar_busqueda(self, movimientos: int, posicion: int):
        """
        Registra una operación de búsqueda completada.
        
        Almacena toda la información relevante de la operación,
        incluyendo tiempo, movimientos y posición.
        
        Args:
            movimientos (int): Cantidad de movimientos realizados
            posicion (int): Posición final del cabezal
        """
        tiempo_fin = time.time()
        
        if not self.acceso_actual:
            self.acceso_actual = {'tiempo_inicio': self.tiempo_inicio_global}

        # Crear registro detallado del acceso
        acceso = MetricaAcceso(
            posicion=posicion,
            movimientos=movimientos,
            tiempo_inicio=self.acceso_actual['tiempo_inicio'],
            tiempo_fin=tiempo_fin
        )

        # Actualizar contadores y registros
        self.movimientos_cabezal += movimientos
        self.solicitudes_procesadas += 1
        self.tiempos_por_solicitud.append(acceso.tiempo_proceso)
        self.historial_accesos.append(acceso)
        self.acceso_actual = None

    def obtener_estadisticas_detalladas(self):
        """
        Genera un reporte completo de estadísticas de rendimiento.
        
        Returns:
            dict: Diccionario con todas las métricas relevantes incluyendo:
                - Tiempos totales y promedios
                - Movimientos totales y promedios
                - Estadísticas de solicitudes procesadas
        """
        if not self.historial_accesos:
            return {
                'tiempo_total': 0,
                'tiempo_promedio': 0,
                'tiempo_min': 0,
                'tiempo_max': 0,
                'movimientos_totales': 0,
                'movimientos_promedio': 0,
                'solicitudes_procesadas': 0
            }

        tiempos_proceso = [acc.tiempo_proceso for acc in self.historial_accesos]
        tiempo_total = self.historial_accesos[-1].tiempo_fin - self.tiempo_inicio_global

        return {
            'tiempo_total': tiempo_total,
            'tiempo_promedio': sum(tiempos_proceso) / len(tiempos_proceso),
            'tiempo_min': min(tiempos_proceso),
            'tiempo_max': max(tiempos_proceso),
            'movimientos_totales': self.movimientos_cabezal,
            'movimientos_promedio': self.movimientos_cabezal / self.solicitudes_procesadas,
            'solicitudes_procesadas': self.solicitudes_procesadas
        }

    def calcular_tiempo_promedio(self):
        """
        Calcula el tiempo promedio de procesamiento por solicitud.
        
        Returns:
            float: Tiempo promedio en segundos, o 0 si no hay solicitudes
        """
        if not self.tiempos_por_solicitud:
            return 0
        return sum(self.tiempos_por_solicitud) / len(self.tiempos_por_solicitud)

    def obtener_tiempo_total(self):
        """
        Calcula el tiempo total transcurrido desde el inicio.
        
        Returns:
            float: Tiempo total en segundos desde el inicio de la medición
        """
        if not self.historial_accesos:
            return 0
        return self.historial_accesos[-1].tiempo_fin - self.tiempo_inicio_global