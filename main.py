"""
Sistema de Simulación de Planificación de Disco
    
Este es el módulo principal del sistema que simula la planificación de disco
utilizando diferentes algoritmos (FIFO, SSTF, SCAN, C-SCAN) junto con DMA y
buses inteligentes.

El sistema permite:
- Simular diferentes algoritmos de planificación
- Visualizar métricas en tiempo real
- Analizar rendimiento del sistema
- Gestionar transferencias mediante DMA
- Controlar el tráfico mediante buses inteligentes

Version: 1.0
"""

from generador.generador import GeneradorSolicitudes
from planificador.planificador import PlanificadorDisco
from dma.dma import DMA
from interfaz.interfaz import InterfazSimulador
import tkinter as tk

def main():
    """
    Punto de entrada principal del sistema.
    
    Inicializa la interfaz gráfica y comienza la simulación del
    sistema de planificación de disco.
    """
    # Crear la ventana principal para la interfaz gráfica
    root = tk.Tk()  
    
    # Inicializar la interfaz gráfica del simulador
    app = InterfazSimulador(root)
    
    # Iniciar el bucle principal de la interfaz
    root.mainloop()

# Verificación estándar de Python para ejecución directa
if __name__ == "__main__":
    main()