import xml.etree.ElementTree as ET
import os
import tkinter as tk
from tkinter import filedialog



def load_xliff_data(xliff_path):
    tree = ET.parse(xliff_path)
    root = tree.getroot()

    entries = {}

    for trans_unit in root.findall(".//trans-unit"):
        internal_name = trans_unit.attrib["internalName"]

        # Parse the requirements string into the same format as we did for the flavor text xml.
        note_element = trans_unit.find("note")
        requirements = note_element.text if note_element is not None else ""
        req_list = sorted(requirements.split(";"))
        req_string = ";".join(req_list)

        
        # Since the requirements are semi-colon separated, we will split and sort them to ensure consistency.
        req_list = sorted(requirements.split(";"))
        req_string = ";".join(req_list)

        # Create the lookup key
        key = (internal_name, req_string)

        if key not in entries:
            entries[key] = []

        entries[key].append(trans_unit.find("target"))

    return entries, root


def update_xliff_from_xml(directory, xliff_entries):
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            tree = ET.parse(filepath)
            root = tree.getroot()

            for flavor_text_def in root.findall('.//FlavorTextDef'):
                internal_name = flavor_text_def.find('InternalName').text
                flavor_text_options = flavor_text_def.findall('.//FlavorTextOption')

                for flavor_text_option in flavor_text_options:
                    # Extract requirements
                    requirements = flavor_text_option.findall('.//Requirements/*')
                    req_dict = {}
                    for requirement in requirements:
                        req_dict[requirement.tag] = requirement.text
                    req_list = [f"{k}={v}" for k, v in sorted(req_dict.items())]
                    req_string = ";".join(req_list)

                    # Extract all text elements
                    text_elements = flavor_text_option.findall('.//Text')

                    # For each text element, fetch the target and update it
                    key = (internal_name, req_string)
                    targets = xliff_entries.get(key, [])
                    for idx, text_element in enumerate(text_elements):
                        if idx < len(targets):
                            targets[idx].text = text_element.text
                        else:
                            print(f"No match found for key: {key} at index {idx}")


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element without excessive newlines."""
    from xml.dom import minidom
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_str = reparsed.toprettyxml(indent="  ")
    return '\n'.join([line for line in pretty_str.split('\n') if line.strip()])

def sanitize_requirements(req_string):
    requirements = [req.strip() for req in req_string.split(';') if req.strip()]
    return ";".join(sorted(requirements))


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

    xliff_entries, xliff_root = load_xliff_data(xliff_path)
    update_xliff_from_xml(directory, xliff_entries)

    
    # Save the updated XLIFF data using xliff_root
    with open(xliff_path, 'w', encoding="utf-8") as f:
        f.write(prettify_xml(xliff_root).replace("ns0:", ""))

    print("XLIFF file updated successfully!")

if __name__ == "__main__":
    main()
