import os
import openai
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, simpledialog
from PyQt5.QtCore import QSettings
from langdetect import detect

class TMXTranslator:
    def __init__(self):
        # Set up QSettings for OpenAI key storage
        self.settings = QSettings("YourOrganization", "TMXTranslator")
        
        # Retrieve and set the openai key if it exists
        openai_key = self.settings.value("openai_key", None)
        if not openai_key:
            openai_key = simpledialog.askstring("OpenAI Key", "Please enter your OpenAI key:")
            self.settings.setValue("openai_key", openai_key)
        openai.api_key = openai_key

    def translate_with_openai(self, label_name, text, target_language):
        prompt = (f"In the context of a sci-fi game and given the label '{label_name}', "
                  f"translate this English string, without using more words and respecting formatting codes into {target_language}: {text}")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def process_tmx_file(self, tmx_path):
        tree = ET.parse(tmx_path)
        root = tree.getroot()
        counter = 0

        total_tus = len(root.findall('.//tu'))
        print(f"Processing {total_tus} translation units (TUs)...")

        for idx, tu in enumerate(root.findall('.//tu'), start=1):
            filename_prop = tu.find("./prop[@type='Filename']")
            if filename_prop is None or "flavortext" not in filename_prop.text.lower():
                continue
            
            print(f"Checking TU {idx}/{total_tus} from file: {filename_prop.text}")

            english_seg = tu.find("./tuv[@{http://www.w3.org/XML/1998/namespace}lang='EN']/seg")
            if english_seg is None:
                continue

            target_seg = tu.find("./tuv[@{http://www.w3.org/XML/1998/namespace}lang!='EN']/seg")
            if target_seg is None:
                continue

            # Detect the language of the target segment
            detected_language = detect(target_seg.text)
            if detected_language == "en":  # If the target segment is detected as English
                print(f"Translating: {target_seg.text}")
                translated_text = self.translate_with_openai(filename_prop.text, english_seg.text, 'FR')
                target_seg.text = translated_text
                counter += 1

                if counter % 5 == 0:
                    print(f"Saving after {counter} translations...")
                    tree.write(tmx_path, encoding="utf-8", xml_declaration=True)

        # Final save after all translations
        print(f"Final save after processing all translations. Total translations made: {counter}")
        tree.write(tmx_path, encoding="utf-8", xml_declaration=True)

    def run(self):
        root = tk.Tk()
        root.withdraw()
        
        # TMX file selection
        tmx_path = filedialog.askopenfilename(filetypes=[("TMX files", "*.tmx"), ("All files", "*.*")], title="Select the TMX file to translate")
        if not tmx_path:
            print("TMX file selection was canceled.")
            return

        self.process_tmx_file(tmx_path)

if __name__ == "__main__":
    translator = TMXTranslator()
    translator.run()
