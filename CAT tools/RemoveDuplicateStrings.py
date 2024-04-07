import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from tkinter import Tk, filedialog

def find_duplicates_in_directory(directory):
    label_data = defaultdict(lambda: {'count': 0, 'files': []})
    
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ET.ElementTree(ET.fromstring(content))
                    for string_table in tree.findall('StringTable'):
                        label = string_table.find('Label').text
                        label_data[label]['count'] += 1
                        label_data[label]['files'].append(file_path)
                        
    duplicates = {label: data for label, data in label_data.items() if data['count'] > 1}
    return duplicates

def remove_duplicate_entries(duplicates):
    for label, data in duplicates.items():
        for file_path in data['files']:
            # Check if the file name starts with "Additional"
            if os.path.basename(file_path).startswith("Additional"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ET.ElementTree(ET.fromstring(content))
                    for string_table in tree.findall('StringTable'):
                        if string_table.find('Label').text == label:
                            tree.getroot().remove(string_table)
                            break
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)

def main():
    root = Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select Directory")
    if not directory:
        print("No directory selected. Exiting.")
        return
    
    duplicates = find_duplicates_in_directory(directory)
    
    if not duplicates:
        print("No duplicates found!")
    else:
        remove_duplicate_entries(duplicates)
        print("Removed duplicate StringTable entries from 'Additional' files.")

if __name__ == "__main__":
    main()
