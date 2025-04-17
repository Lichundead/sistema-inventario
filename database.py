import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': os.getenv('DB_PORT')
}

def get_database_connection():
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            logger.info('Conexión exitosa a la base de datos')
            return connection
    except Error as e:
        logger.error(f'Error al conectar a la base de datos: {e}')
        raise

def test_connection():
    
    try:
        connection = get_database_connection()
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f'Conectado a MySQL versión {db_info}')
            
            cursor = connection.cursor()
            cursor.execute('SELECT DATABASE();')
            database_name = cursor.fetchone()[0]
            logger.info(f'Base de datos actual: {database_name}')
            
            cursor.close()
            connection.close()
            logger.info('Conexión cerrada')
            return True
    except Error as e:
        logger.error(f'Error al conectar a la base de datos: {e}')
        return False

if __name__ == "__main__":
    test_connection()