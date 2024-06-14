#!/usr/bin/python3

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import sys
import binascii
import Ice
Ice.loadSlice('urfs.ice')
import URFS
import tkinter.scrolledtext as scrolledtext


DOWNLOAD_PATH = 'downloads'
BLOCK_SIZE = 1024

class IceClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Cliente Ice GUI")
        self.geometry("600x250")  # 600 píxeles de ancho y 250 píxeles de alto
        self.configure(bg='#f0f0f0')

        # Configura tu cliente Ice aquí
        self.ice_communicator = Ice.initialize(sys.argv)
        proxy = self.ice_communicator.stringToProxy("frontend")
        self.frontend = URFS.FrontendPrx.checkedCast(proxy)
        if not self.frontend:
            raise RuntimeError('Proxy inválido')

        # Crear la interfaz de usuario
        self.create_widgets()

    def create_widgets(self):


        self.title("Interfaz de Aplicación Ice")

        # Configuración de estilos
        button_font = ('Arial', 12, 'bold')
        button_bg = "#4a7a8c"
        button_fg = "white"
        button_padx = 20
        button_pady = 10

        # Marco para organizar los botones
        button_frame = tk.Frame(self, bg='white', padx=10, pady=10)
        button_frame.pack(padx=10, pady=10)

        upload_button = tk.Button(button_frame, text="Subir Archivo", command=self.upload_file, font=button_font, bg=button_bg, fg=button_fg, padx=button_padx, pady=button_pady)
        upload_button.pack(fill='x', expand=True, pady=5)

        download_button = tk.Button(button_frame, text="Descargar Archivo", command=self.download_file, font=button_font, bg=button_bg, fg=button_fg, padx=button_padx, pady=button_pady)
        download_button.pack(fill='x', expand=True, pady=5)

        delete_button = tk.Button(button_frame, text="Eliminar Archivo", command=self.delete_file, font=button_font, bg=button_bg, fg=button_fg, padx=button_padx, pady=button_pady)
        delete_button.pack(fill='x', expand=True, pady=5)

        list_button = tk.Button(button_frame, text="Listar Archivos", command=self.list_files, font=button_font, bg=button_bg, fg=button_fg, padx=button_padx, pady=button_pady)
        list_button.pack(fill='x', expand=True, pady=5)

        self.mainloop()

    def upload_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                with open(file_path, 'rb') as _file:
                    uploader = self.frontend.uploadFile(file_path)
                    while True:
                        data = _file.read(BLOCK_SIZE)
                        if not data:
                            break
                        data = str(binascii.b2a_base64(data, newline=False))
                        uploader.send(data)
                    file_info = uploader.save()
                    messagebox.showinfo("Éxito", f"Archivo subido: {file_info.name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def download_file(self):
        file_hash = simpledialog.askstring("Descargar Archivo", "Introduce el hash del archivo:")
        if file_hash:
            try:
                downloader = self.frontend.downloadFile(file_hash)
                with open(f'{DOWNLOAD_PATH}/{file_hash}', 'wb') as _file:
                    while True:
                        data = downloader.recv(BLOCK_SIZE)
                        data = data[2:-1]
                        decoded_data = binascii.a2b_base64(data)
                        _file.write(decoded_data)
                        if len(data) < BLOCK_SIZE:
                            break
                downloader.destroy()
                messagebox.showinfo("Éxito", "Archivo descargado.")
            except Exception as e:
                messagebox.showerror("Error", "No existe un archivo con el hash escrito")

    def delete_file(self):
        file_hash = simpledialog.askstring("Eliminar Archivo", "Introduce el hash del archivo:")
        if file_hash:
            try:
                self.frontend.removeFile(file_hash)
                messagebox.showinfo("Éxito", "Archivo eliminado.")
            except Exception as e:
                messagebox.showerror("Error", "No existe un archivo con el hash escrito")

    def list_files(self):
        try:
            lista_ficheros = self.frontend.getFileList()
            # Crear una ventana de diálogo nueva
            dialog = tk.Toplevel(self)
            dialog.title("Lista de Archivos")
            dialog.geometry("400x300")  # Puedes ajustar el tamaño según tus necesidades

            # Crear un widget de texto desplazable
            text_area = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=('Arial', 10))
            text_area.pack(expand=True, fill='both')

            # Insertar la lista de archivos en el widget de texto
            for file in lista_ficheros:
                text_area.insert(tk.END, f"Nombre: {file.name}\nHash: {file.hash}\n\n")
            text_area.configure(state='disabled')  # Deshabilitar la edición del texto

        except Exception as e:
            messagebox.showerror("Error", "No se han podido listar los archivos correctamente")


if __name__ == "__main__":
    app = IceClientGUI()
    app.mainloop()

