from PyQt6.QtWidgets import QTableView, QApplication, QMenu, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

class ResultTableView(QTableView):
    """
    A custom QTableView that supports copying selected cells to the 
    clipboard with column headers included and adding new rows.
    """
    add_row_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Enable editing triggers like SSMS
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | 
            QAbstractItemView.EditTrigger.EditKeyPressed | 
            QAbstractItemView.EditTrigger.AnyKeyPressed
        )

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        add_row_action = QAction("Add New Row...", self)
        add_row_action.triggered.connect(self.add_row_requested.emit)
        menu.addAction(add_row_action)
        
        menu.addSeparator()
        
        copy_action = QAction("Copy Selection", self)
        copy_action.triggered.connect(self.copy_selection)
        menu.addAction(copy_action)
        
        menu.exec(self.viewport().mapToGlobal(pos))

    def keyPressEvent(self, event):
        # Check for Ctrl+C (Copy)
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            self.copy_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self):
        """
        Copies the selected cells to the system clipboard in a tab-separated
        format, including headers.
        """
        selection = self.selectionModel().selectedIndexes()
        if not selection:
            return

        # Sort selection by row and column
        selection.sort(key=lambda x: (x.row(), x.column()))

        # Group data by rows
        rows = {}
        columns = set()
        for index in selection:
            r, c = index.row(), index.column()
            if r not in rows:
                rows[r] = {}
            # Use DisplayRole to get the formatted text (e.g., "NULL" for nulls)
            rows[r][c] = self.model().data(index, Qt.ItemDataRole.DisplayRole)
            columns.add(c)

        # Sort columns to maintain order
        sorted_columns = sorted(list(columns))
        
        # Build the clipboard string
        copy_text = []
        
        # 1. Add Headers Row
        headers = []
        for c in sorted_columns:
            header_val = self.model().headerData(c, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            headers.append(str(header_val))
        copy_text.append("\t".join(headers))
        
        # 2. Add Data Rows
        # Note: We only output the data for the columns that were in the selection
        # If a cell is missing in the selection but part of a row that has other 
        # selected cells, we leave it empty.
        sorted_row_ids = sorted(rows.keys())
        for r in sorted_row_ids:
            row_vals = []
            for c in sorted_columns:
                row_vals.append(str(rows[r].get(c, "")))
            copy_text.append("\t".join(row_vals))

        # Join everything and put on clipboard
        final_text = "\n".join(copy_text)
        QApplication.clipboard().setText(final_text)
