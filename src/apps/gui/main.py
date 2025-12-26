"""
Main module for the GUI application.
Provides a desktop interface for Testio using PyQt6.
"""

import sys
import argparse
from pathlib import Path

sys.path.append(".")

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QSplitter, QFrame, QHeaderView, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from src.core.config_parser.parsers import ConfigParser
from src.core.execution.data import ExecutionManagerFactory, ComparisonResult
from src.core.execution.manager import ExecutionManager


class TestRunnerThread(QThread):
    """Background thread for running tests without blocking the UI."""
    progress_signal = pyqtSignal(str, object)  # (file_path, result)
    finished_signal = pyqtSignal(list)

    def __init__(self, execution_data):
        super().__init__()
        self.execution_data = execution_data

    def run(self):
        manager = ExecutionManager()
        all_results = []
        
        for path, exec_data_list in self.execution_data.items():
            for i, data in enumerate(exec_data_list):
                result = manager.run(data)
                self.progress_signal.emit(path, result)
                all_results.append((path, i + 1, result))
        
        self.finished_signal.emit(all_results)


class MainWindow(QMainWindow):
    """Main window for the Testio GUI application."""

    def __init__(self, config_path=None):
        super().__init__()
        self.config_path = config_path
        self.execution_data = None
        self.test_thread = None
        self.init_ui()
        
        if config_path:
            self.load_config(config_path)

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Testio - Testing Framework")
        self.setMinimumSize(1000, 700)
        self.setup_styles()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = self.create_header()
        main_layout.addWidget(header)

        # Main content with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Code editor
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([500, 500])
        main_layout.addWidget(splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a configuration file to begin")

    def setup_styles(self):
        """Set up the application styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f1f5f9;
            }
            QLabel {
                color: #1e293b;
            }
            QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4f46e5;
            }
            QPushButton:pressed {
                background-color: #4338ca;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
            QPushButton#secondary {
                background-color: #e2e8f0;
                color: #1e293b;
            }
            QPushButton#secondary:hover {
                background-color: #cbd5e1;
            }
            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #6366f1;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #6366f1;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QFrame#panel {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            QStatusBar {
                background-color: #e2e8f0;
                color: #1e293b;
            }
        """)

    def create_header(self):
        """Create the header section."""
        header = QFrame()
        header.setObjectName("panel")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title = QLabel("🧪 Testio")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #6366f1;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Load config button
        load_btn = QPushButton("📂 Load Config")
        load_btn.setObjectName("secondary")
        load_btn.clicked.connect(self.browse_config)
        header_layout.addWidget(load_btn)

        # Run tests button
        self.run_btn = QPushButton("▶ Run Tests")
        self.run_btn.clicked.connect(self.run_tests)
        self.run_btn.setEnabled(False)
        header_layout.addWidget(self.run_btn)

        return header

    def create_left_panel(self):
        """Create the left panel with code editor."""
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Label
        label = QLabel("📝 Code Editor")
        label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(label)

        # Config path display
        self.config_label = QLabel("No configuration loaded")
        self.config_label.setStyleSheet("color: #64748b; font-style: italic;")
        layout.addWidget(self.config_label)

        # Code editor
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("# Enter your code here...\n\ndef solution():\n    pass")
        layout.addWidget(self.code_editor)

        return panel

    def create_right_panel(self):
        """Create the right panel with results table."""
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Label with summary
        header_layout = QHBoxLayout()
        label = QLabel("📊 Test Results")
        label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(self.summary_label)
        
        layout.addLayout(header_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["#", "Status", "Input", "Expected", "Actual"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setAlternatingRowColors(True)
        layout.addWidget(self.results_table)

        # Clear button
        clear_btn = QPushButton("🗑 Clear Results")
        clear_btn.setObjectName("secondary")
        clear_btn.clicked.connect(self.clear_results)
        layout.addWidget(clear_btn)

        return panel

    def browse_config(self):
        """Open file dialog to select a config file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Configuration File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.load_config(file_path)

    def load_config(self, path):
        """Load and parse a configuration file."""
        try:
            parser = ConfigParser()
            test_suite_config = parser.parse_from_path(Path(path))
            self.execution_data = ExecutionManagerFactory.from_test_suite_config_local(
                test_suite_config, path
            )
            self.config_path = path
            self.config_label.setText(f"Config: {Path(path).name}")
            self.config_label.setStyleSheet("color: #10b981; font-weight: bold;")
            self.run_btn.setEnabled(True)
            self.status_bar.showMessage(f"Loaded configuration: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration:\n{str(e)}")
            self.status_bar.showMessage("Failed to load configuration")

    def run_tests(self):
        """Run the tests in a background thread."""
        if not self.execution_data:
            QMessageBox.warning(self, "Warning", "Please load a configuration file first.")
            return

        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "Warning", "Please enter some code to test.")
            return

        # Write code to test file(s)
        for path in self.execution_data.keys():
            try:
                Path(path).write_text(code)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to write code to {path}:\n{str(e)}")
                return

        # Disable run button and clear previous results
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Running...")
        self.clear_results()
        self.status_bar.showMessage("Running tests...")

        # Start test runner thread
        self.test_thread = TestRunnerThread(self.execution_data)
        self.test_thread.progress_signal.connect(self.on_test_progress)
        self.test_thread.finished_signal.connect(self.on_tests_finished)
        self.test_thread.start()

    def on_test_progress(self, path, result):
        """Handle progress updates from the test runner."""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Test number
        self.results_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # Status
        status_item = QTableWidgetItem(self.get_status_text(result.result))
        status_item.setForeground(QColor(self.get_status_color(result.result)))
        self.results_table.setItem(row, 1, status_item)
        
        # Input
        self.results_table.setItem(row, 2, QTableWidgetItem(result.input or "(none)"))
        
        # Expected
        self.results_table.setItem(row, 3, QTableWidgetItem(result.expected_output or "(none)"))
        
        # Actual
        actual = result.output or result.error or "(none)"
        self.results_table.setItem(row, 4, QTableWidgetItem(actual))

    def on_tests_finished(self, results):
        """Handle test completion."""
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶ Run Tests")
        
        # Calculate summary
        total = len(results)
        passed = sum(1 for _, _, r in results if r.result == ComparisonResult.MATCH)
        
        # Update summary label
        color = "#10b981" if passed == total else "#ef4444" if passed == 0 else "#f59e0b"
        self.summary_label.setText(f"{passed}/{total} Passed")
        self.summary_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        
        self.status_bar.showMessage(f"Tests completed: {passed}/{total} passed")

    def clear_results(self):
        """Clear the results table."""
        self.results_table.setRowCount(0)
        self.summary_label.setText("")

    @staticmethod
    def get_status_text(result):
        """Get human-readable status text."""
        if result == ComparisonResult.MATCH:
            return "✅ Passed"
        elif result == ComparisonResult.MISMATCH:
            return "❌ Failed"
        elif result == ComparisonResult.TIMEOUT:
            return "⏰ Timeout"
        elif result == ComparisonResult.EXECUTION_ERROR:
            return "⚠️ Error"
        return "Unknown"

    @staticmethod
    def get_status_color(result):
        """Get status color."""
        if result == ComparisonResult.MATCH:
            return "#10b981"
        elif result == ComparisonResult.MISMATCH:
            return "#ef4444"
        elif result == ComparisonResult.TIMEOUT:
            return "#64748b"
        return "#f59e0b"


def main(argv=None):
    """Main entry point for the GUI application."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="Testio GUI Application")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    args = parser.parse_args(argv)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow(config_path=args.config)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
