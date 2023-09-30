
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
        for flavor_text_option in flavor_text_def.findall('.//FlavorTextOption'):
            # Extract the requirements specific to this FlavorTextOption
            requirements = []
            for req_element in flavor_text_option.findall('.//Requirements/*'):
                req_text = f"{req_element.tag}={req_element.text}"
                requirements.append(req_text)
            req_string = ";".join(requirements)


            # Use the requirements or fallback to filename
            meta_info = req_string if requirements else ""

            for idx, text_element in enumerate(flavor_text_option.findall('.//Text')):
                results.append((filepath, internal_name, idx + 1, text_element.text, meta_info))
    return results

def create_xliff_entry(file_name, internal_name, source_text, meta_info, internal_name_counter):
    # Increment the counter for the current internal_name or initialize it to 1 if not encountered before
    internal_name_counter[internal_name] = internal_name_counter.get(internal_name, 0) + 1
    unique_id = str(internal_name_counter[internal_name])
    
    # Create the trans-unit element for XLIFF with the unique ID and store InternalName as an attribute
    trans_unit = ET.Element("trans-unit", id=unique_id, internalName=internal_name)
    
    source = ET.SubElement(trans_unit, "source")
    source.text = source_text
    target = ET.SubElement(trans_unit, "target")
    target.text = source_text  # Placeholder, same as English for now

    # Add context-group for source file
    ##context_group = ET.SubElement(trans_unit, "context-group", purpose="location")
    ##context = ET.SubElement(context_group, "context", {'context-type': 'sourcefile'})
    ##context.text = file_name

    # Add note with meta-info (requirements)
    if meta_info:  # Only add the note if there's meta_info (i.e., requirements)
        note = ET.SubElement(trans_unit, "note")
        note.text = meta_info

    return trans_unit




def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    tk_root = tk.Tk()

    tk_root.withdraw()  # Hide the main window

    directory = filedialog.askdirectory(title="Select the directory with English Flavor Text")  # Show directory selection dialog
    if not directory:
        print("Directory selection was canceled.")
        return

    # GUI to ask for target language code
    target_language_code = simpledialog.askstring("Input", "Please enter the target language code (e.g., FR):", parent=tk_root)
    if not target_language_code:
        print("Language code input was canceled or empty.")
        return

    xliff = ET.Element("xliff", version="1.2", xmlns="urn:oasis:names:tc:xliff:document:1.2")
    file_elem = ET.SubElement(xliff, "file", {
        'original': 'not.available',  # Placeholder for now
        'source-language': 'EN',
        'target-language': target_language_code,
        'datatype': 'plaintext'
    })
    header = ET.SubElement(file_elem, "header")
    body = ET.SubElement(file_elem, "body")

    internal_name_counter = {}  # Initialize the counter dictionary

    # Iterate through each file in the directory and its sub-directories
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            extracted_entries = extract_text_with_meta(filepath)
            if extracted_entries:  # Check if any entries were extracted
                file_elem = ET.SubElement(xliff, "file", {
                    'original': filename,
                    'source-language': 'EN',
                    'target-language': target_language_code,
                    'datatype': 'plaintext'
                })
                body = ET.SubElement(file_elem, "body")
                for _, internal_name, text_index, text_content, meta_info in extracted_entries:
                    trans_unit = create_xliff_entry(filename, internal_name, text_content, meta_info, internal_name_counter)
                    body.append(trans_unit)


    # Ask user where to save the TMX file (only the directory)
    save_directory = filedialog.askdirectory(title="Select directory to save the XLIFF file")
    if not save_directory:
        print("Save directory selection was canceled.")
        return

    output_filename = os.path.join(save_directory, f"FlavorText_{target_language_code}.xliff")

    # Save the XLIFF to a file
    with open(output_filename, 'w', encoding="utf-8") as f:
        f.write(prettify(xliff))


if __name__ == "__main__":
    main()