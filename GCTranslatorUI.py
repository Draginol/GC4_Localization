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

        layout = QVBoxLayout()

        # Create Menu Bar
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Load English Directory Action
        load_action = QAction("Load English Directory", self)
        load_action.triggered.connect(self.load_directory)
        file_menu.addAction(load_action)

        # Save Translations Action
        save_action = QAction("Save Translations", self)
        save_action.triggered.connect(self.save_translations)
        file_menu.addAction(save_action)

        # Adding Language Memory View action to File menu
        self.language_memory_view_action = QAction("Language Memory View", self)
        self.language_memory_view_action.triggered.connect(self.show_language_memory)
        file_menu.addAction(self.language_memory_view_action)

        # Enter OpenAI Key Action
        openai_key_action = QAction("Enter OpenAI Key", self)
        openai_key_action.triggered.connect(self.set_openai_key)
        file_menu.addAction(openai_key_action)

        

        self.language_box = QComboBox(self)
        self.languages = ["English", "French", "German", "Russian", "Spanish", "Italian", "Portuguese", "Polish", "Korean", "Japanese", "Chinese"]
        self.language_box.addItems(self.languages)
        self.language_box.currentIndexChanged.connect(self.switch_language)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['File Name', 'Translated File Name', 'Label', 'English', 'Translation'])
        self.table.setSortingEnabled(True)
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemChanged.connect(self.update_translation)


        self.translate_button = QPushButton("Translate (OpenAI)", self)
        self.translate_button.clicked.connect(self.perform_translation)

        layout.addWidget(self.language_box)
        layout.addWidget(self.table)
        layout.addWidget(self.translate_button)

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

        # Retrieve and set the openai key if it exists
        openai_key = self.settings.value("openai_key", None)
        if openai_key:
            openai.api_key = openai_key

    def import_from_tmx(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "TMX Files (*.tmx);;All Files (*)", options=options)
        
        if file_name:
            with open(file_name, 'r', encoding='utf-8') as file:
                content = file.read()
                # Replace unescaped & characters with &amp;
                adjusted_content = content.replace("&", "&amp;")

            # Parse the adjusted content
            root = ET.fromstring(adjusted_content.encode('utf-8'))

            # Clear the current content of the table
            self.table_widget.setRowCount(0)

            # Extract source (English) and target translations and populate the table
            for tu in root.xpath('//tu'):
                english_text = tu.xpath('./tuv[@xml:lang="EN"]/seg/text()')
                translated_text = tu.xpath('./tuv[not(@xml:lang="EN")]/seg/text()')

                # Convert &amp; back to & for displaying in the application
                if english_text:
                    english_text[0] = english_text[0].replace("&amp;", "&")
                if translated_text:
                    translated_text[0] = translated_text[0].replace("&amp;", "&")

                if english_text and translated_text:
                    row_position = self.table_widget.rowCount()
                    self.table_widget.insertRow(row_position)
                    self.table_widget.setItem(row_position, 0, QTableWidgetItem(english_text[0]))
                    self.table_widget.setItem(row_position, 1, QTableWidgetItem(translated_text[0]))

        # Function to show unique English text entries along with their translations
    def show_language_memory(self):

        # Fetching all English entries and their translations from the table
        english_entries = [self.table.item(row, 3).text() for row in range(self.table.rowCount()) if self.table.item(row, 3)]
        translations = [self.table.item(row, 4).text() for row in range(self.table.rowCount()) if self.table.item(row, 4)]
        
        # Creating a dictionary with unique English entries as keys and their translations as values
        english_translation_dict = dict(zip(english_entries, translations))

        # Displaying the unique entries along with their translations in a new window
        self.memory_window = QWidget()
        self.memory_window.setWindowTitle("Language Memory View")
        layout = QVBoxLayout(self.memory_window)
        
        # Creating a table widget with two columns
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(['English', 'Translation'])
        self.table_widget.setSortingEnabled(True)

        # Add an "Import from TMX" button
        import_from_tmx_button = QPushButton("Import from TMX")
        import_from_tmx_button.clicked.connect(self.import_from_tmx)
        layout.addWidget(import_from_tmx_button)

        # Add an "Export to TMX" button
        export_to_tmx_button = QPushButton("Export to TMX")
        export_to_tmx_button.clicked.connect(self.export_to_tmx)
        layout.addWidget(export_to_tmx_button)


        self.table_widget.itemChanged.connect(self.update_main_from_memory)
        self.table.itemChanged.connect(self.update_translation)
        
        self.table_widget.itemChanged.disconnect(self.update_main_from_memory)
        self.table.itemChanged.disconnect(self.update_translation)
        
        # Populating the table widget with data
        for index, (english, translation) in enumerate(english_translation_dict.items()):
            self.table_widget.insertRow(index)
            self.table_widget.setItem(index, 0, QTableWidgetItem(english))
            self.table_widget.setItem(index, 1, QTableWidgetItem(translation))
        
        layout.addWidget(self.table_widget)
        self.memory_window.show()
        # Connecting signal to detect changes in the translation memory table
        self.table_widget.itemChanged.connect(self.update_main_from_memory)
        self.table.itemChanged.connect(self.update_translation)
        
    def export_to_tmx(self):
        # Fetch the selected language from the combo box
        target_language_code = self.language_box.currentText()  # Assuming the combo box object's name is language_combobox
        # Create the start and end of the basic TMX structure
        tmx_start = '''<?xml version="1.0" encoding="UTF-8"?>
    <tmx version="1.4">
    <header creationtool="GCTranslatorUI" segtype="sentence" adminlang="en-us" srclang="EN" datatype="plaintext" o-tmf="GCTranslatorUI" creationdate="yyyymmddT00:00:00Z" nontrans="yes"/>
    <body>
    '''
        tmx_end = '''
    </body>
    </tmx>
    '''

        # Extract the English text and its corresponding translation to create the TMX content
        translation_units = []
        for row in range(self.table_widget.rowCount()):
            english_text = self.table_widget.item(row, 0).text()
            translated_text = self.table_widget.item(row, 1).text()
            translation_units.append('''
        <tu>
        <tuv xml:lang="EN">
            <seg>''' + english_text + '''</seg>
        </tuv>
        <tuv xml:lang="''' + target_language_code + '''">  
            <seg>''' + translated_text + '''</seg>
        </tuv>
        </tu>
    ''')

        tmx_content = tmx_start + "".join(translation_units) + tmx_end

        # Save the TMX content to a file using a file dialog
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()", "","TMX Files (*.tmx);;All Files (*)", options=options)
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as file:
                file.write(tmx_content)



    def update_translation(self, item):
        # Checking if the modified item is from the Translation column

        if item.tableWidget() == self.table:
            return

        if item.column() == 4:
            # Fetching the English string corresponding to the modified translation
            english_string = self.table.item(item.row(), 3).text()
            new_translation = item.text()

            # Iterating over the main table to find and update rows with the same English string
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == english_string:
                    self.table.item(row, 4).setText(new_translation)

    
    
    # Function to update the main table and memory view based on changes in the translation memory table
    def update_main_from_memory(self, item):
        # Checking if the modified item is from the Translation column of the memory table
        if item.column() == 1:
            # Fetching the English string corresponding to the modified translation in the memory table
            english_string = self.table_widget.item(item.row(), 0).text()
            new_translation = item.text()

            # Iterating over the main table and the memory table to find and update rows with the same English string
            for row in range(self.table.rowCount()):
                if self.table.item(row, 3) and self.table.item(row, 3).text() == english_string:
                    self.table.item(row, 4).setText(new_translation)
            
            for row in range(self.table_widget.rowCount()):
                if self.table_widget.item(row, 0) and self.table_widget.item(row, 0).text() == english_string:
                    self.table_widget.item(row, 1).setText(new_translation)

          
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
        self.table.itemChanged.disconnect(self.update_translation)

        for idx, ((file_name, label), (string, file_path)) in enumerate(self.english_strings.items()):
            self.table.setItem(idx, 0, QTableWidgetItem(file_name))
            # Initialize the Translated File Name column as empty for now
            self.table.setItem(idx, 1, QTableWidgetItem(""))  
            self.table.setItem(idx, 2, QTableWidgetItem(label))
            self.table.setItem(idx, 3, QTableWidgetItem(string))
            self.table.setItem(idx, 4, CustomTableWidgetItem(string, file_path, label))  # Default to English for the translation
        self.table.itemChanged.connect(self.on_item_changed)
        self.table.itemChanged.connect(self.update_translation)


    def switch_language(self):
        self.table.itemChanged.disconnect(self.on_item_changed)
        self.table.itemChanged.disconnect(self.update_translation)
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
        self.table.itemChanged.connect(self.update_translation)


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

        self.translate_button.setText("Translate via OpenAI")
        if total_rows > 4:
            progress.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = TranslationApp()
    mainWin.show()
    sys.exit(app.exec_())
