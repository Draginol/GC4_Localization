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
        filename = os.path.join(directory, f"AdditionalStrings_{count}.xml")
        if not os.path.exists(filename):
            return filename
        count += 1

def collect_labels(directory):
    labels = {}
    for file in os.listdir(directory):
        if file.endswith(".xml"):
            path = os.path.join(directory, file)
            tree = ET.parse(path)
            root = tree.getroot()
            for entry in root:
                label_elem = entry.find("Label")
                if label_elem is not None:
                    labels[label_elem.text] = entry
    return labels

def main():
    english_dir = get_directory("Select directory containing English XML files")
    translated_dir = get_directory("Select directory containing Translated XML files")

    english_labels = collect_labels(english_dir)
    translated_labels = collect_labels(translated_dir).keys()

    missing_entries = ET.Element("StringTableList")
    missing_entries.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    missing_entries.set("xsi:noNamespaceSchemaLocation", "../../Schema/Lib/StringTable.xsd")

    for label, entry in english_labels.items():
        if label not in translated_labels:
            missing_entries.append(entry)

    # Save missing entries to a new file
    if len(missing_entries) > 0:
        output_path = find_next_filename(translated_dir)
        ET.ElementTree(missing_entries).write(output_path)

if __name__ == "__main__":
    main()
