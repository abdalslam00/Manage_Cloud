import os
import sys
import logging
import subprocess
import time
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SSHTunnelManager:
    """
    Manages SSH tunneling via an external batch script (StartCloud.bat).
    """
    def __init__(self):
        load_dotenv()
        # The batch script uses local port 3307
        self.local_db_port = int((os.getenv("LOCAL_DB_PORT") or "3307").strip())
        self.process = None

    def start_tunnel(self):
        """
        Establishes the SSH tunnel by launching the StartCloud.bat script.
        Returns the local bind port if successful.
        """
        try:
            bat_path = resource_path(os.path.join("assets", "StartCloud.bat"))
            logger.info(f"Launching SSH tunnel batch script from: {bat_path}")
            
            if not os.path.exists(bat_path):
                raise FileNotFoundError(f"Batch script not found at {bat_path}")

            # CREATE_NEW_CONSOLE = 0x00000010 (Windows only)
            # This opens the terminal window so the user can see the tunnel status
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NEW_CONSOLE

            self.process = subprocess.Popen(
                [bat_path],
                creationflags=creationflags
            )
            
            logger.info(f"SSH Tunnel batch script launched. Using port {self.local_db_port}.")
            
            # Give the tunnel a brief moment to connect
            time.sleep(2)
            
            return self.local_db_port

        except Exception as e:
            logger.error(f"Failed to launch SSH tunnel batch script: {str(e)}")
            self.stop_tunnel()
            raise e

    def stop_tunnel(self):
        """
        Safely closes the SSH tunnel process.
        """
        if self.process:
            logger.info("Closing SSH tunnel batch script...")
            try:
                if sys.platform == "win32":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.process.pid)], capture_output=True)
                else:
                    self.process.terminate()
            except Exception as e:
                logger.error(f"Error terminating batch script: {str(e)}")
            
            self.process = None
            logger.info("SSH tunnel closed.")

    def __enter__(self):
        return self.start_tunnel()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_tunnel()
