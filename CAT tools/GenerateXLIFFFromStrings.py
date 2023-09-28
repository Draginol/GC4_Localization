import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, simpledialog
from xml.dom.minidom import parseString


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
    for filename in os.listdir(directory):
        if filename.endswith(".xml"):
            high_priority = "_high" in filename or "additional" in filename
            tree = ET.parse(os.path.join(directory, filename))
            root = tree.getroot()
            for entry in root.findall("StringTable"):
                label = entry.find("Label").text
                text = entry.find("String").text
                
                # Escape the text to handle special characters.
                text_escaped = escape_special_chars(text)

                if translated:
                    if label in data_dict:  # We only update the translation if the label is found in the original dict
                        data_dict[label][1] = (text_escaped, high_priority)
                else:
                    data_dict[label] = [(text_escaped, None), None]


def generate_xliff(data, language_code, output_directory):
    entries = []
    trans_unit_id = 1
    for label, ((source, source_priority), target_data) in data.items():
        if target_data:  # check if there's a translation
            target, target_priority = target_data
            entry = f'<trans-unit id="{trans_unit_id}" resname="{label}"><source>{source}</source><target>{target}</target></trans-unit>'
            entries.append(entry)
            trans_unit_id += 1
        else:
            print(f"No translation found for label: {label}")
    
    xliff_content = f"""
    <xliff version="1.2">
        <file original="GCStrings" source-language="en" target-language="{language_code}" datatype="plaintext">
            <body>
                {"".join(entries)}
            </body>
        </file>
    </xliff>
    """

    # Pretty print using minidom
    pretty_xml = parseString(xliff_content).toprettyxml(indent="  ")

    with open(os.path.join(output_directory, f"GCStrings_{language_code}.xliff"), 'w', encoding='utf-8') as f:
        f.write(pretty_xml)



if __name__ == "__main__":
    source_directory = select_directory("Select the source English strings XML directory")
    translated_directory = select_directory("Select the translated XML strings directory")
    output_directory = select_directory("Select the output directory for the TMX file")
    language_code = select_language_code()

    data_dict = {}
    parse_xml(source_directory, data_dict)
    parse_xml(translated_directory, data_dict, translated=True)
    generate_xliff(data_dict, language_code, output_directory)  # updated function name
    print(f"XLIFF file generated as GCStrings_{language_code}.xliff in the selected output directory.")
