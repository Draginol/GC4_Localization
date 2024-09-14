import csv
import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog
import openai
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# Ensure you're using Python 3.9+
if int(os.sys.version_info.major) < 3 or (int(os.sys.version_info.major) == 3 and int(os.sys.version_info.minor) < 9):
    raise Exception("This script requires Python 3.9 or higher.")

additional_strings_version = "v29"  # Variable to set the version of additional strings file

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

def write_pretty_xml(tree, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(prettify_xml(tree.getroot()))

def select_file():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

def translate_text(label_name, text, target_language):
    prompt = (
        f"In the context of a Sci-Fi video game, given the string table entry label '{label_name}' as context, "
        f"translate the following text into {target_language}. Respect all formatting codes and do not include the label. "
        f"Add spaces without breaking meaning if a phrase is long to ensure word wrapping is not broken. Only output the translated text. Text to translate: {text}"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=750,
            n=1,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in getting translation feedback: {e}")
        return None

def create_string_table(label, string):
    string_table = ET.Element("StringTable")
    label_element = ET.SubElement(string_table, "Label")
    label_element.text = label
    string_element = ET.SubElement(string_table, "String")
    string_element.text = string
    return string_table

def create_string_table_list():
    return ET.Element("StringTableList")  # Assuming this is the correct root element

def update_or_create_string(label_to_find, original_text, language, xml_directory):
    found = False
    for xml_file in os.listdir(xml_directory):
        if xml_file.endswith('.xml'):
            xml_file_path = os.path.join(xml_directory, xml_file)
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            for string_table in root.findall('.//StringTable'):
                if string_table.find('Label').text == label_to_find:
                    translated_text = translate_text(label_to_find, original_text, language)
                    if translated_text:
                        string_table.find('String').text = translated_text
                        write_pretty_xml(tree, xml_file_path)
                        print(f"Updated {label_to_find} in {language}/{xml_file}")
                    else:
                        print(f"Failed to translate for {label_to_find} in {language}")
                    found = True
                    break
            if found:
                break

    if not found:
        additional_file_path = os.path.join(xml_directory, f"AdditionalStrings_{additional_strings_version}.xml")
        if os.path.exists(additional_file_path):
            additional_tree = ET.parse(additional_file_path)
            additional_root = additional_tree.getroot()
        else:
            additional_root = create_string_table_list()
            additional_tree = ET.ElementTree(additional_root)

        translated_text = translate_text(label_to_find, original_text, language)
        if translated_text:
            new_string_table = create_string_table(label_to_find, translated_text)
            additional_root.append(new_string_table)
            write_pretty_xml(additional_tree, additional_file_path)
            print(f"Added new string {label_to_find} in {language}/AdditionalStrings_{additional_strings_version}.xml")
        else:
            print(f"Failed to translate and add new string {label_to_find} in {language}")

def process_language_all_labels(labels, language, xml_directory):
    """
    Function to process all labels for a single language.
    """
    if not os.path.isdir(xml_directory):
        print(f"Directory not found: {xml_directory}")
        return

    for label_to_find, original_text in labels:
        update_or_create_string(label_to_find, original_text, language, xml_directory)
      

def update_xml_files(csv_file_path, root_directory):
    # languages = ["Chinese", "French", "German", "Italian", "Japanese", "Korean", "Polish", "Portuguese", "Russian", "Spanish"]
    languages = ["Spanish"]
    # Read all labels and their original texts first
    labels = []
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            label_to_find = row['Label']
            original_text = row['String']
            labels.append((label_to_find, original_text))

    # Initialize ThreadPoolExecutor with max_workers equal to number of languages
    with ThreadPoolExecutor(max_workers=len(languages)) as executor:
        futures = []
        for language in languages:
            xml_directory = os.path.join(root_directory, language, 'Text')
            # Submit a task for each language to process all labels
            futures.append(executor.submit(process_language_all_labels, labels, language, xml_directory))

        # Optionally, wait for all futures to complete and handle exceptions
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"An error occurred during processing: {e}")

def main():
    csv_file = select_file()
    if not csv_file:
        print("No file selected.")
        return

    root_dir = filedialog.askdirectory(title='Select Root Directory')
    if not root_dir:
        print("No directory selected.")
    else:
        update_xml_files(csv_file, root_dir)

if __name__ == "__main__":
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if openai_api_key is None:
        print("OPENAI_API_KEY is not set.")
    else:
        openai.api_key = openai_api_key  # Set the API key
        print("OpenAI API Key found.")
        main()
