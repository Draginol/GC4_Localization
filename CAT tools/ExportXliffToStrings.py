import sys
import os
from lxml import etree as ET  # Using lxml for better XML handling
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

def load_xliff(filepath):
    tree = ET.parse(filepath)
    translations = {}
    for trans_unit in tree.xpath('//trans-unit'):
        label = trans_unit.attrib.get('id')
        target = trans_unit.find('target')
        if label and target is not None:
            translations[label] = target.text
    return translations

def apply_translations_to_directory(translations, directory):
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.xml'):
                filepath = os.path.join(subdir, file)
                tree = ET.parse(filepath)
                modified = False
                for elem in tree.findall('StringTable'):
                    label_elem = elem.find('Label')
                    string_elem = elem.find('String')
                    if label_elem is not None and string_elem is not None and label_elem.text in translations:
                        string_elem.text = translations[label_elem.text]
                        modified = True
                if modified:
                    tree.write(filepath, pretty_print=True, encoding='utf-8')

def main():
    app = QApplication(sys.argv)
    xliff_filepath, _ = QFileDialog.getOpenFileName(None, "Select XLIFF file", "", "XLIFF Files (*.xliff);;All Files (*)")
    
    if not xliff_filepath:
        sys.exit(app.exec_())

    destination_directory = QFileDialog.getExistingDirectory(None, "Select destination directory for XML string files")
    
    if not destination_directory:
        sys.exit(app.exec_())

    translations = load_xliff(xliff_filepath)
    apply_translations_to_directory(translations, destination_directory)

    QMessageBox.information(None, "Success", "Translations applied successfully!")
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
