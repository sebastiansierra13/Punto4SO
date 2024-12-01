from collections import Counter, defaultdict
from planificador.metricas import Metricas
from planificador.metricasView import MetricVisualizer
import time

class PlanificadorDisco:


    """
    Implementa los algoritmos de planificación de disco: FIFO, SSTF, SCAN y C-SCAN.

    Esta clase es el núcleo del sistema de planificación, manejando la selección
    y ejecución de solicitudes según diferentes estrategias de optimización.

    Attributes:
        solicitudes (list): Cola de solicitudes pendientes
        tamano_buffer (int): Tamaño del buffer de solicitudes
        algoritmo (str): Algoritmo de planificación seleccionado
        metricas (Metricas): Sistema de métricas y estadísticas
        posicion_actual (int): Posición actual del cabezal
        direccion (int): Dirección del movimiento en SCAN (1: arriba, -1: abajo)
        max_posicion (int): Posición máxima del disco
        is_running (bool): Estado de ejecución del planificador
        interfaz (InterfazSimulador): Referencia a la interfaz gráfica
        dma (DMA): Sistema de Acceso Directo a Memoria
        patron_accesos (defaultdict): Registro de patrones de acceso
        predictor_accesos (defaultdict): Sistema de predicción de accesos
        inicio_espera (dict): Registro de tiempos de espera de solicitudes
    """

    def __init__(self, solicitudes=None, tamano_buffer=10, algoritmo="FIFO", interfaz=None, dma=None):

        """
        Inicializa el planificador de disco.

        Args:
            solicitudes (list, optional): Lista inicial de solicitudes. Defaults to None.
            tamano_buffer (int, optional): Tamaño del buffer. Defaults to 10.
            algoritmo (str, optional): Algoritmo a utilizar. Defaults to "FIFO".
            interfaz (InterfazSimulador, optional): Referencia a la UI. Defaults to None.
            dma (DMA, optional): Sistema DMA. Defaults to None.

        Raises:
            ValueError: Si se especifica un algoritmo no soportado
        """


        self.solicitudes = solicitudes or []
        self.tamano_buffer = tamano_buffer
        self.algoritmo = algoritmo
        self.metricas = Metricas()
        self.posicion_actual = 0
        self.direccion = 1  # 1: hacia arriba, -1: hacia abajo
        self.max_posicion = 100
        self.is_running = True
        self.interfaz = interfaz
        self.dma = dma

        # Mejoras para predicción y envejecimiento
        self.patron_accesos = defaultdict(list)  # Para SSTF mejorado
        self.predictor_accesos = defaultdict(int)  # Para predicción de movimientos
        self.tiempo_envejecimiento = 5.0  # Segundos antes de aumentar prioridad
        self.tiempos_ultimo_acceso = {}  # Para envejecimiento FIFO
        self.prediccion_cache = {}  # Cache de predicciones
        self.inicio_espera = {}  # Para tracking de tiempo de espera
        
        if self.algoritmo not in ["FIFO", "SSTF", "SCAN", "C-SCAN"]:
            raise ValueError(f"Algoritmo desconocido: {self.algoritmo}")

    def sstf_optimizado(self, posicion_actual):
        """
        Implementa el algoritmo SSTF (Shortest Seek Time First) optimizado.

        Esta implementación considera no solo la distancia más corta, sino también
        las prioridades y patrones de acceso históricos.

        Args:
            posicion_actual (int): Posición actual del cabezal

        Returns:
            Solicitud: Siguiente solicitud a procesar, o None si no hay solicitudes
        """

        if not self.solicitudes:
            return None

        tiempo_actual = time.time()
        
        # Actualizar predicciones basadas en patrones históricos
        for solicitud in self.solicitudes:
            sector = solicitud.posicion
            if sector in self.patron_accesos:
                # Calcular la probabilidad de acceso basada en el historial
                accesos_recientes = [acc for acc in self.patron_accesos[sector] 
                                   if tiempo_actual - acc < 60]  # Últimos 60 segundos
                frecuencia = len(accesos_recientes)
            else:
                frecuencia = 0

        def calcular_puntuacion(solicitud):
            distancia = abs(solicitud.posicion - posicion_actual)
            espera = tiempo_actual - self.inicio_espera.get(id(solicitud), tiempo_actual)
            prediccion = self.predictor_accesos[solicitud.posicion]
            frecuencia = len([acc for acc in self.patron_accesos[solicitud.posicion] 
                            if tiempo_actual - acc < 60])
            
            # Puntuación combinada de todos los factores
            return (
                solicitud.prioridad * 10 +  # Prioridad base
                frecuencia * 5 +            # Frecuencia de acceso histórica
                prediccion * 2 -            # Predicción de accesos futuros
                distancia +                 # Distancia (negativa porque menor es mejor)
                min(espera * 2, 20)         # Tiempo de espera (máximo 20 puntos)
            )

        solicitud = max(self.solicitudes, key=calcular_puntuacion)
        self.solicitudes.remove(solicitud)
        
        # Registrar acceso para futuros patrones
        self.patron_accesos[solicitud.posicion].append(tiempo_actual)
        self.predictor_accesos[solicitud.posicion] += 1
        
        return solicitud

    def scan_optimizado(self, posicion_actual):
        """
        Implementa el algoritmo SCAN optimizado con consideración de prioridades.

        El algoritmo SCAN mueve el cabezal en una dirección hasta llegar al final,
        luego cambia de dirección. Esta implementación considera también las 
        prioridades de las solicitudes.

        Args:
            posicion_actual (int): Posición actual del cabezal

        Returns:
            Solicitud: Siguiente solicitud a procesar, o None si no hay solicitudes
        """

        if not self.solicitudes:
            return None
        
        # Dividir solicitudes según posición actual y dirección
        solicitudes_adelante = [s for s in self.solicitudes if s.posicion >= posicion_actual]
        solicitudes_atras = [s for s in self.solicitudes if s.posicion < posicion_actual]
        
        # Ordenar ambos grupos por posición
        solicitudes_adelante.sort(key=lambda x: x.posicion)
        solicitudes_atras.sort(key=lambda x: x.posicion, reverse=True)
        
        # Seleccionar siguiente solicitud según dirección
        if self.direccion == 1:  # Moviendo hacia arriba
            if solicitudes_adelante:
                solicitud = solicitudes_adelante[0]
                self.solicitudes.remove(solicitud)
            else:
                self.direccion = -1  # Cambiar dirección
                if solicitudes_atras:
                    solicitud = solicitudes_atras[0]
                    self.solicitudes.remove(solicitud)
                else:
                    return None
        else:  # Moviendo hacia abajo
            if solicitudes_atras:
                solicitud = solicitudes_atras[0]
                self.solicitudes.remove(solicitud)
            else:
                self.direccion = 1  # Cambiar dirección
                if solicitudes_adelante:
                    solicitud = solicitudes_adelante[0]
                    self.solicitudes.remove(solicitud)
                else:
                    return None
        
        return solicitud

    def fifo_con_envejecimiento(self):
        """FIFO con sistema de prioridades y envejecimiento"""
        if not self.solicitudes:
            return None

        tiempo_actual = time.time()
        
        # Actualizar prioridades basadas en tiempo de espera
        for solicitud in self.solicitudes:
            tiempo_espera = tiempo_actual - self.inicio_espera.get(id(solicitud), tiempo_actual)
            incrementos = int(tiempo_espera / self.tiempo_envejecimiento)
            if incrementos > 0:
                solicitud.prioridad = min(5, solicitud.prioridad + incrementos)

        # Obtener la solicitud más antigua con mayor prioridad
        solicitud = max(self.solicitudes, key=lambda x: (x.prioridad, -self.solicitudes.index(x)))
        self.solicitudes.remove(solicitud)
        
        return solicitud

    def procesar(self, posicion_actual):
        """
        Procesa la siguiente solicitud según el algoritmo seleccionado.

        Este método implementa la lógica central de selección y procesamiento
        de solicitudes, coordinando con el DMA cuando está disponible.

        Args:
            posicion_actual (int): Posición actual del cabezal

        Returns:
            Solicitud: Solicitud procesada, o None si no hay solicitudes

        Raises:
            ValueError: Si el algoritmo especificado es inválido
        """
        if not self.solicitudes:
            return None
            
        self.metricas.iniciar_solicitud()
        
        # Seleccionar solicitud según el algoritmo
        if self.algoritmo == "FIFO":
            solicitud = self.fifo_con_envejecimiento()
        elif self.algoritmo == "SSTF":
            solicitud = self.sstf_optimizado(posicion_actual)
        elif self.algoritmo in ["SCAN", "C-SCAN"]:
            solicitud = self.scan_optimizado(posicion_actual)
        else:
            raise ValueError("Algoritmo desconocido.")

        # Registrar tiempo de inicio para nuevas solicitudes
        for sol in self.solicitudes:
            if id(sol) not in self.inicio_espera:
                self.inicio_espera[id(sol)] = time.time()
        
        if self.dma:
            self.dma.transferir(solicitud)
        
        movimientos = abs(posicion_actual - solicitud.posicion)
        tiempo_estimado = self.predecir_tiempo_busqueda(movimientos, solicitud)
        time.sleep(tiempo_estimado)
        
        self.metricas.registrar_busqueda(movimientos, solicitud.posicion)
        
        return solicitud

    def predecir_tiempo_busqueda(self, movimientos, solicitud):
        """Predice el tiempo de búsqueda basado en patrones históricos"""
        sector_key = (solicitud.posicion // 10) * 10  # Agrupa sectores similares
        
        if sector_key in self.prediccion_cache:
            return self.prediccion_cache[sector_key] * movimientos
        
        # Tiempo base más variación por movimientos
        tiempo_base = 0.01  # 10ms por movimiento
        return tiempo_base * movimientos
    

    def ejecutar(self):
        """Ejecuta el planificador con las mejoras implementadas"""
        self.log(f"Planificador: Iniciando simulación con algoritmo {self.algoritmo}")
        posicion_actual = 0
        
        # Inicializar tiempos de espera para todas las solicitudes
        for solicitud in self.solicitudes:
            self.inicio_espera[id(solicitud)] = time.time()
        
        while self.solicitudes:
            solicitud = self.procesar(posicion_actual)
            if solicitud:
                tiempo_proceso = self.metricas.tiempos_por_solicitud[-1]
                self.log(
                    f"Planificador: Procesado {solicitud} en {tiempo_proceso:.3f}s",
                    "success" if tiempo_proceso < 0.3 else "warning"
                )
                posicion_actual = solicitud.posicion
                
                # Limpiar referencias de solicitudes procesadas
                self.inicio_espera.pop(id(solicitud), None)
                
        self.log("Planificador: Simulación completada", "success")
        self.mostrar_analisis_rendimiento()



    def log(self, mensaje, tipo="info"):
        """
        Registra un mensaje tanto en la consola como en la interfaz si está disponible.
        """
        print(mensaje)
        if self.interfaz:
            self.interfaz.agregar_log(mensaje, tipo)



    
    def obtener_metricas(self):
        """
        Obtiene un diccionario con las métricas actuales del planificador.
        """
        estadisticas = self.metricas.obtener_estadisticas_detalladas()
        return {
            "solicitudes_procesadas": self.metricas.solicitudes_procesadas,
            "movimientos_cabezal": self.metricas.movimientos_cabezal,
            "tiempo_promedio": self.metricas.calcular_tiempo_promedio(),
            "tiempos_por_solicitud": self.metricas.tiempos_por_solicitud,
            # Métricas adicionales para los algoritmos mejorados
            "patrones_acceso": len(self.patron_accesos),
            "predicciones_realizadas": len(self.prediccion_cache),
            "direccion_actual": "Ascendente" if self.direccion == 1 else "Descendente",
            "tiempo_total": estadisticas.get('tiempo_total', 0),
            "tiempo_min": estadisticas.get('tiempo_min', 0),
            "tiempo_max": estadisticas.get('tiempo_max', 0)
        }
    

    def mostrar_analisis_rendimiento(self):
        """
        Muestra el análisis de rendimiento detallado en la interfaz.
        """
        estadisticas = self.metricas.obtener_estadisticas_detalladas()
        tiempo_total = self.metricas.obtener_tiempo_total()
        movimientos_promedio = estadisticas['movimientos_promedio']

        self.log("\n=== Análisis de Rendimiento ===", "info")
        self.log(f"Algoritmo: {self.algoritmo}", "info")
        self.log(f"Movimientos totales: {estadisticas['movimientos_totales']}", "info")
        self.log(f"Tiempo total: {tiempo_total:.2f}s", "info")
        self.log(f"Tiempo promedio por solicitud: {estadisticas['tiempo_promedio']:.3f}s", "info")
        self.log(f"Promedio movimientos/acceso: {movimientos_promedio:.2f}", "info")

        # Análisis adicional para algoritmos mejorados
        if self.algoritmo == "SSTF":
            self.log("\nAnálisis de Patrones:", "info")
            sectores_frecuentes = sorted(
                self.patron_accesos.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )[:5]
            for sector, accesos in sectores_frecuentes:
                self.log(f"Sector {sector}: {len(accesos)} accesos", "info")
                
        elif self.algoritmo in ["SCAN", "C-SCAN"]:
            self.log(f"\nDirección actual: {'Ascendente' if self.direccion == 1 else 'Descendente'}", "info")
            
        # Análisis de sectores más accedidos
        sectores = {}
        for acc in self.metricas.historial_accesos:
            sectores[acc.posicion] = sectores.get(acc.posicion, 0) + 1

        self.log("\nSectores más accedidos:", "info")
        for sector, accesos in sorted(sectores.items(), key=lambda x: (-x[1], x[0]))[:5]:
            self.log(f"Sector {sector}: {accesos} accesos", "info")

        # Análisis de predicciones
        if self.prediccion_cache:
            self.log("\nPredicciones de tiempo:", "info")
            tiempo_promedio_predicho = sum(self.prediccion_cache.values()) / len(self.prediccion_cache)
            self.log(f"Tiempo promedio predicho: {tiempo_promedio_predicho:.3f}s", "info")


    