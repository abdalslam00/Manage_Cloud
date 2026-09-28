import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QHBoxLayout, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from dotenv import load_dotenv, set_key

class ConnectionDialog(QDialog):
    """
    A dialog for configuring SSH and Database connection settings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Settings")
        self.resize(400, 500)
        
        load_dotenv()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # SSH Configuration Group
        ssh_group = QGroupBox("SSH Configuration")
        ssh_form = QFormLayout()
        
        self.ssh_host = QLineEdit()
        self.ssh_port = QLineEdit()
        self.ssh_port.setPlaceholderText("22")
        self.ssh_user = QLineEdit()
        self.ssh_password = QLineEdit()
        self.ssh_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        ssh_form.addRow("SSH Host:", self.ssh_host)
        ssh_form.addRow("SSH Port:", self.ssh_port)
        ssh_form.addRow("SSH User:", self.ssh_user)
        ssh_form.addRow("SSH Password:", self.ssh_password)
        ssh_group.setLayout(ssh_form)
        layout.addWidget(ssh_group)
        
        # Database Configuration Group
        db_group = QGroupBox("Database Configuration")
        db_form = QFormLayout()
        
        self.db_user = QLineEdit()
        self.db_password = QLineEdit()
        self.db_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.db_port = QLineEdit()
        self.db_port.setPlaceholderText("3306")
        self.local_db_port = QLineEdit()
        self.local_db_port.setPlaceholderText("3307")
        self.db_name = QLineEdit()
        
        db_form.addRow("DB User:", self.db_user)
        db_form.addRow("DB Password:", self.db_password)
        db_form.addRow("DB Port:", self.db_port)
        db_form.addRow("Local DB Port:", self.local_db_port)
        db_form.addRow("DB Name:", self.db_name)
        db_group.setLayout(db_form)
        layout.addWidget(db_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setDefault(True)
        self.connect_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.connect_btn)
        
        layout.addLayout(button_layout)

    def load_settings(self):
        """Pre-fills the form with existing environment variables."""
        self.ssh_host.setText(os.getenv("SSH_HOST", ""))
        self.ssh_port.setText(os.getenv("SSH_PORT", "22"))
        self.ssh_user.setText(os.getenv("SSH_USER", ""))
        self.ssh_password.setText(os.getenv("SSH_PASSWORD", ""))
        
        self.db_user.setText(os.getenv("DB_USER", ""))
        self.db_password.setText(os.getenv("DB_PASSWORD", ""))
        self.db_port.setText(os.getenv("DB_PORT", "3306"))
        self.local_db_port.setText(os.getenv("LOCAL_DB_PORT", "3307"))
        self.db_name.setText(os.getenv("DB_NAME", ""))

    def get_connection_data(self):
        """Returns the form data as a dictionary with stripped strings."""
        return {
            "SSH_HOST": self.ssh_host.text().strip(),
            "SSH_PORT": self.ssh_port.text().strip(),
            "SSH_USER": self.ssh_user.text().strip(),
            "SSH_PASSWORD": self.ssh_password.text().strip(),
            "DB_USER": self.db_user.text().strip(),
            "DB_PASSWORD": self.db_password.text().strip(),
            "DB_PORT": self.db_port.text().strip(),
            "LOCAL_DB_PORT": self.local_db_port.text().strip(),
            "DB_NAME": self.db_name.text().strip()
        }

    def save_settings(self):
        """Saves values back to .env file."""
        data = self.get_connection_data()
        env_path = ".env"
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write("")
        
        for key, value in data.items():
            set_key(env_path, key, value)
