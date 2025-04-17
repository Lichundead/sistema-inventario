# main.py
import sys
import os
import logging
import tkinter as tk # Importar tkinter como tk
import tkinter.messagebox as messagebox # Para mostrar errores críticos si GUI falla

# --- Configuración del PYTHONPATH ---
# Añadir el directorio raíz del proyecto al PYTHONPATH para que encuentre 'src' y 'database'
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- Fin Configuración PYTHONPATH ---


# --- Configuración Inicial del Logging ---
# Configurar ANTES de importar otros módulos que puedan loggear
log_format = '%(asctime)s - %(levelname)s - [%(name)s] - %(message)s' # Incluir nombre del módulo
logging.basicConfig(level=logging.INFO, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__) # Logger para este módulo (main)
# -----------------------------------------


# --- Importar Componentes Principales ---
# Importar DESPUÉS de configurar logging y PYTHONPATH
try:
    # Asume que estos módulos están directamente bajo el directorio raíz o en src
    from src.view import principal
    # Asume que database.py está en el directorio raíz
    # Importar la excepción personalizada definida en database.py
    from database import create_connection_pool, ConnectionError as DBConnectionError
except ImportError as ie:
     # Usar el logger configurado
     logger.critical(f"Error de importación crítico: {ie}. Asegúrate que la estructura de carpetas es correcta (ej. src/, database.py) y ejecutas desde la carpeta raíz del proyecto.", exc_info=True)
     # Intentar mostrar messagebox como último recurso
     try:
          # Intentar inicializar Tk para mostrar el error si es posible
          root = tk.Tk()
          root.withdraw() # Ocultar ventana principal de Tk
          messagebox.showerror("Error de Inicio - Importación", f"No se pudieron cargar componentes esenciales:\n{ie}\n\nAsegúrate de ejecutar desde la carpeta raíz del proyecto.")
          root.destroy()
     except tk.TclError: # Capturar error si Tkinter no está disponible
          print(f"ERROR CRÍTICO DE IMPORTACIÓN (TK no disponible): {ie}. No se puede iniciar la aplicación.")
     except Exception as e_tk: # Capturar otros errores al mostrar messagebox
          print(f"ERROR CRÍTICO DE IMPORTACIÓN (Error al mostrar messagebox): {ie}. Error TK: {e_tk}")
     sys.exit(1) # Salir si no se pueden importar módulos clave
except Exception as e_import:
     logger.critical(f"Error inesperado durante la importación inicial: {e_import}", exc_info=True)
     try:
          root = tk.Tk(); root.withdraw()
          messagebox.showerror("Error de Inicio - Inesperado", f"Error inesperado al cargar la aplicación:\n{e_import}")
          root.destroy()
     except tk.TclError:
          print(f"ERROR CRÍTICO INESPERADO (TK no disponible): {e_import}. No se puede iniciar la aplicación.")
     except Exception as e_tk:
          print(f"ERROR CRÍTICO INESPERADO (Error al mostrar messagebox): {e_import}. Error TK: {e_tk}")
     sys.exit(1)
# -----------------------------------------


def run_app():
    """Inicializa y ejecuta la aplicación principal."""
    logger.info("=========================================")
    logger.info("  Iniciando Sistema de Inventario Tahona ")
    logger.info("=========================================")

    # 1. Inicializar Pool de Base de Datos
    try:
        logger.info("Inicializando pool de conexiones a la base de datos...")
        create_connection_pool() # Llama a la función de database.py
        logger.info("Pool de conexiones inicializado correctamente.")
    # Capturar la excepción específica definida en database.py
    except DBConnectionError as ce:
        logger.critical(f"Fallo CRÍTICO al inicializar pool de BD: {ce}")
        # Usar tk importado para el messagebox
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Error Crítico de BD", f"No se pudo conectar a la base de datos:\n{ce}\n\nVerifica la configuración (.env) y el servidor de base de datos.\nLa aplicación se cerrará.")
        root.destroy()
        sys.exit(1) # Salir si no hay conexión a BD
    except Exception as e_pool:
        # Capturar cualquier otro error durante la inicialización del pool
        logger.critical(f"Error inesperado al inicializar pool de BD: {e_pool}", exc_info=True)
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Error Crítico", f"Error inesperado al conectar a la BD:\n{e_pool}\nLa aplicación se cerrará.")
        root.destroy()
        sys.exit(1)

    # 2. Lanzar la interfaz principal
    try:
        logger.info("Lanzando interfaz gráfica principal...")
        # Llama a la función main() dentro del módulo src.view.principal
        # Esta función main() crea la instancia de MainWindow y llama a app.run()
        principal.main()
        logger.info("La aplicación ha finalizado normalmente (ventana cerrada).")
    except Exception as e_main:
        # Capturar errores no manejados dentro de la ejecución de la app principal
        # (ej. errores graves en el event loop o inicialización de MainWindow)
        logger.critical(f"Error crítico no manejado durante la ejecución de la aplicación: {e_main}", exc_info=True)
        # Intentar mostrar un último mensaje
        try:
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Error Fatal", f"La aplicación encontró un error fatal y debe cerrarse:\n{e_main}")
            root.destroy()
        except tk.TclError: # Usar tk.TclError importado
            logger.error("No se pudo mostrar el messagebox de error fatal (TclError).")
        except Exception as e_msgbox:
             logger.error(f"No se pudo mostrar el messagebox de error fatal (Otro Error): {e_msgbox}")

if __name__ == "__main__":
    # Este bloque se ejecuta solo si ejecutas este script directamente
    run_app()

