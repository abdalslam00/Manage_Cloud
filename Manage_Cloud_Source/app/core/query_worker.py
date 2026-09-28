import logging
from PyQt6.QtCore import QThread, pyqtSignal
from app.utils.sql_translator import SQLTranslator

logger = logging.getLogger(__name__)

class QueryWorker(QThread):
    """
    Handles SQL query execution in a separate thread to prevent UI freezing.
    Supports multi-statement scripts.
    """
    started_signal = pyqtSignal()
    finished_signal = pyqtSignal(list, list, int)
    error_signal = pyqtSignal(str)

    def __init__(self, db_manager, query):
        super().__init__()
        self.db_manager = db_manager
        self.query = query

    def run(self):
        """Executes the query and emits results or errors."""
        self.started_signal.emit()
        try:
            statements = SQLTranslator.split_statements(self.query)
            last_results = []
            last_headers = []
            total_affected_rows = 0
            
            with self.db_manager.get_cursor() as cursor:
                for stmt in statements:
                    stmt = stmt.strip()
                    if not stmt:
                        continue
                        
                    logger.info(f"Executing statement: {stmt[:100]}...")
                    cursor.execute(stmt)
                    
                    affected_rows = cursor.rowcount
                    if affected_rows > 0:
                        total_affected_rows += affected_rows
                        
                    # Fetch results if any
                    try:
                        results = cursor.fetchall()
                        if results:
                            last_results = results
                            last_headers = list(results[0].keys())
                    except Exception:
                        # Some statements don't return results
                        pass
                
                self.finished_signal.emit(last_results, last_headers, total_affected_rows)
                
                if total_affected_rows > 0:
                    logger.info(f"Script execution finished. Total affected rows: {total_affected_rows}")
                
        except Exception as e:
            logger.error(f"Worker Query Error: {str(e)}")
            self.error_signal.emit(str(e))
