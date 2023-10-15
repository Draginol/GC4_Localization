import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, simpledialog
from xml.dom.minidom import parseString
import json

def select_directory(title):
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title=title)

def select_language_code():
    root = tk.Tk()
    root.withdraw()
    return simpledialog.askstring("Input", "Enter the language code (e.g., DE for German):")

def escape_special_chars(text):
    """Convert special characters to their HTML entity codes."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def parse_xml(directory, data_dict, translated=False):
    high_priority_keywords = [
        "Ability", "Advisor", "Artifact", "Diplomatic", "FactionText", "UIText", 
        "Race", "PLanet", "Korath", "Improvement", "HotSpot", "GameText", "GameTerm"
    ]
    
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            high_priority = any(keyword in filename for keyword in high_priority_keywords)
            tree = ET.parse(os.path.join(directory, filename))
            root = tree.getroot()
            for entry in root.findall("StringTable"):
                label = entry.find("Label").text
                text = entry.find("String").text

                if text is None:
                    print(f"Warning: Empty text found for label: {label} in file: {filename}")
                    continue
                
                # Escape the text to handle special characters.
                text_escaped = escape_special_chars(text)

                if translated:
                    if label in data_dict:  # We only update the translation if the label is found in the original dict
                        data_dict[label][1] = (text_escaped, high_priority)
                else:
                    # Storing the filename and priority as part of the source data
                    data_dict[label] = [(text_escaped, filename, high_priority), None]

def generate_xliff(data, language_code, output_directory):
    grouped_by_file = {}
    
    # Organizing the data by filename
    for label, ((source, filename, source_priority), target_data) in data.items():
        if filename not in grouped_by_file:
            grouped_by_file[filename] = []
        grouped_by_file[filename].append((label, source, target_data, source_priority))

    all_files_content = []

    # Creating XLIFF content for each filename
    for filename, entries in grouped_by_file.items():
        trans_units = []
        for label, source, target_data, source_priority in entries:
            if target_data:  # check if there's a translation
                target, target_priority = target_data

                # Metadata as string without escaped characters
                metadata = 'highpriority = {}'.format(str(source_priority).lower())

                trans_unit = '<trans-unit id="{}">'.format(label)  # Using label as id
                trans_unit += '<source>{}</source>'.format(source)
                trans_unit += '<target>{}</target>'.format(target)

                # Adding context-group for source file
                trans_unit += '<context-group purpose="location">'
                trans_unit += '<context context-type="sourcefile">{}</context>'.format(filename)
                trans_unit += '</context-group>'

                trans_unit += '<note>{}</note>'.format(metadata)
                trans_unit += '</trans-unit>'

                trans_units.append(trans_unit)
            else:
                print(f"No translation found for label: {label}")
        
        file_content = """
        <file original="{}" source-language="en" target-language="{}" datatype="plaintext">
            <body>
                {}
            </body>
        </file>
        """.format(filename, language_code, ''.join(trans_units))
        all_files_content.append(file_content)

    xliff_content = """
    <xliff version="1.2">
        {}
    </xliff>
    """.format(''.join(all_files_content))

    # Pretty print using minidom
    pretty_xml = parseString(xliff_content).toprettyxml(indent="  ")

    with open(os.path.join(output_directory, f"GCStrings_{language_code}.xliff"), 'w', encoding='utf-8') as f:
        f.write(pretty_xml)


if __name__ == "__main__":
    source_directory = select_directory("Select the source English strings XML directory")
    translated_directory = select_directory("Select the translated XML strings directory")
    output_directory = select_directory("Select the output directory for the XLIFF file")
    language_code = select_language_code()

    data_dict = {}
    parse_xml(source_directory, data_dict)
    parse_xml(translated_directory, data_dict, translated=True)
    generate_xliff(data_dict, language_code, output_directory)
    print(f"XLIFF file generated as GCStrings_{language_code}.xliff in the selected output directory.")
