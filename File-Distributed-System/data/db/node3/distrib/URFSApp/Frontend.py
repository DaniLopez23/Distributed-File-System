#!/usr/bin/python3

import sys
import Ice
import IceStorm
from util import get_topic_manager
import os
import logging
import colorlog

Ice.loadSlice('urfs.ice')
import URFS
import IceGrid

class FrontendUpdatesI(URFS.FrontendUpdates):
    
    def __init__(self, topic_mgr, oldFrontend, oldFrontend_proxy, current=None):
        """
        Inicializa una instancia de clase con un administrador de topics, un Frontend anterior, un proxy del Frontend anterior 
        y un parámetro current, y crea un editor para un topic de actualizaciones de archivos.
        
        :param topic_mgr: Objeto que gestiona temas de IceStorm. Se utiliza para crear o recuperar un tema para publicar mensajes.
        :param oldFrontend: Objeto que representa el Frontend antiguo.
        :param oldFrontend_proxy: Objeto proxy que representa la interfaz anterior. Se utiliza para comunicarse con el Frontend anterior 
        y realizar diversas operaciones en él.
        :param current: Parámetro opcional que representa el objeto actual. Se usa para pasar la referencia del objeto actual.
        :return: El código devuelve el valor 2 si el parámetro `topic_mgr` no es válido.
        """
        self.oldFrontend = oldFrontend
        self.oldFrontend_proxy = oldFrontend_proxy
        self.newF = None
        topic_name = "FileUpdatesTopic"

    # DECLARACION DE PUBLICADOR (FILEUPDATES)
        if not topic_mgr:
            print('Invalid proxy')
            return 2
        
        try:
            topic = topic_mgr.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_mgr.retrieve(topic_name)

        self.publisher = topic.getPublisher()

    def newFrontend(self, newFrontend_proxy, current=None):
        """
        Actualiza el registro de archivos de un nuevo Frontend utilizando el registro de archivos del Frontend anterior 
        a través del canal de eventos de actualizaciones de archivos.
        
        :param newFrontend_proxy: Objeto proxy que representa un nuevo Frontend. Se utiliza para comunicarse 
        con el nuevo Frontend y realizar operaciones en ella.
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        self.newF = URFS.FrontendPrx.uncheckedCast(newFrontend_proxy)
        logging.info(f"new frontend --> {newFrontend_proxy} (old frontend --> {self.oldFrontend_proxy})", )


        #ACTUALIZAR REGISTRO DE FICHEROS DEL FRONTEND MEDIANTE EL REGISTRO DE FICHEROS DE LOS FRONTEND ANTIGUOS A TRAVES DEL CANAL DE EVENTOS FILEUPDATES
        file_updates = URFS.FileUpdatesPrx.uncheckedCast(self.publisher) #

        for file_data in self.oldFrontend.files:
            logging.info(f"actualizando registro de ficheros del nuevo frontend --> {file_data}")
            file_updates.new(file_data)
        

class FileUpdatesI(URFS.FileUpdates):
    def __init__(self, frontend, current=None):
        """
        Constructor que inicializa un objeto con un Frontend y un parámetro current.
        
        :param frontend: Referencia a un objeto que representa el Frontend de la aplicación.
        :param current:  Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        self.frontend = frontend
        
    def new(self, file_data, hash, current=None):
        """
        Registra información sobre un archivo nuevo y lo agrega al registro del Frontend.
        
        :param file_data: Objeto que contiene información sobre un archivo. Tiene como atributo "fileInfo", que proporciona detalles 
        sobre el archivo, como su nombre o su hash.
        :param hash: Valor hash que representa los datos del archivo. Se utiliza como identificador único del archivo.
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        logging.info(f"Nuevo archivo --> {file_data.fileInfo}")
        self.frontend.addTo_registro(file_data)
    
    def removed(self, file_data, current=None):
        """
        Registra la eliminación de un archivo con un hash específico y lo elimina del registro del Frontend.
        
        :param file_data: Objeto que contiene información sobre un archivo. Tiene como atributo "fileInfo", 
        que proporciona detalles sobre el archivo, como su nombre o su hash.
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        logging.info(f"Archivo eliminado con hash {file_data.fileInfo.hash}")
        self.frontend.removeFrom_registro(file_data)

