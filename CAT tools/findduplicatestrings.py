import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from tkinter import Tk, filedialog

def find_duplicates_in_directory(directory):
    # Dictionary to hold counts and associated strings of each label
    label_data = defaultdict(lambda: {'count': 0, 'strings': set()})
    
    # Iterate over all files in the directory
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                with open(os.path.join(root_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Parse the XML
                    tree = ET.ElementTree(ET.fromstring(content))
                    for string_table in tree.findall('StringTable'):
                        label = string_table.find('Label').text
                        string_content = string_table.find('String').text
                        label_data[label]['count'] += 1
                        label_data[label]['strings'].add(string_content)
                        
    # Filter out labels with counts greater than 1
    duplicates = {label: data for label, data in label_data.items() if data['count'] > 1}
    return duplicates

def main():
    # Initialize the tkinter root window (it won't be shown)
    root = Tk()
    root.withdraw()
    
    # Open a file dialog to select a directory
    directory = filedialog.askdirectory(title="Select Directory")
    if not directory:
        print("No directory selected. Exiting.")
        return
    
    duplicates = find_duplicates_in_directory(directory)
    
    if not duplicates:
        print("No duplicates found!")
    else:
        print("Found the following duplicate labels:")
        for label, data in duplicates.items():
            count = data['count']
            unique_strings = data['strings']
            print(f"{label}: {count} occurrences")
            if len(unique_strings) == 1:
                print(f"  All occurrences have the same string: {list(unique_strings)[0]}")
            else:
                print(f"  Different strings found: {', '.join(unique_strings)}")

if __name__ == "__main__":
    main()
