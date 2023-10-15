import os
import shutil
import tkinter as tk
from tkinter import filedialog
from lxml import etree as ET  # Using lxml instead of xml.etree

def save_with_crlf(tree, filepath):
    """Save XML with CRLF line endings and with pretty printing."""
    xml_string = ET.tostring(tree, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(xml_string)

def load_xliff_data(xliff_path):
    tree = ET.parse(xliff_path)
    root = tree.getroot()
    
    xliff_dict = {}
    
    for file_node in root.findall(".//file"):
        filename = file_node.attrib['original']

        for trans_unit in file_node.findall(".//trans-unit"):
            source_text = trans_unit.find("source").text
            target_text = trans_unit.find("target").text
            internal_name = trans_unit.attrib.get('internalName', '')
            id_number = trans_unit.attrib.get('id', '0')

            # Store filename, internalName, id, and target in the dictionary
            xliff_dict[source_text] = {
                'filename': filename,
                'internalName': internal_name,
                'id': id_number,
                'target': target_text
            }
    
    return xliff_dict


def update_xml_files_from_xliff(copied_files, dest_directory, xliff_data):
    for filename in copied_files:
        dest_filepath = os.path.join(dest_directory, filename)
        tree = ET.parse(dest_filepath)
        root = tree.getroot()

        for flavor_text_def in root.findall('.//FlavorTextDef'):
            internal_name = flavor_text_def.find('.//InternalName').text
            flavor_text_options = flavor_text_def.findall('.//FlavorTextOption')

            for flavor_text_option in flavor_text_options:
                text_elements = flavor_text_option.findall('.//Text')
                
                for i, text_element in enumerate(text_elements):
                    # Try direct match with source text first
                    matched_entry = None
                    for source_text, xliff_entry in xliff_data.items():
                        if source_text == text_element.text:
                            matched_entry = xliff_entry
                            break

                    if matched_entry:
                        text_element.text = matched_entry['target']
                    else:
                        # If no direct match, use the id to match and replace
                        matching_keys = [key for key, value in xliff_data.items() if value.get('filename') == filename and value.get('internalName') == internal_name and int(value.get('id')) == i+1]
                        if matching_keys:
                            text_element.text = xliff_data[matching_keys[0]]['target']

        save_with_crlf(tree, dest_filepath)  # Using the function to save with CRLF


def main():
    tk_root = tk.Tk()
    tk_root.withdraw()

    xliff_path = filedialog.askopenfilename(title="Select the XLIFF file")
    if not xliff_path:
        print("XLIFF file selection was canceled.")
        return

    # Derive the English directory path from the selected XLIFF file path
    base_dir = os.path.dirname(xliff_path)
    src_directory = os.path.join(base_dir, "../english/text")

    dest_directory = filedialog.askdirectory(title="Select the destination directory for translated flavor text XML")
    if not dest_directory:
        print("Destination directory selection was canceled.")
        return

    copied_files = []

    # Copying only XML files with <FlavorTextDefs> root from source to destination and making them writable
    for item in os.listdir(src_directory):
        s = os.path.join(src_directory, item)
        d = os.path.join(dest_directory, item)
        
        # Checking if the XML file has <FlavorTextDefs> as root
        tree = ET.parse(s)
        root = tree.getroot()
        if root.tag == "FlavorTextDefs":
            shutil.copy2(s, d)
            os.chmod(d, 0o777)  # set the file's permission to be writable
            copied_files.append(item)

    xliff_data = load_xliff_data(xliff_path)
    update_xml_files_from_xliff(copied_files, dest_directory, xliff_data)

    print("Flavor text XML files updated successfully!")

if __name__ == "__main__":
    main()
