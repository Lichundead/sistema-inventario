import tkinter as tk
from tkinter import ttk, messagebox
import logging
from src.utils.utils import populate_treeview
from src.view.producto import menu_productos

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.tree = None  # Inicializar tree como None
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        self.window.title("Sistema Inventario Tahona")
        self.window.geometry("1280x720")
        
        # Configurar el grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(1, weight=1)

        # Crear frames principales
        self.left_frame = ttk.Frame(self.window, padding="20")
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        
        self.right_frame = ttk.Frame(self.window, padding="20")
        self.right_frame.grid(row=0, column=1, sticky="nsew")

    def create_widgets(self):
        style = ttk.Style()
        style.configure(
            "Big.TButton",
            font=("Arial", 16, "bold"),  
            padding=(20, 15),           
            width=20                    
        )

        # Título
        ttk.Label(
            self.left_frame,
            text="Menú Principal",
            font=("Arial", 28, "bold")  # Título más grande también
        ).pack(pady=40)  # Más espacio vertical

        # Botones con el nuevo estilo
        ttk.Button(
            self.left_frame,
            text="Gestión de Productos",
            style="Big.TButton",        # Aplicar el estilo personalizado
            command=self.open_productos
        ).pack(pady=20)                 # Más espacio entre botones

        ttk.Button(
            self.left_frame,
            text="Salir",
            style="Big.TButton",        # Aplicar el estilo personalizado
            command=self.window.destroy
        ).pack(pady=20)

        # Crear Treeview
        self.create_treeview()

    def create_treeview(self):
        # Frame para la tabla
        table_frame = ttk.Frame(self.right_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Crear el Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=("id_productos", "nombre", "cantidad"),
            show="headings"
        )

        # Configurar las columnas
        self.tree.heading("id_productos", text="ID Producto")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("cantidad", text="Cantidad")

        self.tree.column("id_productos", width=100, anchor="center")
        self.tree.column("nombre", width=300, anchor="w")
        self.tree.column("cantidad", width=100, anchor="center")

        # Crear scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        # Configurar el scroll del Treeview
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Posicionar los widgets usando grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configurar el grid del frame
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Cargar datos iniciales
        self.refresh_treeview()

    def refresh_treeview(self):
        try:
            logger.info("Actualizando Treeview")
            populate_treeview(self.tree)
        except Exception as e:
            logger.error(f"Error al actualizar Treeview: {e}")
            messagebox.showerror(
                "Error",
                "No se pudieron cargar los productos"
            )

    def open_productos(self):
        try:
            menu_productos(self.tree)
        except Exception as e:
            logger.error(f"Error al abrir menú de productos: {e}")
            messagebox.showerror(
                "Error",
                "No se pudo abrir el menú de productos"
            )

    def run(self):
        try:
            logger.info("Iniciando aplicación")
            self.window.mainloop()
        except Exception as e:
            logger.error(f"Error en la aplicación: {e}")
            raise

def main():
    try:
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.critical(f"Error crítico en la aplicación: {e}")
        messagebox.showerror("Error", "Error crítico en la aplicación")

