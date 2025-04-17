from typing import List, Optional
import logging
from src.model.producto import Producto, ProductoDao, DatabaseError

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductoController:
    """Controlador para la gestión de productos"""

    @staticmethod
    def new(id_producto: int, nombre: str, cantidad: int, valor_unidad: float) -> None:
       
        try:
            # Verificar si ya existe el producto
            existing_product = ProductoDao.read_one(id_producto)
            if existing_product:
                raise ValueError(f"Ya existe un producto con ID {id_producto}")
            
            # Crear y validar el nuevo producto
            new_product = Producto(id_producto, nombre, cantidad, valor_unidad)
            
            # Guardar en la base de datos
            ProductoDao.create(new_product)
            logger.info(f"Producto creado exitosamente: {new_product}")
            
        except (ValueError, DatabaseError) as e:
            logger.error(f"Error al crear producto: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al crear producto: {e}")
            raise ValueError(f"Error inesperado: {e}")

    @staticmethod
    def modify(id_producto_original: int, nuevo_id: int, nombre: str, 
               cantidad: int, valor_unidad: float) -> None:
        
        try:
            # Verificar que el producto existe
            producto_original = ProductoDao.read_one(id_producto_original)
            if not producto_original:
                raise ValueError(f"No existe un producto con ID {id_producto_original}")
            
            # Si el ID va a cambiar, verificar que el nuevo ID no exista
            if id_producto_original != nuevo_id:
                existing = ProductoDao.read_one(nuevo_id)
                if existing:
                    raise ValueError(f"Ya existe un producto con ID {nuevo_id}")
            
            # Crear y validar el producto modificado
            producto_modificado = Producto(nuevo_id, nombre, cantidad, valor_unidad)
            
            # Actualizar en la base de datos
            ProductoDao.update(producto_modificado)
            logger.info(f"Producto modificado exitosamente: {producto_modificado}")
            
        except (ValueError, DatabaseError) as e:
            logger.error(f"Error al modificar producto: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al modificar producto: {e}")
            raise ValueError(f"Error inesperado: {e}")

    @staticmethod
    def delete(id_producto: int) -> None:
        
        try:
            # Intentar eliminar el producto
            ProductoDao.delete(id_producto)
            logger.info(f"Producto eliminado exitosamente: ID {id_producto}")
            
        except (ValueError, DatabaseError) as e:
            logger.error(f"Error al eliminar producto: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al eliminar producto: {e}")
            raise ValueError(f"Error inesperado: {e}")

    @staticmethod
    def get_all() -> List[Producto]:
        
        try:
            productos = ProductoDao.read_all()
            logger.info(f"Recuperados {len(productos)} productos")
            return productos
            
        except DatabaseError as e:
            logger.error(f"Error al obtener productos: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al obtener productos: {e}")
            return []

    @staticmethod
    def get_one(id_producto: int) -> Optional[Producto]:
        
        try:
            producto = ProductoDao.read_one(id_producto)
            if producto:
                logger.info(f"Producto recuperado: {producto}")
            else:
                logger.info(f"Producto no encontrado: ID {id_producto}")
            return producto
            
        except DatabaseError as e:
            logger.error(f"Error al obtener producto: {e}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado al obtener producto: {e}")
            return None