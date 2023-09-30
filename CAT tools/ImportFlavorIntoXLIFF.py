import xml.etree.ElementTree as ET
import os
import tkinter as tk
from tkinter import filedialog



def load_xliff_data(xliff_path):
    tree = ET.parse(xliff_path)
    root = tree.getroot()

    entries = {}
    order = []

    name_counter = {}  # This dictionary will help track the count of trans-units with the same internalName

    for trans_unit in root.findall(".//trans-unit"):
        internal_name = trans_unit.attrib["internalName"]

        # Update the count for the current internalName
        if internal_name in name_counter:
            name_counter[internal_name] += 1
        else:
            name_counter[internal_name] = 1

        count = name_counter[internal_name]  # Use the current count for this internalName

        note_element = trans_unit.find("note")
        requirements = note_element.text if note_element is not None else ""

        key = (internal_name, count, requirements)
        if key not in entries:
            entries[key] = []
        entries[key].append(trans_unit.find("target"))
        order.append(key)

    return entries, root, order


def update_xliff_from_xml(directory, xliff_entries):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            tree = ET.parse(filepath)
            root = tree.getroot()

            for flavor_text_def in root.findall('.//FlavorTextDef'):
                internal_name = flavor_text_def.find('InternalName').text

                for idx, flavor_text_option in enumerate(flavor_text_def.findall('.//FlavorTextOption')):
                    requirements = []
                    for req_element in flavor_text_option.findall('.//Requirements/*'):
                        req_text = f"{req_element.tag}={req_element.text}"
                        requirements.append(req_text)
                    req_string = ";".join(requirements)

                    for text_element in flavor_text_option.findall('.//Text'):
                        translated_text = text_element.text

                        lookup_key = (internal_name, idx+1, req_string if requirements else "")
                        target_elements = xliff_entries.get(lookup_key)

                        if target_elements:
                            for target_element in target_elements:
                                target_element.text = translated_text
                        else:
                            print(f"No match found for key: {lookup_key}")

def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element without excessive newlines."""
    from xml.dom import minidom
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_str = reparsed.toprettyxml(indent="  ")
    return '\n'.join([line for line in pretty_str.split('\n') if line.strip()])



def main():
    tk_root = tk.Tk()
    tk_root.withdraw()

    xliff_path = filedialog.askopenfilename(title="Select the XLIFF file to update")
    if not xliff_path:
        print("XLIFF file selection was canceled.")
        return

    directory = filedialog.askdirectory(title="Select the directory containing the XML files to import from")
    if not directory:
        print("Directory selection was canceled.")
        return

    xliff_entries, xliff_root, order = load_xliff_data(xliff_path)
    update_xliff_from_xml(directory, xliff_entries)
    
    # Save the updated XLIFF data using xliff_root
    with open(xliff_path, 'w', encoding="utf-8") as f:
        f.write(prettify_xml(xliff_root).replace("ns0:", ""))

    print("XLIFF file updated successfully!")

if __name__ == "__main__":
    main()
