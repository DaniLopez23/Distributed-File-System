#!/usr/bin/python3

import os
import sys
import binascii
import Ice
import IceStorm
import hashlib
from util import get_topic_manager
import logging
import colorlog

Ice.loadSlice('urfs.ice')
import URFS

STORAGE_PATH = 'storage'
class UploaderI(URFS.Uploader):
    def __init__(self, filename, publisher, filemanager):      
        """
        Esta función inicializa un objeto con atributos para manejo de archivos, editor, nombre, 
        nombre de archivo, archivo y objeto hash.
        
        :param publisher: Es un parámetro que se utiliza para gestionar la publicación de eventos en el canal FileUpdates. 
        :param filemanager: Es un parámetro que representa el objeto de manejo de archivos que se utilizará.
        para administrar archivos. El propósito de este parámetro es proporcionar una forma de interactuar con los archivos.
        """
        self.filemanager = filemanager
        self.publisher = publisher
        self.filename = os.path.basename(filename)
        full_path = f'{STORAGE_PATH}/{self.filename}' 
        self.file = open(full_path, 'wb')
        self.hash_object = hashlib.md5()

    def send(self, block, current=None):
        """
        La función decodifica y almacena datos de un bloque si está en el formato correcto; de lo
        contrario, registra un mensaje de error.
        
        :param block: El parámetro `block` es una cadena que representa un bloque de datos. Se espera que
        esté en formato base64, comenzando con "b'" y terminando con "'"
        """
        if block.startswith("b'") and block.endswith("'"): # Comprueba si el bloque comienza con "b'" y termina con "'"
            block = block[2:-1]  # Elimina el prefijo "b'" y el sufijo "'"
            decoded_data = binascii.a2b_base64(block)  # Decodifica los datos de base64 a bytes
            self.file.write(decoded_data)  # Almacena los datos en el atributo data
            self.hash_object.update(decoded_data)  # Actualiza el objeto hash con los datos decodificados
            logging.info(f"Recibiendo datos. Tamaño: {len(decoded_data)}")
        else:
            logging.error("El formato de los datos del bloque es incorrecto.")

    def save(self, current=None):
        """
        Este método guarda un archivo después de calcular su hash. Luego verifica si ya existe un archivo 
        con el mismo hash en el directorio especificado por STORAGE_PATH. Si el archivo ya existe, se lanza 
        un error y se elimina el archivo existente. Si no existe, los datos del archivo se envían a un canal 
        de actualización de archivos.
        
        :return: El método devuelve una instancia de la clase `URFS.FileInfo` con los atributos `filename` y `hash`.
        """
        self.hash = self.hash_object.hexdigest()  # Obtiene el hash en formato hexadecimal
        for file in os.listdir(STORAGE_PATH):  # Comprueba si un archivo con ese hash ya existe en el directorio
            f = open(f'{STORAGE_PATH}/{file}', 'rb') 
            file_data = f.read()
            file_hash = hashlib.md5(file_data).hexdigest()
            
            if file_hash == self.hash:
                    f.close()  
                    os.remove(os.path.join(STORAGE_PATH, self.filename))
                    self.file.close() 
                    raise URFS.FileAlreadyExistsError(self.hash)

        file_updates = URFS.FileUpdatesPrx.uncheckedCast(self.publisher)
        logging.info(f"Archivo guardado. Nombre: {self.filename} Hash: {self.hash}")

        if not file_updates:
            logging.error('No se ha podido generar file_updates')
        else:
            logging.info(f"Enviando file_data a canal de eventos file_updates --> {self.filename} {self.hash}")
        
        file_updates.new(URFS.FileData(URFS.FileInfo(self.filename, self.hash), URFS.FileManagerPrx.uncheckedCast(self.filemanager)))
        self.file.close()   
        return URFS.FileInfo(self.filename, self.hash)
            
    def destroy(self, current=None):
        """
        Elimina la instancia actual del objeto desde su adaptador y registra un mensaje para confirmar que el objeto ha sido destruido.
        
        :param current: Es un parámetro opcional que representa el contexto de solicitud actual.
        Se utiliza en aplicaciones Ice para acceder a información sobre la solicitud actual, como la 
        identidad del cliente o la conexión actual. En este contexto, se utiliza para acceder a las propiedades 
        o métodos de la instancia actual del objeto que se está destruyendo.
        """
        current.adapter.remove(current.id)  # Eliminar la instancia actual del objeto desde su adaptador      
        logging.info(f'El archivo "{self.filename}" ha sido destruido.')  # Registrar un mensaje para confirmar que la instancia del objeto ha sido destruida


