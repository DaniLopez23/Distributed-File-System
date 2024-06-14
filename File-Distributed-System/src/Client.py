#!/usr/bin/python3

import sys
import binascii

import Ice
import argparse
import logging
import colorlog

Ice.loadSlice('urfs.ice')
import URFS

DOWNLOAD_PATH = 'downloads'
BLOCK_SIZE = 1024


class Client(Ice.Application):
    def run(self, argv):
        """
        La función actúa como un controlador de comandos de línea de comandos para una aplicación. Se encarga de interpretar y ejecutar comandos 
        específicos relacionados con la gestión de archivos en un sistema remoto. Estos comandos incluyen operaciones como cargar, descargar, eliminar y enumerar archivos.
        El método inicia estableciendo una conexión con un sistema remoto a través de un objeto comunicador. Utiliza las propiedades del comunicador para 
        configurar y obtener un proxy representando la interfaz 'frontend' del sistema remoto. 

        Una vez establecido el proxy, la función evalúa los argumentos pasados por el usuario. Estos argumentos son accesibles a través del parámetro argv. 
        Dependiendo de los argumentos proporcionados, la función ejecuta la acción correspondiente. Por ejemplo, si se proporciona el argumento de carga (upload), 
        se llama al método upload_request con los detalles pertinentes. De manera similar, se manejan otros comandos como download, remove y list.
        Esto se realiza a través de la interfaz del proxy 'frontend' del sistema remoto. 
        En caso de no poder establecer un proxy válido, la función lanza un error, indicando que el proxy proporcionado es inválido.
        
        :param argv: Lista de argumentos de la línea de comandos pasados al método `run`. Normalmente incluye el nombre del script que se está ejecutando y cualquier argumento
        adicional proporcionado por el usuario al ejecutar el script
        """
        ic = self.communicator()
        properties = ic.getProperties()

        # proxy_string = properties.getProperty('ReplicatedFrontendAdapter:tcp -h localhost -p 4061')
        
        proxy = ic.stringToProxy("frontend")
        self.frontend = URFS.FrontendPrx.checkedCast(proxy)
        
        if not self.frontend:
            raise RuntimeError('Proxy inválido')

        if ARGS.upload:
            self.upload_request(ARGS.upload)
        elif ARGS.download:
            self.download_request(ARGS.download)
        elif ARGS.remove:
            self.remove_request(ARGS.remove)
        elif ARGS.list:
            lista_ficheros=self.frontend.getFileList()
            logging.info("Listado de ficheros obtenido: ")
            print(lista_ficheros)

    def upload_request(self, file_name):
        """
        Esta función gestiona la carga de un archivo al servidor frontend. Realiza dos verificaciones principales: 
        primero, asegura que el archivo exista en el sistema local y, segundo, verifica si el nombre del archivo 
        ya está en uso en el servidor. En caso de errores, como la inexistencia del archivo o el uso previo del 
        nombre del archivo, registra los errores correspondientes y termina la ejecución.

        :param file_name: El nombre del archivo que se desea cargar en el servidor.
        :return: No devuelve ningún valor. En caso de éxito, la función registra la información del archivo cargado.
         Si se encuentra un error (archivo no encontrado o nombre de archivo en uso), la función termina sin realizar la carga.
        """

        try:  #Comprueba si file_name existe
            open(file_name, 'rb')
        except FileNotFoundError:
            logging.error('Archivo no encontrado')
            return
        try:
            uploader = self.frontend.uploadFile(file_name)
        except URFS.FileNameInUseError:
            logging.error('El nombre del archivo ya está en uso')
            return
        
        with open(file_name, 'rb') as _file:
            while True:
                data = _file.read(BLOCK_SIZE)
                if not data:
                    break
                data = str(binascii.b2a_base64(data, newline=False)) # "b'...'" ¡CUIDADO!
                logging.info("Enviando datos. Tamaño: {}".format(len(data)))
                uploader.send(data)
        try:
            file_info = uploader.save()
        except URFS.FileAlreadyExistsError as e:
            logging.error(f'El archivo ya existe: {e.hash}')
            uploader.destroy()
            return
        uploader.destroy()
        logging.info(f'Subida del archivo finalizada. Archivo: {file_info.name}: {file_info.hash}')

    def download_request(self, file_hash):
        """
        Esta función se encarga de descargar un archivo desde un servidor frontend utilizando su hash único como identificador.
        El archivo descargado se guarda en un directorio local específico. La función maneja el error en caso de que el archivo
        con el hash proporcionado no se encuentre en el servidor.

        :param file_hash: El hash del archivo que se desea descargar. Este hash actúa como un identificador único para
        localizar y recuperar el archivo específico desde el servidor mediante el método `downloadFile`.

        :return: No retorna ningún valor. La función realiza la descarga y guarda el archivo en el sistema local. Si el archivo
        no se encuentra, registra un mensaje de error y finaliza sin realizar la descarga.
        """
        try:
            downloader = self.frontend.downloadFile(file_hash)
        except URFS.FileNotFoundError:
            logging.error('Archivo no encontrado')
            return
        
        with open(f'{DOWNLOAD_PATH}/{file_hash}', 'wb') as _file: #Abrir directorio y escribir en un archivo que no existe con el nombre del hash
            while True:
                data = downloader.recv(BLOCK_SIZE)
                
                data = data[2:-1]  # Elimina el prefijo "b''" y el sufijo "'"
                decoded_data = binascii.a2b_base64(data)  # Decodifica los datos de base64 a bytes
                
                _file.write(decoded_data)
                logging.info(f"Recibiendo datos. Tamaño: {len(decoded_data)}")
                if len(data) < BLOCK_SIZE:
                    break
        
        downloader.destroy()
        logging.info('Descarga finalizada')

    def remove_request(self, file_hash):
        """
        Esta función se encarga de eliminar un archivo en un sistema remoto. Utiliza un identificador único, conocido como 
        'file_hash', para localizar el archivo específico en el sistema remoto y proceder con su eliminación.

        Si el archivo con el hash proporcionado no existe en el sistema remoto, se captura una excepción de 'URFS.FileNotFoundError' 
        y se registra un error. Si el archivo se elimina con éxito, se registra un mensaje indicando que el archivo ha sido eliminado.

        :param file_hash: Es un identificador único para el archivo que se va a eliminar. Este hash se utiliza para buscar 
        y eliminar el archivo específico del sistema remoto.

        :return: La función no devuelve ningún valor. Realiza la eliminación del archivo en el sistema remoto y registra el 
        resultado de la operación. En caso de que el archivo con el hash proporcionado no se encuentre, se registra un mensaje
        de error indicando que el archivo no fue encontrado.
        """
        try:
            self.frontend.removeFile(file_hash)
        except URFS.FileNotFoundError:
            logging.error('Archivo no encontrado')
            return

        logging.info('Archivo eliminado')
    

