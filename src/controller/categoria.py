# src/controller/categoria.py
from typing import List, Optional
import logging
# Importar modelo y excepciones
# Asegúrate que src.model.producto está accesible
from src.model.producto import Categoria, CategoriaDao, DatabaseError, ProductoDao

# Configuración del logging
logger = logging.getLogger(__name__)

class CategoriaController:
    """Controlador para la gestión de Categorías"""

    @staticmethod
    def get_all() -> List[Categoria]:
        """Obtiene todas las categorías."""
        try:
            categorias = CategoriaDao.read_all()
            logger.info(f"Controlador: Recuperadas {len(categorias)} categorías")
            return categorias
        except DatabaseError as e:
            logger.error(f"Controlador: Error de BD al obtener categorías: {e}")
            raise # Relanzar para que la vista lo maneje
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al obtener categorías: {e}", exc_info=True)
            # Es mejor relanzar un error más específico si es posible
            raise ValueError(f"Error inesperado al obtener categorías: {e}") from e

    @staticmethod
    def get_one(id_categoria: int) -> Optional[Categoria]:
        """Obtiene una categoría por su ID."""
        try:
            return CategoriaDao.read_one(id_categoria)
        except DatabaseError as e:
            logger.error(f"Controlador: Error de BD al obtener categoría {id_categoria}: {e}")
            raise
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al obtener categoría {id_categoria}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al obtener categoría: {e}") from e

    @staticmethod
    def create(nombre: str, descripcion: Optional[str] = None) -> Optional[int]:
        """Crea una nueva categoría."""
        try:
            # Validación básica en el controlador
            nombre_limpio = nombre.strip() if nombre else ""
            if not nombre_limpio:
                 raise ValueError("El nombre de la categoría no puede estar vacío.")
            # Crear objeto temporal (ID no es relevante aquí, DAO lo ignora al insertar)
            # Usar ID 1 temporalmente para pasar la validación del constructor si permite ID 1
            categoria = Categoria(id_categoria=1, nombre=nombre_limpio, descripcion=descripcion)
            # Llamar al DAO
            new_id = CategoriaDao.create(categoria)
            logger.info(f"Controlador: Categoría '{nombre_limpio}' creada con ID {new_id}.")
            return new_id
        except (ValueError, DatabaseError) as e:
            # Errores esperados (nombre vacío, nombre duplicado, error DB)
            logger.warning(f"Controlador: Error al crear categoría '{nombre}': {e}")
            raise # Relanzar para que la vista muestre el mensaje específico
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al crear categoría '{nombre}': {e}", exc_info=True)
            raise ValueError(f"Error inesperado al crear categoría: {e}") from e

    @staticmethod
    def update(id_categoria: int, nombre: str, descripcion: Optional[str] = None) -> None:
        """Actualiza una categoría existente."""
        try:
            nombre_limpio = nombre.strip() if nombre else ""
            if not nombre_limpio:
                 raise ValueError("El nombre de la categoría no puede estar vacío.")
            # Crear objeto con los datos a actualizar
            categoria = Categoria(id_categoria=id_categoria, nombre=nombre_limpio, descripcion=descripcion)
            # Llamar al DAO (valida si existe y maneja error de nombre duplicado)
            CategoriaDao.update(categoria)
            logger.info(f"Controlador: Categoría ID {id_categoria} actualizada.")
        except (ValueError, DatabaseError) as e:
            logger.warning(f"Controlador: Error al actualizar categoría ID {id_categoria}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al actualizar categoría ID {id_categoria}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al actualizar categoría: {e}") from e

    @staticmethod
    def delete(id_categoria: int) -> None:
        """Elimina una categoría."""
        # ID 1 ('Sin Categoría') no se puede eliminar (DAO también lo valida)
        if id_categoria == 1:
            # Lanzar error directamente aquí para evitar llamada a DAO innecesaria
            logger.warning("Controlador: Intento de eliminar categoría ID 1 denegado.")
            raise ValueError("La categoría 'Sin Categoría' no se puede eliminar.")
        try:
            # El DAO maneja la lógica de FK constraint y si la categoría existe
            CategoriaDao.delete(id_categoria)
            logger.info(f"Controlador: Categoría ID {id_categoria} eliminada.")
        except (ValueError, DatabaseError) as e:
            # Errores esperados: no existe, tiene productos asociados, error DB
            logger.warning(f"Controlador: Error al eliminar categoría ID {id_categoria}: {e}")
            raise # Relanzar para la vista
        except Exception as e:
            logger.error(f"Controlador: Error inesperado al eliminar categoría ID {id_categoria}: {e}", exc_info=True)
            raise ValueError(f"Error inesperado al eliminar categoría: {e}") from e

