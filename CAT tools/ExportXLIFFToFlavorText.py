import os
import shutil
import tkinter as tk
from tkinter import filedialog
from lxml import etree as ET

def save_with_crlf(tree, filepath):
    xml_string = ET.tostring(tree, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_string)

def load_xliff_data(xliff_path):
    tree = ET.parse(xliff_path)
    root = tree.getroot()
    
    xliff_dict = {}
    for file_node in root.findall(".//file"):
        filename = file_node.attrib['original']
        xliff_dict[filename] = []

        for trans_unit in file_node.findall(".//trans-unit"):
            source_text = trans_unit.find("source").text
            target_text = trans_unit.find("target").text
            internal_name = trans_unit.attrib.get('internalName', '')

            xliff_dict[filename].append({
                'internalName': internal_name,
                'source': source_text,
                'target': target_text
            })
    
    return xliff_dict

def update_xml_file_from_xliff(src_directory, dest_directory, filename, xliff_entries):
    src_filepath = os.path.join(src_directory, filename)
    dest_filepath = os.path.join(dest_directory, filename)

    if not os.path.exists(src_filepath):
        print(f"Source file not found: {src_filepath}")
        return

    shutil.copy2(src_filepath, dest_filepath)

    dest_tree = ET.parse(dest_filepath)
    dest_root = dest_tree.getroot()

    for xliff_entry in xliff_entries:
        internal_name = xliff_entry['internalName']
        source_text = xliff_entry['source'][:70]  # Consider only the first 70 characters
        target_text = xliff_entry['target']

        for flavor_text_def in dest_root.findall(f".//FlavorTextDef[InternalName='{internal_name}']"):
            for text_element in flavor_text_def.findall('.//Text'):
                if text_element.text and text_element.text.startswith(source_text):
                    text_element.text = target_text
                    break

    save_with_crlf(dest_tree, dest_filepath)


def main():
    tk_root = tk.Tk()
    tk_root.withdraw()

    xliff_path = filedialog.askopenfilename(title="Select the XLIFF file")
    if not xliff_path:
        print("XLIFF file selection was canceled.")
        return

    base_dir = os.path.dirname(xliff_path)
    src_directory = os.path.join(base_dir, "../english/text")
    dest_directory = os.path.join(base_dir, "Text")

    xliff_data = load_xliff_data(xliff_path)

    for filename, xliff_entries in xliff_data.items():
        update_xml_file_from_xliff(src_directory, dest_directory, filename, xliff_entries)

    print("Flavor text XML files updated successfully!")

if __name__ == "__main__":
    main()
