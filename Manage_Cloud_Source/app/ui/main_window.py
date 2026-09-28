import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar, 
    QStatusBar, QMessageBox, QDockWidget, QTreeWidget, 
    QTreeWidgetItem, QSplitter, QPlainTextEdit, QTableView,
    QSystemTrayIcon, QMenu, QFileDialog
)
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtCore import Qt, QTimer

from app.ui.connection_dialog import ConnectionDialog
from app.ui.widgets import ResultTableView
from app.ui.widgets.add_row_dialog import AddRowDialog
from app.core.gateway import DBGateway
from app.models.database_models import ResultTableModel
from app.core.query_worker import QueryWorker
from app.utils.logger import setup_app_logging
from app.utils.sql_translator import SQLTranslator

class MainWindow(QMainWindow):
    """
    Main Application Window for the MySQL Cloud Manager.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manage Cloud - MySQL Database Manager")
        self.resize(1000, 700)
        
        # Load theme
        self.load_stylesheet()
        
        # Initialize UI components
        self.init_menu_bar()
        self.init_tool_bar()
        self.init_status_bar()
        self.init_object_explorer()
        self.init_log_console()
        self.init_central_widget()
        
        # Initialize Backend & Logging
        self.gateway = DBGateway()
        setup_app_logging(self.log_output.appendPlainText)
        
        self.worker = None
        self.current_db = None
        self.current_table = None
        self.init_tray_icon()
        
        # Open connection dialog on startup
        QTimer.singleShot(100, self.show_connection_dialog)

    def load_stylesheet(self):
        """Loads the QSS stylesheet from assets."""
        qss_path = os.path.join("assets", "dark_theme.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    def init_menu_bar(self):
        """Initializes the Menu Bar."""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("About", self)
        help_menu.addAction(about_action)

    def init_tool_bar(self):
        """Initializes the Tool Bar."""
        tool_bar = QToolBar("Main Toolbar")
        self.addToolBar(tool_bar)
        
        # Add basic actions
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.show_connection_dialog)
        tool_bar.addAction(connect_action)
        
        tool_bar.addSeparator()
        
        self.run_action = QAction("Run Query", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self.execute_query)
        tool_bar.addAction(self.run_action)
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.populate_explorer)
        tool_bar.addAction(refresh_action)

    def show_connection_dialog(self):
        """Shows the connection settings dialog."""
        dialog = ConnectionDialog(self)
        if dialog.exec():
            # Save settings and attempt connection
            dialog.save_settings()
            self.attempt_connection()

    def attempt_connection(self):
        """Attempts to connect to the database via SSH tunnel."""
        self.statusBar().showMessage("Connecting...")
        try:
            if self.gateway.connect():
                self.statusBar().showMessage("Connected Successfully")
                self.populate_explorer()
                QMessageBox.information(self, "Success", "Successfully connected to the database!")
            else:
                self.statusBar().showMessage("Connection Failed")
        except Exception as e:
            self.statusBar().showMessage(f"Error: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")

    def init_tray_icon(self):
        """Initializes the System Tray Icon."""
        self.tray_icon = QSystemTrayIcon(self)
        # Using a standard icon placeholder since we don't have a custom .ico yet
        self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DriveHDIcon))
        
        tray_menu = QMenu()
        restore_action = QAction("Restore", self)
        restore_action.triggered.connect(self.showNormal)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        
        tray_menu.addAction(restore_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        """Handle application closing and ensure resources are freed."""
        # 1. Stop background worker if running
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.statusBar().showMessage("Waiting for query worker to finish...")
            self.worker.wait(2000)  # Wait up to 2 seconds
            if self.worker.isRunning():
                self.worker.terminate()
        
        # 2. Disconnect SSH and MySQL
        if self.gateway:
            self.gateway.disconnect()
            
        # 3. Hide Tray
        self.tray_icon.hide()
        
        super().closeEvent(event)

    def init_status_bar(self):
        """Initializes the Status Bar."""
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

    def init_object_explorer(self):
        """Initializes the Object Explorer Dock Widget."""
        self.explorer_dock = QDockWidget("Object Explorer", self)
        self.explorer_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Databases")
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.itemDoubleClicked.connect(self.on_explorer_item_double_clicked)
        self.tree.customContextMenuRequested.connect(self.show_explorer_context_menu)
        self.explorer_dock.setWidget(self.tree)
        
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.explorer_dock)

    def init_log_console(self):
        """Initializes the Log Console Dock Widget at the bottom."""
        self.log_dock = QDockWidget("Log Console", self)
        self.log_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        self.log_output.setPlaceholderText("Application logs will appear here...")
        
        self.log_dock.setWidget(self.log_output)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

    def populate_explorer(self):
        """Fetches databases and tables to populate the tree using MySQLManager methods."""
        if not self.gateway.db_manager:
            return

        self.tree.clear()
        try:
            db_manager = self.gateway.get_db()
            
            # Get list of databases via manager
            databases = db_manager.get_databases()
            
            for db_name in databases:
                db_item = QTreeWidgetItem(self.tree, [db_name])
                
                # Get tables for this database via manager
                tables = db_manager.get_tables(db_name)
                
                for table_name in tables:
                    QTreeWidgetItem(db_item, [table_name])
                    
        except Exception as e:
            logger.error(f"Failed to populate explorer: {str(e)}")
            self.statusBar().showMessage(f"Explorer Error: {str(e)}")

    def show_explorer_context_menu(self, pos):
        """Shows context menu for items in the object explorer."""
        item = self.tree.itemAt(pos)
        if not item:
            return
            
        menu = QMenu()
        parent = item.parent()
        
        if parent: # It's a table
            db_name = parent.text(0)
            table_name = item.text(0)
            
            truncate_action = QAction(f"Truncate Table '{table_name}'", self)
            truncate_action.triggered.connect(lambda: self.truncate_table(db_name, table_name))
            menu.addAction(truncate_action)
            
            copy_name_action = QAction("Copy Name", self)
            copy_name_action.triggered.connect(lambda: self.sql_editor.insertPlainText(f"`{db_name}`.`{table_name}`"))
            menu.addAction(copy_name_action)
            
        else: # It's a database
            db_name = item.text(0)
            
            export_schema_action = QAction("Export Schema (Structure Only)", self)
            export_schema_action.triggered.connect(lambda: self.export_db_schema(db_name))
            menu.addAction(export_schema_action)
            
            refresh_db_action = QAction("Refresh Tables", self)
            refresh_db_action.triggered.connect(self.populate_explorer)
            menu.addAction(refresh_db_action)

        menu.exec(self.tree.mapToGlobal(pos))

    def truncate_table(self, db_name, table_name):
        """Truncates a table, automatically disabling foreign key checks."""
        reply = QMessageBox.question(
            self, "Confirm Truncate",
            f"Are you sure you want to truncate `{db_name}`.`{table_name}`?\nThis will delete all data in the table.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Construct a safe truncate command
            query = f"SET FOREIGN_KEY_CHECKS = 0;\nTRUNCATE TABLE `{db_name}`.`{table_name}`;\nSET FOREIGN_KEY_CHECKS = 1;"
            self.statusBar().showMessage(f"Truncating table {table_name}...")
            
            # Start worker
            self.worker = QueryWorker(self.gateway.get_db(), query)
            self.worker.started_signal.connect(self.on_query_started)
            self.worker.finished_signal.connect(self.on_query_finished)
            self.worker.error_signal.connect(self.on_query_error)
            self.worker.start()

    def export_db_schema(self, db_name):
        """Exports the schema of a database to a .sql file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Database Schema", f"{db_name}_schema.sql", "SQL Files (*.sql)"
        )
        
        if file_path:
            try:
                self.statusBar().showMessage(f"Exporting schema for {db_name}...")
                schema_content = self.gateway.get_db().get_database_schema(db_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(schema_content)
                
                QMessageBox.information(self, "Export Successful", f"Schema for '{db_name}' exported to:\n{file_path}")
                self.statusBar().showMessage("Export completed.")
            except Exception as e:
                logger.error(f"Failed to export schema: {str(e)}")
                QMessageBox.critical(self, "Export Error", f"Failed to export schema:\n{str(e)}")

    def on_explorer_item_double_clicked(self, item, column):
        """Handles double-clicking a table in the object explorer."""
        parent = item.parent()
        if parent:  # If it has a parent, it's a table
            self.current_db = parent.text(0)
            self.current_table = item.text(0)
            
            # Formulate the query
            query = f"SELECT * FROM `{self.current_db}`.`{self.current_table}` LIMIT 1000;"
            
            # Update editor and run
            self.sql_editor.setPlainText(query)
            self.execute_query()

    def init_central_widget(self):
        """Initializes the Central Widget with an SQL Editor and Results table."""
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create Splitter
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 1. SQL Editor (Top)
        self.sql_editor = QPlainTextEdit()
        self.sql_editor.setPlaceholderText("-- Write your SQL query here... (Press F5 to Run)")
        self.sql_editor.setFont(QFont("Consolas", 11))
        self.sql_editor.setObjectName("SQLEditor")
        
        # 2. Results Table View (Bottom)
        self.results_view = ResultTableView()
        self.results_view.setAlternatingRowColors(True)
        self.results_model = ResultTableModel()
        self.results_view.setModel(self.results_model)
        
        # Add to splitter
        self.splitter.addWidget(self.sql_editor)
        self.splitter.addWidget(self.results_view)
        
        # Set initial sizes (40% editor, 60% table)
        self.splitter.setSizes([300, 500])
        
        self.main_layout.addWidget(self.splitter)
        self.setCentralWidget(self.central_widget)
        
        # Connect signals
        self.results_view.add_row_requested.connect(self.on_add_row_requested)
        self.results_model.cell_edited.connect(self.on_cell_edited)

    def execute_query(self):
        """Executes the SQL query using a background thread."""
        # 1. Get selected text if any, otherwise get full text
        cursor = self.sql_editor.textCursor()
        selected_text = cursor.selection().toPlainText().strip()
        
        if selected_text:
            query = selected_text
            self.statusBar().showMessage("Executing selected script...")
        else:
            query = self.sql_editor.toPlainText().strip()
            self.statusBar().showMessage("Executing full script...")

        if not query:
            return
            
        if not self.gateway.db_manager:
            QMessageBox.warning(self, "Not Connected", "Please connect to a database first.")
            return
            
        # 2. Apply translations
        translated_query = SQLTranslator.translate(query)
        if translated_query != query:
            self.log_output.appendPlainText("-- Translation Applied: Some keywords were modernized for MySQL.")
            
        # 3. Initialize and start the worker thread
        self.worker = QueryWorker(self.gateway.get_db(), translated_query)
        
        # Connect signals
        self.worker.started_signal.connect(self.on_query_started)
        self.worker.finished_signal.connect(self.on_query_finished)
        self.worker.error_signal.connect(self.on_query_error)
        
        self.worker.start()

    def on_query_started(self):
        """Handles state when query begins."""
        self.run_action.setEnabled(False)
        self.statusBar().showMessage("Executing query in background...")
        # We no longer clear the results model here to prevent UI flicker 
        # and to keep data visible during in-place edits.

    def on_query_finished(self, data, headers, affected_rows):
        """Handles successful query completion."""
        self.run_action.setEnabled(True)
        if data:
            self.results_model.update_data(data, headers)
            self.results_view.resizeColumnsToContents()
            self.statusBar().showMessage(f"Query successful. {len(data)} rows returned.")
        elif affected_rows > 0:
            self.statusBar().showMessage(f"Query successful. {affected_rows} rows affected.")
        else:
            self.statusBar().showMessage("Query executed successfully. No rows returned.")

    def on_query_error(self, message):
        """Handles query errors."""
        self.run_action.setEnabled(True)
        self.statusBar().showMessage(f"Query Error: {message}")
        QMessageBox.critical(self, "SQL Error", f"Error executing query:\n{message}")

    def on_add_row_requested(self):
        """Handles the request to add a new row to the current table."""
        if not self.current_db or not self.current_table:
            QMessageBox.warning(self, "No Table Selected", 
                              "Please double-click a table in the explorer first to select it.")
            return
            
        headers = self.results_model._headers
        if not headers:
            QMessageBox.warning(self, "No Columns", "The current results set has no columns.")
            return
            
        dialog = AddRowDialog(headers, self.current_table, self)
        if dialog.exec():
            data = dialog.get_data()
            
            # Construct INSERT query
            cols = []
            vals = []
            for col, val in data.items():
                if val is not None:
                    cols.append(f"`{col}`")
                    # Basic escaping (should ideally use parameters, but execute_query uses raw SQL)
                    # For safety in this tool, we wrap in quotes
                    escaped_val = val.replace("'", "''")
                    vals.append(f"'{escaped_val}'")
            
            if not cols:
                return

            insert_query = f"INSERT INTO `{self.current_db}`.`{self.current_table}` ({', '.join(cols)}) VALUES ({', '.join(vals)});"
            
            # Show in editor and execute
            self.sql_editor.setPlainText(insert_query)
            self.execute_query()

    def on_cell_edited(self, row, col, old_val, new_val):
        """Handles in-place editing of table cells."""
        if not self.current_db or not self.current_table:
            # We don't have enough context to perform an automatic UPDATE
            self.statusBar().showMessage("Cannot auto-update: Table context missing.")
            return
            
        headers = self.results_model._headers
        row_data = self.results_model._data[row]
        column_to_update = headers[col]
        
        # 1. Build WHERE clause to identify the row uniquely
        where_clauses = []
        pk_candidates = ['id', 'ID', 'Id', 'uid', 'uuid', 'pk']
        pk_col = None
        
        for pk in pk_candidates:
            if pk in row_data:
                pk_col = pk
                break
        
        if pk_col:
            pk_val = row_data[pk_col]
            where_clauses.append(f"`{pk_col}` = '{pk_val}'")
        else:
            # Fallback: use all available columns in the row (using old values for current row)
            for header in headers:
                val = row_data[header]
                if val is None:
                    where_clauses.append(f"`{header}` IS NULL")
                else:
                    # Use old_val for the column being edited to match the record BEFORE change
                    current_match_val = old_val if header == column_to_update else val
                    escaped_match_val = str(current_match_val).replace("'", "''")
                    where_clauses.append(f"`{header}` = '{escaped_match_val}'")

        # 2. Build UPDATE statement
        escaped_new_val = str(new_val).replace("'", "''")
        update_query = f"UPDATE `{self.current_db}`.`{self.current_table}`\n"
        update_query += f"SET `{column_to_update}` = '{escaped_new_val}'\n"
        update_query += f"WHERE {' AND '.join(where_clauses)}\nLIMIT 1;"
        
        # 3. Show in editor and run
        self.log_output.appendPlainText(f"-- Auto-Update: {column_to_update} changed from '{old_val}' to '{new_val}'")
        self.sql_editor.setPlainText(update_query)
        self.execute_query()
