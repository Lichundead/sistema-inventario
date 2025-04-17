# src/utils/utils.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, List, Dict, Any # Asegurarse que List está importado
# Importar Producto para type hinting
# Necesitamos saber la estructura del objeto Producto que recibimos
# Asume que src.model.producto está accesible
from src.model.producto import Producto

# Configuración del logging
logger = logging.getLogger(__name__)

def populate_treeview(tree: ttk.Treeview, productos: List[Producto]) -> None:
    """
    Llena un Treeview con la lista de productos proporcionada,
    incluyendo el nombre de la categoría.

    Args:
        tree: El widget ttk.Treeview a llenar.
        productos: Una lista de objetos Producto (que deben tener el atributo nombre_categoria).
    """
    # Limpiar primero
    clear_treeview(tree)

    try:
        if not isinstance(tree, ttk.Treeview):
            # Esto no debería pasar si se usa correctamente
            logger.error("populate_treeview recibió algo que no es un Treeview.")
            return

        # Verificar si hay productos
        if not productos:
            # logger.info("No hay productos para mostrar en el Treeview") # Puede ser muy verboso
            return

        # Insertar los productos en el Treeview
        for i, producto in enumerate(productos): # Usar enumerate para alternar filas
            # Obtener el nombre de la categoría, usar 'Sin Categoría' si es None o vacío
            # El DAO ya debería devolver 'Sin Categoría' si id=1, o el nombre correcto.
            # Si nombre_categoria es None (por un LEFT JOIN fallido o dato inconsistente), mostrar algo.
            categoria_nombre = producto.nombre_categoria if producto.nombre_categoria else "N/A"

            # Obtener las columnas definidas en el Treeview para asegurar el orden correcto
            columns = tree['columns']
            # Crear tupla de valores en el orden de las columnas
            # Asumiendo columnas: ('id_productos', 'nombre', 'cantidad', 'categoria')
            # Ajustar si el orden o nombres de columnas en el Treeview son diferentes
            values_tuple = (
                producto.id_productos,
                producto.nombre,
                producto.cantidad,
                categoria_nombre # Asegurarse que esta es la 4ta columna definida
            )

            # Verificar si el número de valores coincide con las columnas
            if len(values_tuple) != len(columns):
                 logger.error(f"Discrepancia entre valores ({len(values_tuple)}) y columnas ({len(columns)}) del Treeview. Columnas: {columns}")
                 # Podríamos omitir esta fila o detenernos
                 continue # Omitir esta fila

            # Añadir tags para estilo de filas alternas (opcional)
            tag = 'oddrow' if i % 2 else 'evenrow'
            tree.insert("", tk.END, values=values_tuple, tags=(tag,))

        # Configurar estilo de filas alternas (hacerlo una vez después del bucle)
        tree.tag_configure('oddrow', background='#f0f0f0') # Gris claro
        tree.tag_configure('evenrow', background='#ffffff') # Blanco

        # logger.info(f"Treeview actualizado con {len(productos)} productos") # Log verboso

    except AttributeError as ae:
         # Error si el objeto Producto no tiene alguno de los atributos esperados
         logger.error(f"Error de atributo al poblar Treeview (¿falta atributo en Producto?): {ae}", exc_info=True)
         messagebox.showerror("Error Interno", "Error al procesar datos de producto para mostrar.")
    except Exception as e:
        logger.error(f"Error general al actualizar Treeview: {e}", exc_info=True)
        # No mostrar messagebox aquí, la función que llama debería manejar errores de carga

def clear_treeview(tree: ttk.Treeview) -> None:
   """Limpia todos los items de un Treeview de forma segura."""
   if tree and isinstance(tree, ttk.Treeview): # Verificar que es un Treeview válido
       # Obtener los items antes de iterar, ya que la lista cambia durante el borrado
       items_to_delete = tree.get_children()
       if items_to_delete:
           # logger.debug(f"Limpiando {len(items_to_delete)} items del Treeview...")
           for item in items_to_delete:
               try:
                   if tree.exists(item): # Verificar si el item aún existe antes de borrar
                       tree.delete(item)
               except tk.TclError as e:
                   # Puede ocurrir si el item ya fue borrado o el treeview está siendo destruido
                   logger.warning(f"Error menor al limpiar treeview (item {item}): {e}")
                   pass # Intentar continuar limpiando el resto
           # logger.debug("Treeview limpiado.")
   # else:
   #      logger.warning("clear_treeview recibió un objeto None o inválido.")


# --- Otras funciones de utils (si las hubiera) ---
# Ejemplo: configure_treeview_columns, add_treeview_scrollbar, etc.
# Se podrían añadir aquí si se usan en múltiples vistas.

# def configure_treeview_columns(tree: ttk.Treeview, columns_config: Dict[str, Dict[str, Any]]) -> None:
#     """Configura las columnas de un Treeview."""
#     tree["columns"] = tuple(columns_config.keys())
#     tree["displaycolumns"] = tuple(columns_config.keys()) # O un subconjunto
#     tree.show = "headings"
#     for col, config in columns_config.items():
#         tree.heading(col, text=config.get("heading", col.title()))
#         tree.column(
#             col,
#             width=config.get("width", 100),
#             minwidth=config.get("minwidth", 40),
#             anchor=config.get("anchor", "w"),
#             stretch=config.get("stretch", tk.YES)
#         )

