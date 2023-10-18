import sys
import os
from lxml import etree as ET  # Using lxml for better XML handling
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox

def load_xliff(filepath):
    tree = ET.parse(filepath)
    translations = {}
    for trans_unit in tree.xpath('//trans-unit'):
        label = trans_unit.attrib.get('resname')  # Use 'resname' instead of 'id'
        target = trans_unit.find('target')
        if label and target is not None:
            translations[label] = target.text
    return translations

def save_with_crlf(tree, filepath):
    """Save XML with CRLF line endings and with pretty printing."""
    xml_string = ET.tostring(tree, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_string)

def apply_translations_to_directory(translations, directory):
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.xml'):
                filepath = os.path.join(subdir, file)
                try:
                    # Read the XML content
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse the XML content
                    tree = ET.fromstring(content)
                    modified = False
                    
                    for elem in tree.findall('StringTable'):
                        label_elem = elem.find('Label')
                        string_elem = elem.find('String')
                        if label_elem is not None and string_elem is not None and label_elem.text in translations:
                            string_elem.text = translations[label_elem.text]
                            modified = True
                    
                    # Write the modified XML content back to the file
                    if modified:
                        save_with_crlf(tree, filepath)
                except Exception as e:
                    print(f"Error processing file {filepath}: {e}")




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
