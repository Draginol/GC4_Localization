import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox
import openai
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Ensure you're using Python 3.9+
if int(os.sys.version_info.major) < 3 or (int(os.sys.version_info.major) == 3 and int(os.sys.version_info.minor) < 9):
    raise Exception("This script requires Python 3.9 or higher.")

# Define the version for the new strings file
strings_version = "v29"

# Lock for printing to avoid jumbled logs from multiple threads
print_lock = threading.Lock()

def indent(elem, level=0):
    """
    Indent the XML for pretty printing without adding extra blank lines.
    Compatible with Python versions before 3.9.
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

def translate_text(label_name, text, target_language):
    """
    Translate the given text into the target language using OpenAI's GPT model.
    """
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
        with print_lock:
            print(f"Error translating '{label_name}' to {target_language}: {e}")
        return None

def process_language(language, missing_strings, language_dir):
    """
    Process a single language: translate missing strings and create the new strings file.
    """
    if not os.path.isdir(language_dir):
        with print_lock:
            print(f"Directory not found for language '{language}': {language_dir}")
        return

    if not missing_strings:
        with print_lock:
            print(f"No missing strings found for language '{language}'. Skipping translation.")
        return

    translated_root = ET.Element("StringTableList")

    with print_lock:
        print(f"Translating {len(missing_strings)} strings for language '{language}'...")

    for label, string in missing_strings.items():
        translated_text = translate_text(label, string, language)
        if translated_text:
            string_table = ET.Element("StringTable")
            label_elem = ET.SubElement(string_table, "Label")
            label_elem.text = label
            string_elem = ET.SubElement(string_table, "String")
            string_elem.text = translated_text
            translated_root.append(string_table)
            with print_lock:
                print(f"Translated '{label}' for '{language}'.")
        else:
            with print_lock:
                print(f"Failed to translate '{label}' for '{language}'. Skipping.")

    # Define the new strings file path
    new_strings_file = os.path.join(language_dir, f"{language}_Strings_{strings_version}.xml")

    # Write the translated strings to the new XML file
    write_pretty_xml(translated_root, new_strings_file)

    with print_lock:
        print(f"Created '{new_strings_file}' with translated strings for '{language}'.")

def find_missing_strings(root_dir, languages):
    """
    For each language, find missing strings by locating the *_MissingStrings.xml file.
    Returns a dictionary mapping language to its missing strings.
    """
    missing_strings_per_language = {}

    for language in languages:
        language_text_dir = os.path.join(root_dir, language, 'Text')
        missing_strings_file = os.path.join(language_text_dir, f"{language}_MissingStrings.xml")

        if not os.path.isfile(missing_strings_file):
            with print_lock:
                print(f"No MissingStrings file found for language '{language}' at '{missing_strings_file}'. Skipping.")
            continue

        try:
            tree = ET.parse(missing_strings_file)
            root = tree.getroot()
            missing_strings = {}
            for string_table in root.findall('.//StringTable'):
                label = string_table.find('Label').text.strip()
                string = string_table.find('String').text.strip()
                missing_strings[label] = string
            missing_strings_per_language[language] = missing_strings
            with print_lock:
                print(f"Found {len(missing_strings)} missing strings for language '{language}'.")
        except ET.ParseError as e:
            with print_lock:
                print(f"Error parsing '{missing_strings_file}': {e}")
            continue

    return missing_strings_per_language

def main_translation():
    """
    Main function to handle the translation of missing strings.
    """
    # Select the root directory containing language subdirectories
    with print_lock:
        print("Please select the Root Directory containing language subdirectories...")
    root_dir = select_directory("Select Root Directory Containing Language Subdirectories")
    if not root_dir:
        messagebox.showerror("Error", "No root directory selected.")
        return

    # Define the list of languages
    languages = ["Chinese", "French", "German", "Italian", "Japanese", "Korean", "Polish", "Portuguese", "Russian", "Spanish"]

    # Find all missing strings per language
    with print_lock:
        print("Identifying missing strings across all languages...")
    missing_strings = find_missing_strings(root_dir, languages)

    if not missing_strings:
        with print_lock:
            print("No missing strings found for any language. Exiting.")
        messagebox.showinfo("No Missing Strings", "No missing strings found for any language.")
        return

    # Initialize ThreadPoolExecutor with max_workers equal to number of languages
    with ThreadPoolExecutor(max_workers=len(missing_strings)) as executor:
        futures = []
        for language, strings in missing_strings.items():
            language_text_dir = os.path.join(root_dir, language, 'Text')
            futures.append(executor.submit(process_language, language, strings, language_text_dir))

        # Wait for all translations to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                with print_lock:
                    print(f"An error occurred during translation: {e}")

    messagebox.showinfo("Completed", "Translation of missing strings completed successfully.")

def main():
    """
    Entry point of the script.
    """
    try:
        main_translation()
    except Exception as e:
        with print_lock:
            print(f"An unexpected error occurred: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Retrieve OpenAI API key from environment variable
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if openai_api_key is None:
        print("OPENAI_API_KEY is not set. Please set the environment variable and try again.")
        messagebox.showerror("Error", "OPENAI_API_KEY is not set. Please set the environment variable and try again.")
    else:
        # Set the API key
        openai.api_key = openai_api_key
        print("OpenAI API Key found.")

        # Run the translation process
        main()
