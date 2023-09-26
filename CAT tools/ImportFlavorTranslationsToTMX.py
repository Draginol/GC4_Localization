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
                
                # Loop through each FlavorTextOption
                for flavor_text_option in flavor_text_def.findall('.//FlavorTextOption'):
                    requirements = []
                    for req_element in flavor_text_option.findall('./Requirements/*'):
                        req_text = ET.tostring(req_element, encoding='utf-8', method='xml').decode('utf-8').strip()
                        requirements.append(req_text)
                    req_string = "\n".join(requirements)
                    
                    # Loop through each Text element inside the current FlavorTextOption
                    for idx, text_element in enumerate(flavor_text_option.findall('.//Text')):
                        key = (internal_name, idx + 1, req_string)
                        translation_dict[key] = (os.path.basename(filepath), text_element.text)
    return translation_dict



def update_tmx_with_translation(tmx_path, translations):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    
    changes = []

    for tu in root.findall('.//tu'):
        prop_internal_name = tu.find("./prop[@type='InternalName']")
        prop_text_index = tu.find("./prop[@type='TextIndex']")
        prop_requirements = tu.find("./prop[@type='Requirements']")
        
        if prop_internal_name is not None and prop_text_index is not None:
            req_string = prop_requirements.text if prop_requirements is not None else ""
            key = (prop_internal_name.text, int(prop_text_index.text), req_string)
            if key in translations:
                filename, translated_text = translations[key]
                for tuv in tu.findall('./tuv'):
                    lang = tuv.attrib.get('{http://www.w3.org/XML/1998/namespace}lang')
                    if lang and lang != 'EN':
                        seg_element = tuv.find('./seg')
                        changes.append((filename, seg_element.text, translated_text))
                        seg_element.text = translated_text
                        break
    tree.write(tmx_path, encoding="utf-8", xml_declaration=True)
    return changes


def main():
    root = tk.Tk()
    root.withdraw()
    
    tmx_path = filedialog.askopenfilename(filetypes=[("TMX files", "*.tmx"), ("All files", "*.*")], title="Select the TMX file to update")
    if not tmx_path:
        print("TMX file selection was canceled.")
        return
    
    translated_dir = filedialog.askdirectory(title="Select directory containing translated files")
    if not translated_dir:
        print("Directory selection was canceled.")
        return
    
    translations = build_translation_dict(translated_dir)
    changes = update_tmx_with_translation(tmx_path, translations)
    for filename, old_text, new_text in changes:
        print(f"File: {filename}")
        print("Old Translation:", old_text)
        print("New Translation:", new_text)
        print("-" * 80)
    print("TMX file has been updated.")

if __name__ == "__main__":
    main()