class FrontendI(URFS.Frontend):
    def __init__(self, broker):
        """
        Constructor que inicializa un objeto con un broker y una lista vacía de archivos. Esta lista sera el registro del Frontend
        
        :param broker: Variable que representa un objeto de broker. Se utiliza para establecer una conexión o 
        comunicación con un sistema de intermediario de mensajería.
        """
        self.broker = broker
        self.files = []


    def getFileList(self, current=None):
        """
        Devuelve una lista de información de archivo para cada archivo en la lista de archivos.
        
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        logging.info("Petición de listar ficheros")
        file_info_list = []
        for file_info in self.files:
            file_info_list.append(file_info.fileInfo)
        return file_info_list
    
    def uploadFile(self, name, current=None):
        """
        Crea un cargador para un archivo con el nombre dado y registra la solicitud.
        
        :param name: El nombre del archivo que se va a cargar
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        :return: El objeto `uploader` generado a partir de `filemanager_for_upload`con el nombre del archivo que se 
        quiere subir.
        """
        filemanager_for_upload = self.get_filemanager_for_upload(self.broker)
        for file_data in self.files:
            if file_data.fileInfo.name == os.path.basename(name):
                raise URFS.FileNameInUseError()
        logging.info(f"Petición de subir fichero con nombre: {name}")
        uploader = filemanager_for_upload.createUploader(name)
        return uploader
        

    def downloadFile(self, hash, current=None):
        """
        Descarga un archivo con un hash determinado desde un administrador de archivos, es decir, desde un filemanager.
        
        :param hash: Identificador único para el archivo que debe descargarse. Se utiliza para ubicar el 
        archivo en el administrador de archivos y crear un objeto de descarga para descargar el archivo
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        :return: una instancia del objeto `downloader`.
        """
        
        logging.info(f"Petición de descargar fichero con hash: {hash}")

    #OBTENER FILEMANAGER QUE TENGA EL FICHERO CON EL HASH
        filemanager_for_download = self.get_filemanager_for_download_remove(hash, self.broker)
        if not filemanager_for_download:
            raise URFS.FileNotFoundError()

        downloader = filemanager_for_download.createDownloader(hash)
        return downloader

    def removeFile(self, hash, current=None):
        """
        Comprueba si existe un archivo con un hash determinado en una lista de archivos y, de ser así, 
        lo elimina utilizando un administrador de archivos.
        
        :param hash: Identificador único para un archivo. Se utiliza para localizar y eliminar el archivo 
        de una lista de archivos
        :param current: Parámetro opcional que representa el objeto actual. Si se pasa como parámetro
        Zeroc Ice puede tener comportamientos inesperados.
        """
        if not any(file_data.fileInfo.hash == hash for file_data in self.files):
            raise URFS.FileNotFoundError()
    
        filemanager_for_download_remove = self.get_filemanager_for_download_remove(hash, self.broker)
        filemanager_for_download_remove.removeFile(hash)    

    def replyNewFrontend(self, oldFrontend, current=None):
        """
        Imprime la información del Frontend nuevo y antiguo.
        
        :param oldFrontend: rpresenta el antiguo objeto del Frontend. Se utiliza para mostrar información 
        sobre la interfaz anterior
        :param current: Objeto que representa el nuevo Frontend. Puede tener un atributo "adapter" y un
        atributo "id". Se espera que el atributo `adapter` tenga un método `createProxy`, que se utiliza 
        para crear un proxy para la nueva interfaz.
        """
        print(f"Valor de oldFrontend: {oldFrontend}", flush=True)   
        print(f"Valor del nuevo Frontend: {current.adapter.createProxy(current.id)}", flush=True)

    def addTo_registro(self, new_file_data):
        """
        Agrega un nuevo archivo de datos al registro si aún no existe.
        
        :param new_file_data: Objeto que representa los datos de un nuevo archivo que debe agregarse al registro
        """
        file_data_already_exists = False
        if len(self.files) == 0:
            self.files.append(new_file_data)
        else:  
     #COMPRUEBA SI EL FICHERO YA ESTA EN EL REGISTRO (PARA EVITAR DUPLICADOS POR EL FRONTEND UPDATES) 
            for file_data in list(self.files):  # Crea una copia de self.files
                if file_data.fileInfo.hash == new_file_data.fileInfo.hash:                   
                    file_data_already_exists = True  
            
            if not file_data_already_exists:
                self.files.append(new_file_data)

        logging.info(f"Actualizada lista de archivos --> {self.files}")
    
    def removeFrom_registro(self, file_data_to_remove):
        """
        Elimina un archivo específico de una lista de archivos según su valor hash.
        
        :param file_data_to_remove: Objeto que representa los datos del archivo que deben eliminarse de la lista `self.files`. 
        Se supone que este objeto tiene un atributo `fileInfo`, que a su vez tiene un atributo `hash`. Se utiliza el atributo `hash`
        """
        for file_data in list(self.files):
            if file_data.fileInfo.hash == file_data_to_remove.fileInfo.hash:
                self.files.remove(file_data)
                break

        logging.info(f"Actualizada lista de archivos --> {self.files}")

    def get_filemanager_for_upload(self, broker):     #OBTIENE FILEMANAGER QUE MENOS CARGADO ESTE (MENOS FICHEROS EN EL REGISTRO)
        """
        Se encarga de seleccionar el administrador de archivos (file manager) que está menos cargado, es decir, 
        que tiene la menor cantidad de archivos. Este método es útil para equilibrar la 
        carga entre diferentes administradores de archivos.

        Primero, la función obtiene todos los file managers disponibles. Luego, para cada uno de ellos, inicializa 
        un contador en un diccionario.

        Después, la función recorre la lista de archivos y aumenta el contador correspondiente al administrador 
        de archivos de cada archivo en el diccionario.

        Si ya se han cargado archivos antes (es decir, el diccionario no está vacío), la función selecciona el 
        administrador de archivos con el contador más bajo y lo devuelve.

        Si es la primera vez que se suben archivos (es decir, el diccionario está vacío), la función selecciona 
        un administrador de archivos predeterminado ("FileManager1") y lo devuelve.

        :param broker: Instancia de broker IceGrid. Se utiliza para comunicarse con el registro IceGrid y obtener
        los servidores proxy para los administradores de archivos.
        :return: Devuelve una instancia de la clase `URFS.FileManagerPrx` que representa al administrador de 
        archivos seleccionado para la carga.
        """

        
        query = IceGrid.QueryPrx.checkedCast(broker.stringToProxy("IceGrid/Query")) 
        file_managers = query.findAllObjectsByType("::URFS::FileManager") #OBTIENE TODOS LOS FILEMANAGERS DISPONIBLES
        contador_filemanagers = {}

        for fm in file_managers:
            file_manager_proxy_str = fm.ice_toString()
            file_manager_proxy = URFS.FileManagerPrx.checkedCast(broker.stringToProxy(file_manager_proxy_str))
            contador_filemanagers[file_manager_proxy] = 0  # Add the FileManager to the dictionary with a count of 0
       
        for file_data in list(self.files):
            filemanager = file_data.fileManager
            if filemanager in contador_filemanagers:
                contador_filemanagers[filemanager] += 1
            else:
                contador_filemanagers[filemanager] = 1
        
        if contador_filemanagers: #Controlamos que no sea la primera vez que se sube algún archivo
            selected_filemanager = min(contador_filemanagers, key=contador_filemanagers.get)
            # filemanager_proxy = broker.stringToProxy(selected_filemanager)
            filemanager_for_upload = URFS.FileManagerPrx.checkedCast(selected_filemanager)

            if not filemanager_for_upload:
                raise RuntimeError('Invalid proxy')
            
            return filemanager_for_upload
        
        else:
            filemanager_proxy = broker.stringToProxy("FileManager1")
            filemanager_for_upload = URFS.FileManagerPrx.checkedCast(filemanager_proxy)

            if not filemanager_for_upload:
                raise RuntimeError('Invalid proxy')
            
            return filemanager_for_upload

    def get_filemanager_for_download_remove(self, hash, broker):
        """
        Retorna el gestor de archivos para descargar y eliminar un archivo basado en su hash.
        
        Inicialmente, la función recorre la lista de archivos buscando un archivo que coincida con el hash proporcionado.
        Si existe tal archivo, selecciona el gestor de archivos asociado a dicho archivo.

        A continuación, se crea un objeto proxy para el gestor de archivos seleccionado utilizando el broker. Si se produce 
        algún problema durante la creación del proxy, se lanza una excepción de tipo 'RuntimeError' con el mensaje 'Invalid proxy'.
        
        :param hash: Identificador único de un archivo. Se emplea para buscar un archivo específico en la lista de archivos.
        :param broker: Sirve como intermediario en la comunicación entre el cliente y el servidor. Su responsabilidad es crear 
        y gestionar conexiones con objetos remotos. En este código, se utiliza para crear un objeto proxy para el gestor de archivos seleccionado.
        :return: Devuelve una instancia de `URFS.FileManagerPrx` si encuentra un archivo que coincide con el hash proporcionado en la lista
        `self.files`. Si no se encuentra ningún archivo coincidente, devuelve "None".
        """
        for file_data in list(self.files):
            if file_data.fileInfo.hash == hash:
                selected_filemanager = file_data.fileManager

                filemanager_proxy = broker.stringToProxy(str(selected_filemanager))
                filemanager_for_download = URFS.FileManagerPrx.checkedCast(filemanager_proxy)

                if not filemanager_for_download:
                    raise RuntimeError('Invalid proxy')
                return filemanager_for_download

        return None

class Frontend(Ice.Application):
    def run(self, argv):
        """
        La función anterior configura el registro, crea servidores proxy y adaptadores, se suscribe a temas,
        activa adaptadores, crea un editor y espera el cierre.

        En primer lugar, configura el registro para el nivel de depuración (DEBUG), lo que significa que todos los mensajes 
        de registro (DEBUG, INFO, WARNING, ERROR, CRITICAL) serán capturados. Tras esto, crea un formato colorido para los registros y 
        un controlador para la consola. Este controlador se ajusta también a nivel de depuración (DEBUG). Luego, se limpian los controladores 
        existentes y se agrega este nuevo controlador al sistema de registro.

        A continuación, se crea un objeto "broker" (intermediario) y se obtienen sus propiedades. También se registra la versión de ZeroC Ice.
        Tras esto, se declara:
        - "FileManager": Para ello se obtiene la propiedad 'FileManager1' y 'FileManagerAdapter1.Proxy' de las propiedades. Luego, crea un proxy 
        a partir de esa propiedad y realiza un "cast" para obtener el "FileManager". Si el FileManager no es válido, se lanzará un error.
        - "Servant" para "Frontend": Para ello se crea un adaptador y agrega el sirviente a este. También configura la identidad y crea un proxy 
        para el sirviente e imprime la información de la conexión.
	    - "Topic Manager" y el "Subscriptor" para "FrontendUpdates" y "FileUpdates": Para ello se crea adaptadores para estos y los agrega. 
        También se crean y suscriben temas para estos. El "Topic Manager" y los temas son parte de IceStorm, que es un servicio de publicación/suscripción.
        - "Publicador" para "FrontendUpdates": Se crea o recupera el tema correspondiente y obtiene el publicador de este. Luego, realiza un
        "cast" para obtener "FrontendUpdates" y notifica el nuevo "Frontend".

        Por último, espera a que el "broker" se cierre y cancela la suscripción a los temas y devuelve el valor 0.

        :param argv: El parámetro `argv` es una lista de argumentos de la línea de comandos pasados al
        método `run`. Se utiliza para proporcionar información adicional u opciones de configuración al
        método
        :return: El código devuelve el valor 0.
        """

        broker = self.communicator()
        properties = broker.getProperties()
        
        logging.basicConfig(level=logging.DEBUG)   ## Configura el nivel de registro (por ejemplo, DEBUG, INFO, WARNING, ERROR, CRITICAL)

        ice_program_name = properties.getProperty("Ice.ProgramName")

        # Configurar un formato colorido para los registros
        log_format = '%(log_color)s[%(levelname)s][' + ice_program_name + ']%(reset)s - %(message)s'

        # Crear un controlador para la consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # Puedes ajustar el nivel según tus necesidades
        console_handler.setFormatter(colorlog.ColoredFormatter(log_format))

        # Agregar los controladores al sistema de registro
        logging.getLogger().handlers = []  # Limpiar cualquier controlador existente
        logging.getLogger().addHandler(console_handler)
            

        logging.info(f'ZeroC Ice version: {Ice.stringVersion()}')

        # DECLARACION DEL SERVANT (FRONTEND)
        frontend_servant = FrontendI(broker)
        adapter = broker.createObjectAdapter("FrontendAdapter")
        _id = properties.getProperty('Identity')
        logging.debug(f"Identity: {_id}")
        frontend_proxy = adapter.add(frontend_servant, broker.stringToIdentity(_id))

        # adapter = broker.createObjectAdapter("FrontendAdapter1")
        # frontend_proxy = adapter.add(frontend_servant, broker.stringToIdentity("Frontend1"))

        # Imprimir a informacion de la conexion
        logging.info(f"Frontend arrancado con proxy --> {frontend_proxy}")
        
        #DECLARACION DEL TOPIC MANAGER
        topic_mgr = get_topic_manager(broker)

        # DECLARACION DE SUBSCRIPTOR (FRONTENDUPDATES)
        frontend_updates_servant = FrontendUpdatesI(topic_mgr, frontend_servant, frontend_proxy)
        frontend_updates_adapter = broker.createObjectAdapter("FrontendUpdatesAdapter")
        frontend_updates_topic_name = "FrontendUpdatesTopic"

        subscriber_frontend_updates = frontend_updates_adapter.addWithUUID(frontend_updates_servant)
        identity_frontend_updates = subscriber_frontend_updates.ice_getIdentity()
        direct_proxy_frontend_updates = frontend_updates_adapter.createDirectProxy(identity_frontend_updates)
    
        try:
            topic_frontend_updates = topic_mgr.create(frontend_updates_topic_name)
        except IceStorm.TopicExists:
            topic_frontend_updates = topic_mgr.retrieve(frontend_updates_topic_name)
        
        topic_frontend_updates.subscribeAndGetPublisher({}, direct_proxy_frontend_updates)
        logging.info("Waiting events in frontend updates... '{}'".format(direct_proxy_frontend_updates))
        frontend_updates_adapter.activate()

        # DECLARACION DE SUBSCRIPTOR (FILEUPDATES)
        if not topic_mgr:
            print("Invalid proxy")
            return 2
        
        file_updates_servant = FileUpdatesI(frontend_servant)
        file_updates_adapter = broker.createObjectAdapter("FileUpdatesAdapter")
        file_updates_topic_name = "FileUpdatesTopic"

        subscriber_file_updates = file_updates_adapter.addWithUUID(file_updates_servant)        
        identity_file_updates = subscriber_file_updates.ice_getIdentity()
        direct_proxy_file_updates = file_updates_adapter.createDirectProxy(identity_file_updates)
        file_updates_adapter.activate()

        try:
            topic_file_updates = topic_mgr.create(file_updates_topic_name)
        except IceStorm.TopicExists:
            topic_file_updates = topic_mgr.retrieve(file_updates_topic_name)

        topic_file_updates.subscribeAndGetPublisher({}, direct_proxy_file_updates)
        logging.info("Waiting events in file updates... '{}'".format(direct_proxy_file_updates))
        adapter.activate()

        # DECLARACION DE PUBLICADOR (FRONTEND_UPDATES)
        if not topic_mgr:
            print('Invalid proxy')
            return 2
        
        topic_name = "FrontendUpdatesTopic"
        try:
            topic = topic_mgr.create(topic_name)
        except IceStorm.TopicExists:
            topic = topic_mgr.retrieve(topic_name)

        self.publisher = topic.getPublisher()

        frontend_updates = URFS.FrontendUpdatesPrx.uncheckedCast(self.publisher)
        frontend_updates.newFrontend(URFS.FrontendPrx.uncheckedCast(frontend_proxy))
        
        self.shutdownOnInterrupt()
        broker.waitForShutdown()

        topic_file_updates.unsubscribe(subscriber_file_updates)
        topic_frontend_updates.unsubscribe(subscriber_frontend_updates)

        return 0 

server = Frontend()
sys.exit(server.main(sys.argv))