if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)     #Configurar el nivel de registro (por ejemplo, DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_format = '%(log_color)s[%(levelname)s]%(reset)s - %(message)s'     # Configurar un formato colorido para los registros

    # Crear un controlador para la consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Puedes ajustar el nivel según tus necesidades
    console_handler.setFormatter(colorlog.ColoredFormatter(log_format))

    # Agregar los controladores al sistema de registro
    logging.getLogger().handlers = []  # Limpiar cualquier controlador existente
    logging.getLogger().addHandler(console_handler)

    my_parser = argparse.ArgumentParser()
    my_group = my_parser.add_mutually_exclusive_group(required=False)

    my_group.add_argument('-u', '--upload',
        help='Carga un archivo en el sistema, proporcionando su ruta',
        action='store',
        type=str,)
    my_group.add_argument('-d', '--download',
        help=' Descarga un archivo del sistema, proporcionando su hash',
        action='store',
        type=str,)
    my_group.add_argument('-r', '--remove',
        help='Elimina un archivo del sistema, proporcionando su hash',
        action='store',
        type=str,)
    my_group.add_argument('-l', '--list',
        help='Lista todos los archivos en el sistema',
        action='store_true',
        default=False)
    my_group.add_argument('-t', '--test',
        help='Prueba la conexión',
        action='store_true',
        default=False)
    
    ARGS, unknown = my_parser.parse_known_args()
    sys.exit(Client().main(sys.argv))
