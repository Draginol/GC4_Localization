import sys
import subprocess

def install_module(module_name):
    """Install the given module using pip."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])

# List of modules to check
required_modules = ["PyQt5", "openai","lxml","subprocess","threading"]

for module in required_modules:
    try:
        __import__(module)
    except ImportError:
        print(f"{module} not found. Installing...")
        install_module(module)

import os
import openai
from xml.etree import ElementTree as ET
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QPushButton, QFileDialog, QComboBox, QWidget, QMessageBox,QInputDialog)
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

        layout = QVBoxLayout()

        self.language_box = QComboBox(self)
        self.languages = ["English", "French", "German", "Russian", "Spanish", "Italian", "Portuguese", "Polish", "Korean", "Japanese", "Chinese"]
        self.language_box.addItems(self.languages)
        self.language_box.currentIndexChanged.connect(self.switch_language)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['File Name', 'Translated File Name', 'Label', 'English', 'Translation'])
        # Enable sorting on the QTableWidget
        self.table.setSortingEnabled(True)
        
        self.table.itemChanged.connect(self.on_item_changed)

        self.load_button = QPushButton("Load English Directory", self)
        self.load_button.clicked.connect(self.load_directory)

        self.save_button = QPushButton("Save Translations", self)
        self.save_button.clicked.connect(self.save_translations)

        self.translate_button = QPushButton("Translate", self)
        self.translate_button.clicked.connect(self.perform_translation)
        layout.addWidget(self.load_button)
        layout.addWidget(self.translate_button)


        
        layout.addWidget(self.language_box)
        layout.addWidget(self.table)
        layout.addWidget(self.save_button)

        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.english_strings = {}
        self.changed_items = set()

        self.parent_directory = ""
        self.settings = QSettings("Stardock", "GC4Translator")
        last_directory = self.settings.value("last_directory", "H:\\Projects\\GC4\\GalCiv4\\Game\\Data\\English")
        if os.path.exists(last_directory):
            self.parent_directory = last_directory

        # Add the OpenAI Key button
        self.openai_key_button = QPushButton("Enter OpenAI Key", self)
        self.openai_key_button.clicked.connect(self.set_openai_key)
        layout.addWidget(self.openai_key_button)

        # Retrieve and set the openai key if it exists
        openai_key = self.settings.value("openai_key", None)
        if openai_key:
            openai.api_key = openai_key

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
        if item.column() == 4:  # Check if the translation column was changed
            self.changed_items.add(item)

    def save_translations(self):
        import html  # Ensure this import is at the top
        file_updates = {}

        print(f"Saving files...")
        # Group items by file path
        for item in self.changed_items:
            if sip.isdeleted(item):  # Check if the item is still valid
                continue
            
            # Retrieve the file path from the "Translated File Name" column
            trans_file_path_item = self.table.item(item.row(), 1)
            
            # If the cell is empty, skip this item
            if not trans_file_path_item or not trans_file_path_item.text():
                continue
            
            selected_language = self.language_box.currentText()
            trans_directory = os.path.join(self.parent_directory, selected_language, "text")
            trans_file_path = os.path.join(trans_directory, trans_file_path_item.text())


            if trans_file_path not in file_updates:
                file_updates[trans_file_path] = []

            file_updates[trans_file_path].append(item)

        num_changed_files = len(file_updates)

        if num_changed_files > 3:
            # Create a QProgressDialog for saving
            progress = QProgressDialog("Saving translations...", None, 0, num_changed_files, self)
            progress.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            progress.setWindowModality(Qt.WindowModal)  # This will block the main window
            progress.show()

        current_file_count = 0

        # For each file, make a single pass and update translations
        for file_path, items in file_updates.items():
            parser = ET.XMLParser(remove_blank_text=True)  # Use lxml's parser
            tree = ET.parse(file_path, parser)  # Use the parser
            # Set the attributes on the root element
            root = tree.getroot()

            default_ns = root.nsmap[None] if None in root.nsmap else None

            namespaces = {
                'xsi': "http://www.w3.org/2001/XMLSchema-instance"
            }
            if default_ns:
                namespaces[None] = default_ns
            root.set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation", "../../Schema/Lib/StringTable.xsd")

            for item in items:
                for elem in tree.findall('StringTable'):
                    if elem.find('Label').text == item.label:
                        fixed_text = html.unescape(item.text())  # Decode the entities
                        elem.find('String').text = fixed_text
            
            try:
                xml_content = ET.tostring(tree, pretty_print=True, encoding='utf-8', xml_declaration=True)
                
                # Decode the XML content
                xml_str = xml_content.decode('utf-8')

                xml_str = xml_str.replace('\r\n', '\r')
                
                xml_str = xml_str.replace('\r', '\r\n')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
            except PermissionError:
                QMessageBox.warning(self, "Error", f"Permission denied when trying to write to {file_path}")
                return

            current_file_count += 1
            if num_changed_files > 3:
                # Update the progress dialog
                progress.setValue(current_file_count)
                QApplication.processEvents()  # Process events to update the UI immediately

        # Close the progress dialog if it was shown
        if num_changed_files > 3:
            progress.close()

        self.changed_items.clear()

    def load_directory(self):
        default_directory = "H:\\Projects\\GC4\\GalCiv4\\Game\\Data\\English"
        
        # If self.parent_directory is set, use it; otherwise, use the default_directory
        starting_directory = self.parent_directory if self.parent_directory else default_directory

        directory = QFileDialog.getExistingDirectory(self, "Select English Directory", starting_directory)
        
        if directory:
            self.parent_directory = os.path.dirname(directory)
            self.settings.setValue("last_directory", directory)

            for subdir, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".xml"):
                        file_path = os.path.join(subdir, file)
                        file_name = os.path.basename(file_path)
                        tree = ET.parse(file_path)
                        for elem in tree.findall('StringTable'):
                            label = elem.find('Label').text
                            string = elem.find('String').text
                            self.english_strings[(file_name, label)] = (string, file_path)  # Store with filename and label

            self.populate_table()



    def populate_table(self):
        self.table.setRowCount(len(self.english_strings))
        self.table.itemChanged.disconnect(self.on_item_changed)

        for idx, ((file_name, label), (string, file_path)) in enumerate(self.english_strings.items()):
            self.table.setItem(idx, 0, QTableWidgetItem(file_name))
            # Initialize the Translated File Name column as empty for now
            self.table.setItem(idx, 1, QTableWidgetItem(""))  
            self.table.setItem(idx, 2, QTableWidgetItem(label))
            self.table.setItem(idx, 3, QTableWidgetItem(string))
            self.table.setItem(idx, 4, CustomTableWidgetItem(string, file_path, label))  # Default to English for the translation
        self.table.itemChanged.connect(self.on_item_changed)


    def switch_language(self):
        self.table.itemChanged.disconnect(self.on_item_changed)
        lang = self.language_box.currentText()
        if lang != "English":
            sibling_directory = os.path.join(self.parent_directory, lang, "text") # Construct the path for translated files
            translations = {}

            for subdir, _, files in os.walk(sibling_directory):
                for file in files:
                    if file.endswith(".xml"):
                        file_path = os.path.join(subdir, file)
                        tree = ET.parse(file_path)
                        for elem in tree.findall('StringTable'):
                            label = elem.find('Label').text
                            string = elem.find('String').text
                            translations[label] = (string, file_path)

            for idx, (file_name, label) in enumerate(self.english_strings.keys()):
                translation, trans_file_path = translations.get(label, (self.english_strings[(file_name, label)][0], self.english_strings[(file_name, label)][1]))
                # Set the translated file name in the 2nd column
                self.table.setItem(idx, 1, QTableWidgetItem(os.path.basename(trans_file_path)))
                self.table.setItem(idx, 4, CustomTableWidgetItem(translation, trans_file_path, label))
        self.table.itemChanged.connect(self.on_item_changed)


    def translate_to_language(self, text, row, target_language):
        label_item = self.table.item(row, 2)  # Assuming the Label column is at index 2
        label_name = label_item.text()
        prompt = f"In the context of a sci-fi game and given the label '{label_name}', translate this English string, without using more words and respecting formatting codes into {target_language}: {text}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
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
                    translation_item = self.table.item(row, 4)
                    if not translation_item:
                        file_path = self.table.item(row, 0).text()
                        label = self.table.item(row, 2).text()
                        translation_item = CustomTableWidgetItem("", file_path, label)
                        self.table.setItem(row, 4, translation_item)

                    translation_item.setText(translated_text)

                    self.translate_button.setText(f"Translating {idx + 1} of {total_rows} entries")
                    if total_rows > 4:
                        progress.setValue(idx + 1)
                    QApplication.processEvents()

            # Save translations after each chunk
            self.save_translations()
            translation_counter += len(chunk)

        self.translate_button.setText("Translate")
        if total_rows > 4:
            progress.close()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = TranslationApp()
    mainWin.show()
    sys.exit(app.exec_())
