import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, List, Dict, Any
from src.controller.producto import ProductoController

logger = logging.getLogger(__name__)

def populate_treeview(tree: ttk.Treeview) -> None:
    
    try:
        # Verificar que tree es un widget Treeview válido
        if not isinstance(tree, ttk.Treeview):
            raise TypeError("Se esperaba un widget Treeview válido")

        # Limpiar los datos existentes
        for item in tree.get_children():
            tree.delete(item)

        # Obtener los productos
        productos = ProductoController.get_all()
        
        if not productos:
            logger.info("No hay productos para mostrar")
            return

        # Insertar los productos en el Treeview
        for producto in productos:
            tree.insert(
                "",
                "end",
                values=(
                    producto.id_productos,
                    producto.nombre,
                    producto.cantidad
                )
            )

        logger.info(f"Treeview actualizado con {len(productos)} productos")

    except TypeError as e:
        logger.error(f"Error de tipo en Treeview: {e}")
        raise
    except Exception as e:
        logger.error(f"Error al actualizar Treeview: {e}")
        raise

def clear_treeview(tree: ttk.Treeview) -> None:
   
    for item in tree.get_children():
        tree.delete(item)

def configure_treeview_columns(tree: ttk.Treeview, columns: Dict[str, Dict[str, Any]]) -> None:
   
    for col, config in columns.items():
        tree.column(
            col,
            width=config.get("width", 100),
            anchor=config.get("anchor", "w")
        )
        tree.heading(
            col,
            text=config.get("heading", col.title())
        )

def add_treeview_scrollbar(tree: ttk.Treeview, parent: Any) -> None:
    
    # Scrollbar vertical
    vsb = ttk.Scrollbar(
        parent,
        orient="vertical",
        command=tree.yview
    )
    vsb.pack(side='right', fill='y')
    
    # Scrollbar horizontal
    hsb = ttk.Scrollbar(
        parent,
        orient="horizontal",
        command=tree.xview
    )
    hsb.pack(side='bottom', fill='x')
    
    # Configurar el Treeview para usar los scrollbars
    tree.configure(
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set
    )

def search_in_treeview(tree: ttk.Treeview, search_text: str, column: int = 1) -> None:
    
    # Deseleccionar items actuales
    tree.selection_remove(tree.selection())
    
    # Buscar y seleccionar coincidencias
    for item in tree.get_children():
        value = str(tree.item(item)['values'][column]).lower()
        if search_text.lower() in value:
            tree.selection_add(item)
            tree.see(item)  # Hacer visible el item

def export_treeview_data(tree: ttk.Treeview, filename: str) -> None:
    
    try:
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            # Escribir encabezados
            headers = [tree.heading(col)["text"] for col in tree["columns"]]
            writer.writerow(headers)
            
            # Escribir datos
            for item in tree.get_children():
                row = tree.item(item)["values"]
                writer.writerow(row)
                
        logger.info(f"Datos exportados exitosamente a {filename}")
        
    except Exception as e:
        logger.error(f"Error al exportar datos: {e}")
        messagebox.showerror(
            "Error",
            f"No se pudieron exportar los datos: {e}"
        )

def sort_treeview_column(tree: ttk.Treeview, col: int, reverse: bool) -> None:
    
    # Obtener datos
    data = [
        (tree.item(item)["values"], item)
        for item in tree.get_children('')
    ]
    
    # Ordenar
    data.sort(key=lambda x: x[0][col], reverse=reverse)
    
    # Mover items
    for idx, (_, item) in enumerate(data):
        tree.move(item, '', idx)