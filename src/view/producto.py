import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
import logging
from src.controller.producto import ProductoController
from src.utils.utils import populate_treeview

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductForm(ttk.Frame):
    """Clase para el formulario de productos"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.entries: Dict[str, ttk.Entry] = {}
        self.setup_form()

    def setup_form(self) -> None:
        """Configura el formulario con sus campos"""
        # Configurar validadores
        validate_number = self.register(self.validate_numeric)
        validate_float = self.register(self.validate_float)
        
        # Campos del formulario
        fields = {
            "id_producto": {
                "label": "ID Producto:",
                "validate": "key",
                "validatecommand": (validate_number, "%P")
            },
            "nombre": {
                "label": "Nombre:"
            },
            "cantidad": {
                "label": "Cantidad:",
                "validate": "key",
                "validatecommand": (validate_number, "%P")
            },
            "valor_unidad": {
                "label": "Valor Unidad:",
                "validate": "key",
                "validatecommand": (validate_float, "%P")
            }
        }
        
        # Crear campos
        for i, (key, config) in enumerate(fields.items()):
            ttk.Label(self, text=config["label"]).grid(
                row=i, column=0, padx=5, pady=5, sticky="e"
            )
            
            entry = ttk.Entry(self)
            if "validate" in config:
                entry.configure(
                    validate=config["validate"],
                    validatecommand=config["validatecommand"]
                )
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entries[key] = entry

    @staticmethod
    def validate_numeric(value: str) -> bool:
        """Valida que el valor sea numérico"""
        if value == "":
            return True
        return value.isdigit()

    @staticmethod
    def validate_float(value: str) -> bool:
        """Valida que el valor sea un número decimal"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario"""
        try:
            return {
                "id_producto": int(self.entries["id_producto"].get()),
                "nombre": self.entries["nombre"].get().strip(),
                "cantidad": int(self.entries["cantidad"].get()),
                "valor_unidad": float(self.entries["valor_unidad"].get())
            }
        except ValueError as e:
            raise ValueError("Por favor complete todos los campos correctamente") from e

    def set_data(self, data: Dict[str, Any]) -> None:
        """Establece los datos en el formulario"""
        for key, value in data.items():
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, str(value))

    def clear(self) -> None:
        """Limpia todos los campos del formulario"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

class ProductList(ttk.Frame):
    """Clase para la lista de productos"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_list()

    def setup_list(self) -> None:
        """Configura la lista de productos"""
        # Crear scrollbar
        scrollbar = ttk.Scrollbar(self)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Crear lista
        self.listbox = tk.Listbox(
            self,
            width=60,
            height=15,
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configurar scrollbar
        scrollbar.config(command=self.listbox.yview)

    def refresh(self) -> None:
        """Actualiza la lista de productos"""
        self.listbox.delete(0, tk.END)
        try:
            productos = ProductoController.get_all()
            for producto in productos:
                self.listbox.insert(
                    tk.END,
                    f"{producto.id_productos} - {producto.nombre} - {producto.cantidad}"
                )
        except Exception as e:
            logger.error(f"Error al cargar productos: {e}")
            messagebox.showerror("Error", "Error al cargar la lista de productos")

    def get_selected_id(self) -> Optional[int]:
        """Obtiene el ID del producto seleccionado"""
        selection = self.listbox.curselection()
        if not selection:
            return None
        
        item = self.listbox.get(selection[0])
        return int(item.split(' - ')[0])

class ProductWindow:
    """Clase principal para la ventana de gestión de productos"""
    
    def __init__(self, tree: ttk.Treeview):
        self.tree = tree
        self.window = tk.Toplevel()
        self.setup_window()
        self.create_widgets()

    def setup_window(self) -> None:
        """Configura la ventana"""
        self.window.title("Gestión de Productos")
        self.window.geometry("800x600")
        self.window.grab_set()  # Hacer modal

    def create_widgets(self) -> None:
        """Crea los widgets de la ventana"""
        # Título
        ttk.Label(
            self.window,
            text="Gestión de Productos",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Formulario
        self.form = ProductForm(self.window)
        self.form.pack(pady=10, padx=10, fill=tk.X)

        # Botones
        button_frame = ttk.Frame(self.window)
        button_frame.pack(pady=10, fill=tk.X)

        ttk.Button(
            button_frame,
            text="Agregar",
            command=self.add_product
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Modificar",
            command=self.modify_product
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Eliminar",
            command=self.delete_product
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Limpiar",
            command=self.form.clear
        ).pack(side=tk.LEFT, padx=5)

        # Lista de productos
        self.product_list = ProductList(self.window)
        self.product_list.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Cargar productos iniciales
        self.product_list.refresh()

    def add_product(self) -> None:
        """Agrega un nuevo producto"""
        try:
            data = self.form.get_data()
            ProductoController.new(
                data["id_producto"],
                data["nombre"],
                data["cantidad"],
                data["valor_unidad"]
            )
            self.form.clear()
            self.refresh_views()
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
        except Exception as e:
            logger.error(f"Error al agregar producto: {e}")
            messagebox.showerror("Error", str(e))

    def modify_product(self) -> None:
        """Modifica un producto existente"""
        try:
            selected_id = self.product_list.get_selected_id()
            if not selected_id:
                messagebox.showwarning("Advertencia", "Seleccione un producto para modificar")
                return

            data = self.form.get_data()
            ProductoController.modify(
                selected_id,
                data["id_producto"],
                data["nombre"],
                data["cantidad"],
                data["valor_unidad"]
            )
            self.form.clear()
            self.refresh_views()
            messagebox.showinfo("Éxito", "Producto modificado correctamente")
        except Exception as e:
            logger.error(f"Error al modificar producto: {e}")
            messagebox.showerror("Error", str(e))

    def delete_product(self) -> None:
        """Elimina un producto"""
        try:
            selected_id = self.product_list.get_selected_id()
            if not selected_id:
                messagebox.showwarning("Advertencia", "Seleccione un producto para eliminar")
                return

            if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este producto?"):
                return

            ProductoController.delete(selected_id)
            self.form.clear()
            self.refresh_views()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
        except Exception as e:
            logger.error(f"Error al eliminar producto: {e}")
            messagebox.showerror("Error", str(e))

    def refresh_views(self) -> None:
        """Actualiza todas las vistas"""
        self.product_list.refresh()
        populate_treeview(self.tree)

def menu_productos(tree: ttk.Treeview) -> None:
    """Función principal para mostrar la ventana de productos"""
    try:
        ProductWindow(tree)
    except Exception as e:
        logger.error(f"Error al abrir ventana de productos: {e}")
        messagebox.showerror("Error", "Error al abrir la ventana de productos")