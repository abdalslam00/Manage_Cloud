import logging
from PyQt6.QtCore import QObject, pyqtSignal

class LogSignalEmitter(QObject):
    """Emitter to safely bridge logging and PyQt UI thread."""
    new_log = pyqtSignal(str)

class QPlainTextEditLogger(logging.Handler):
    """
    A custom logging handler that sends log messages to a PyQt6 signal emitter.
    """
    def __init__(self, parent=None):
        super().__init__()
        self.emitter = LogSignalEmitter()
        
    def emit(self, record):
        msg = self.format(record)
        self.emitter.new_log.emit(msg)

def setup_app_logging(log_widget_callback):
    """
    Sets up the application's logging to feed into the specified callback (UI widget).
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create handler
    handler = QPlainTextEditLogger()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Connect signal to the callback
    handler.emitter.new_log.connect(log_widget_callback)
    
    # Add handler to the root logger
    logger.addHandler(handler)
    
    return handler
