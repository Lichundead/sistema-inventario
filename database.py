# database.py
import mysql.connector
from mysql.connector import pooling # Importar pooling
from mysql.connector import Error as MySQLError # Renombrar Error de mysql para evitar colisión
import os
from dotenv import load_dotenv
import logging
from typing import Optional

# Configurar logging
logger = logging.getLogger(__name__)

# --- NUEVO: Definir excepción personalizada ---
class ConnectionError(Exception):
    """Excepción personalizada para errores de conexión o pool."""
    pass
# ------------------------------------------

# Cargar variables de entorno
load_dotenv()

# Configuración del Pool
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT', 3306))
}

POOL_NAME = "inventory_pool"
POOL_SIZE = 5

cnx_pool: Optional[pooling.MySQLConnectionPool] = None

def create_connection_pool():
    """Crea e inicializa el pool de conexiones si no existe."""
    global cnx_pool
    if cnx_pool is not None: return

    if not all([DB_CONFIG['database'], DB_CONFIG['user']]):
         logger.critical("Faltan variables de entorno críticas para la BD (DB_NAME, DB_USER).")
         # Usar la excepción definida aquí
         raise ConnectionError("Configuración de base de datos incompleta en el archivo .env")

    try:
        logger.info(f"Creando pool de conexiones '{POOL_NAME}'...")
        cnx_pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=POOL_NAME, pool_size=POOL_SIZE, pool_reset_session=True, **DB_CONFIG
        )
        logger.info(f"Pool '{POOL_NAME}' creado.")
        conn_test = cnx_pool.get_connection(); conn_test.close()
        logger.info("Conexión de prueba del pool OK.")
    # Capturar error específico de MySQL y relanzar como nuestra ConnectionError
    except MySQLError as e:
        logger.error(f"Error CRÍTICO de MySQL al crear pool '{POOL_NAME}': {e}")
        cnx_pool = None
        raise ConnectionError(f"No se pudo inicializar el pool de conexiones (MySQL Error): {e}") from e
    except Exception as ex:
        logger.error(f"Error inesperado al crear pool: {ex}")
        cnx_pool = None
        raise ConnectionError(f"Error inesperado al inicializar pool: {ex}") from ex

def get_database_connection():
    """Obtiene una conexión del pool. Crea el pool si es necesario."""
    global cnx_pool
    if cnx_pool is None:
        logger.warning("Pool no inicializado. Intentando crear ahora...")
        create_connection_pool() # Puede lanzar ConnectionError si falla

    try:
        connection = cnx_pool.get_connection()
        if connection.is_connected():
            return connection
        else:
             logger.error("Se obtuvo una conexión no válida del pool.")
             # Usar la excepción definida aquí
             raise ConnectionError("Conexión del pool no válida.")
    # Capturar error específico de MySQL y relanzar como nuestra ConnectionError
    except MySQLError as e:
        logger.error(f"Error de MySQL al obtener conexión del pool '{POOL_NAME}': {e}")
        raise ConnectionError(f"No se pudo obtener conexión del pool (MySQL Error): {e}") from e
    except Exception as ex:
        logger.error(f"Error inesperado al obtener conexión del pool: {ex}")
        raise ConnectionError(f"Error inesperado al obtener conexión: {ex}") from ex

def test_connection():
    """Prueba obtener una conexión del pool."""
    connection = None
    try:
        connection = get_database_connection()
        if connection and connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f'Conectado a MySQL versión {db_info} usando el pool')
            cursor = connection.cursor(); cursor.execute('SELECT DATABASE();')
            db_name = cursor.fetchone()[0]; logger.info(f'BD actual: {db_name}')
            cursor.close(); return True
        else:
             logger.error("Fallo al obtener conexión del pool para la prueba.")
             return False
    # Capturar nuestra ConnectionError específica
    except ConnectionError as ce:
         logger.error(f"Error de conexión durante la prueba: {ce}")
         return False
    except MySQLError as e: # Otros errores de MySQL
        logger.error(f'Error de MySQL durante la prueba de conexión del pool: {e}')
        return False
    except Exception as ex: # Otros errores inesperados
        logger.error(f'Error inesperado durante la prueba de conexión del pool: {ex}')
        return False
    finally:
        if connection and connection.is_connected(): connection.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    print("Ejecutando prueba de conexión a la base de datos...")
    try:
        create_connection_pool()
        if test_connection(): print("Prueba de conexión EXITOSA.")
        else: print("Prueba de conexión FALLIDA.")
    except ConnectionError as e: print(f"ERROR CRÍTICO: No se pudo inicializar o probar el pool: {e}")
    except Exception as e: print(f"ERROR INESPERADO durante la prueba: {e}")

