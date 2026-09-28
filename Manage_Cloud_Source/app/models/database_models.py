from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal

class ResultTableModel(QAbstractTableModel):
    """
    A custom table model to display MySQL query results efficiently.
    Supports in-place editing.
    """
    cell_edited = pyqtSignal(int, int, object, object)  # row, col, old_val, new_val

    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data or []
        self._headers = headers or []

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        row_data = self._data[index.row()]
        col_name = self._headers[index.column()]
        val = row_data.get(col_name)

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return str(val) if val is not None else ""
            
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if index.isValid() and role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            col_name = self._headers[col]
            old_value = self._data[row].get(col_name)
            
            if str(old_value) == value:
                return False
                
            # Emit signal for MainWindow to handle database update
            self.cell_edited.emit(row, col, old_value, value)
            
            # Update local data
            self._data[row][col_name] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            else:
                return str(section + 1)
        return None

    def update_data(self, data, headers):
        """Updates the model with new results."""
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
