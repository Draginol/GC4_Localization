import os
import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog

def find_duplicate_labels(directory):
    label_counts = {}

    # Iterate over all files in the directory to count label occurrences
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                tree = ET.parse(os.path.join(root_dir, file))
                for string_table in tree.findall('StringTable'):
                    label = string_table.find('Label').text
                    label_counts[label] = label_counts.get(label, 0) + 1

    # Return labels that occur more than once
    return {label for label, count in label_counts.items() if count > 1}

def remove_first_duplicate(file_path, duplicate_labels):
    tree = ET.parse(file_path)
    root = tree.getroot()

    modified = False  # Flag to track if the file was modified
    handled_labels = set()  # Track labels that have been handled in this file

    # Iterate over all StringTable entries in the XML
    for string_table in root.findall('StringTable'):
        label = string_table.find('Label').text
        if label in duplicate_labels and label not in handled_labels:
            root.remove(string_table)  # Remove the first occurrence of the duplicate label
            modified = True
            handled_labels.add(label)  # Mark this label as handled in this file

    # If the file was modified (had a duplicate removed), save it
    if modified:
        tree.write(file_path)

    return modified

def main():
    # Initialize the tkinter root window (it won't be shown)
    root = Tk()
    root.withdraw()

    # Open a file dialog to select a directory
    directory = filedialog.askdirectory(title="Select Directory")
    if not directory:
        print("No directory selected. Exiting.")
        return

    # Find all duplicate labels across XML files in the directory
    duplicate_labels = find_duplicate_labels(directory)

    # Write the duplicate labels to duplicates.txt
    with open('duplicates.txt', 'w') as f:
        for label in duplicate_labels:
            f.write(label + "\n")

    modified_files = 0
    # Process each XML file in the directory to remove the first occurrence of each duplicate label
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                if remove_first_duplicate(os.path.join(root_dir, file), duplicate_labels):
                    modified_files += 1

    print(f"{len(duplicate_labels)} duplicate labels written to duplicates.txt.")
    print(f"{modified_files} XML files were modified.")

if __name__ == "__main__":
    main()
