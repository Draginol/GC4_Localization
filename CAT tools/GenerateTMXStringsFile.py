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
            tree = ET.parse(os.path.join(directory, filename))
            root = tree.getroot()
            for entry in root.findall("StringTable"):
                label = entry.find("Label").text
                text = entry.find("String").text
                
                # Escape the text to handle special characters.
                text_escaped = escape_special_chars(text)

                if translated:
                    if label in data_dict:  # We only update the translation if the label is found in the original dict
                        data_dict[label][1] = text_escaped
                else:
                    data_dict[label] = [text_escaped, None]


def generate_tmx(data, language_code, output_directory):
    entries = []
    for label, (source, target) in data.items():
        if target:  # check if there's a translation
            entry = f'<tu><tuv xml:lang="en"><seg>{source}</seg></tuv><tuv xml:lang="{language_code}"><seg>{target}</seg></tuv></tu>'
            entries.append(entry)
    
    tmx_content = """
    <tmx version="1.4">
    <body>
    """ + "\n".join(entries) + """
    </body>
    </tmx>
    """

    # Pretty print using minidom
    pretty_xml = parseString(tmx_content).toprettyxml(indent="  ")

    with open(os.path.join(output_directory, f"GCStrings_{language_code}.tmx"), 'w', encoding='utf-8') as f:
        f.write(pretty_xml)



if __name__ == "__main__":
    source_directory = select_directory("Select the source English strings XML directory")
    translated_directory = select_directory("Select the translated XML strings directory")
    output_directory = select_directory("Select the output directory for the TMX file")
    language_code = select_language_code()

    data_dict = {}
    parse_xml(source_directory, data_dict)
    parse_xml(translated_directory, data_dict, translated=True)
    generate_tmx(data_dict, language_code, output_directory)
    print(f"TMX file generated as GCStrings_{language_code}.tmx in the selected output directory.")
