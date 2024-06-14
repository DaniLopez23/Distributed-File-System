[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/pgx_oHy2)
# URFS

## Introducción 🌟

Bienvenidos al Proyecto URFS (Unified Remote File System). Este sistema proporciona una solución eficiente para la gestión remota de archivos utilizando ZeroC Ice, complementado con una interfaz gráfica de usuario desarrollada en Tkinter. El proyecto URFS permite realizar operaciones como subir, descargar, eliminar y listar archivos en un sistema remoto de manera sencilla y eficaz. ¡Disfruta utilizando y explorando el proyecto URFS! 🌐💻


## Requisitos Previos 📋

Antes de comenzar, asegúrate de tener instalado lo siguiente:
- Python 3.x
- ZeroC Ice
- Tkinter (generalmente incluido en la instalación estándar de Python)
- `colorlog`: una biblioteca de Python para registros coloridos. Para instalar `colorlog`, puedes usar pip:

    ```bash
    pip install colorlog
    ```

## Configuración y Ejecución 🚀

Para ejecutar el proyecto URFS, sigue estos pasos:

1. **Iniciar los Servicios de Ice configurados con IceGrid**:  
   Utiliza los siguientes comandos para iniciar los servicios necesarios y arrancar todos los nodos en una terminal:
   ```bash
   make app-workspace
   make run-aplication-icegrid
   ```
   Utiliza los siguientes comandos para iniciar los nodos en cada terminal

   ```bash
   make app-workspace
   make run-node1
   make run-node2
   make run-node3

   ```
   Además para asegurar el correcto funcionamiento de todos los componentes en el caso de que se haga una limpieza de la aplicación habria que ejecutar lo siguiente:

   Arrancar la interfaz de usuario de icegrid con el comando:
   ```bash
   icegridgui
   ```
   Cargar el registry en el icegridgui y añadir al registry el archivo URFSApp.xml 
   Y por ultimo realizar la distribucion de la aplicación: Tools > Aplication > Path Distribution (seleccionamos URFSApp)


2. **Ejecutar la Interfaz Gráfica de Usuario (GUI)**:  
   Para iniciar la GUI, ejecuta:
   ```bash
   make run-gui
   ```
   Esto abrirá la interfaz de usuario de Tkinter, donde podrás interactuar con el sistema de archivos remoto.

3. **Operaciones de Cliente**:  
   Puedes realizar operaciones como subir, descargar, eliminar y listar archivos utilizando la interfaz gráfica de usuario o por línea de comandos.

En el README.md, puedes explicar el comando `test-client-icegrid` de la siguiente manera:



## Prueba del Cliente URFS con IceGrid (`test-client-icegrid`)

El comando `test-client-icegrid` en el `Makefile` está diseñado para probar automáticamente las funcionalidades clave del cliente URFS en el entorno IceGrid. Estas pruebas incluyen subir archivos, listarlos, descargarlos y eliminarlos. A continuación se detalla cada paso del comando:

1. **Crear Directorio de Descargas**:  
   Antes de iniciar las pruebas, se asegura de que exista un directorio `downloads` para almacenar los archivos descargados. Si el directorio no existe, se crea.
   ```bash
   mkdir -p downloads
   ```

2. **Subir Archivo**:  
   Se sube un archivo al sistema remoto. El archivo a subir está especificado por la variable `$(FILE)` en el `Makefile`. Esta operación se realiza dos veces para el mismo archivo.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --upload $(FILE)
   ```

3. **Subir Archivo con Diferente Nombre**:  
   Se sube el mismo archivo pero con un nombre diferente, especificado por `$(SAME_FILE_DIFFERENT_NAME)`, para probar la gestión de nombres de archivos en el servidor.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --upload $(SAME_FILE_DIFFERENT_NAME)
   ```

4. **Listar Archivos**:  
   Se solicita al sistema listar todos los archivos disponibles. Esto verifica si los archivos subidos previamente se muestran en la lista.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --list
   ```

5. **Descargar Archivo**:  
   Se descarga un archivo especificado por su hash (`$(FILE_HASH)`). Este paso prueba la capacidad de recuperar archivos del sistema.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --download $(FILE_HASH)
   ```

6. **Eliminar Archivo**:  
   Se elimina el archivo que se descargó en el paso anterior, utilizando el mismo hash.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --remove $(FILE_HASH)
   ```

7. **Volver a Listar Archivos**:  
   Finalmente, se lista de nuevo los archivos para confirmar que el archivo eliminado ya no aparece en la lista.
   ```bash
   ./src/Client.py --Ice.Config=URFS_App_config/locator.config --list
   ```

Estos pasos permiten verificar el correcto funcionamiento de las funcionalidades del cliente URFS. Es una forma rápida y eficiente de asegurar que el sistema se comporta como se espera.

## Limpieza y Mantenimiento 🧹

- Para limpiar archivos temporales y restablecer el entorno, puedes usar:
  ```bash
  make clean
  ```
- Para una limpieza más profunda, incluyendo la eliminación de todos los datos y configuraciones, usa:
  ```bash
  make vclean
  ```



----
----
Currently, you have only some initial files at your disposal for implementing the URFS project.

- A `Makefile` that instructs you on how to execute each element of the system (these commands will be utilized during the evaluation, so you must develop the system in accordance with them).
- A Slice file named `urfs.ice`, where interfaces have been specified.
- A basic implementation of the `Client.py` script (providing only the upload process).
- An `example.png` image for testing purposes.

Develop the app according to the specifications, and remember that **you cannot modify `urfs.ice` and the `Makefile`**.
