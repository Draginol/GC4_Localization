import os
import jieba
import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk
import re

import re

def segment_text(text):
    # This regex pattern will find all sequences of Chinese characters.
    chinese_pattern = r'[\u4e00-\u9fff]+'
    
    segments = []
    last_end = 0
    
    for match in re.finditer(chinese_pattern, text):
        # Add the preceding non-Chinese sequence
        segments.append(text[last_end:match.start()])
        # Segment the Chinese sequence and add it
        segments.append(' '.join(jieba.cut(match.group(), cut_all=False)))
        last_end = match.end()
        
    # Add the remaining non-Chinese sequence (if any)
    segments.append(text[last_end:])
    
    return ''.join(segments)


def process_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    for string_elem in root.findall(".//String") + root.findall(".//Text"):
        text = string_elem.text
        if text is None:
            continue
        new_text = []
        count = 0
        
        for char in text:
            new_text.append(char)
            if '\u4e00' <= char <= '\u9fff':  # Check if the character is a Chinese character
                count += 1
            else:
                count = 0

            if count > 12:
                new_text.append(" ")
                count = 0

        string_elem.text = segment_text(''.join(new_text))

     # Writing the XML content to file with utf-8 encoding in text mode
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(ET.tostring(root, encoding="unicode"))


if __name__ == '__main__':
    root = Tk()
    root.withdraw()  # Hide the main window
    dir_name = filedialog.askdirectory(title="Select Directory")

    for filename in os.listdir(dir_name):
        if filename.endswith(".xml"):
            process_file(os.path.join(dir_name, filename))
