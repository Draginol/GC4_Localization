import sys
import subprocess

def install_module(module_name):
    """Install the given module using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])

# List of modules to check
required_modules = ["PyQt5", "openai","lxml"]

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f"{module} not found. Installing...")
        install_module(module)
import re
import os
import openai
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QWidget, QMessageBox,QInputDialog,QAction,QListWidget)
from PyQt5.QtCore import QSettings
from PyQt5 import sip
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt
from lxml import etree as ET  # Use lxml's ElementTree API
from concurrent.futures import ThreadPoolExecutor

import threading

openai.api_key = "Your OPENAI_API_KEY"


class CustomTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, file_path, label):
        super().__init__(text)
        self.file_path = file_path
        self.label = label

    def __hash__(self):
        return hash((self.file_path, self.label))

    def __eq__(self, other):
        if isinstance(other, CustomTableWidgetItem):
            return self.file_path == other.file_path and self.label == other.label
        return False

class TranslationApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Translation Tool")
        self.setGeometry(100, 100, 800, 600)
        self.settings = QSettings("Stardock", "XLIFFTranslator")  # Initialize the QSettings object
        self.current_file_path = None
        layout = QVBoxLayout()

        # Create Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Load English Directory Action
        load_action = QAction("Load XLIFF File", self)
        load_action.triggered.connect(self.load_directory)
        file_menu.addAction(load_action)

        # Save Translations Action
        save_action = QAction("Save XLIFF File", self)
        save_action.triggered.connect(self.save_to_file)
        file_menu.addAction(save_action)

        # Enter OpenAI Key Action
        openai_key_action = QAction("Enter OpenAI Key", self)
        openai_key_action.triggered.connect(self.set_openai_key)
        file_menu.addAction(openai_key_action)

        self.language_box = QComboBox(self)
        self.languages = ["English", "French", "German", "Russian", "Spanish", "Italian", "Portuguese", "Polish", "Korean", "Japanese", "Chinese"]
        self.language_box.addItems(self.languages)
        self.language_box.currentIndexChanged.connect(self.switch_language)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['File Name', 'Label', 'English', 'Translation'])
        self.table.setSortingEnabled(True)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemChanged.connect(self.update_translation)

        self.translate_button = QPushButton("Translate", self)
        self.translate_button.clicked.connect(self.perform_translation)

        layout.addWidget(self.language_box)
        layout.addWidget(self.table)
        layout.addWidget(self.translate_button)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.english_strings = {}
        self.changed_items = set()

        self.parent_directory = self.settings.value("last_directory", "..\\")

        # Retrieve and set the openai key if it exists
        openai_key = self.settings.value("openai_key", None)
        if openai_key:
            openai.api_key = openai_key

    def load_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open XLIFF File", self.parent_directory, "XLIFF Files (*.xliff);;All Files (*)", options=options)
        if file_name:
            # Save the directory of the selected file to QSettings
            directory = os.path.dirname(file_name)
            self.settings.setValue("last_directory", directory)
            self.parse_and_populate(file_name)
            self.current_file_path = file_name
    
    
    def update_translation(self, item):
        # Adjusted column index to check the modified Translation column
        if item.column() == 3:
            english_string = self.table.item(item.row(), 2).text()
            new_translation = item.text()

            for row in range(self.table.rowCount()):
                if self.table.item(row, 2) and self.table.item(row, 2).text() == english_string:
                    self.table.item(row, 3).setText(new_translation)

          
    def set_openai_key(self):
        # Open an input dialog to get the OpenAI key
        key, ok = QInputDialog.getText(self, 'OpenAI Key', 'Enter your OpenAI key:')
        if ok:
            # Set the key in the openai library
            openai.api_key = key
            # Store the key using QSettings
            self.settings.setValue("openai_key", key)
            # Optional: You can display a message saying the key has been set
            QMessageBox.information(self, "Success", "OpenAI Key has been set successfully!")

    
    def on_item_changed(self, item):
        if item.column() == 3:  # Check if the translation column was changed
            self.changed_items.add(item)

    def save_to_file(self):
        if not self.current_file_path:
            QMessageBox.warning(self, "Error", "No file is loaded.")
            return

        tree = ET.parse(self.current_file_path)
        root = tree.getroot()

        for row in range(self.table.rowCount()):
            file_name = self.table.item(row, 0).text()
            internal_name = self.table.item(row, 1).text()
            translation = self.table.item(row, 3).text()

            xpath_expr = f"file[@original='{file_name}']/body/trans-unit[@internalName='{internal_name}']/target"
            target_element = root.find(xpath_expr)
            if target_element is not None:
                target_element.text = translation

        tree.write(self.current_file_path, encoding='utf-8', xml_declaration=True)
        QMessageBox.information(self, "Success", "File has been saved successfully!")

        
    def load_directory(self):
        self.load_file()

    def populate_table(self):
        self.table.setRowCount(len(self.english_strings))
        self.table.itemChanged.disconnect(self.on_item_changed)
        self.table.itemChanged.disconnect(self.update_translation)

        for idx, ((file_name, label), (source_text, target_text)) in enumerate(self.english_strings.items()):
            self.table.setItem(idx, 0, QTableWidgetItem(file_name))
            self.table.setItem(idx, 1, QTableWidgetItem(label))
            self.table.setItem(idx, 2, CustomTableWidgetItem(source_text, file_name, label))
            self.table.setItem(idx, 3, CustomTableWidgetItem(target_text, file_name, label))

        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemChanged.connect(self.update_translation)

    def parse_and_populate(self, file_name):
        tree = ET.parse(file_name)
        root = tree.getroot()
        
        self.english_strings.clear()
        
        for file_tag in root.findall('file'):
            original_filename = file_tag.get('original')
            for trans_unit in file_tag.findall('body/trans-unit'):
                internal_name = trans_unit.get('internalName')
                source_text = trans_unit.find('source').text
                target_text = trans_unit.find('target').text
                
                # Use the tuple (original_filename, internal_name) as the key
                self.english_strings[(original_filename, internal_name)] = (source_text, target_text)
        
        self.populate_table()

    def switch_language(self):
        self.table.itemChanged.disconnect(self.on_item_changed)
        self.table.itemChanged.disconnect(self.update_translation)
        lang = self.language_box.currentText()
        
    def translate_to_language(self, text, row, target_language):
        label_item = self.table.item(row, 2)  # Assuming the Label column is at index 2
        label_name = label_item.text()
        prompt = f"In the context of a sci-fi game and given the label '{label_name}' to provide a bit of information, translate this English string, without using more words and respecting formatting codes into {target_language}: {text}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                n=1,
                stop=None,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in getting translation feedback: {e}")
            return None

    def perform_translation(self):
        translation_lock = threading.Lock()
        translation_counter = 0
        selected_rows = list(set(item.row() for item in self.table.selectedItems()))
        total_rows = len(selected_rows)

        # Create a QProgressDialog
        if total_rows > 4:
            progress = QProgressDialog("Please Wait...", None, 0, total_rows, self)
            progress.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()

        def translate_row(row): 
            print(f"Translating row {row} in thread {threading.current_thread().name}")
            english_text_item = self.table.item(row, 3)
            english_text = english_text_item.text()
            target_language = self.language_box.currentText()
            translated_text = self.translate_to_language(english_text, row, target_language)
            return row, translated_text

        # Split the rows into chunks
        CHUNK_SIZE = 10
        chunks = [selected_rows[i:i + CHUNK_SIZE] for i in range(0, len(selected_rows), CHUNK_SIZE)]

        for chunk in chunks:
            with ThreadPoolExecutor(max_workers=4) as executor:
                for idx, (row, translated_text) in enumerate(executor.map(translate_row, chunk), start=translation_counter):
                    translation_item = self.table.item(row, 3)
                    if not translation_item:
                        file_path = self.table.item(row, 0).text()
                        label = self.table.item(row, 2).text()
                        translation_item = CustomTableWidgetItem("", file_path, label)
                        self.table.setItem(row, 3, translation_item)

                    translation_item.setText(translated_text)

                    self.translate_button.setText(f"Translating {idx + 1} of {total_rows} entries")
                    if total_rows > 4:
                        progress.setValue(idx + 1)
                    QApplication.processEvents()

            # Save translations after each chunk
            if (translation_counter % 10) == 0:
                self.save_to_file()
            translation_counter += len(chunk)

        self.translate_button.setText("Translate")
        if total_rows > 4:
            progress.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = TranslationApp()
    mainWin.show()
    sys.exit(app.exec_())
