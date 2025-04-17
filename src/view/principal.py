# src/view/principal.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, Dict, List, Callable # Añadir Callable

# Importar controladores
# Asegúrate que src.controller.* están accesibles
from src.controller.producto import ProductoController
from src.controller.categoria import CategoriaController # Importar nuevo controlador

# Importar la función de utilidad modificada
# Asegúrate que src.utils.utils está accesible
from src.utils.utils import populate_treeview, clear_treeview # Usar clear_treeview

# Importar las funciones para abrir las ventanas de gestión
# Asegúrate que src.view.* están accesibles
from src.view.producto import menu_productos
from src.view.categoria import menu_categorias # Importar nueva función

# Importar excepciones y modelos para manejo de errores y type hinting
# Asegúrate que src.model.producto está accesible
from src.model.producto import DatabaseError, Categoria # Importar Categoria para type hinting

# Configuración del logging
logger = logging.getLogger(__name__)

class MainWindow:
    """Clase principal de la aplicación."""
    def __init__(self):
        self.window = tk.Tk()
        self.tree: Optional[ttk.Treeview] = None
        # Atributos para filtros
        self.search_entry: Optional[ttk.Entry] = None
        self.category_filter_combo: Optional[ttk.Combobox] = None
        self.category_map: Dict[str, Optional[int]] = {} # Mapa nombre categoría -> id_categoria

        self.setup_window()
        self.create_widgets()
        # self.initialize_db_pool() # Llamar aquí si se usa pool (ver main.py mejor)

    def setup_window(self):
        """Configura la ventana principal."""
        self.window.title("Sistema Inventario Tahona v1.0") # Ejemplo título con versión
        self.window.geometry("1280x720")
        # Centrar ventana (opcional)
        # self.center_window()

        # Configurar grid para expansión
        self.window.grid_rowconfigure(0, weight=1) # Fila principal se expande
        self.window.grid_columnconfigure(1, weight=1) # Columna derecha (contenido) se expande

        # Frames principales
        self.left_frame = ttk.Frame(self.window, padding="20", style="Left.TFrame") # Estilo opcional
        self.left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = ttk.Frame(self.window, padding="10") # Menos padding aquí
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        # Configurar expansión de filas/columnas en right_frame
        self.right_frame.grid_rowconfigure(1, weight=1) # Fila 1 (tabla) se expande
        self.right_frame.grid_columnconfigure(0, weight=1) # Columna 0 (tabla) se expande

        # Estilos ttk (opcional)
        style = ttk.Style()
        style.configure("Left.TFrame", background="#f0f0f0") # Ejemplo de estilo para frame izquierdo


    def center_window(self):
         """Centra la ventana principal en la pantalla."""
         self.window.update_idletasks() # Asegura que las dimensiones estén calculadas
         width = self.window.winfo_width()
         height = self.window.winfo_height()
         x = (self.window.winfo_screenwidth() // 2) - (width // 2)
         y = (self.window.winfo_screenheight() // 2) - (height // 2)
         self.window.geometry(f'{width}x{height}+{x}+{y}')


    def create_widgets(self):
        """Crea todos los widgets de la ventana principal."""
        # Estilo para botones grandes del menú
        style = ttk.Style()
        style.configure("Big.TButton", font=("Arial", 14), padding=(15, 10), width=22) # Ajustar tamaño

        # --- Left Frame (Menú) ---
        menu_label = ttk.Label(self.left_frame, text="Menú Principal", font=("Arial", 24, "bold"), background="#f0f0f0")
        menu_label.pack(pady=(20, 40)) # Más espacio arriba

        ttk.Button(self.left_frame, text="Gestión de Productos", style="Big.TButton", command=self.open_productos).pack(pady=15, fill=tk.X, padx=10)
        ttk.Button(self.left_frame, text="Gestión de Categorías", style="Big.TButton", command=self.open_categorias).pack(pady=15, fill=tk.X, padx=10)

        # Espaciador (opcional)
        ttk.Frame(self.left_frame, height=50, style="Left.TFrame").pack()

        ttk.Button(self.left_frame, text="Salir", style="Big.TButton", command=self.window.destroy).pack(pady=15, fill=tk.X, padx=10, side=tk.BOTTOM) # Abajo


        # --- Right Frame (Filtros y Tabla) ---

        # Frame para Filtros
        filter_frame = ttk.Frame(self.right_frame, padding=(0, 5))
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5) # Usar grid aquí también

        ttk.Label(filter_frame, text="Buscar Nombre:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="w")
        self.search_entry = ttk.Entry(filter_frame, width=25)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5) # No necesita expandirse tanto
        self.search_entry.bind("<KeyRelease>", self.apply_filters) # Filtrar al escribir

        ttk.Label(filter_frame, text="Categoría:").grid(row=0, column=2, padx=(15, 5), pady=5, sticky="w")
        self.category_filter_combo = ttk.Combobox(filter_frame, state="readonly", width=25)
        self.category_filter_combo.grid(row=0, column=3, padx=5, pady=5)
        self.category_filter_combo.bind("<<ComboboxSelected>>", self.apply_filters) # Filtrar al seleccionar

        # Botón para limpiar filtros (opcional)
        clear_filter_btn = ttk.Button(filter_frame, text="Limpiar Filtros", command=self.clear_filters)
        clear_filter_btn.grid(row=0, column=4, padx=(10, 0), pady=5)

        # Poblar el combobox de categorías
        self.populate_category_filter()

        # Frame para la Tabla Principal (Treeview)
        table_frame = ttk.Frame(self.right_frame)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(5,0)) # Fila 1, se expande
        table_frame.grid_rowconfigure(0, weight=1); table_frame.grid_columnconfigure(0, weight=1)

        # Crear Treeview
        columns = ("id_productos", "nombre", "cantidad", "categoria")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        # Configurar columnas y encabezados
        self.tree.heading("id_productos", text="ID"); self.tree.column("id_productos", width=80, anchor="center", stretch=tk.NO)
        self.tree.heading("nombre", text="Nombre"); self.tree.column("nombre", width=450, anchor="w") # Más ancho
        self.tree.heading("cantidad", text="Cant."); self.tree.column("cantidad", width=80, anchor="center", stretch=tk.NO)
        self.tree.heading("categoria", text="Categoría"); self.tree.column("categoria", width=200, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")

        # Cargar datos iniciales aplicando filtros (vacíos al inicio)
        self.apply_filters()


    def populate_category_filter(self):
        """Obtiene categorías y llena el Combobox de filtro."""
        if not self.category_filter_combo: return
        logger.info("Poblando filtro de categorías...")
        current_selection = self.category_filter_combo.get() # Guardar selección actual
        self.category_map = {" [ Todas ] ": None}
        category_names = [" [ Todas ] "]
        try:
            categorias: List[Categoria] = CategoriaController.get_all()
            for cat in sorted(categorias, key=lambda c: c.nombre): # Ordenar alfabéticamente
                # Evitar duplicados en el nombre visible (aunque UNIQUE en BD)
                if cat.nombre not in self.category_map:
                     self.category_map[cat.nombre] = cat.id_categoria
                     category_names.append(cat.nombre)
            self.category_filter_combo['values'] = category_names
            # Restaurar selección o poner "Todas"
            if current_selection in category_names: self.category_filter_combo.set(current_selection)
            else: self.category_filter_combo.set(" [ Todas ] ")
            logger.info(f"Filtro de categorías poblado/actualizado.")
        except (DatabaseError, ValueError, Exception) as e:
             logger.error(f"Error al poblar filtro de categorías: {e}")
             # No mostrar messagebox aquí si es llamado como callback
             self.category_filter_combo['values'] = [" [ Todas ] "]
             self.category_filter_combo.set(" [ Todas ] ")


    def apply_filters(self, event=None):
        """Aplica los filtros actuales y refresca el Treeview."""
        if not self.tree or not self.search_entry or not self.category_filter_combo:
            logger.warning("Intentando aplicar filtros antes de que UI esté lista.")
            return

        search_term = self.search_entry.get()
        selected_category_name = self.category_filter_combo.get()
        category_id = self.category_map.get(selected_category_name, None)

        logger.debug(f"Aplicando filtros: Término='{search_term}', Categoría='{selected_category_name}' (ID={category_id})")
        try:
            # Llamar al controlador con los filtros
            filtered_products = ProductoController.search_products(
                search_term=search_term,
                category_id=category_id
            )
            # Poblar el treeview con los resultados filtrados
            populate_treeview(self.tree, filtered_products) # Usar función de utils
            # logger.info(f"Treeview actualizado con {len(filtered_products)} productos filtrados.") # Muy verboso
        except (DatabaseError, ValueError, Exception) as e:
             logger.error(f"Error al aplicar filtros y refrescar Treeview: {e}")
             messagebox.showerror("Error de Búsqueda/Filtro", f"No se pudieron obtener los productos filtrados:\n{e}")
             clear_treeview(self.tree) # Limpiar tabla en caso de error

    def clear_filters(self):
         """Limpia los campos de filtro y actualiza la tabla."""
         logger.info("Limpiando filtros...")
         if self.search_entry: self.search_entry.delete(0, tk.END)
         if self.category_filter_combo: self.category_filter_combo.set(" [ Todas ] ")
         self.apply_filters() # Aplicar filtros vacíos para mostrar todo

    def refresh_treeview(self):
        """Refresca el Treeview principal aplicando los filtros actuales."""
        # Este método ahora es redundante si usamos apply_filters directamente,
        # pero lo mantenemos por si se necesita una recarga forzada sin cambiar filtros.
        logger.info("Llamada a refresh_treeview, aplicando filtros actuales...")
        self.apply_filters()

    def open_productos(self):
        """Abre la ventana de gestión de productos."""
        if not self.tree: return
        try:
            # Pasar self.refresh_treeview como callback para que la ventana hija
            # pueda refrescar esta tabla principal al hacer cambios.
            # NOTA: Esto aún usa el refresh completo. La actualización eficiente
            # requeriría un callback más complejo o un patrón Observer.
            menu_productos(self.tree) # menu_productos ahora refresca el tree principal
        except Exception as e:
            logger.error(f"Error al abrir menú de productos: {e}", exc_info=True)
            messagebox.showerror("Error", "No se pudo abrir el menú de productos")

    # --- MÉTODO MODIFICADO ---
    def open_categorias(self):
        """Abre la ventana de gestión de categorías y pasa un callback."""
        logger.info("Abriendo gestión de categorías...")
        try:
            # Pasar self.populate_category_filter como callback
            # para que la ventana hija pueda actualizar el combo al cerrar o al hacer cambios.
            menu_categorias(parent_update_callback=self.populate_category_filter)
        except Exception as e:
            logger.error(f"Error al abrir la ventana de categorías: {e}", exc_info=True)
            messagebox.showerror("Error", "No se pudo abrir la gestión de categorías.")


    def run(self):
        """Inicia el bucle principal de la aplicación."""
        try:
            logger.info("Iniciando aplicación...")
            # Centrar ventana antes de iniciar mainloop (opcional)
            # self.center_window()
            self.window.mainloop()
            logger.info("Aplicación cerrada.")
        except Exception as e:
            # Capturar errores inesperados durante el mainloop (raro)
            logger.critical(f"Error crítico en el bucle principal: {e}", exc_info=True)

# --- Funciones fuera de la clase ---

def setup_logging():
     """Configura el logging básico para la aplicación."""
     log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
     # Configurar nivel INFO o DEBUG según necesidad
     logging.basicConfig(level=logging.INFO, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
     # Podrías añadir un FileHandler aquí si quieres guardar logs a archivo
     # try:
     #     log_file = "inventario_app.log"
     #     file_handler = logging.FileHandler(log_file, encoding='utf-8')
     #     file_handler.setFormatter(logging.Formatter(log_format))
     #     logging.getLogger().addHandler(file_handler)
     #     logger.info(f"Logging configurado. Logs también en: {log_file}")
     # except Exception as e_log:
     #     logger.error(f"No se pudo configurar el logging a archivo: {e_log}")
     # else:
     logger.info("Logging configurado.")

def main():
    """Función principal para lanzar la aplicación."""
    setup_logging() # Configurar logging al inicio
    try:
        # Inicializar pool de BD si se usa
        try:
            # Asume que database.py está accesible
            from database import create_connection_pool, ConnectionError as DBConnectionError
            create_connection_pool()
        except ImportError:
             logger.warning("Módulo database o create_connection_pool no encontrado.")
             # Decidir si la app puede continuar sin BD o debe salir
             messagebox.showwarning("Advertencia", "No se encontró el módulo de base de datos.")
             # return # O salir: sys.exit(1)
        except DBConnectionError as ce:
             logger.critical(f"Fallo al inicializar pool de BD: {ce}")
             messagebox.showerror("Error Crítico de BD", f"No se pudo conectar a la base de datos:\n{ce}\nLa aplicación se cerrará.")
             return # Salir si no hay BD
        except Exception as e_pool:
             logger.critical(f"Error inesperado al inicializar pool de BD: {e_pool}", exc_info=True)
             messagebox.showerror("Error Crítico", f"Error inesperado al conectar a la BD:\n{e_pool}\nLa aplicación se cerrará.")
             return # Salir

        # Crear y correr la aplicación
        app = MainWindow()
        app.run()
    except Exception as e:
        # Captura errores muy críticos durante la inicialización de MainWindow o run()
        logger.critical(f"Error crítico irrecuperable en main(): {e}", exc_info=True)
        # Intentar mostrar un último mensaje si es posible
        try:
             messagebox.showerror("Error Fatal", f"La aplicación encontró un error fatal y debe cerrarse:\n{e}")
        except:
             pass # Ignorar si ni siquiera se puede mostrar el messagebox

if __name__ == "__main__":
    main()

