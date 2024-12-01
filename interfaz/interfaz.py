# Archivo: interfaz_simulador.py
import threading
import time
from tkinter import Canvas, Frame, Scrollbar, messagebox, Toplevel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from generador.generador import GeneradorSolicitudes
from planificador.planificador import PlanificadorDisco
from dma.dma import DMA

import numpy as np

class InterfazSimulador:
    """
    Interfaz gráfica mejorada para el simulador de planificación de disco.
    
    Esta clase implementa una GUI completa que permite:
    - Configurar parámetros de simulación
    - Visualizar y monitorear el estado del sistema
    - Controlar la ejecución de la simulación
    - Mostrar métricas y estadísticas en tiempo real
    - Gestionar el estado del DMA y bus inteligente
    
    Attributes:
        root (tk.Tk): Ventana principal de la aplicación
        planificador (PlanificadorDisco): Instancia del planificador
        dma (DMA): Sistema de Acceso Directo a Memoria
        solicitudes (list): Lista de solicitudes actuales
        lock_buffer (threading.Condition): Lock para sincronización
        
    Note:
        La interfaz utiliza ttkbootstrap para un diseño moderno y responsive.
    """

    def __init__(self, root):

        """
        Inicializa la interfaz gráfica del simulador.
        
        Configura todos los componentes de la GUI incluyendo:
        - Panel de configuración
        - Área de visualización de solicitudes
        - Controles de simulación
        - Gráficos de rendimiento
        - Panel de logs
        - Monitor DMA/Bus
        
        Args:
            root (tk.Tk): Ventana principal de la aplicación
        """
            
        self.root = root
        self.root.title("Simulador de Gestión de Disco")
        self.root.style = ttk.Style(theme="superhero")

        # Crear canvas principal con scroll
        self.main_canvas = Canvas(root)
        self.main_scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)

        # Configurar el frame scrollable
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        # Crear ventana en el canvas
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=root.winfo_screenwidth()-50)

        # Configurar el canvas
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        
        # Ubicar el canvas y scrollbar en el root
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        # Agregar binding para el scroll con el mouse
        root.bind("<MouseWheel>", lambda e: self.main_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Crear contenedores principales para las dos columnas (ahora dentro del scrollable_frame)
        self.frame_izquierdo = ttk.Frame(self.scrollable_frame)
        self.frame_izquierdo.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.frame_derecho = ttk.Frame(self.scrollable_frame)
        self.frame_derecho.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Configurar el grid
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)
        self.scrollable_frame.grid_rowconfigure(0, weight=1)

        # Configurar tamaño inicial de la ventana
        self.root.geometry(f"{root.winfo_screenwidth()-100}x800")

        # === COLUMNA IZQUIERDA ===
        # Configuración de parámetros
        self.frame_config = ttk.LabelFrame(self.frame_izquierdo, text="Configuración de Parámetros", padding=(10, 10))
        self.frame_config.pack(fill="x", padx=5, pady=5)

        ttk.Label(self.frame_config, text="Algoritmo de Planificación:").grid(row=0, column=0, sticky="w")
        self.algoritmo_var = ttk.StringVar(value="FIFO")
        # En la clase InterfazSimulador, modificar la creación del combobox de algoritmos
        self.algoritmo_menu = ttk.Combobox(self.frame_config, textvariable=self.algoritmo_var, 
                                        values=["FIFO", "SSTF", "SCAN", "C-SCAN"], 
                                        state="readonly")

        # Agregar selector de dirección
        ttk.Label(self.frame_config, text="Dirección Inicial:").grid(row=4, column=0, sticky="w")
        self.direccion_var = ttk.StringVar(value="Ascendente")
        self.direccion_menu = ttk.Combobox(self.frame_config, textvariable=self.direccion_var,
                                        values=["Ascendente", "Descendente"],
                                        state="readonly")
        self.direccion_menu.grid(row=4, column=1, pady=5)
        self.algoritmo_menu.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(self.frame_config, text="Número de Solicitudes:").grid(row=1, column=0, sticky="w")
        self.num_solicitudes_var = ttk.IntVar(value=10)
        self.num_solicitudes_entry = ttk.Entry(self.frame_config, textvariable=self.num_solicitudes_var)
        self.num_solicitudes_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(self.frame_config, text="Tamaño del Buffer:").grid(row=2, column=0, sticky="w")
        self.tamano_buffer_var = ttk.IntVar(value=5)
        self.tamano_buffer_entry = ttk.Entry(self.frame_config, textvariable=self.tamano_buffer_var)
        self.tamano_buffer_entry.grid(row=2, column=1, pady=5, padx=5)

        self.alta_carga_var = ttk.BooleanVar(value=False)
        self.alta_carga_check = ttk.Checkbutton(self.frame_config, text="Alta Carga", 
                                            variable=self.alta_carga_var, bootstyle="round-toggle")
        self.alta_carga_check.grid(row=3, column=0, columnspan=2, pady=5)

        # Área de resultados (tabla)
        self.frame_resultados = ttk.LabelFrame(self.frame_izquierdo, text="Solicitudes", padding=(10, 10))
        self.frame_resultados.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear frame con scrollbar para la tabla
        self.tabla_frame = ttk.Frame(self.frame_resultados)
        self.tabla_frame.pack(fill="both", expand=True)

        self.tabla_scroll = ttk.Scrollbar(self.tabla_frame)
        self.tabla_scroll.pack(side="right", fill="y")

        self.tabla_solicitudes = ttk.Treeview(self.tabla_frame, columns=("ID", "Tipo", "Posición", "Prioridad"), 
                                            show="headings", yscrollcommand=self.tabla_scroll.set)
        self.tabla_solicitudes.pack(side="left", fill="both", expand=True)
        self.tabla_scroll.config(command=self.tabla_solicitudes.yview)

        # Configurar columnas de la tabla
        for col in ("ID", "Tipo", "Posición", "Prioridad"):
            self.tabla_solicitudes.heading(col, text=col)
            self.tabla_solicitudes.column(col, width=70)

        # Botones de control
        self.frame_control = ttk.Frame(self.frame_izquierdo)
        self.frame_control.pack(fill="x", padx=5, pady=5)

        self.iniciar_button = ttk.Button(self.frame_control, text="Iniciar Simulación", 
                                    command=self.iniciar_simulacion, bootstyle="success-outline")
        self.iniciar_button.pack(side="left", padx=5)

        self.generar_button = ttk.Button(self.frame_control, text="Generar Solicitudes", 
                                    command=self.generar_solicitudes, bootstyle="primary-outline")
        self.generar_button.pack(side="left", padx=5)

        self.mostrar_metricas_button = ttk.Button(self.frame_control, text="Mostrar Métricas", 
                                                command=self.mostrar_metricas, bootstyle="info-outline")
        self.mostrar_metricas_button.pack(side="left", padx=5)

        # === COLUMNA DERECHA ===
        # Área de gráficos
        self.frame_graficos = ttk.LabelFrame(self.frame_derecho, text="Gráficos", padding=(10, 10))
        self.frame_graficos.pack(fill="both", expand=True, padx=5, pady=5)

        self.figura = Figure(figsize=(8, 4), dpi=100)
        self.ax_movimientos = self.figura.add_subplot(121, title="Movimientos del Cabezal")
        self.ax_tiempos = self.figura.add_subplot(122, title="Tiempos por Solicitud")

        self.canvas_matplotlib = FigureCanvasTkAgg(self.figura, master=self.frame_graficos)
        self.canvas_matplotlib.get_tk_widget().pack(fill="both", expand=True)

        # Panel de logs
        self.frame_logs = ttk.LabelFrame(self.frame_derecho, text="Logs de Ejecución", padding=(10, 10))
        self.frame_logs.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = ttk.Text(self.frame_logs, height=10, width=60, wrap="word")
        self.log_scroll = ttk.Scrollbar(self.frame_logs, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.log_scroll.set)
        
        self.log_scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        # Configurar tags para los logs
        self.log_text.tag_configure("info", foreground="white")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warning", foreground="yellow")


        # Variables internas
        self.planificador = None
        self.solicitudes = []
        self.lock_buffer = threading.Condition()

        # Crear y configurar el panel DMA/Bus
        self.crear_panel_dma_bus()
        # Iniciar la actualización periódica del estado
        self.actualizar_estado_dma_bus()
    
    def crear_panel_dma_bus(self):
        """Crea el panel de monitoreo de DMA y Bus"""
        self.frame_dma_bus = ttk.LabelFrame(self.frame_derecho, text="Estado DMA y Bus Inteligente", padding=(10, 10))
        self.frame_dma_bus.pack(fill="both", expand=True, padx=5, pady=5)
        
        # === Sección DMA ===
        self.frame_dma = ttk.LabelFrame(self.frame_dma_bus, text="DMA", padding=5)
        self.frame_dma.pack(fill="x", padx=5, pady=5)
        
        # Configuración DMA
        self.frame_dma_config = ttk.Frame(self.frame_dma)
        self.frame_dma_config.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.frame_dma_config, text="Tamaño Caché DMA:").pack(side="left")
        self.cache_size_var = ttk.IntVar(value=100)
        self.cache_size_entry = ttk.Entry(self.frame_dma_config, textvariable=self.cache_size_var, width=10)
        self.cache_size_entry.pack(side="left", padx=5)
        
        # Estado DMA
        self.dma_labels = {}
        for stat in ['Buffer Uso', 'Cache Hits', 'Cache Miss', 'Hit Rate']:
            frame = ttk.Frame(self.frame_dma)
            frame.pack(fill="x", padx=2, pady=2)
            ttk.Label(frame, text=f"{stat}:").pack(side="left")
            self.dma_labels[stat] = ttk.Label(frame, text="0")
            self.dma_labels[stat].pack(side="right")

        # === Sección Bus Inteligente ===
        self.frame_bus = ttk.LabelFrame(self.frame_dma_bus, text="Bus Inteligente", padding=5)
        self.frame_bus.pack(fill="x", padx=5, pady=5)
        
        # Configuración de prioridades del bus
        self.frame_bus_config = ttk.Frame(self.frame_bus)
        self.frame_bus_config.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(self.frame_bus_config, text="Pesos de Prioridad:").pack(side="left")
        self.prioridad_weights = {}
        for i in range(1, 6):
            frame = ttk.Frame(self.frame_bus_config)
            frame.pack(side="left", padx=5)
            ttk.Label(frame, text=f"P{i}:").pack(side="left")
            self.prioridad_weights[i] = ttk.Entry(frame, width=3)
            self.prioridad_weights[i].insert(0, str(i))
            self.prioridad_weights[i].pack(side="left")

        # Botones de control
        self.frame_control_dma_bus = ttk.Frame(self.frame_dma_bus)
        self.frame_control_dma_bus.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(self.frame_control_dma_bus, 
                text="Aplicar Cambios", 
                command=self.aplicar_cambios_dma_bus,
                bootstyle="info-outline").pack(side="left", padx=5)

        # Estado del Bus
        self.bus_labels = {}
    
        for stat in ['Solicitudes Totales', 'Solicitudes Procesadas', 'Tiempo Promedio']:
            frame = ttk.Frame(self.frame_bus)
            frame.pack(fill="x", padx=2, pady=2)
            ttk.Label(frame, text=f"{stat}:").pack(side="left")
            self.bus_labels[stat] = ttk.Label(frame, text="0")
            self.bus_labels[stat].pack(side="right")

    def aplicar_cambios_dma_bus(self):
        """Aplica los cambios de configuración al DMA y Bus"""
        try:
            # Actualizar DMA
            if hasattr(self, 'dma'):
                nuevo_cache = self.cache_size_var.get()
                self.dma.set_cache_size(nuevo_cache)
                self.agregar_log(f"Tamaño de caché DMA actualizado a {nuevo_cache}", "success")
                
            # Actualizar Bus
            if hasattr(self, 'planificador') and hasattr(self.planificador, 'dma'):
                bus = self.planificador.dma.bus
                for prioridad, entry in self.prioridad_weights.items():
                    peso = int(entry.get())
                    bus.set_priority_weight(prioridad, peso)
                self.agregar_log("Pesos de prioridad del bus actualizados", "success")
        except ValueError as e:
            self.agregar_log(f"Error: Valores inválidos - {str(e)}", "error")
        except Exception as e:
            self.agregar_log(f"Error al aplicar cambios: {str(e)}", "error")

    def actualizar_estado_dma_bus(self):
        """Actualiza los indicadores de estado del DMA y Bus"""
        if hasattr(self, 'planificador') and hasattr(self.planificador, 'dma'):
            dma = self.planificador.dma
            bus = dma.bus
            
            # Actualizar estado DMA
            status_dma = dma.get_status()
            self.dma_labels['Buffer Uso'].config(
                text=f"{status_dma['buffer_used']}/{status_dma['buffer_size']} ({status_dma['buffer_usage_percent']:.1f}%)")
            self.dma_labels['Cache Hits'].config(text=str(status_dma['cache_hits']))
            self.dma_labels['Cache Miss'].config(text=str(status_dma['cache_misses']))
            self.dma_labels['Hit Rate'].config(text=f"{status_dma['hit_rate']:.1f}%")
            
            # Actualizar estado Bus
            status_bus = bus.get_status()
            self.bus_labels['Solicitudes Totales'].config(text=str(status_bus['solicitudes_totales']))
            self.bus_labels['Solicitudes Procesadas'].config(text=str(status_bus['solicitudes_procesadas']))
            self.bus_labels['Tiempo Promedio'].config(text=f"{status_bus['tiempo_promedio']:.3f}s")
        
        # Programar siguiente actualización
        self.root.after(100, self.actualizar_estado_dma_bus)

    def generar_solicitudes(self):
        try:
            # Obtener parámetros desde los campos de entrada
            num_solicitudes = self.num_solicitudes_var.get()
            alta_carga = self.alta_carga_var.get()

            # Crear instancia de GeneradorSolicitudes con los parámetros
            generador = GeneradorSolicitudes(num_solicitudes=num_solicitudes, alta_carga=alta_carga)

            # Generar solicitudes
            self.solicitudes = generador.generar()

            # Actualizar la tabla de solicitudes
            self.actualizar_tabla_solicitudes()

            # Mensaje de éxito
            messagebox.showinfo("Éxito", f"Se generaron {len(self.solicitudes)} solicitudes.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar solicitudes: {e}")

    def agregar_log(self, mensaje, tipo="info"):
            """
            Agrega un mensaje al área de logs con el formato especificado.
            """
            self.log_text.insert("end", f"{mensaje}\n", tipo)
            self.log_text.see("end")  # Auto-scroll al final
            self.root.update_idletasks()  # Actualizar la interfaz

    def limpiar_logs(self):
        """
        Limpia el área de logs.
        """
        self.log_text.delete(1.0, "end")


    def iniciar_simulacion(self):
        if not self.solicitudes:
            messagebox.showerror("Error", "No hay solicitudes generadas.")
            return

        # Obtener el algoritmo seleccionado desde la interfaz
        algoritmo = self.algoritmo_var.get()
        if algoritmo not in ["FIFO", "SSTF", "SCAN", "C-SCAN"]:
            messagebox.showerror("Error", f"Algoritmo desconocido: {algoritmo}")
            return

        # Crear instancia de DMA
        self.dma = DMA(buffer_size=self.tamano_buffer_var.get())

        # Iniciar el planificador
        self.planificador = PlanificadorDisco(
            solicitudes=self.solicitudes,
            tamano_buffer=self.tamano_buffer_var.get(),
            algoritmo=algoritmo,
            interfaz=self,
            dma=self.dma  # Pasar la instancia de DMA al planificador
        )

        # Ejecutar el planificador en un hilo separado
        threading.Thread(target=self.planificador.ejecutar, daemon=True).start()
        self.agregar_log("Simulación en progreso...", "info")

    def mostrar_metricas(self):
        """
        Muestra las métricas finales en un cuadro de diálogo y actualiza los gráficos.
        """
        try:
            if not self.planificador:
                raise ValueError("El planificador no está inicializado. Por favor, genera las solicitudes primero.")
            
            # Obtener las métricas desde el planificador
            metricas = self.planificador.obtener_metricas()
            
            # Actualizar gráficos
            self.mostrar_grafico_metricas(metricas)
            
            # Mostrar métricas en diálogo
            mensaje = (
                f"Solicitudes procesadas: {metricas['solicitudes_procesadas']}\n"
                f"Movimientos totales del cabezal: {metricas['movimientos_cabezal']}\n"
                f"Tiempo promedio por solicitud: {metricas['tiempo_promedio']:.3f} segundos"
            )
            messagebox.showinfo("Métricas", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar métricas: {e}")


    def mostrar_grafico_metricas(self, metricas):
        """
        Muestra gráficos basados en las métricas calculadas.
        """
        try:
            # Limpiar los gráficos existentes
            self.ax_movimientos.clear()
            self.ax_tiempos.clear()

            # Gráfico de movimientos del cabezal
            self.ax_movimientos.set_title("Movimientos del Cabezal")
            tiempos = range(1, len(self.planificador.metricas.historial_accesos) + 1)
            # Usar las posiciones reales, no los movimientos
            posiciones = [acc.posicion for acc in self.planificador.metricas.historial_accesos]
            self.ax_movimientos.plot(tiempos, posiciones, 'b-', marker='o')
            self.ax_movimientos.set_xlabel("Número de Solicitud")
            self.ax_movimientos.set_ylabel("Posición del Cabezal")
            self.ax_movimientos.grid(True)

            # Gráfico de tiempos por solicitud
            self.ax_tiempos.set_title("Tiempos por Solicitud")
            if self.planificador.metricas.tiempos_por_solicitud:
                tiempos_x = range(1, len(self.planificador.metricas.tiempos_por_solicitud) + 1)
                # Usar los tiempos de proceso reales
                tiempos_proceso = [acc.tiempo_proceso for acc in self.planificador.metricas.historial_accesos]
                self.ax_tiempos.plot(tiempos_x, 
                                tiempos_proceso,
                                'g-', 
                                marker='o',
                                label="Tiempo de Proceso")
                self.ax_tiempos.set_xticks(tiempos_x)
                self.ax_tiempos.legend()
            else:
                self.ax_tiempos.text(0.5, 0.5, "Sin datos", fontsize=12, ha="center", va="center")
            
            self.ax_tiempos.set_xlabel("Número de Solicitud")
            self.ax_tiempos.set_ylabel("Tiempo (s)")
            self.ax_tiempos.grid(True)

            # Ajustar layout y dibujar
            self.figura.tight_layout()
            self.canvas_matplotlib.draw()

        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar métricas: {e}")

    def actualizar_tabla_solicitudes(self):
        # Limpia la tabla antes de insertar nuevas solicitudes
        for row in self.tabla_solicitudes.get_children():
            self.tabla_solicitudes.delete(row)

        # Inserta las solicitudes generadas en la tabla
        for solicitud in self.solicitudes:
            self.tabla_solicitudes.insert("", "end", values=(
                solicitud.id_dispositivo, solicitud.tipo, solicitud.posicion, solicitud.prioridad
            ))

