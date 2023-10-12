import os
import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk
import re
import subprocess
from janome.tokenizer import Tokenizer

def clean_japanese_text(text):
    # This regex pattern identifies spaces between Japanese characters and removes them.
    return re.sub(r'(?<=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF\uFF65-\uFF9F])\s+(?=[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF\uFF65-\uFF9F])', '', text)

def segment_text(text):
    # Define a regex pattern for Japanese text sequences
    japanese_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF\uFF65-\uFF9F]+'
    
    # Segment only the Japanese text sequences and preserve everything else
    segments = []
    last_end = 0

    for match in re.finditer(japanese_pattern, text):
        # Add the preceding non-Japanese sequence
        segments.append(text[last_end:match.start()])
        
        # For the matched Japanese sequence, break it into chunks of 10 characters and insert a space
        japanese_sequence = match.group()
        chunks = [japanese_sequence[i:i+10] for i in range(0, len(japanese_sequence), 10)]
        segments.append(' '.join(chunks))
        
        last_end = match.end()
    
    # Add the remaining non-Japanese sequence (if any)
    segments.append(text[last_end:])
    
    return ''.join(segments)



def process_file(filename):
    print(f"Processing file: {filename}")  # Print the name of the current file
    tree = ET.parse(filename)
    root = tree.getroot()

    for string_elem in root.findall(".//String") + root.findall(".//Text"):
        text = string_elem.text
        if text is None:
            continue

        segmented = segment_text(text)

        string_elem.text = segmented

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(ET.tostring(root, encoding="unicode"))

if __name__ == '__main__':
    
    root = Tk()
    root.withdraw()  # Hide the main window
    dir_name = filedialog.askdirectory(title="Select Directory")

    for filename in os.listdir(dir_name):
        if filename.endswith(".xml"):
            process_file(os.path.join(dir_name, filename))
