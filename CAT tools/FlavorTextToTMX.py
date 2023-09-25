import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import simpledialog, filedialog
from xml.dom import minidom

def extract_text_with_meta(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    root = ET.fromstring(content)
    results = []
    for flavor_text_def in root.findall('.//FlavorTextDef'):
        internal_name = flavor_text_def.find('InternalName').text
        for idx, text_element in enumerate(flavor_text_def.findall('.//FlavorTextOption/Text')):
            results.append((internal_name, idx + 1, text_element.text))
    return results

def create_tmx_entry(internal_name, text_index, source_text, target_language_code):
    tu = ET.Element("tu")
    prop_name = ET.SubElement(tu, "prop", type="InternalName")
    prop_name.text = internal_name
    prop_index = ET.SubElement(tu, "prop", type="TextIndex")
    prop_index.text = str(text_index)

    tuv_en = ET.SubElement(tu, "tuv", {'xml:lang': 'EN'})
    seg_en = ET.SubElement(tuv_en, "seg")
    seg_en.text = source_text

    tuv_target = ET.SubElement(tu, "tuv", {'xml:lang': target_language_code})
    seg_target = ET.SubElement(tuv_target, "seg")
    seg_target.text = source_text  # Same content as English, ready for translation

    return tu

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    directory = filedialog.askdirectory(title="Select a directory")  # Show directory selection dialog
    if not directory:
        print("Directory selection was canceled.")
        return

    # GUI to ask for target language code
    target_language_code = simpledialog.askstring("Input", "Please enter the target language code (e.g., FR):", parent=root)
    if not target_language_code:
        print("Language code input was canceled or empty.")
        return

    # Create the root TMX structure
    tmx = ET.Element("tmx", version="1.4")
    header = ET.SubElement(tmx, "header", {
        'creationtool': 'CustomTMXTool', 'creationtoolversion': '1.0',
        'datatype': 'plaintext', 'segtype': 'sentence',
        'adminlang': 'en-us', 'srclang': 'EN', 'o-tmf': 'PlainText'
    })
    body = ET.SubElement(tmx, "body")

    # Iterate through each file in the directory and its sub-directories
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            for internal_name, text_index, text_content in extract_text_with_meta(filepath):
                tu = create_tmx_entry(internal_name, text_index, text_content, target_language_code)
                body.append(tu)

    # Ask user where to save the TMX file (only the directory)
    save_directory = filedialog.askdirectory(title="Select directory to save the TMX file")
    if not save_directory:
        print("Save directory selection was canceled.")
        return

    output_filename = os.path.join(save_directory, f"FlavorText_{target_language_code}.tmx")

    # Save the TMX to a file
    with open(output_filename, 'w', encoding="utf-8") as f:
        f.write(prettify(tmx))

if __name__ == "__main__":
    main()
