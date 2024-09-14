import csv
import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

def indent(elem, level=0):
    """
    Indent the XML for pretty printing without adding extra blank lines.
    This is a custom implementation to ensure compatibility with Python versions before 3.9.
    If you're using Python 3.9+, you can replace this with ET.indent(elem, space="  ")
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def prettify_xml(element):
    """
    Return a pretty-printed XML string for the Element without extra blank lines.
    Uses ET.indent if available (Python 3.9+), otherwise uses a custom indent function.
    """
    try:
        ET.indent(element, space="  ")
    except AttributeError:
        indent(element)
    return ET.tostring(element, encoding='utf-8', xml_declaration=True).decode('utf-8')

def write_pretty_xml(element, file_path):
    """
    Write the XML Element to a file with proper formatting.
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(prettify_xml(element))

def select_directory(title):
    """
    Open a directory selection dialog and return the selected path.
    """
    root = tk.Tk()
    root.withdraw()
    selected_dir = filedialog.askdirectory(title=title)
    return selected_dir

def parse_english_strings(english_dir):
    """
    Parse all XML files in the English directory and extract Label and String pairs.
    Returns a dictionary with Label as key and String as value.
    """
    english_strings = {}
    for xml_file in os.listdir(english_dir):
        if xml_file.endswith('.xml'):
            xml_path = os.path.join(english_dir, xml_file)
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for string_table in root.findall('.//StringTable'):
                    label = string_table.find('Label').text.strip()
                    string = string_table.find('String').text.strip()
                    english_strings[label] = string
            except ET.ParseError as e:
                print(f"Error parsing {xml_path}: {e}")
    return english_strings

def get_existing_labels(language_dir):
    """
    Parse all XML files in the language directory and collect existing Labels.
    Returns a set of Labels.
    """
    existing_labels = set()
    for xml_file in os.listdir(language_dir):
        if xml_file.endswith('.xml'):
            xml_path = os.path.join(language_dir, xml_file)
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                for string_table in root.findall('.//StringTable'):
                    label = string_table.find('Label').text.strip()
                    existing_labels.add(label)
            except ET.ParseError as e:
                print(f"Error parsing {xml_path}: {e}")
    return existing_labels

def create_missing_strings_file(language, missing_strings, language_dir):
    """
    Create or update the LanguageName_MissingStrings.xml file with the missing strings.
    """
    file_name = f"{language}_MissingStrings.xml"
    file_path = os.path.join(language_dir, file_name)
    
    if os.path.exists(file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing {file_path}: {e}")
            return
    else:
        root = ET.Element("StringTableList")
        tree = ET.ElementTree(root)
    
    for label, string in missing_strings.items():
        # Check if the label already exists to avoid duplicates
        exists = False
        for string_table in root.findall('.//StringTable'):
            existing_label = string_table.find('Label').text.strip()
            if existing_label == label:
                exists = True
                break
        if not exists:
            string_table = ET.Element("StringTable")
            label_elem = ET.SubElement(string_table, "Label")
            label_elem.text = label
            string_elem = ET.SubElement(string_table, "String")
            string_elem.text = string
            root.append(string_table)
    
    write_pretty_xml(root, file_path)
    print(f"Created/Updated {file_name} with {len(missing_strings)} missing strings.")

def process_language(language, english_strings, root_dir):
    """
    Process a single language directory to find missing strings and create a MissingStrings XML file.
    """
    language_dir = os.path.join(root_dir, language, 'Text')
    if not os.path.isdir(language_dir):
        print(f"Directory not found for language '{language}': {language_dir}")
        return
    
    print(f"Processing language: {language}")
    existing_labels = get_existing_labels(language_dir)
    missing_strings = {}
    
    for label, string in english_strings.items():
        if label not in existing_labels:
            missing_strings[label] = string
    
    if missing_strings:
        create_missing_strings_file(language, missing_strings, language_dir)
    else:
        print(f"No missing strings found for language '{language}'.")

def verify_localization(english_dir, root_dir):
    """
    Verify that all labels in the English directory are present in each language directory.
    Create MissingStrings XML files for any missing labels.
    """
    print("Parsing English strings...")
    english_strings = parse_english_strings(english_dir)
    print(f"Found {len(english_strings)} strings in English directory.")
    
    languages = ["Chinese", "French", "German", "Italian", "Japanese", "Korean", "Polish", "Portuguese", "Russian", "Spanish"]
    
    with ThreadPoolExecutor(max_workers=len(languages)) as executor:
        futures = []
        for language in languages:
            futures.append(executor.submit(process_language, language, english_strings, root_dir))
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred during processing: {e}")

def main():
    """
    Main function to run the localization verification script.
    """
    print("Select the English XML directory...")
    english_dir = select_directory("Select English XML Directory")
    if not english_dir:
        messagebox.showerror("Error", "No English directory selected.")
        return
    
    print("Select the Root Directory containing language directories...")
    root_dir = select_directory("Select Root Directory Containing Language Directories")
    if not root_dir:
        messagebox.showerror("Error", "No root directory selected.")
        return
    
    verify_localization(english_dir, root_dir)
    messagebox.showinfo("Completed", "Localization verification completed successfully.")

if __name__ == "__main__":
    main()
