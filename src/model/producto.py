from mysql.connector import Error
from database import get_database_connection
from typing import Optional, List
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos"""
    pass

class Producto:
    def __init__(self, id_productos: int, nombre: str, cantidad: int, valor_unidad: float) -> None:
        self.validate_data(id_productos, nombre, cantidad, valor_unidad)
        self.id_productos = id_productos
        self.nombre = nombre
        self.cantidad = cantidad
        self.valor_unidad = valor_unidad

    @staticmethod
    def validate_data(id_productos: int, nombre: str, cantidad: int, valor_unidad: float) -> None:
        # Validar que nombre sea string y no esté vacío
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre no puede estar vacío")
        
        # Validar tipos y valores numéricos
        if not isinstance(id_productos, int) or id_productos < 0:
            raise ValueError("El ID debe ser un número entero positivo")
        
        if not isinstance(cantidad, int) or cantidad < 0:
            raise ValueError("La cantidad debe ser un número entero positivo")
        
        try:
            valor_unidad = float(valor_unidad)
            if valor_unidad < 0:
                raise ValueError("El valor unitario no puede ser negativo")
        except (TypeError, ValueError):
            raise ValueError("El valor unitario debe ser un número válido")

class ProductoDao:
    @staticmethod
    def fromDbToObject(value: tuple) -> Producto:
        # Asegurarse de que value tenga el formato correcto
        if len(value) < 4:
            raise ValueError("Datos incompletos desde la base de datos")
        try:
            return Producto(
                id_productos=int(value[1]),  # id_productos está en el índice 1
                nombre=str(value[2]),        # nombre está en el índice 2
                cantidad=int(value[3]),      # cantidad está en el índice 3
                valor_unidad=float(value[4]) # valor_unidad está en el índice 4
            )
        except Exception as e:
            logger.error(f"Error al convertir datos de DB a objeto: {e}")
            raise

    @staticmethod
    def create(producto: Producto) -> None:
        """Crea un nuevo producto en la base de datos."""
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    conn.start_transaction()
                    cur.execute("""
                        INSERT INTO productos 
                        (id_productos, nombre, cantidad, valor_unidad) 
                        VALUES (%s, %s, %s, %s)
                    """, (producto.id_productos, producto.nombre, 
                         producto.cantidad, producto.valor_unidad))
                    conn.commit()
                    logger.info(f"Producto creado exitosamente: {producto}")
        except Error as e:
            conn.rollback()
            logger.error(f"Error al crear producto: {e}")
            raise DatabaseError(f"Error al crear el producto: {e}")

    @staticmethod
    def read_all() -> List[Producto]:
        """Lee todos los productos de la base de datos."""
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM productos ORDER BY id_productos")
                    result = cur.fetchall()
                    productos = [ProductoDao.fromDbToObject(value) for value in result]
                    logger.info(f"Recuperados {len(productos)} productos")
                    return productos
        except Error as e:
            logger.error(f"Error al leer productos: {e}")
            raise DatabaseError(f"Error al leer los productos: {e}")

    @staticmethod
    def read_one(id_productos: int) -> Optional[Producto]:
        """Lee un producto específico de la base de datos."""
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM productos 
                        WHERE id_productos = %s
                    """, (id_productos,))
                    result = cur.fetchone()
                    if result is None:
                        logger.info(f"Producto no encontrado: ID {id_productos}")
                        return None
                    producto = ProductoDao.fromDbToObject(result)
                    logger.info(f"Producto recuperado: {producto}")
                    return producto
        except Error as e:
            logger.error(f"Error al leer producto {id_productos}: {e}")
            raise DatabaseError(f"Error al leer el producto: {e}")

    @staticmethod
    def update(producto: Producto) -> None:
        """Actualiza un producto en la base de datos."""
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    conn.start_transaction()
                    cur.execute("""
                        UPDATE productos
                        SET nombre = %s,
                            cantidad = %s,
                            valor_unidad = %s
                        WHERE id_productos = %s
                    """, (producto.nombre, producto.cantidad, 
                         producto.valor_unidad, producto.id_productos))
                    if cur.rowcount == 0:
                        raise DatabaseError(f"No se encontró el producto con ID {producto.id_productos}")
                    conn.commit()
                    logger.info(f"Producto actualizado: {producto}")
        except Error as e:
            conn.rollback()
            logger.error(f"Error al actualizar producto: {e}")
            raise DatabaseError(f"Error al actualizar el producto: {e}")

    @staticmethod
    def delete(id_productos: int) -> None:
        """Elimina un producto de la base de datos."""
        try:
            with get_database_connection() as conn:
                with conn.cursor() as cur:
                    conn.start_transaction()
                    # Primero verificar si el producto existe
                    cur.execute("SELECT id_productos FROM productos WHERE id_productos = %s", (id_productos,))
                    if cur.fetchone() is None:
                        raise ValueError(f"No existe un producto con ID {id_productos}")
                    
                    # Si existe, entonces eliminarlo
                    cur.execute("DELETE FROM productos WHERE id_productos = %s", (id_productos,))
                    conn.commit()
                    logger.info(f"Producto eliminado: ID {id_productos}")
        except Error as e:
            conn.rollback()
            logger.error(f"Error al eliminar producto {id_productos}: {e}")
            raise DatabaseError(f"Error al eliminar el producto: {e}")