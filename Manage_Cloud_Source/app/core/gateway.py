import logging
from .ssh_tunnel import SSHTunnelManager
from .connection_manager import MySQLManager

logger = logging.getLogger(__name__)

class DBGateway:
    """
    Orchestrates the SSH tunnel and MySQL connection to provide a unified
    interface for database operations.
    """
    def __init__(self):
        self.ssh_manager = SSHTunnelManager()
        self.db_manager = None
        self.local_port = None

    def connect(self):
        """
        Connects to the database through an SSH tunnel.
        Steps:
        1. Establish SSH Tunnel.
        2. Establish MySQL Connection using the tunnel's local port.
        """
        try:
            # 1. Start SSH Tunnel
            logger.info("Gateway: Initializing SSH Tunnel...")
            self.local_port = self.ssh_manager.start_tunnel()
            
            # 2. Start MySQL Manager
            logger.info(f"Gateway: Initializing MySQL Connection on local port {self.local_port}...")
            self.db_manager = MySQLManager(port=self.local_port)
            self.db_manager.connect()
            
            logger.info("Gateway: Successfully connected to database via SSH tunnel.")
            return True
            
        except Exception as e:
            logger.error(f"Gateway: Connection process failed: {str(e)}")
            self.disconnect()
            raise e

    def disconnect(self):
        """
        Gracefully shuts down connections in reverse order:
        1. Close MySQL Connection.
        2. Close SSH Tunnel.
        """
        logger.info("Gateway: Starting graceful shutdown...")
        
        # 1. Disconnect MySQL
        if self.db_manager:
            try:
                self.db_manager.disconnect()
            except Exception as e:
                logger.error(f"Gateway: Error disconnecting MySQL: {str(e)}")
            finally:
                self.db_manager = None

        # 2. Stop SSH Tunnel
        if self.ssh_manager:
            try:
                self.ssh_manager.stop_tunnel()
            except Exception as e:
                logger.error(f"Gateway: Error stopping SSH tunnel: {str(e)}")
        
        logger.info("Gateway: Shutdown complete.")

    def get_db(self):
        """
        Returns the MySQL manager instance if connected.
        """
        if not self.db_manager:
            raise ConnectionError("Gateway is not connected. Call connect() first.")
        return self.db_manager

    def __enter__(self):
        self.connect()
        return self.get_db()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
