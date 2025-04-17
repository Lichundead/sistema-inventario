# src/view/producto.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Tuple, List, Callable # Añadir List, Callable
import logging

# Controladores
# Asegúrate que src.controller.* están accesibles
from src.controller.producto import ProductoController
from src.controller.categoria import CategoriaController # Necesario para poblar combo

# Modelo y Excepciones
# Asegúrate que src.model.producto está accesible
from src.model.producto import Producto, DatabaseError, Categoria

# Utils
# Asegúrate que src.utils.utils está accesible
from src.utils.utils import populate_treeview, clear_treeview # Usar clear_treeview

# Configuración del logging
logger = logging.getLogger(__name__)

class ProductForm(ttk.Frame):
    """Formulario para ingresar datos de un producto, incluye categoría."""
    def __init__(self, parent):
        super().__init__(parent)
        self.widget_map: Dict[str, tk.Widget] = {} # Usar mapa para widgets
        # Mapa para el combobox de categoría: nombre_visible -> id_categoria
        self.category_combo_map: Dict[str, int] = {}
        self.setup_form()
        self.populate_category_combobox() # Llenar el combo al crear

    def setup_form(self) -> None:
        """Configura el formulario con sus campos."""
        validate_number = self.register(self.validate_numeric)
        validate_float = self.register(self.validate_float)

        # --- Campos del formulario ---
        # ID Producto
        ttk.Label(self, text="ID Producto (*):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        id_entry = ttk.Entry(self, validate="key", validatecommand=(validate_number, "%P"))
        id_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.widget_map["id_producto"] = id_entry

        # Nombre
        ttk.Label(self, text="Nombre (*):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        nombre_entry = ttk.Entry(self)
        nombre_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.widget_map["nombre"] = nombre_entry

        # Cantidad
        ttk.Label(self, text="Cantidad (*):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        cantidad_entry = ttk.Entry(self, validate="key", validatecommand=(validate_number, "%P"))
        cantidad_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.widget_map["cantidad"] = cantidad_entry

        # Valor Unidad
        ttk.Label(self, text="Valor Unidad (*):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        valor_entry = ttk.Entry(self, validate="key", validatecommand=(validate_float, "%P"))
        valor_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.widget_map["valor_unidad"] = valor_entry

        # --- NUEVO: Categoría ---
        ttk.Label(self, text="Categoría (*):").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        category_combo = ttk.Combobox(self, state="readonly")
        category_combo.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        self.widget_map["categoria"] = category_combo

        # Configurar expansión de columna
        self.grid_columnconfigure(1, weight=1)

    def populate_category_combobox(self):
        """Obtiene categorías y llena el Combobox."""
        combo = self.widget_map.get("categoria")
        if not isinstance(combo, ttk.Combobox): return

        logger.info("Poblando combobox de categorías en formulario producto...")
        self.category_combo_map.clear()
        category_names = []
        default_category_id = 1 # ID de 'Sin Categoría'
        default_cat_name = "Sin Categoría" # Nombre por defecto

        try:
            categorias: List[Categoria] = CategoriaController.get_all()
            found_default = False
            # Ordenar categorías alfabéticamente para el combo
            for cat in sorted(categorias, key=lambda c: c.nombre):
                # Evitar nombres duplicados en el combo (aunque UNIQUE en BD)
                if cat.nombre not in self.category_combo_map:
                     self.category_combo_map[cat.nombre] = cat.id_categoria
                     category_names.append(cat.nombre)
                     if cat.id_categoria == default_category_id:
                          default_cat_name = cat.nombre # Usar el nombre real de la BD
                          found_default = True

            # Asegurarse que 'Sin Categoría' esté si no vino de la BD
            if not found_default and default_category_id not in self.category_combo_map.values():
                 logger.warning("Categoría por defecto ID 1 no encontrada en BD. Usando nombre genérico.")
                 # Añadirla manualmente al mapa y lista si es necesario
                 if default_cat_name not in self.category_combo_map:
                      self.category_combo_map[default_cat_name] = default_category_id
                      category_names.insert(0, default_cat_name) # Ponerla al inicio

            combo['values'] = category_names
            # Establecer selección por defecto
            if default_cat_name in category_names:
                 combo.set(default_cat_name)
            elif category_names: # Si no está la por defecto, seleccionar la primera
                 combo.set(category_names[0])
            # else: # Si no hay categorías, el combo estará vacío
            #      combo.set("")

            logger.info(f"Combobox de categorías poblado con {len(category_names)} opciones.")

        except (DatabaseError, ValueError, Exception) as e:
             logger.error(f"Error al poblar combobox de categorías: {e}")
             messagebox.showerror("Error", "No se pudieron cargar las categorías para seleccionar.")
             combo['values'] = [] # Vaciar en caso de error


    @staticmethod
    def validate_numeric(value: str) -> bool:
        """Valida que el valor sea numérico."""
        return value.isdigit() or value == ""

    @staticmethod
    def validate_float(value: str) -> bool:
        """Valida que el valor sea un número decimal."""
        if value == "": return True
        try: float(value); return True
        except ValueError: return False

    def get_data(self) -> Dict[str, Any]:
        """Obtiene los datos del formulario, incluyendo id_categoria."""
        # Obtener valores de los widgets usando el mapa
        id_str = self.widget_map["id_producto"].get()
        nombre_str = self.widget_map["nombre"].get().strip()
        cantidad_str = self.widget_map["cantidad"].get()
        valor_str = self.widget_map["valor_unidad"].get()
        categoria_nombre_sel = self.widget_map["categoria"].get()

        # Validar campos obligatorios
        if not all([id_str, nombre_str, cantidad_str, valor_str, categoria_nombre_sel]):
             raise ValueError("Todos los campos marcados con (*) son obligatorios.")

        # Obtener ID de categoría desde el nombre seleccionado
        id_categoria = self.category_combo_map.get(categoria_nombre_sel)
        if id_categoria is None:
             # Esto no debería pasar si el combo está bien poblado y es readonly
             logger.error(f"No se encontró ID para categoría seleccionada: '{categoria_nombre_sel}'")
             raise ValueError("Categoría seleccionada inválida.")

        try:
            # Convertir a tipos correctos
            return {
                "id_producto": int(id_str),
                "nombre": nombre_str,
                "cantidad": int(cantidad_str),
                "valor_unidad": float(valor_str),
                "id_categoria": id_categoria # Devolver el ID numérico
            }
        except ValueError as e:
            # Mejorar mensajes de error de conversión
            if "invalid literal for int()" in str(e):
                 raise ValueError("ID Producto y Cantidad deben ser números enteros.") from e
            if "could not convert string to float" in str(e):
                 raise ValueError("Valor Unidad debe ser un número decimal.") from e
            raise ValueError("Error en el formato de los datos numéricos.") from e


    def set_data(self, data: Producto) -> None:
        """Establece los datos de un producto en el formulario."""
        self.clear()
        # Usar mapa para establecer valores
        self.widget_map["id_producto"].insert(0, str(data.id_productos))
        self.widget_map["nombre"].insert(0, data.nombre)
        self.widget_map["cantidad"].insert(0, str(data.cantidad))
        self.widget_map["valor_unidad"].insert(0, str(data.valor_unidad))

        # Seleccionar categoría en el Combobox
        combo = self.widget_map.get("categoria")
        if isinstance(combo, ttk.Combobox):
            # Buscar el nombre de la categoría que corresponde al id_categoria del producto
            cat_name_to_select = None
            # El objeto Producto ahora puede tener nombre_categoria gracias al JOIN en get_one
            if data.nombre_categoria:
                 cat_name_to_select = data.nombre_categoria
            else:
                 # Si no vino el nombre (ej. al crear), buscarlo en el mapa del combo
                 for name, cat_id in self.category_combo_map.items():
                      if cat_id == data.id_categoria:
                           cat_name_to_select = name
                           break

            if cat_name_to_select and cat_name_to_select in combo['values']:
                combo.set(cat_name_to_select)
            else:
                # Si no se encuentra, seleccionar 'Sin Categoría' o la primera opción
                default_cat_name = "Sin Categoría"
                logger.warning(f"No se encontró el nombre para id_categoria {data.id_categoria} en el combobox. Seleccionando por defecto.")
                if default_cat_name in combo['values']:
                     combo.set(default_cat_name)
                elif combo['values']:
                     combo.set(combo['values'][0])
                else: # Si el combo está vacío por error de carga
                     combo.set("")


    def clear(self) -> None:
        """Limpia todos los campos del formulario."""
        for name, widget in self.widget_map.items():
             if name == "categoria" and isinstance(widget, ttk.Combobox):
                  # Poner categoría por defecto al limpiar
                  default_cat_name = "Sin Categoría"
                  if default_cat_name in widget['values']:
                       widget.set(default_cat_name)
                  elif widget['values']:
                       widget.set(widget['values'][0])
                  else:
                       widget.set("")
             elif isinstance(widget, ttk.Entry):
                  # Manejar validación al limpiar
                  validate_state = widget.cget("validate")
                  if validate_state != 'none': widget.configure(validate='none')
                  widget.delete(0, tk.END)
                  if validate_state != 'none': widget.configure(validate=validate_state)
             elif isinstance(widget, tk.Text):
                  widget.delete("1.0", tk.END)
        # Foco inicial
        if "id_producto" in self.widget_map:
             self.widget_map["id_producto"].focus()


class ProductList(ttk.Frame):
    """Lista de productos usando ttk.Treeview (con actualización eficiente)."""
    # Esta lista no muestra la categoría, solo ID, Nombre, Cantidad, Valor
    def __init__(self, parent):
        super().__init__(parent)
        self.tree: Optional[ttk.Treeview] = None
        self.product_item_map: Dict[int, str] = {} # id_producto -> item_id
        self.setup_treeview()

    def setup_treeview(self) -> None:
        """Configura el Treeview para la lista local."""
        columns = ("id_producto", "nombre", "cantidad", "valor_unidad") # Columnas base
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id_producto", text="ID"); self.tree.column("id_producto", width=80, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.heading("nombre", text="Nombre"); self.tree.column("nombre", width=250, anchor=tk.W)
        self.tree.heading("cantidad", text="Cantidad"); self.tree.column("cantidad", width=80, anchor=tk.CENTER, stretch=tk.NO)
        self.tree.heading("valor_unidad", text="Valor Unit."); self.tree.column("valor_unidad", width=100, anchor=tk.E, stretch=tk.NO)
        # Scrollbars
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew"); vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
        # Estilo filas
        self.tree.tag_configure('oddrow', background='#f0f0f0')
        self.tree.tag_configure('evenrow', background='#ffffff')

    def _get_product_values(self, producto: Producto) -> Tuple:
        """Devuelve tupla SIN categoría para esta lista local."""
        return (producto.id_productos, producto.nombre, producto.cantidad, producto.valor_unidad)

    def refresh(self) -> None:
        """Recarga todos los productos en esta lista local."""
        if not self.tree: return
        clear_treeview(self.tree) # Usar función de utils
        self.product_item_map.clear()
        try:
            # Obtiene todos los productos (incluyen categoría, pero no la usamos aquí)
            productos = ProductoController.get_all()
            for i, producto in enumerate(productos):
                values = self._get_product_values(producto) # Obtiene valores sin categoría
                tag = 'oddrow' if i % 2 else 'evenrow'
                item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
                self.product_item_map[producto.id_productos] = item_id
        except (DatabaseError, ValueError, Exception) as e:
            logger.error(f"Error al refrescar lista local de productos: {e}")
            messagebox.showerror("Error", "No se pudo cargar la lista de productos.")

    def add_item(self, producto: Producto) -> None:
        """Añade un producto a esta lista local."""
        if not self.tree or producto.id_productos in self.product_item_map: return
        values = self._get_product_values(producto)
        tag = 'oddrow' if len(self.product_item_map) % 2 else 'evenrow'
        item_id = self.tree.insert("", tk.END, values=values, tags=(tag,))
        self.product_item_map[producto.id_productos] = item_id
        self.tree.see(item_id) # Hacer visible
        self.tree.selection_set(item_id) # Seleccionar

    def update_item(self, producto: Producto) -> None:
        """Actualiza un producto en esta lista local."""
        if not self.tree or producto.id_productos not in self.product_item_map: return
        item_id = self.product_item_map[producto.id_productos]
        values = self._get_product_values(producto)
        if self.tree.exists(item_id): # Verificar si existe
             self.tree.item(item_id, values=values)

    def delete_item(self, product_id: int) -> None:
        """Elimina un producto de esta lista local."""
        if not self.tree or product_id not in self.product_item_map: return
        try:
            item_id = self.product_item_map[product_id]
            if self.tree.exists(item_id):
                 self.tree.delete(item_id)
            del self.product_item_map[product_id]
        except Exception as e:
             logger.error(f"Error al eliminar item {product_id} del treeview local: {e}")

    def get_selected_id(self) -> Optional[int]:
        """Obtiene el ID del producto seleccionado en esta lista."""
        if not self.tree: return None
        selected_items = self.tree.selection()
        if not selected_items: return None
        item_id = selected_items[0]
        if not self.tree.exists(item_id): return None # Verificar si existe
        item_values = self.tree.item(item_id, 'values')
        if not item_values: return None
        try: return int(item_values[0]) # ID es el primer valor
        except (ValueError, IndexError, TypeError): return None


class ProductWindow:
    """Ventana Toplevel para gestionar productos."""
    def __init__(self, tree_principal: ttk.Treeview):
        self.tree_principal = tree_principal # Para refresco completo (aún)
        self.window = tk.Toplevel()
        self.form: Optional[ProductForm] = None
        self.product_list: Optional[ProductList] = None
        self.setup_window()
        self.create_widgets()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_window(self) -> None:
        """Configura la ventana."""
        self.window.title("Gestión de Productos")
        self.window.geometry("850x600") # Un poco más ancho para el form
        self.window.minsize(650, 450)
        try:
             self.window.grab_set() # Modal
             self.window.transient()
        except tk.TclError:
             logger.warning("No se pudo hacer la ventana modal (grab_set falló).")


    def create_widgets(self) -> None:
        """Crea los widgets de la ventana."""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        # Layout con grid
        main_frame.rowconfigure(2, weight=1) # Fila 2 (lista) se expande
        main_frame.columnconfigure(0, weight=1) # Columna principal se expande

        ttk.Label(main_frame, text="Gestión de Productos", font=("Arial", 16, "bold")).grid(row=0, column=0, pady=10, sticky="ew")

        # Frame superior (Formulario y Botones)
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=1, column=0, pady=5, sticky="nsew")
        top_frame.columnconfigure(0, weight=1) # Formulario se expande

        # Formulario (ahora incluye combo de categoría)
        self.form = ProductForm(top_frame)
        self.form.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        # Botones
        button_frame = ttk.Frame(top_frame)
        button_frame.grid(row=0, column=1, sticky="nw", padx=5)
        ttk.Button(button_frame, text="Agregar", command=self.add_product).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Modificar", command=self.modify_product).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Eliminar", command=self.delete_product).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Limpiar", command=self.clear_form_and_selection).pack(pady=2, fill=tk.X)

        # Separador (opcional)
        # ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, pady=10, sticky="ew")

        # Frame inferior (Lista)
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, pady=(10,10), padx=10, sticky="nsew") # Fila 2
        list_frame.rowconfigure(1, weight=1); list_frame.columnconfigure(0, weight=1)
        ttk.Label(list_frame, text="Productos Existentes (Seleccione para editar/eliminar):", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=(0,5))
        self.product_list = ProductList(list_frame)
        self.product_list.grid(row=1, column=0, sticky="nsew")

        # Carga inicial
        self.product_list.refresh()

        # Binding para seleccionar producto y llenar formulario
        if self.product_list.tree:
            self.product_list.tree.bind("<<TreeviewSelect>>", self.on_product_select)

        # Foco inicial
        if self.form: self.form.widget_map["id_producto"].focus()

    def on_product_select(self, event=None) -> None:
        """Llena el formulario al seleccionar un producto."""
        if not self.product_list or not self.form: return
        selected_id = self.product_list.get_selected_id()
        if selected_id is None: return # No hacer nada si no hay selección válida
        try:
            # Usar get_one que ahora trae nombre_categoria
            producto = ProductoController.get_one(selected_id)
            if producto:
                self.form.set_data(producto) # set_data ahora maneja la categoría
            else:
                # El producto seleccionado ya no existe (quizás borrado por otra instancia?)
                self.form.clear()
                messagebox.showwarning("Advertencia", f"El producto ID {selected_id} ya no existe.", parent=self.window)
                if self.product_list: self.product_list.refresh() # Recargar lista local
        except (DatabaseError, ValueError, Exception) as e:
            logger.error(f"Error al obtener producto seleccionado {selected_id}: {e}")
            messagebox.showerror("Error", f"No se pudieron cargar los datos del producto ID: {selected_id}", parent=self.window)
            self.form.clear()

    def clear_form_and_selection(self) -> None:
        """Limpia formulario y deselecciona lista."""
        if self.form: self.form.clear()
        if self.product_list and self.product_list.tree:
            selection = self.product_list.tree.selection()
            if selection: self.product_list.tree.selection_remove(selection)

    def _handle_successful_update(self):
        """Acciones comunes tras éxito: limpiar form y refrescar tabla principal."""
        self.clear_form_and_selection()
        self.refresh_main_treeview() # Refrescar tabla principal (aún completo)

    def add_product(self) -> None:
        """Agrega un nuevo producto."""
        if not self.form or not self.product_list: return
        try:
            # get_data ahora incluye id_categoria y valida campos
            data = self.form.get_data()
            # Llamar al controlador para crear
            ProductoController.new(
                data["id_producto"], data["nombre"], data["cantidad"],
                data["valor_unidad"], data["id_categoria"] # Pasar id_categoria
            )
            # Actualizar lista local eficientemente si se creó bien
            new_product = ProductoController.get_one(data["id_producto"])
            if new_product: self.product_list.add_item(new_product)
            else: self.product_list.refresh() # Fallback: recargar si no se encontró

            self._handle_successful_update() # Limpiar form, refrescar principal
            messagebox.showinfo("Éxito", "Producto agregado correctamente.", parent=self.window)
        except (ValueError, DatabaseError) as e:
             # Errores de validación, ID duplicado, FK inválida, DB error
             messagebox.showerror("Error al Agregar", str(e), parent=self.window)
        except Exception as e:
             logger.error(f"Error inesperado al agregar producto: {e}", exc_info=True)
             messagebox.showerror("Error Inesperado", "Ocurrió un error al agregar.", parent=self.window)

    def modify_product(self) -> None:
        """Modifica un producto existente."""
        if not self.product_list or not self.form: return
        selected_id = self.product_list.get_selected_id()
        if selected_id is None: messagebox.showwarning("Advertencia", "Seleccione producto a modificar.", parent=self.window); return

        try:
            # get_data ahora incluye id_categoria y valida
            data = self.form.get_data()
            original_id = selected_id
            new_id = data["id_producto"] # El ID que está AHORA en el formulario

            # Confirmar si el usuario cambió el ID en el formulario
            if new_id != original_id:
                 if not messagebox.askyesno("Confirmar Cambio de ID", f"¿Seguro que desea cambiar ID {original_id} a {new_id}?", parent=self.window): return

            # Llamar al controlador para modificar
            ProductoController.modify(
                original_id, new_id, data["nombre"], data["cantidad"],
                data["valor_unidad"], data["id_categoria"] # Pasar id_categoria
            )
            # Actualizar lista local eficientemente
            modified_product = ProductoController.get_one(new_id)
            if modified_product:
                 # Manejar cambio de ID en el mapa local
                 if original_id != new_id and original_id in self.product_list.product_item_map:
                      # Si ID cambió, el item viejo ya no existe con ese ID
                      # Borrar mapeo viejo y actualizar/añadir el nuevo
                      self.product_list.delete_item(original_id) # Intenta borrar item viejo
                      self.product_list.add_item(modified_product) # Añade nuevo
                 elif original_id in self.product_list.product_item_map: # Si ID no cambió
                      self.product_list.update_item(modified_product)
                 else: # Si el item original no estaba mapeado? Recargar
                      self.product_list.refresh()
            else: self.product_list.refresh() # Fallback

            self._handle_successful_update() # Limpiar form, refrescar principal
            messagebox.showinfo("Éxito", "Producto modificado correctamente.", parent=self.window)
        except (ValueError, DatabaseError) as e:
             # Errores de validación, ID no encontrado, nuevo ID duplicado, FK inválida, DB error
             messagebox.showerror("Error al Modificar", str(e), parent=self.window)
        except Exception as e:
             logger.error(f"Error inesperado al modificar producto {selected_id}: {e}", exc_info=True)
             messagebox.showerror("Error Inesperado", "Ocurrió un error al modificar.", parent=self.window)

    def delete_product(self) -> None:
        """Elimina un producto."""
        if not self.product_list: return
        selected_id = self.product_list.get_selected_id()
        if selected_id is None: messagebox.showwarning("Advertencia", "Seleccione producto a eliminar.", parent=self.window); return

        # Obtener nombre para mensaje de confirmación
        prod_to_delete = ProductoController.get_one(selected_id)
        prod_name = f"ID {selected_id}" if not prod_to_delete else f"'{prod_to_delete.nombre}' (ID {selected_id})"

        if not messagebox.askyesno("Confirmar Eliminación", f"¿Seguro de eliminar el producto {prod_name}?", parent=self.window): return

        try:
            product_id_to_delete = selected_id
            # Llamar al controlador para eliminar
            ProductoController.delete(product_id_to_delete)
            # Actualizar lista local eficientemente
            self.product_list.delete_item(product_id_to_delete)
            self._handle_successful_update() # Limpiar form, refrescar principal
            messagebox.showinfo("Éxito", f"Producto {prod_name} eliminado.", parent=self.window)
        except (ValueError, DatabaseError) as e:
             # Errores: producto no encontrado, error DB
             messagebox.showerror("Error al Eliminar", str(e), parent=self.window)
        except Exception as e:
             logger.error(f"Error inesperado al eliminar producto {selected_id}: {e}", exc_info=True)
             messagebox.showerror("Error Inesperado", "Ocurrió un error al eliminar.", parent=self.window)

    def refresh_main_treeview(self) -> None:
        """Refresca el Treeview de la ventana principal (aún completo)."""
        logger.debug("Refrescando Treeview principal...")
        try:
            # Obtener todos los productos (ya con categoría)
            all_products = ProductoController.get_all()
            # Poblar el treeview principal
            populate_treeview(self.tree_principal, all_products)
            logger.debug("Treeview principal refrescado.")
        except Exception as e:
             logger.error(f"Error al refrescar el Treeview principal: {e}")
             # Podríamos limpiar el treeview principal en caso de error
             # clear_treeview(self.tree_principal)

    def on_close(self):
        """Acción al cerrar la ventana."""
        logger.info("Cerrando ventana de gestión de productos.")
        try:
             self.window.grab_release()
        except tk.TclError: pass
        self.window.destroy()


# Función de entrada
def menu_productos(tree_principal: ttk.Treeview) -> None:
    """Muestra la ventana de gestión de productos."""
    try:
        ProductWindow(tree_principal)
    except Exception as e:
        logger.error(f"Error al abrir ventana de productos: {e}", exc_info=True)
        messagebox.showerror("Error", "No se pudo abrir la gestión de productos.")

