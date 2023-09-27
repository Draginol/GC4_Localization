import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog

def tmx_to_sdlxliff(tmx_file):
    tree = ET.parse(tmx_file)
    root = tree.getroot()
    
    sdlxliff_root = ET.Element('xliff', version="1.2", xmlns="urn:oasis:names:tc:xliff:document:1.2")
    file_elem = ET.SubElement(sdlxliff_root, 'file', original="file.ext", datatype="plaintext")
    body = ET.SubElement(file_elem, 'body')

    for tu in root.findall(".//tu"):
        source_text, target_text = None, None
        for tuv in tu.findall("./tuv"):
            lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
            seg_elem = tuv.find("./seg")
            
            if seg_elem is None:
                print(f"Warning: <tuv> with lang '{lang}' does not have a <seg> element inside <tu> with id '{tu.get('tuid')}'")
                continue
            
            if lang == 'en':
                source_text = seg_elem.text
            else:
                target_text = seg_elem.text

        if source_text and target_text:
            trans_unit = ET.SubElement(body, 'trans-unit', id=str(tu.get('tuid', '0')))
            source_elem = ET.SubElement(trans_unit, 'source', lang="en")
            source_elem.text = source_text
            target_elem = ET.SubElement(trans_unit, 'target', lang=lang)
            target_elem.text = target_text
        else:
            print(f"Missing text for tu with id {tu.get('tuid')}")

    sdlxliff_filename = os.path.splitext(tmx_file)[0] + ".sdlxliff"
    ET.ElementTree(sdlxliff_root).write(sdlxliff_filename, encoding="utf-8", xml_declaration=True)
    print(f"Output saved to: {sdlxliff_filename}")

def main():
    root = tk.Tk()
    root.withdraw()
    tmx_file_path = filedialog.askopenfilename(title="Select TMX file", filetypes=[("TMX files", "*.tmx")])

    if tmx_file_path:
        tmx_to_sdlxliff(tmx_file_path)

if __name__ == "__main__":
    main()
