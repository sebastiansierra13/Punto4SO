import random

class Solicitud:
    """
    Representa una solicitud individual de operación en el disco duro.

    Esta clase encapsula toda la información necesaria para definir una operación
    de lectura o escritura en el disco, incluyendo su origen, destino y prioridad.

    Attributes:
        id_dispositivo (int): Identificador único del dispositivo que realiza la solicitud
        posicion (int): Sector específico del disco donde se realizará la operación
        tipo (str): Tipo de operación a realizar ('lectura' o 'escritura')
        prioridad (int): Nivel de prioridad de la solicitud (1-5, siendo 5 la más alta)
    """
    def __init__(self, id_dispositivo, posicion, tipo, prioridad=1):
        """
        Inicializa una nueva solicitud de disco.

        Args:
            id_dispositivo (int): ID del dispositivo que realiza la solicitud
            posicion (int): Posición en el disco donde realizar la operación
            tipo (str): Tipo de operación ('lectura' o 'escritura')
            prioridad (int, optional): Nivel de prioridad. Defaults to 1.
        """
        self.id_dispositivo = id_dispositivo  # Identificador del dispositivo origen
        self.posicion = posicion  # Sector del disco objetivo
        self.tipo = tipo  # Tipo de operación a realizar
        self.prioridad = prioridad  # Nivel de prioridad de la solicitud

    def __repr__(self):
        """
        Proporciona una representación en string de la solicitud.

        Returns:
            str: Representación formateada que incluye todos los atributos
                relevantes de la solicitud en un formato legible.
        """
        return f"[Dispositivo: {self.id_dispositivo}, {self.tipo.capitalize()}, " \
               f"Posición: {self.posicion}, Prioridad: {self.prioridad}]"


class GeneradorSolicitudes:
    """
    Generador automático de solicitudes de disco para simulación.

    Esta clase se encarga de crear conjuntos de solicitudes aleatorias pero realistas
    para simular diferentes patrones de acceso al disco. Permite configurar la cantidad
    y características de las solicitudes generadas.

    Attributes:
        num_solicitudes (int): Cantidad de solicitudes a generar
        max_posicion (int): Límite superior para las posiciones en el disco
        alta_carga (bool): Indica si se debe simular una carga alta del sistema
    """
    def __init__(self, num_solicitudes=10, max_posicion=100, alta_carga=False):
        """
        Inicializa el generador de solicitudes.

        Args:
            num_solicitudes (int, optional): Número de solicitudes a generar. Defaults to 10.
            max_posicion (int, optional): Posición máxima en el disco. Defaults to 100.
            alta_carga (bool, optional): Activar modo de alta carga. Defaults to False.
        """
        self.num_solicitudes = num_solicitudes  # Cantidad de solicitudes a generar
        self.max_posicion = max_posicion  # Límite máximo de posición en disco
        self.alta_carga = alta_carga  # Indicador de modo alta carga

    def generar(self):
        """
        Genera un conjunto de solicitudes aleatorias.

        El método crea solicitudes con características aleatorias pero realistas,
        considerando diferentes tipos de operación, posiciones en el disco y
        niveles de prioridad. En modo de alta carga, las posiciones se distribuyen
        en un rango mayor.

        Returns:
            list[Solicitud]: Lista de objetos Solicitud generados aleatoriamente
        """
        solicitudes = []
        for _ in range(self.num_solicitudes):
            # Generar parámetros aleatorios para cada solicitud
            tipo = random.choice(["lectura", "escritura"])  # Tipo de operación aleatorio
            
            # Calcular posición según modo de carga
            max_pos = self.max_posicion * 10 if self.alta_carga else self.max_posicion
            posicion = random.randint(0, max_pos)
            
            prioridad = random.randint(1, 5)  # Prioridad aleatoria entre 1 y 5
            id_dispositivo = random.randint(1, 3)  # Simula 3 dispositivos conectados
            
            # Crear y agregar la nueva solicitud
            solicitudes.append(Solicitud(id_dispositivo, posicion, tipo, prioridad))
        
        return solicitudes