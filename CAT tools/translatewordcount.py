import os
import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog

def count_words_in_elements(xml_file, element_tags):
    """
    Parse the XML file and count words inside the specified elements.
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        word_count = 0
        for tag in element_tags:
            for element in root.findall(f'.//{tag}'):
                if element.text:
                    word_count += len(element.text.split())
        
        return word_count
    
    except Exception as e:
        print(f"Error processing XML file {xml_file}: {e}")
        return 0

def main():
    root = Tk()
    root.withdraw()
    
    directory = filedialog.askdirectory(title="Select directory containing XML files")
    if not directory:
        return

    total_word_count = 0
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            file_path = os.path.join(directory, file_name)
            word_count = count_words_in_elements(file_path, ['String', 'Text'])
            print(f"Words in {file_name}: {word_count}")
            total_word_count += word_count

    print(f"Total words in directory: {total_word_count}")

if __name__ == "__main__":
    main()
