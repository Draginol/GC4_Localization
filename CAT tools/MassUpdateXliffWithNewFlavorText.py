
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import glob

def choose_file(title, filetypes):
    """ Function to open a file dialog and return the selected file path """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    return file_path

def read_xml(file_path):
    """ Function to read an XML file and return the root element """
    tree = ET.parse(file_path)
    return tree.getroot()


def process_file_element(file_element, english_root, translated_root):
    """ Process each trans-unit within a file element """
    for trans_unit in file_element.findall('body/trans-unit'):
        if trans_unit.get('id') == '1':
            internal_name = trans_unit.get('internalName')
            source_text = trans_unit.find('source').text

            # Find corresponding entry in the English XML file
            english_entry = find_entry_by_internal_name(english_root, internal_name)
            if english_entry:
                english_text = english_entry.find('.//Text').text
                if source_text != english_text:
                    trans_unit.find('source').text = escape_xml(english_text)
                    trans_unit.find('target').text = " "  # Resetting target text to a single space

   # Check for any new entries in the English XML file to add to the xliff
    for english_entry in english_root.iter('FlavorTextDef'):
        internal_name = english_entry.find('InternalName').text
        if not find_trans_unit_by_internal_name(file_element, internal_name):
            source_text = english_entry.find('.//Text').text
            add_new_trans_unit(file_element, internal_name, source_text) 


def find_trans_unit_by_internal_name(file_element, internal_name):
    """ Find a translation unit in a file element by its internal name """
    for trans_unit in file_element.findall('body/trans-unit'):
        if trans_unit.get('internalName') == internal_name:
            return trans_unit
    return None


def add_new_trans_unit(file_element, internal_name, text):
    """ Add a new translation unit to the xliff file under a specific file element """
    body_element = file_element.find('body')
    if body_element is None:
        body_element = ET.SubElement(file_element, 'body')

    new_trans_unit = ET.SubElement(body_element, 'trans-unit', id="1", internalName=internal_name)
    ET.SubElement(new_trans_unit, 'source').text = escape_xml(text)
    ET.SubElement(new_trans_unit, 'target').text = " "  # Initial target text set to a single space



def update_xliff(xliff_root, english_xml_filename, english_root, translated_root):
    """ Update the xliff file based on the English XML file """
    for file_element in xliff_root.findall(".//file"):
        if file_element.get('original') == english_xml_filename:
            process_file_element(file_element, english_root, translated_root)

def find_entry_by_internal_name(root, internal_name):
    """ Find an entry in an XML file by its internal name """
    for entry in root.iter('FlavorTextDef'):
        if entry.find('InternalName').text == internal_name:
            return entry
    return None


def escape_xml(text):
    """ Escape XML special characters in text, but leave quotation marks unchanged """
    text = text.replace('&', '&amp;')  # Replace & first to avoid double escaping
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    # Do not replace quotation marks
    return text


def prettify_xml(element):
    """Return a pretty-printed XML string for the Element without extra whitespace."""
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)

    # Removing extra whitespace
    return '\n'.join([line for line in reparsed.toprettyxml(indent="  ").split('\n') if line.strip()])

def save_xml(root, file_path):
    """ Save the XML root to a file with UTF-8 encoding and pretty formatting """
    pretty_xml = prettify_xml(root)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(pretty_xml)

def post_process_xml(file_path):
    """ Replace escaped quotation marks with literal ones in the XML file """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content = content.replace('&quot;', '"')

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    xliff_file = choose_file("Select the .xliff file", [("XLIFF files", "*.xliff")])
    xliff_root = read_xml(xliff_file)

    # Determine the path to the ../english/text directory
    english_text_dir = os.path.join(os.path.dirname(xliff_file), "../english/text")

    # Process each XML file in the directory
    for xml_file in glob.glob(os.path.join(english_text_dir, "*.xml")):
        english_root = read_xml(xml_file)
        
        # Check if the root element is <FlavorTextDefs> and it contains <FlavorTextDef>
        if english_root.tag == 'FlavorTextDefs' and any(child.tag == 'FlavorTextDef' for child in english_root):
            english_xml_filename = os.path.basename(xml_file)
            update_xliff(xliff_root, english_xml_filename, english_root, None)  # No translated_root

    save_xml(xliff_root, xliff_file)
    post_process_xml(xliff_file)  # Call this function after saving

if __name__ == "__main__":
    main()
