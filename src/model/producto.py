# src/model/producto.py
from mysql.connector import Error, cursor
# Asegúrate que database.py está accesible
from database import get_database_connection, ConnectionError as DBConnectionError # Importar error específico también
from typing import Optional, List, Dict, Any
import logging

# Configuración del logging
logger = logging.getLogger(__name__) # Obtener logger para este módulo

class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos"""
    pass

# --- Clase Categoria ---
class Categoria:
    """Representa una categoría de producto."""
    def __init__(self, id_categoria: int, nombre: str, descripcion: Optional[str] = None) -> None:
        # Validación básica
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")
        # ID 1 es especial ('Sin Categoría'), otros deben ser > 0
        if not isinstance(id_categoria, int) or (id_categoria <= 0 and id_categoria != 1):
             raise ValueError("El ID de categoría debe ser un entero positivo (o 1 para 'Sin Categoría')")

        self.id_categoria = id_categoria
        self.nombre = nombre.strip() # Guardar sin espacios extra
        self.descripcion = descripcion.strip() if descripcion else None

    def __repr__(self) -> str:
        return f"Categoria(id_categoria={self.id_categoria}, nombre='{self.nombre}')"

# --- Clase CategoriaDao ---
class CategoriaDao:
    """Objeto de Acceso a Datos para la tabla Categorías."""
    @staticmethod
    def create(categoria: Categoria) -> Optional[int]:
        """Crea una nueva categoría y devuelve su ID autogenerado."""
        conn = None
        last_id = None
        sql = "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s)"
        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, (categoria.nombre, categoria.descripcion))
                last_id = cur.lastrowid
                conn.commit()
                logger.info(f"Categoría creada: '{categoria.nombre}' con ID: {last_id}")
                return last_id
        except Error as e:
            if conn: conn.rollback()
            if e.errno == 1062: # Error de constraint UNIQUE para 'nombre'
                 logger.warning(f"Intento de crear categoría con nombre duplicado: {categoria.nombre}")
                 raise ValueError(f"Ya existe una categoría con el nombre '{categoria.nombre}'") from e
            logger.error(f"Error de BD ({e.errno}) al crear categoría: {e.msg}") # Usar e.msg para mensaje
            raise DatabaseError(f"Error al crear la categoría: {e.msg}") from e
        except DBConnectionError as ce: raise ce # Relanzar error de conexión del pool
        finally:
            # Devuelve la conexión al pool (si se usa pooling) o la cierra
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def read_all() -> List[Categoria]:
        """Lee todas las categorías ordenadas por nombre."""
        conn = None
        sql = "SELECT id_categoria, nombre, descripcion FROM categorias ORDER BY nombre"
        try:
            conn = get_database_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql)
                result = cur.fetchall()
                categorias = [Categoria(**row) for row in result]
                return categorias
        except Error as e:
            logger.error(f"Error de BD ({e.errno}) al leer categorías: {e.msg}")
            raise DatabaseError(f"Error al leer las categorías: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def read_one(id_categoria: int) -> Optional[Categoria]:
        """Lee una categoría específica por su ID."""
        conn = None
        sql = "SELECT id_categoria, nombre, descripcion FROM categorias WHERE id_categoria = %s"
        try:
            conn = get_database_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql, (id_categoria,))
                result = cur.fetchone()
                if result:
                    return Categoria(**result)
                logger.warning(f"Categoría con ID {id_categoria} no encontrada.")
                return None
        except Error as e:
            logger.error(f"Error de BD ({e.errno}) al leer categoría {id_categoria}: {e.msg}")
            raise DatabaseError(f"Error al leer la categoría: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def update(categoria: Categoria) -> None:
        """Actualiza una categoría existente."""
        conn = None
        sql = "UPDATE categorias SET nombre = %s, descripcion = %s WHERE id_categoria = %s"
        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, (categoria.nombre, categoria.descripcion, categoria.id_categoria))
                if cur.rowcount == 0:
                    conn.rollback() # Importante deshacer si no se encontró
                    raise ValueError(f"No se encontró la categoría con ID {categoria.id_categoria} para actualizar")
                conn.commit()
                logger.info(f"Categoría actualizada: {categoria}")
        except Error as e:
            if conn: conn.rollback()
            if e.errno == 1062: # Nombre duplicado
                 logger.warning(f"Intento de actualizar categoría a nombre duplicado: {categoria.nombre}")
                 raise ValueError(f"Ya existe otra categoría con el nombre '{categoria.nombre}'") from e
            logger.error(f"Error de BD ({e.errno}) al actualizar categoría: {e.msg}")
            raise DatabaseError(f"Error al actualizar la categoría: {e.msg}") from e
        except ValueError as ve: # Capturar el ValueError de rowcount 0
             logger.warning(ve)
             raise # Relanzar para el controlador/vista
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def delete(id_categoria: int) -> None:
        """Elimina una categoría por su ID."""
        conn = None
        sql = "DELETE FROM categorias WHERE id_categoria = %s"
        # Asegurarse que no se borra la categoría por defecto ID 1
        if id_categoria == 1:
             logger.warning("Intento de eliminar la categoría por defecto (ID 1). Operación denegada.")
             raise ValueError("La categoría 'Sin Categoría' (ID 1) no se puede eliminar.")

        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, (id_categoria,))
                if cur.rowcount == 0:
                    conn.rollback()
                    raise ValueError(f"No existe una categoría con ID {id_categoria} para eliminar")
                conn.commit()
                logger.info(f"Categoría eliminada: ID {id_categoria}")
        except Error as e:
            if conn: conn.rollback()
            # Error de restricción de clave foránea
            if e.errno == 1451:
                 logger.error(f"Error FK al eliminar categoría {id_categoria}: {e.msg}")
                 raise ValueError("No se puede eliminar: La categoría tiene productos asociados.") from e
            logger.error(f"Error de BD ({e.errno}) al eliminar categoría {id_categoria}: {e.msg}")
            raise DatabaseError(f"Error al eliminar la categoría: {e.msg}") from e
        except ValueError as ve: # Capturar ValueError de ID 1 o rowcount 0
            logger.warning(ve)
            raise # Relanzar para el controlador/vista
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()


# --- Clase Producto ---
class Producto:
    """Representa un producto del inventario."""
    def __init__(self, id_productos: int, nombre: str, cantidad: int, valor_unidad: float, id_categoria: Optional[int] = 1, nombre_categoria: Optional[str] = None) -> None:
        # Asignar id_categoria por defecto si es None
        processed_id_categoria = id_categoria if id_categoria is not None else 1
        # Validar datos
        self.validate_data(id_productos, nombre, cantidad, valor_unidad, processed_id_categoria)

        # Asignar atributos
        self.id_productos = id_productos
        self.nombre = nombre.strip()
        self.cantidad = cantidad
        self.valor_unidad = float(valor_unidad) # Asegurar que sea float
        self.id_categoria = processed_id_categoria
        self.nombre_categoria = nombre_categoria # Solo para lectura desde JOIN

    @staticmethod
    def validate_data(id_productos: int, nombre: str, cantidad: int, valor_unidad: float, id_categoria: int) -> None:
        """Valida los datos al crear/actualizar un producto."""
        if not isinstance(nombre, str) or not nombre.strip(): raise ValueError("El nombre no puede estar vacío")
        if not isinstance(id_productos, int) or id_productos < 0: raise ValueError("El ID de producto debe ser un número entero no negativo")
        if not isinstance(cantidad, int) or cantidad < 0: raise ValueError("La cantidad debe ser un número entero no negativo")
        try:
            valor = float(valor_unidad)
            if valor < 0: raise ValueError("El valor unitario no puede ser negativo")
        except (TypeError, ValueError): raise ValueError("El valor unitario debe ser un número válido")
        # id_categoria ahora siempre debería ser un int >= 1
        if not isinstance(id_categoria, int) or id_categoria <= 0:
             raise ValueError("El ID de categoría asociado al producto debe ser un entero positivo.")

    def __repr__(self) -> str:
        """Representación textual del objeto Producto."""
        cat_repr = f", id_categoria={self.id_categoria}"
        if self.nombre_categoria: cat_repr += f", nombre_categoria='{self.nombre_categoria}'"
        return (f"Producto(id_productos={self.id_productos}, nombre='{self.nombre}', "
                f"cantidad={self.cantidad}, valor_unidad={self.valor_unidad}{cat_repr})")


# --- Clase ProductoDao ---
class ProductoDao:
    """Objeto de Acceso a Datos para la tabla Productos."""
    @staticmethod
    def create(producto: Producto) -> None:
        """Crea un nuevo producto en la base de datos."""
        conn = None
        sql = "INSERT INTO productos (id_productos, nombre, cantidad, valor_unidad, id_categoria) VALUES (%s, %s, %s, %s, %s)"
        params = (producto.id_productos, producto.nombre, producto.cantidad, producto.valor_unidad, producto.id_categoria)
        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, params)
                conn.commit()
                logger.info(f"Producto creado: {producto}")
        except Error as e:
            if conn: conn.rollback()
            if e.errno == 1062: raise ValueError(f"Ya existe un producto con el ID {producto.id_productos}") from e
            if e.errno == 1452: raise ValueError(f"La categoría seleccionada (ID: {producto.id_categoria}) no existe.") from e
            logger.error(f"Error de BD ({e.errno}) al crear producto: {e.msg}")
            raise DatabaseError(f"Error al crear el producto: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def read_all() -> List[Producto]:
        """Lee todos los productos uniendo con categorías."""
        conn = None
        sql = """
            SELECT p.id_productos, p.nombre, p.cantidad, p.valor_unidad, p.id_categoria,
                   c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            ORDER BY p.id_productos
        """
        try:
            conn = get_database_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql)
                result = cur.fetchall()
                productos = [Producto(**row) for row in result]
                return productos
        except Error as e:
            logger.error(f"Error de BD ({e.errno}) al leer productos con categorías: {e.msg}")
            raise DatabaseError(f"Error al leer los productos: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def read_one(id_productos: int) -> Optional[Producto]:
        """Lee un producto específico por ID, uniendo con categoría."""
        conn = None
        sql = """
            SELECT p.id_productos, p.nombre, p.cantidad, p.valor_unidad, p.id_categoria,
                   c.nombre as nombre_categoria
            FROM productos p
            LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
            WHERE p.id_productos = %s
        """
        try:
            conn = get_database_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql, (id_productos,))
                result = cur.fetchone()
                if result:
                    return Producto(**result)
                logger.warning(f"Producto con ID {id_productos} no encontrado.")
                return None
        except Error as e:
            logger.error(f"Error de BD ({e.errno}) al leer producto {id_productos}: {e.msg}")
            raise DatabaseError(f"Error al leer el producto: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def update(producto: Producto) -> None:
        """Actualiza un producto existente."""
        conn = None
        sql = "UPDATE productos SET nombre = %s, cantidad = %s, valor_unidad = %s, id_categoria = %s WHERE id_productos = %s"
        params = (producto.nombre, producto.cantidad, producto.valor_unidad, producto.id_categoria, producto.id_productos)
        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, params)
                if cur.rowcount == 0:
                     conn.rollback()
                     raise ValueError(f"No se encontró o no se modificó el producto con ID {producto.id_productos}")
                conn.commit()
                logger.info(f"Producto actualizado: {producto}")
        except Error as e:
            if conn: conn.rollback()
            if e.errno == 1452: raise ValueError(f"La categoría seleccionada (ID: {producto.id_categoria}) no existe.") from e
            logger.error(f"Error de BD ({e.errno}) al actualizar producto: {e.msg}")
            raise DatabaseError(f"Error al actualizar el producto: {e.msg}") from e
        except ValueError as ve: # Capturar el ValueError de rowcount 0
             logger.warning(ve)
             raise # Relanzar para el controlador/vista
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    @staticmethod
    def delete(id_productos: int) -> None:
        """Elimina un producto por su ID."""
        conn = None
        sql = "DELETE FROM productos WHERE id_productos = %s"
        try:
            conn = get_database_connection()
            with conn.cursor() as cur:
                conn.start_transaction()
                cur.execute(sql, (id_productos,))
                if cur.rowcount == 0:
                    conn.rollback()
                    raise ValueError(f"No existe un producto con ID {id_productos} para eliminar")
                conn.commit()
                logger.info(f"Producto eliminado: ID {id_productos}")
        except Error as e:
            if conn: conn.rollback()
            logger.error(f"Error de BD ({e.errno}) al eliminar producto {id_productos}: {e.msg}")
            raise DatabaseError(f"Error al eliminar el producto: {e.msg}") from e
        except ValueError as ve: # Capturar ValueError de rowcount 0
            logger.warning(ve)
            raise # Relanzar para el controlador/vista
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

    # --- Método search ---
    @staticmethod
    def search(search_term: Optional[str] = None, category_id: Optional[int] = None) -> List[Producto]:
        """Busca productos por término (en nombre) y/o ID de categoría."""
        conn = None
        try:
            conn = get_database_connection()
            with conn.cursor(dictionary=True) as cur:
                sql = """
                    SELECT p.id_productos, p.nombre, p.cantidad, p.valor_unidad, p.id_categoria,
                           c.nombre as nombre_categoria
                    FROM productos p
                    LEFT JOIN categorias c ON p.id_categoria = c.id_categoria
                """
                params = []
                conditions = []

                if search_term:
                    conditions.append("p.nombre LIKE %s")
                    # Añadir wildcards para búsqueda parcial ('contiene')
                    params.append(f"%{search_term}%")

                if category_id is not None:
                    # Validar que sea un entero positivo
                    if not isinstance(category_id, int) or category_id <= 0:
                         logger.warning(f"ID de categoría inválido recibido en DAO.search: {category_id}. Ignorando filtro.")
                    else:
                         conditions.append("p.id_categoria = %s")
                         params.append(category_id)

                if conditions:
                    sql += " WHERE " + " AND ".join(conditions)

                sql += " ORDER BY p.id_productos" # O por p.nombre, etc.

                # logger.debug(f"DAO Search SQL: {sql} PARAMS: {tuple(params)}") # Log para depuración
                cur.execute(sql, tuple(params))
                result = cur.fetchall()
                productos = [Producto(**row) for row in result]
                return productos

        except Error as e:
            logger.error(f"Error de BD ({e.errno}) al buscar productos (term='{search_term}', cat={category_id}): {e.msg}")
            raise DatabaseError(f"Error al buscar productos: {e.msg}") from e
        except DBConnectionError as ce: raise ce
        finally:
            if conn and conn.is_connected(): conn.close()

