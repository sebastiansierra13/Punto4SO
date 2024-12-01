import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

class MetricVisualizer:
    """
    Visualizador de métricas del sistema de planificación de disco.
    
    Esta clase se encarga de generar visualizaciones gráficas detalladas
    del rendimiento del sistema, incluyendo movimientos del cabezal,
    distribución de accesos y rendimiento temporal.
    
    Attributes:
        figure (Figure): Objeto Figure de matplotlib para la generación de gráficos
    """
    def __init__(self, figure=None):
        """
        Inicializa el visualizador de métricas.
        
        Args:
            figure (Figure, optional): Objeto Figure pre-existente. Si no se proporciona,
                                     se crea uno nuevo.
        """
        self.figure = figure if figure else Figure(figsize=(10, 6))
       
    def plot_metrics(self, metricas, historial_accesos):
        """
        Genera visualizaciones completas de las métricas del sistema.
        
        Crea tres gráficos diferentes:
        1. Movimientos del cabezal a lo largo del tiempo
        2. Distribución de accesos en el disco
        3. Rendimiento temporal acumulado
        
        Args:
            metricas (dict): Diccionario con métricas generales del sistema
            historial_accesos (list): Lista de accesos con timestamps y posiciones
        
        Returns:
            Figure: Objeto Figure con los gráficos generados
        """
        # Limpiar figura existente para nueva visualización
        self.figure.clear()
       
        # Configurar layout de subplots
        grid = self.figure.add_gridspec(2, 2)
        ax1 = self.figure.add_subplot(grid[0, 0])
        ax2 = self.figure.add_subplot(grid[0, 1])
        ax3 = self.figure.add_subplot(grid[1, :])
       
        # 1. Gráfico de movimientos del cabezal
        tiempos = [acc['tiempo'] for acc in historial_accesos]
        posiciones = [acc['posicion'] for acc in historial_accesos]
        ax1.plot(tiempos, posiciones, 'b-', label='Posición del cabezal')
        ax1.set_title('Movimiento del Cabezal vs Tiempo')
        ax1.set_xlabel('Tiempo (s)')
        ax1.set_ylabel('Posición')
        ax1.grid(True)
       
        # 2. Histograma de distribución de accesos
        ax2.hist(posiciones, bins=20, color='green', alpha=0.7)
        ax2.set_title('Distribución de Accesos')
        ax2.set_xlabel('Posición')
        ax2.set_ylabel('Frecuencia')
       
        # 3. Gráfico de rendimiento temporal acumulado
        movimientos = [acc['movimientos'] for acc in historial_accesos]
        tiempos_normalizados = [(t - tiempos[0]) for t in tiempos]
        ax3.plot(tiempos_normalizados, np.cumsum(movimientos), 
                'r-', label='Movimientos acumulados')
        ax3.set_title('Rendimiento Temporal')
        ax3.set_xlabel('Tiempo (s)')
        ax3.set_ylabel('Movimientos Acumulados')
        ax3.grid(True)
       
        # Ajustar layout para visualización óptima
        self.figure.tight_layout()
        return self.figure
       
    def plot_comparison(self, metricas_por_algoritmo):
        """
        Genera gráficos comparativos entre diferentes algoritmos.
        
        Crea dos gráficos de barras que comparan:
        1. Movimientos totales entre algoritmos
        2. Tiempos totales entre algoritmos
        
        Args:
            metricas_por_algoritmo (dict): Diccionario con métricas por algoritmo
        
        Returns:
            Figure: Objeto Figure con los gráficos comparativos
        """
        # Limpiar figura para nueva comparación
        self.figure.clear()
       
        # Configurar subplots para comparación
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
       
        # Extraer datos para comparación
        algoritmos = list(metricas_por_algoritmo.keys())
        movimientos = [m['movimientos_totales'] for m in metricas_por_algoritmo.values()]
        tiempos = [m['tiempo_total'] for m in metricas_por_algoritmo.values()]
       
        # Gráfico comparativo de movimientos
        ax1.bar(algoritmos, movimientos, color=['blue', 'green', 'red'])
        ax1.set_title('Comparación de Movimientos')
        ax1.set_ylabel('Movimientos Totales')
       
        # Gráfico comparativo de tiempos
        ax2.bar(algoritmos, tiempos, color=['blue', 'green', 'red'])
        ax2.set_title('Comparación de Tiempos')
        ax2.set_ylabel('Tiempo Total (s)')
       
        # Ajustar layout para visualización óptima
        self.figure.tight_layout()
        return self.figure