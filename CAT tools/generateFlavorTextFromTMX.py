import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog

def extract_translations_from_tmx(tmx_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    translations = {}
    namespace = {'xml': 'http://www.w3.org/XML/1998/namespace'}
    for tu in root.findall('.//tu'):
        english_text = tu.find("./tuv[@xml:lang='EN']/seg", namespaces=namespace).text
        translated_tuv = tu.find("./tuv[@xml:lang!='EN']/seg", namespaces=namespace)
        translated_text = translated_tuv.text if translated_tuv is not None else english_text
        translations[english_text] = translated_text
    return translations


def process_flavor_text_file(filepath, translations):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    root = ET.fromstring(content)
    
    # Check if the file contains FlavorTextDef elements
    if not root.findall('.//FlavorTextDef'):
        return ''

    for flavor_text_def in root.findall('.//FlavorTextDef'):
        for text_element in flavor_text_def.findall('.//FlavorTextOption/Text'):
            if text_element.text in translations:
                text_element.text = translations[text_element.text]
    
    # Convert only the FlavorTextDef elements to a string
    modified_content = ''.join(ET.tostring(flavor_text_def, encoding="utf-8").decode("utf-8") for flavor_text_def in root.findall('.//FlavorTextDef'))
    
    return modified_content




def main():
    root = tk.Tk()
    root.withdraw()

    # TMX file selection
    tmx_path = filedialog.askopenfilename(filetypes=[("TMX files", "*.tmx"), ("All files", "*.*")], title="Select the TMX file")
    if not tmx_path:
        print("TMX file selection was canceled.")
        return
    
    # Determine the target language from the TMX
    target_language_code = determine_target_language(tmx_path)
    if not target_language_code:
        print("Could not determine the target language from the TMX file.")
        return

    # Directory selection for English flavor text files
    directory = filedialog.askdirectory(title="Select directory containing English flavor text files")
    if not directory:
        print("Directory selection was canceled.")
        return

    # Extract translations from the TMX
    translations = extract_translations_from_tmx(tmx_path)

    # Process each XML file and combine the results within the FlavorTextDefs tags
    combined_xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    combined_xml_content += '<FlavorTextDefs xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="../../Schema/FlavorText.xsd">\n'

    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            processed_content = process_flavor_text_file(filepath, translations)
            if processed_content:
                combined_xml_content += processed_content + "\n"

    combined_xml_content += '</FlavorTextDefs>'

    # Select directory to save the combined XML content
    output_directory = filedialog.askdirectory(title="Select directory to save the combined XML file")
    if not output_directory:
        print("Output directory selection was canceled.")
        return
    
    output_file = os.path.join(output_directory, f"FlavorText_{target_language_code}.xml")
    with open(output_file, 'w', encoding="utf-8") as f:
        f.write(combined_xml_content)
    print(f"Combined XML saved to: {output_file}")

def determine_target_language(tmx_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    for tuv in root.findall('.//tuv'):
        lang = tuv.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
        if lang and lang != 'EN':
            return lang
    return None

if __name__ == "__main__":
    main()