class DownloaderI(URFS.Downloader):
    def __init__(self, file):
        """
        Inicializa un objeto DownloaderI con un archivo. Abre el archivo especificado en modo binario para lectura.
        
        :param file: Esta es una cadena que representa la ruta completa o el nombre del archivo que se va a abrir. 
        Es el archivo con el que este objeto DownloaderI trabajará.
        """
        self.file = file
        self.f = open(self.file, 'rb')  # Abre el archivo en modo binario para lectura

    def recv(self, size, current=None):
        """
        Lee una cantidad especificada de datos del archivo. Registra el tamaño de los datos leídos 
        y devuelve estos datos codificados en la codificación base64.
        
        :param size: Es el número de bytes que se leerán del archivo.
        :return: Devuelve una cadena que representa los datos binarios leídos, codificados en base64.
        """
        data = self.f.read(int(size))
        logging.info(f"Enviando datos con tamaño de {len(data)}")
        return str(binascii.b2a_base64(data, newline=False))

    def destroy(self, current=None):
        """
        Elimina el objeto actual de su adaptador y registra un mensaje indicando que el objeto ha sido destruido.
        
        :param current: Es un parámetro opcional que representa el contexto de solicitud actual.
        Se utiliza en aplicaciones Ice para acceder a información sobre la solicitud actual, como la 
        identidad del cliente o la conexión actual. En este contexto, se utiliza para acceder a las propiedades 
        o métodos de la instancia actual del objeto que se está destruyendo.
        """
        current.adapter.remove(current.id)
        logging.info(f'El archivo {self.file} ha sido destruido')


