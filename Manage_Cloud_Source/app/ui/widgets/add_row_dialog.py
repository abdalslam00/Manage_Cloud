from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QScrollArea, QWidget, QLabel
)
from PyQt6.QtCore import Qt

class AddRowDialog(QDialog):
    """
    A dynamic dialog to enter values for a new database row.
    """
    def __init__(self, headers, table_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add New Row - {table_name}" if table_name else "Add New Row")
        self.setMinimumWidth(400)
        self.headers = headers
        self.inputs = {}
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Scroll area for many columns
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        form_layout = QFormLayout(scroll_content)
        
        for header in self.headers:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(f"Enter {header}...")
            form_layout.addRow(QLabel(f"{header}:"), line_edit)
            self.inputs[header] = line_edit
            
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Returns a dictionary of column names and their entered values."""
        data = {}
        for header, line_edit in self.inputs.items():
            val = line_edit.text().strip()
            # If empty, we might want to treat it as NULL or empty string
            # For now, let's just return the text
            data[header] = val if val != "" else None
        return data
