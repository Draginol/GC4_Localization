import os
import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk

def get_directory(prompt):
    root = Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(title=prompt)
    root.destroy()
    return directory

def find_next_filename(directory):
    count = 1
    while True:
        filename = os.path.join(directory, f"MissingStrings_{count}.xml")
        if not os.path.exists(filename):
            return filename
        count += 1

def extract_labels_from_file(path):
    """Extract labels from a single XML file."""
    labels = set()
    tree = ET.parse(path)
    root = tree.getroot()
    for entry in root:
        label_elem = entry.find("Label")
        if label_elem is not None:
            labels.add(label_elem.text)
    return labels

def collect_labels(directory):
    """Extract labels from all XML files in the directory."""
    all_labels = set()
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            path = os.path.join(directory, filename)
            all_labels.update(extract_labels_from_file(path))
    return all_labels

def main():
    english_dir = get_directory("Select directory containing English XML files")
    translated_dir = get_directory("Select directory containing Translated XML files")

    english_labels = collect_labels(english_dir)
    translated_labels = collect_labels(translated_dir)

    missing_labels = english_labels - translated_labels

    if missing_labels:
        missing_entries = ET.Element("StringTableList")
        missing_entries.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        missing_entries.set("xsi:noNamespaceSchemaLocation", "../../Schema/Lib/StringTable.xsd")

        for label in missing_labels:
            entry = ET.SubElement(missing_entries, "StringTable")
            ET.SubElement(entry, "Label").text = label
            ET.SubElement(entry, "String").text = "(MISSING TRANSLATION)"

        output_path = find_next_filename(translated_dir)
        ET.ElementTree(missing_entries).write(output_path)

if __name__ == "__main__":
    main()
