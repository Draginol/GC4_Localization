import os
import re
from tkinter import filedialog, Tk

def pick_folder():
    root = Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory()
    return folder_path

def search_files_in_directory(directory, file_extension):
    found_files = []
    for root_dir, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(file_extension):
                found_files.append(os.path.join(root_dir, file))
    return found_files

def check_broken_tags(file_path):
    with open(file_path, 'r', encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        for index, line in enumerate(content):
            matches = re.findall(r'\[HS_.*?\]', line)
            for match in matches:
                # Check if there's no corresponding closing tag in the same line
                if not re.search(r'\[/' + match[1:] + r'\]', line):
                    print(f"Broken tag found in {file_path} at line {index + 1}: {match}")

def main():
    directory = pick_folder()
    if not directory:
        print("No directory selected. Exiting...")
        return

    xml_files = search_files_in_directory(directory, ".xml")
    for xml_file in xml_files:
        check_broken_tags(xml_file)

if __name__ == "__main__":
    main()
