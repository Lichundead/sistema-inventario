# src/view/categoria.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, List, Callable # Añadir Callable para el callback
import logging
# Asegúrate que src.controller.categoria está accesible
from src.controller.categoria import CategoriaController # Usar el controlador de categorías
# Asegúrate que src.model.producto está accesible
from src.model.producto import Categoria, DatabaseError # Importar modelo y excepción
# Importar utils para clear_treeview
from src.utils.utils import clear_treeview

# Configuración del logging
logger = logging.getLogger(__name__)

class CategoryForm(ttk.Frame):
    """Formulario para ingresar datos de una categoría."""
    def __init__(self, parent):
        super().__init__(parent)
        # Cambiar entries a un diccionario para acceder por nombre
        self.widget_map: Dict[str, tk.Widget] = {}
        self.category_id: Optional[int] = None # Para saber si estamos editando
        self.setup_form()

    def setup_form(self) -> None:
        """Configura los campos del formulario."""
        ttk.Label(self, text="ID Categoría:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        id_entry = ttk.Entry(self, state="readonly", width=10) # Ancho fijo para ID
        id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w") # Alinear a la izquierda
        self.widget_map["id"] = id_entry

        ttk.Label(self, text="Nombre (*):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        nombre_entry = ttk.Entry(self)
        nombre_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew") # Ocupar más espacio
        self.widget_map["nombre"] = nombre_entry

        ttk.Label(self, text="Descripción:").grid(row=2, column=0, padx=5, pady=(5,0), sticky="ne")
        desc_text = tk.Text(self, height=4, width=30, wrap=tk.WORD, relief=tk.SOLID, borderwidth=1) # Añadir borde
        desc_text.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.widget_map["descripcion"] = desc_text

        # Scrollbar para descripción
        desc_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=desc_text.yview)
        desc_scroll.grid(row=2, column=3, pady=5, sticky="nsw") # Colocar a la derecha del Text
        desc_text['yscrollcommand'] = desc_scroll.set

        # Configurar expansión de columna de widgets
        self.grid_columnconfigure(1, weight=1)

    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario."""
        nombre = self.widget_map["nombre"].get().strip()
        # Obtener descripción de forma segura
        descripcion_widget = self.widget_map.get("descripcion")
        descripcion = None
        if isinstance(descripcion_widget, tk.Text):
             descripcion = descripcion_widget.get("1.0", tk.END).strip()

        if not nombre:
            raise ValueError("El campo 'Nombre' es obligatorio.")

        return {
            "id_categoria": self.category_id, # Devuelve el ID actual (si se está editando)
            "nombre": nombre,
            "descripcion": descripcion if descripcion else None # Guardar None si está vacío
        }

    def set_data(self, data: Categoria) -> None:
        """Establece los datos de una categoría en el formulario."""
        self.clear()
        self.category_id = data.id_categoria # Guardar ID para la modificación

        # Mostrar ID (no editable)
        id_entry = self.widget_map.get("id")
        if isinstance(id_entry, ttk.Entry):
            id_entry.configure(state="normal")
            id_entry.insert(0, str(data.id_categoria))
            id_entry.configure(state="readonly")

        # Establecer nombre
        nombre_entry = self.widget_map.get("nombre")
        if isinstance(nombre_entry, ttk.Entry):
             nombre_entry.insert(0, data.nombre)

        # Establecer descripción
        desc_widget = self.widget_map.get("descripcion")
        if isinstance(desc_widget, tk.Text) and data.descripcion:
            desc_widget.insert("1.0", data.descripcion)

    def clear(self) -> None:
        """Limpia el formulario."""
        self.category_id = None # Resetear ID

        # Limpiar ID
        id_entry = self.widget_map.get("id")
        if isinstance(id_entry, ttk.Entry):
            id_entry.configure(state="normal")
            id_entry.delete(0, tk.END)
            id_entry.configure(state="readonly")

        # Limpiar Nombre
        nombre_entry = self.widget_map.get("nombre")
        if isinstance(nombre_entry, ttk.Entry):
             nombre_entry.delete(0, tk.END)

        # Limpiar Descripción
        desc_widget = self.widget_map.get("descripcion")
        if isinstance(desc_widget, tk.Text):
            desc_widget.delete("1.0", tk.END)

        # Poner el foco en el nombre al limpiar
        if isinstance(nombre_entry, ttk.Entry):
             nombre_entry.focus()


class CategoryList(ttk.Frame):
    """Lista de categorías usando ttk.Treeview con actualización eficiente."""
    def __init__(self, parent):
        super().__init__(parent)
        self.tree: Optional[ttk.Treeview] = None
        self.category_item_map: Dict[int, str] = {} # id_categoria -> item_id
        self.setup_treeview()

    def setup_treeview(self) -> None:
        """Configura el Treeview."""
        columns = ("id", "nombre", "descripcion")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.column("id", width=50, anchor=tk.CENTER, stretch=tk.NO) # No estirar ID
        self.tree.heading("nombre", text="Nombre")
        self.tree.column("nombre", width=180, anchor=tk.W)
        self.tree.heading("descripcion", text="Descripción")
        self.tree.column("descripcion", width=250, anchor=tk.W)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Configurar estilo de filas alternas (hacerlo una vez)
        self.tree.tag_configure('oddrow', background='#f0f0f0') # Gris claro
        self.tree.tag_configure('evenrow', background='#ffffff') # Blanco

    def _get_category_values(self, categoria: Categoria) -> tuple:
        """Obtiene los valores de la categoría para el Treeview."""
        desc = categoria.descripcion if categoria.descripcion else ""
        return (categoria.id_categoria, categoria.nombre, desc)

    def refresh(self) -> None:
        """Recarga todas las categorías en el Treeview."""
        if not self.tree: return
        # Limpiar vista y mapa
        clear_treeview(self.tree) # Usar función de utils
        self.category_item_map.clear()
        try:
            categorias = CategoriaController.get_all()
            for i, cat in enumerate(categorias): # Usar enumerate para tags
                values = self._get_category_values(cat)
                tag = 'oddrow' if i % 2 else 'evenrow'
                item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
                self.category_item_map[cat.id_categoria] = item_id
        except (DatabaseError, ValueError, Exception) as e:
            logger.error(f"Error al refrescar lista de categorías: {e}")
            messagebox.showerror("Error", "No se pudieron cargar las categorías.")

    def add_item(self, categoria: Categoria) -> None:
        """Añade una categoría al Treeview."""
        if not self.tree or categoria.id_categoria in self.category_item_map: return
        values = self._get_category_values(categoria)
        # Añadir con tag de estilo apropiado
        tag = 'oddrow' if len(self.category_item_map) % 2 else 'evenrow'
        item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
        self.category_item_map[categoria.id_categoria] = item_id
        self.tree.see(item_id) # Asegurarse que el nuevo item es visible
        self.tree.selection_set(item_id) # Seleccionar el nuevo item

    def update_item(self, categoria: Categoria) -> None:
        """Actualiza una categoría en el Treeview."""
        if not self.tree or categoria.id_categoria not in self.category_item_map: return
        item_id = self.category_item_map[categoria.id_categoria]
        values = self._get_category_values(categoria)
        self.tree.item(item_id, values=values) # Actualizar valores (tags se mantienen)

    def delete_item(self, category_id: int) -> bool: # Devolver bool indicando éxito
        """Elimina una categoría del Treeview. Devuelve True si se eliminó, False si no."""
        if not self.tree or category_id not in self.category_item_map:
             logger.warning(f"Intento de eliminar categoría ID {category_id} no mapeada.")
             return False
        # No permitir borrar la categoría "Sin Categoría" (ID 1)
        if category_id == 1:
             # Ya se valida en el controlador y DAO, pero por si acaso en la UI.
             # messagebox.showwarning("Acción no permitida", "La categoría 'Sin Categoría' no se puede eliminar.")
             return False

        try:
            item_id = self.category_item_map[category_id]
            if self.tree.exists(item_id): # Verificar si existe antes de borrar
                 self.tree.delete(item_id)
                 logger.info(f"Item de categoría ID {category_id} eliminado del Treeview.")
            else:
                 logger.warning(f"Item {item_id} para categoría ID {category_id} no encontrado en Treeview al intentar borrar.")
            # Eliminar del mapa incluso si no se encontró en el tree (para consistencia)
            del self.category_item_map[category_id]
            return True # Eliminación lógica exitosa (del mapa)
        except Exception as e:
             logger.error(f"Error al eliminar item (Cat ID: {category_id}) del Treeview: {e}")
             return False # Falló la eliminación del widget

    def get_selected_id(self) -> Optional[int]:
        """Obtiene el ID de la categoría seleccionada."""
        if not self.tree: return None
        selected_items = self.tree.selection()
        if not selected_items: return None
        # Asegurarse que el item seleccionado aún existe
        item_id = selected_items[0]
        if not self.tree.exists(item_id): return None

        item_values = self.tree.item(item_id, 'values')
        if not item_values: return None
        try:
            return int(item_values[0]) # ID está en la primera columna
        except (ValueError, IndexError, TypeError):
             logger.error(f"Error al convertir ID seleccionado a entero: {item_values}")
             return None


class CategoryWindow:
    """Ventana Toplevel para gestionar categorías."""
    # Añadir parámetro callback
    def __init__(self, parent_update_callback: Optional[Callable] = None):
        self.parent_update_callback = parent_update_callback # Guardar callback
        self.window = tk.Toplevel()
        self.form: Optional[CategoryForm] = None
        self.category_list: Optional[CategoryList] = None
        self.setup_window()
        self.create_widgets()
        # Asociar cierre de ventana con limpieza (opcional)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_window(self) -> None:
        """Configura la ventana."""
        self.window.title("Gestión de Categorías")
        self.window.geometry("700x500")
        self.window.minsize(500, 350)
        try:
             # Intentar hacerla modal (puede fallar en algunos entornos)
             self.window.grab_set()
             self.window.transient() # Asociar con ventana principal (si existe)
        except tk.TclError:
             logger.warning("No se pudo hacer la ventana modal (grab_set falló).")


    def create_widgets(self) -> None:
        """Crea los widgets."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Layout usando grid para más control
        main_frame.rowconfigure(2, weight=1) # Fila 2 (lista) se expande
        main_frame.columnconfigure(0, weight=1) # Columna principal se expande

        # Título
        ttk.Label(main_frame, text="Gestión de Categorías", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10, sticky="ew")

        # Frame superior (Formulario y Botones)
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=1, column=0, pady=5, sticky="nsew")
        top_frame.columnconfigure(0, weight=1) # Formulario se expande

        # Formulario
        self.form = CategoryForm(top_frame)
        self.form.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        # Botones
        button_frame = ttk.Frame(top_frame)
        button_frame.grid(row=0, column=1, sticky="nw", padx=5) # Alinear arriba a la derecha
        ttk.Button(button_frame, text="Agregar", command=self.add_category).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Modificar", command=self.modify_category).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Eliminar", command=self.delete_category).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Limpiar", command=self.clear_form_and_selection).pack(pady=2, fill=tk.X)

        # Separador (opcional)
        # ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, pady=10, sticky="ew")

        # Frame inferior (Lista)
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, pady=(10,10), padx=10, sticky="nsew") # Fila 2
        list_frame.rowconfigure(1, weight=1) # Treeview se expande
        list_frame.columnconfigure(0, weight=1) # Treeview se expande

        ttk.Label(list_frame, text="Categorías Existentes:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=(0,5))
        self.category_list = CategoryList(list_frame)
        self.category_list.grid(row=1, column=0, sticky="nsew")

        # Carga inicial
        self.category_list.refresh()

        # Binding
        if self.category_list.tree:
            self.category_list.tree.bind("<<TreeviewSelect>>", self.on_category_select)

        # Foco inicial en el nombre
        if self.form: self.form.widget_map["nombre"].focus()


    def on_category_select(self, event=None) -> None:
        """Llena el formulario al seleccionar una categoría."""
        if not self.category_list or not self.form: return
        selected_id = self.category_list.get_selected_id()
        if selected_id is None:
             # Podríamos limpiar el form si se deselecciona, pero puede ser molesto
             # self.form.clear()
             return
        try:
            categoria = CategoriaController.get_one(selected_id)
            if categoria:
                self.form.set_data(categoria)
            else:
                # La categoría seleccionada ya no existe (refresco pendiente?)
                self.form.clear()
                messagebox.showwarning("Advertencia", f"La categoría ID {selected_id} ya no existe.", parent=self.window)
                # Forzar refresco de la lista local
                if self.category_list: self.category_list.refresh()
        except (DatabaseError, ValueError, Exception) as e:
            logger.error(f"Error al obtener categoría seleccionada {selected_id}: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los datos de la categoría ID: {selected_id}", parent=self.window)
            self.form.clear()

    def clear_form_and_selection(self) -> None:
        """Limpia formulario y deselecciona lista."""
        if self.form: self.form.clear()
        if self.category_list and self.category_list.tree:
            selection = self.category_list.tree.selection()
            if selection: self.category_list.tree.selection_remove(selection)

    def _handle_successful_update(self):
        """Acciones comunes tras agregar/modificar/eliminar exitosamente."""
        self.clear_form_and_selection()
        # Llamar al callback para actualizar la ventana principal si existe
        if self.parent_update_callback:
            logger.info("Llamando callback para actualizar UI principal.")
            try:
                self.parent_update_callback()
            except Exception as e:
                 logger.error(f"Error al ejecutar callback de actualización: {e}")

    def add_category(self) -> None:
        """Agrega una nueva categoría."""
        if not self.form or not self.category_list: return
        try:
            data = self.form.get_data() # Puede lanzar ValueError si nombre vacío
            new_id = CategoriaController.create(data["nombre"], data["descripcion"]) # Puede lanzar ValueError (duplicado), DatabaseError
            if new_id:
                # Obtener la categoría recién creada para añadirla a la lista
                new_category = CategoriaController.get_one(new_id)
                if new_category:
                    self.category_list.add_item(new_category)
                    self._handle_successful_update() # Limpiar, llamar callback
                    messagebox.showinfo("Éxito", f"Categoría '{new_category.nombre}' agregada.", parent=self.window)
                else:
                    # Si no se encontró después de crear (muy raro), refrescar todo
                    self.category_list.refresh()
                    self._handle_successful_update()
                    messagebox.showinfo("Éxito", "Categoría agregada (recargando lista).", parent=self.window)
            # else: # Controlador lanza excepción si falla, no debería llegar aquí sin ID

        except (ValueError, DatabaseError) as e:
            messagebox.showerror("Error al Agregar", str(e), parent=self.window)
        except Exception as e:
            logger.error(f"Error inesperado al agregar categoría: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", "Ocurrió un error al agregar la categoría.", parent=self.window)

    def modify_category(self) -> None:
        """Modifica la categoría seleccionada."""
        if not self.form or not self.category_list: return
        selected_id = self.category_list.get_selected_id()
        if selected_id is None:
            messagebox.showwarning("Advertencia", "Seleccione una categoría para modificar.", parent=self.window)
            return
        # ID 1 ('Sin Categoría') no se puede modificar
        if selected_id == 1:
             messagebox.showwarning("Acción no permitida", "La categoría 'Sin Categoría' no se puede modificar.", parent=self.window)
             return

        try:
            data = self.form.get_data() # Puede lanzar ValueError si nombre vacío
            # Asegurarse de que el ID en el form es el seleccionado
            if data["id_categoria"] != selected_id:
                 logger.error("Discrepancia entre ID seleccionado y ID en formulario de categoría.")
                 messagebox.showerror("Error Interno", "El ID de la categoría seleccionada no coincide.", parent=self.window)
                 return

            # Llamar al controlador (puede lanzar ValueError, DatabaseError)
            CategoriaController.update(selected_id, data["nombre"], data["descripcion"])
            # Obtener datos actualizados para el treeview
            updated_category = CategoriaController.get_one(selected_id)
            if updated_category:
                self.category_list.update_item(updated_category)
                self._handle_successful_update()
                messagebox.showinfo("Éxito", f"Categoría '{updated_category.nombre}' modificada.", parent=self.window)
            else:
                # Si no se encontró después de modificar (raro), refrescar todo
                self.category_list.refresh()
                self._handle_successful_update()
                messagebox.showinfo("Éxito", "Categoría modificada (recargando lista).", parent=self.window)

        except (ValueError, DatabaseError) as e:
            messagebox.showerror("Error al Modificar", str(e), parent=self.window)
        except Exception as e:
            logger.error(f"Error inesperado al modificar categoría {selected_id}: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", "Ocurrió un error al modificar la categoría.", parent=self.window)

    def delete_category(self) -> None:
        """Elimina la categoría seleccionada."""
        if not self.category_list: return
        selected_id = self.category_list.get_selected_id()
        if selected_id is None:
            messagebox.showwarning("Advertencia", "Seleccione una categoría para eliminar.", parent=self.window)
            return
        # ID 1 ya se valida en el controlador/DAO, pero doble check
        if selected_id == 1:
             messagebox.showwarning("Acción no permitida", "La categoría 'Sin Categoría' no se puede eliminar.", parent=self.window)
             return

        # Obtener nombre para el mensaje de confirmación
        cat_to_delete = CategoriaController.get_one(selected_id)
        cat_name = f"ID {selected_id}" if not cat_to_delete else f"'{cat_to_delete.nombre}' (ID {selected_id})"

        if not messagebox.askyesno("Confirmar Eliminación",
                                   f"¿Está seguro de eliminar la categoría {cat_name}?\n"
                                   "Los productos asociados pasarán a 'Sin Categoría'.", parent=self.window):
            return
        try:
            # Llamar al controlador (puede lanzar ValueError, DatabaseError)
            CategoriaController.delete(selected_id)
            # Eliminar del treeview localmente
            deleted_from_view = self.category_list.delete_item(selected_id)
            if deleted_from_view:
                 self._handle_successful_update()
                 messagebox.showinfo("Éxito", f"Categoría {cat_name} eliminada.", parent=self.window)
            # else: # Si delete_item devolvió False (ej. ID 1), no hacer nada más

        except (ValueError, DatabaseError) as e:
            # Mostrar error específico (ej. si tiene productos y no se pudo SET DEFAULT/NULL)
            messagebox.showerror("Error al Eliminar", str(e), parent=self.window)
        except Exception as e:
            logger.error(f"Error inesperado al eliminar categoría {selected_id}: {e}", exc_info=True)
            messagebox.showerror("Error Inesperado", "Ocurrió un error al eliminar la categoría.", parent=self.window)

    def on_close(self):
        """Acción al cerrar la ventana."""
        logger.info("Cerrando ventana de gestión de categorías.")
        # Liberar grab si existe antes de destruir
        try:
             self.window.grab_release()
        except tk.TclError:
             pass # Ignorar si grab_release falla (ej. ventana ya no existe)
        self.window.destroy()


# Función de entrada para esta ventana
# Aceptar el callback como argumento
def menu_categorias(parent_update_callback: Optional[Callable] = None) -> None:
    """Muestra la ventana de gestión de categorías."""
    try:
        # Pasar el callback a la ventana
        CategoryWindow(parent_update_callback)
    except Exception as e:
        logger.error(f"Error al abrir ventana de categorías: {e}", exc_info=True)
        messagebox.showerror("Error", "No se pudo abrir la gestión de categorías.")

