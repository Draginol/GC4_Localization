import os
import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk
from xml.dom.minidom import parseString

def get_all_xml_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.xml')]

def get_internal_name_text_pairs(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    if root.tag != "FlavorTextDefs":
        return []
    pairs = [(entry.find('InternalName').text, entry.find('FlavorTextOption/Text').text) for entry in root.findall('FlavorTextDef')]
    return pairs


def prettify_and_cleanup(xml_content):
    pretty_xml = parseString(xml_content).toprettyxml(indent="  ")
    # Removing lines that only contain whitespace
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    cleaned_content = '\n'.join(lines)
    
    # Replacing XML escaped characters with their actual representations
    replacements = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&apos;': "'"
    }
    for escape, char in replacements.items():
        cleaned_content = cleaned_content.replace(escape, char)
    
    return cleaned_content



def append_to_xliff(xliff_file, file_to_pairs_map):
    tree = ET.parse(xliff_file)
    root = tree.getroot()
    source_language = "EN"  # default value (can be adjusted if necessary)
    
    # Get the target language from any existing file element.
    # If there are multiple file elements with different target languages, this will only get the first.
    target_language = root.find('./file').attrib.get('target-language', 'es')

    for filename, pairs in file_to_pairs_map.items():
        file_element = root.find(f'./file[@original="{filename}"]')
        if not file_element:
            # If no file element exists for this filename, create a new one
            file_element = ET.SubElement(root, 'file', datatype="plaintext")
            file_element.set('original', filename)
            file_element.set('source-language', source_language)
            file_element.set('target-language', target_language)
            ET.SubElement(file_element, 'body')


        body = file_element.find('./body')
        existing_ids = {int(unit.attrib['id']) for unit in body.findall('trans-unit')}
        max_id = max(existing_ids) if existing_ids else 0
        existing_internal_names = {unit.attrib.get('internalName') for unit in body.findall('trans-unit')}

        for internal_name, text in pairs:
            if internal_name not in existing_internal_names:
                max_id += 1
                trans_unit = ET.SubElement(body, 'trans-unit', id=str(max_id), internalName=internal_name)
                ET.SubElement(trans_unit, 'source').text = text
                ET.SubElement(trans_unit, 'target').text = text
                existing_internal_names.add(internal_name)

    cleaned_xml = prettify_and_cleanup(ET.tostring(root, encoding="unicode", method="xml"))

    with open(xliff_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_xml)



def main():
    root = Tk()
    root.withdraw()  # To hide the small tkinter window

    english_directory = filedialog.askdirectory(title="Select the directory containing English XML FlavorText files")
    xml_files = get_all_xml_files(english_directory)

    file_to_pairs_map = {}
    for xml_file in xml_files:
        pairs = get_internal_name_text_pairs(xml_file)
        if pairs:
            file_to_pairs_map[os.path.basename(xml_file)] = pairs

    parent_directory = os.path.dirname(os.path.dirname(english_directory))

    # List of language directories
    language_dirs = ["Polish", "Chinese", "French", "German", "Greek", "Italian", "Japanese", "Korean", "Portuguese", "Russian", "Spanish"]

    for lang_dir in language_dirs:
        full_lang_dir = os.path.join(parent_directory, lang_dir)
        # Look for FlavorText_*.xliff files in the language directory
        xliff_files = [f for f in os.listdir(full_lang_dir) if f.startswith("FlavorText_") and f.endswith(".xliff")]

        for xliff_file in xliff_files:
            full_xliff_path = os.path.join(full_lang_dir, xliff_file)
            append_to_xliff(full_xliff_path, file_to_pairs_map)

if __name__ == "__main__":
    main()
