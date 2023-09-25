import os
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog

def is_flavor_text_def(filepath):
    """Check if the XML file contains FlavorTextDef elements."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    root = ET.fromstring(content)
    return bool(root.findall('.//FlavorTextDef'))

def main():
    root = tk.Tk()
    root.withdraw()

    # Directory selection
    directory = filedialog.askdirectory(title="Select directory to search for FlavorTextDef XML files")
    if not directory:
        print("Directory selection was canceled.")
        return

    # Check each XML file in the directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.xml'):  # Only check XML files
                filepath = os.path.join(dirpath, filename)
                if is_flavor_text_def(filepath):
                    print(f"Deleting: {filepath}")
                    os.remove(filepath)

if __name__ == "__main__":
    main()
