# src/controller/producto.py
from typing import List, Optional
import logging
# Asegurarse que se importa ProductoDao y DatabaseError
# Asume que src.model.producto está accesible
from src.model.producto import Producto, ProductoDao, DatabaseError

# Configuración del logging
logger = logging.getLogger(__name__)

class ProductoController:
    """Controlador para la gestión de productos"""

    @staticmethod
    def new(id_producto: int, nombre: str, cantidad: int, valor_unidad: float, id_categoria: Optional[int] = 1) -> None:
        """Crea un nuevo producto."""
        try:
            # Crear y validar el nuevo producto (ahora incluye id_categoria)
            # El constructor de Producto asigna 1 si id_categoria es None
            new_product = Producto(id_producto, nombre, cantidad, valor_unidad, id_categoria)

            # Guardar en la base de datos (DAO maneja errores de duplicado, FK)
            ProductoDao.create(new_product)
            logger.info(f"Controlador: Producto creado exitosamente: ID {id_producto}")

        except (ValueError, DatabaseError) as e:
            logger.warning(f"Controlador: Error al crear producto ID {id_producto}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al crear producto ID {id_producto}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al crear producto: {e}") from e

    @staticmethod
    def modify(id_producto_original: int, nuevo_id: int, nombre: str,
               cantidad: int, valor_unidad: float, id_categoria: Optional[int] = 1) -> None:
        """Modifica un producto existente."""
        try:
            # Si el ID va a cambiar, verificar que el nuevo ID no esté ya en uso por OTRO producto
            if id_producto_original != nuevo_id:
                existing_with_new_id = ProductoDao.read_one(nuevo_id)
                if existing_with_new_id:
                    # No permitir cambiar a un ID que ya existe
                    raise ValueError(f"Ya existe otro producto con el nuevo ID {nuevo_id}")

            # Crear y validar el producto modificado (constructor valida)
            # El constructor de Producto asigna 1 si id_categoria es None
            producto_modificado = Producto(nuevo_id, nombre, cantidad, valor_unidad, id_categoria)

            # Actualizar en la base de datos (DAO verifica si el original existe y maneja FK)
            ProductoDao.update(producto_modificado)
            logger.info(f"Controlador: Producto ID {id_producto_original} modificado (nuevo ID: {nuevo_id}).")

        except (ValueError, DatabaseError) as e:
            logger.warning(f"Controlador: Error al modificar producto ID {id_producto_original}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al modificar producto ID {id_producto_original}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al modificar producto: {e}") from e

    @staticmethod
    def delete(id_producto: int) -> None:
        """Elimina un producto."""
        try:
            # Intentar eliminar el producto (DAO verifica si existe)
            ProductoDao.delete(id_producto)
            logger.info(f"Controlador: Producto ID {id_producto} eliminado.")

        except (ValueError, DatabaseError) as e:
            logger.warning(f"Controlador: Error al eliminar producto ID {id_producto}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al eliminar producto ID {id_producto}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al eliminar producto: {e}") from e

    @staticmethod
    def get_all() -> List[Producto]:
        """Obtiene todos los productos (con nombre de categoría)."""
        try:
            productos = ProductoDao.read_all() # DAO ahora hace el JOIN
            logger.info(f"Controlador: Recuperados {len(productos)} productos totales.")
            return productos
        except DatabaseError as e:
            logger.error(f"Controlador: Error de BD al obtener todos los productos: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al obtener todos los productos: {e}", exc_info=True)
            # Devolver lista vacía o relanzar como ValueError
            raise ValueError(f"Error inesperado al obtener productos: {e}") from e


    @staticmethod
    def get_one(id_producto: int) -> Optional[Producto]:
        """Obtiene un producto por ID (con nombre de categoría)."""
        try:
            producto = ProductoDao.read_one(id_producto) # DAO ahora hace el JOIN
            # No loggear aquí para no ser muy verboso, DAO ya lo hace si es necesario
            return producto
        except DatabaseError as e:
            logger.error(f"Controlador: Error de BD al obtener producto {id_producto}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al obtener producto {id_producto}: {e}", exc_info=True)
            # Devolver None o relanzar como ValueError
            raise ValueError(f"Error inesperado al obtener producto: {e}") from e

    # --- NUEVO MÉTODO ---
    @staticmethod
    def search_products(search_term: Optional[str] = None, category_id: Optional[int] = None) -> List[Producto]:
        """Busca productos por término de búsqueda y/o ID de categoría."""
        try:
            # Limpiar término de búsqueda
            term = search_term.strip() if search_term else None
            # Validar category_id (None o > 0)
            cat_id = category_id if isinstance(category_id, int) and category_id > 0 else None

            productos = ProductoDao.search(search_term=term, category_id=cat_id)
            logger.info(f"Controlador: Encontrados {len(productos)} productos para búsqueda='{term}', categoría={cat_id}")
            return productos
        except DatabaseError as e:
            logger.error(f"Controlador: Error de BD al buscar productos: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al buscar productos: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al buscar productos: {e}") from e

