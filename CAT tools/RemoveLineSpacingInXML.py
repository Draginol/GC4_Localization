import os
import tkinter as tk
from tkinter import filedialog
import shutil

def select_root_directory():
    """Opens a dialog to select the root directory."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    directory = filedialog.askdirectory(title="Select Root Directory")
    return directory

def remove_extra_blank_lines(file_path):
    """Removes extra blank lines from the XML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        new_lines = []
        previous_line_blank = False

        for line in lines:
            stripped_line = line.rstrip()
            if not stripped_line:
                if not previous_line_blank:
                    new_lines.append('\n')  # Keep only one blank line
                    previous_line_blank = True
                # Else: Skip additional blank lines
            else:
                new_lines.append(line.rstrip() + '\n')  # Remove trailing spaces
                previous_line_blank = False

        # Write the processed lines back to the file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)

        print(f"Processed: {file_path}")

    except Exception as e:
        print(f"Failed to process {file_path}: {e}")

def process_xml_files(root_directory):
    """Recursively processes all XML files in the root directory."""
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                file_path = os.path.join(dirpath, filename)
                backup_path = file_path + '.bak'
                try:
                    # Create a backup of the original file
                    shutil.copy2(file_path, backup_path)
                    remove_extra_blank_lines(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

def main():
    root_directory = select_root_directory()
    if not root_directory:
        print("No directory selected. Exiting.")
        return
    print(f"Selected directory: {root_directory}")
    process_xml_files(root_directory)
    print("Processing complete.")

if __name__ == "__main__":
    main()
