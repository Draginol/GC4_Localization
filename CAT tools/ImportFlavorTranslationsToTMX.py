import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog

def build_translation_dict(translated_dir):
    translation_dict = {}
    for dirpath, dirnames, filenames in os.walk(translated_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            root = ET.fromstring(content)
            for flavor_text_def in root.findall('.//FlavorTextDef'):
                internal_name = flavor_text_def.find('InternalName').text
                for idx, text_element in enumerate(flavor_text_def.findall('.//FlavorTextOption/Text')):
                    key = (os.path.basename(filepath), internal_name, idx + 1)
                    translation_dict[key] = text_element.text
    return translation_dict

def update_tmx_with_translation(tmx_path, translations):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    
    for tu in root.findall('.//tu'):
        prop_filename = tu.find("./prop[@type='Filename']")
        prop_internal_name = tu.find("./prop[@type='InternalName']")
        prop_text_index = tu.find("./prop[@type='TextIndex']")
        
        if prop_filename is not None and prop_internal_name is not None and prop_text_index is not None:
            key = (prop_filename.text, prop_internal_name.text, int(prop_text_index.text))
            if key in translations:
                for tuv in tu.findall('./tuv'):
                    lang = tuv.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if lang and lang != 'EN':
                        seg_element = tuv.find('./seg')
                        seg_element.text = translations[key]
                        break
    tree.write(tmx_path, encoding="utf-8", xml_declaration=True)


def main():
    root = tk.Tk()
    root.withdraw()
    
    # TMX file selection
    tmx_path = filedialog.askopenfilename(filetypes=[("TMX files", "*.tmx"), ("All files", "*.*")], title="Select the TMX file to update")
    if not tmx_path:
        print("TMX file selection was canceled.")
        return
    
    # Directory containing the translated files
    translated_dir = filedialog.askdirectory(title="Select directory containing translated files")
    if not translated_dir:
        print("Directory selection was canceled.")
        return
    
    translations = build_translation_dict(translated_dir)
    update_tmx_with_translation(tmx_path, translations)
    print("TMX file has been updated.")

if __name__ == "__main__":
    main()
