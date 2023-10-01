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
    
    for trans_unit in root.findall(".//trans-unit"):
        source_text = trans_unit.find("source").text
        target_text = trans_unit.find("target").text
        xliff_dict[source_text] = target_text
    
    return xliff_dict

def update_xml_files_from_xliff(copied_files, dest_directory, xliff_data):
    for filename in copied_files:
        dest_filepath = os.path.join(dest_directory, filename)
            
        tree = ET.parse(dest_filepath)
        root = tree.getroot()

        for flavor_text_def in root.findall('.//FlavorTextDef'):
            for flavor_text_option in flavor_text_def.findall('.//FlavorTextOption'):
                for text_element in flavor_text_option.findall('.//Text'):
                    if text_element.text in xliff_data:
                        text_element.text = xliff_data[text_element.text]

        save_with_crlf(tree, dest_filepath)  # Using the function to save with CRLF


def main():
    tk_root = tk.Tk()
    tk_root.withdraw()

    xliff_path = filedialog.askopenfilename(title="Select the XLIFF file")
    if not xliff_path:
        print("XLIFF file selection was canceled.")
        return

    src_directory = filedialog.askdirectory(title="Select the directory with the English flavor text XML files")
    if not src_directory:
        print("Source directory selection was canceled.")
        return

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