class FileManagerI(URFS.FileManager):
    def __init__(self, broker):
        """
        Este método constructor inicializa un publicador para un tema de actualizaciones de archivos. 
        Utiliza un intermediario (broker) dado para facilitar la comunicación con el servicio IceStorm.
        
        :param broker: Es el objeto proxy utilizado para establecer la conexión con el servicio IceStorm. 
        Este objeto es crucial para gestionar la comunicación entre el publicador y el suscriptor.
        """
        self.publisher=None
        self.topic_mgr = get_topic_manager(broker) # Obtenemos el gestor de temas a partir del intermediario (broker).

        if not self.topic_mgr: # Comprobamos si el gestor de temas es válido. Si no es válido, registramos un error y lanzamos una excepción.
            logging.error('Proxy inválido')
            raise Exception('Proxy inválido')
        
        topic_name = "FileUpdatesTopic" 
        try: # Intentamos crear un nuevo tema. Si el tema ya existe, simplemente lo recuperamos.
            topic = self.topic_mgr.create(topic_name)
        except IceStorm.TopicExists:
            topic = self.topic_mgr.retrieve(topic_name)

        self.publisher = topic.getPublisher() # Obtenemos el publicador del tema.

    def createUploader(self, filename, current=None):
        """
        Este método crea un objeto de subida (uploader) y devuelve su proxy correspondiente.
        
        :param filename: El parámetro de nombre de archivo es una cadena que representa el nombre del
        archivo que se cargará
        :param current: Es un parámetro opcional que representa el contexto de solicitud actual.
        Se utiliza en aplicaciones Ice para acceder a información sobre la solicitud actual, como la 
        identidad del cliente o la conexión actual. En este código, se utiliza para crear un objeto proxy para el usuario 
        que está subiendo el archivo en este momento.
        
        :return: Devuelve un objeto de tipo `URFS.UploaderPrx`. Este objeto es el proxy del objeto de subida (uploader) y se utiliza para interactuar con él.
        """
        servant = UploaderI(filename, self.publisher, current.adapter.createProxy(current.id))
        proxy = current.adapter.addWithUUID(servant)
        return URFS.UploaderPrx.checkedCast(proxy)
                
    def createDownloader(self, hash, current=None):
        """
        Busca un archivo en un directorio según su hash y devuelve un objeto proxy para descargar el archivo.
        
        :param hash: Es una cadena que representa el valor hash de un archivo. Se
        utiliza para buscar un archivo en el directorio `STORAGE_PATH`
        :param current: Es un parámetro opcional que representa el contexto de solicitud actual.
        Se utiliza en aplicaciones Ice para acceder a información sobre la solicitud actual, como la 
        identidad del cliente o la conexión actual. En este código, se utiliza para agregar 
        el servidor `DownloaderI` al adaptador
        :return: un objeto proxy de tipo `URFS.DownloaderPrx`.
        """
        for filename in os.listdir(STORAGE_PATH):   #Busca fichero en directorio STORAGE_PATH por el hash
            with open(os.path.join(STORAGE_PATH, filename), 'rb') as f:
                file_data = f.read()
                file_hash = hashlib.md5(file_data).hexdigest()
                if file_hash == hash:                    
                    self.file = os.path.join(STORAGE_PATH, filename)
                    break
        else:
            raise URFS.FileNotFoundError()
        
        servant = DownloaderI(os.path.join(STORAGE_PATH, filename))
        proxy = current.adapter.addWithUUID(servant)
        return URFS.DownloaderPrx.checkedCast(proxy)

    def removeFile(self, hash, current=None):
        """
        Elimina un archivo del directorio STORAGE_PATH según su hash.
        
        param hash: Es una cadena que representa el valor hash de un archivo.
        Si no encuentra el archivo, lanza una excepción.
        
        """
        for filename in os.listdir(STORAGE_PATH):
            with open(os.path.join(STORAGE_PATH, filename), 'rb') as f:
                file_data = f.read()
                file_hash = hashlib.md5(file_data).hexdigest()
                if file_hash == hash:
                    os.remove(os.path.join(STORAGE_PATH, filename))
                    logging.info(f"File removed: {filename} {hash}")
                    name = filename
                    break
        
        file_updates = URFS.FileUpdatesPrx.uncheckedCast(self.publisher)
        if not file_updates:
            logging.error('No se ha podido generar file_updates')
        else:
            logging.info(f"Enviando info de borrado de archivo  a canal de eventos file_updates")

        file_updates.removed(URFS.FileData(URFS.FileInfo(name, hash), URFS.FileManagerPrx.uncheckedCast(current.adapter.createProxy(current.id))))

class FileManager(Ice.Application):
    def run(self, argv):
        
        broker = self.communicator()
        properties = broker.getProperties()
    
        #CONFIGURACIÓN DE LOGGING
        logging.basicConfig(level=logging.DEBUG) ## Configurar el nivel de registro (por ejemplo, DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        ice_program_name = properties.getProperty("Ice.ProgramName")
        # Configurar un formato colorido para los registros
        log_format = '%(log_color)s[%(levelname)s][' + ice_program_name + ']%(reset)s - %(message)s'
        
        console_handler = logging.StreamHandler() # Crear un controlador para la consola
        console_handler.setLevel(logging.DEBUG) 
        console_handler.setFormatter(colorlog.ColoredFormatter(log_format))

        # Agregar los controladores al sistema de registro
        logging.getLogger().handlers = []  # Limpiar cualquier controlador existente
        logging.getLogger().addHandler(console_handler)

    
        servant = FileManagerI(broker)

        adapter = broker.createObjectAdapter("FileManagerAdapter")
        _id = properties.getProperty("Identity")
        proxy = adapter.add(servant, broker.stringToIdentity(_id))

        # adapter = broker.createObjectAdapter("FileManagerAdapter1")
        # proxy = adapter.add(servant, broker.stringToIdentity("FileManager1"))

        logging.info(f'ZeroC Ice version: {Ice.stringVersion()}')

        adapter.activate()
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        return 0


server = FileManager()
sys.exit(server.main(sys.argv))
