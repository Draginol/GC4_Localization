import os
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("XLIFF files", "*.xliff"), ("All files", "*.*")])
    return file_path

def select_directory():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    dir_path = filedialog.askdirectory()
    return dir_path

def update_xml_files(xliff_path, xml_dir):
    # Parse the XLIFF file
    xliff_tree = ET.parse(xliff_path)
    xliff_root = xliff_tree.getroot()

    for trans_unit in xliff_root.findall('.//trans-unit'):
        trans_unit_id = trans_unit.get('id')
        translated_text = trans_unit.find('target').text if trans_unit.find('target') is not None else ""

        # Search and update in each XML file
        for xml_file in os.listdir(xml_dir):
            if xml_file.endswith('.xml'):
                xml_file_path = os.path.join(xml_dir, xml_file)
                xml_tree = ET.parse(xml_file_path)
                xml_root = xml_tree.getroot()

                updated = False
                for string_table in xml_root.findall('.//StringTable'):
                    label = string_table.find('Label').text
                    if label == trans_unit_id:
                        string_table.find('String').text = translated_text
                        updated = True
                        break

                if updated:
                    xml_tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)

xliff_file = select_file()
xml_directory = select_directory()
update_xml_files(xliff_file, xml_directory)

print("Translation update completed.")
