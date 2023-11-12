import os
import xml.etree.ElementTree as ET
import csv
from tkinter import Tk
from tkinter.filedialog import askdirectory

def find_xml_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".xml"):
                yield os.path.join(root, file)

def parse_xml_for_internal_names_and_text(file_path):
    internal_names_dict = {}
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for ftd in root.findall('.//FlavorTextDef'):
            internal_name = ftd.find('InternalName')
            text_element = ftd.find('.//FlavorTextOption/Text')
            if internal_name is not None and text_element is not None:
                internal_names_dict[internal_name.text] = text_element.text
        return internal_names_dict
    except ET.ParseError:
        return {}
    except FileNotFoundError:
        return {}

def find_xliff_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith("FlavorText_") and file.endswith(".xliff"):
                yield os.path.join(root, file)

def check_xliff_file(file_path, internal_names_dict):
    discrepancies = []
    xliff_internal_names = set()
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for file in root.findall('.//file'):
            for unit in file.findall('.//trans-unit'):
                internal_name = unit.get('internalName')
                if internal_name:
                    xliff_internal_names.add(internal_name)
                    if unit.get('id') == '1':
                        source_text = unit.find('source').text
                        if internal_name in internal_names_dict and source_text != internal_names_dict[internal_name]:
                            discrepancies.append((internal_name, internal_names_dict[internal_name]))
        missing_names = set(internal_names_dict.keys()) - xliff_internal_names
        for name in missing_names:
            discrepancies.append((name, internal_names_dict.get(name, '')))
        return discrepancies
    except ET.ParseError:
        return []

def write_to_csv(entries, file_path):
    csv_file_path = file_path.replace('.xliff', '.csv')
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['InternalName', 'English Text'])
        for name, text in entries:
            writer.writerow([name, text])

def main():
    root = Tk()
    root.withdraw()  # Hide the Tkinter GUI
    directory = askdirectory(title='Select Root Directory')  # Show the file dialog

    if not directory:
        print("No directory selected. Exiting.")
        return

    internal_names_dict = {}
    xml_dir = os.path.join(directory, 'english', 'text')

    for xml_file in find_xml_files(xml_dir):
        internal_names_dict.update(parse_xml_for_internal_names_and_text(xml_file))

    for xliff_file in find_xliff_files(directory):
        discrepancies = check_xliff_file(xliff_file, internal_names_dict)
        if discrepancies:
            write_to_csv(discrepancies, xliff_file)

if __name__ == "__main__":
    main()
