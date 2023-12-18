import os
import shutil
import stat
import tkinter as tk
from tkinter import filedialog

def set_file_writeable(file_path):
    if os.path.exists(file_path):
        os.chmod(file_path, stat.S_IWRITE)

def select_directory(title):
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title=title)
    root.destroy()
    return directory

def copy_language_folders(src_root, dest_root, languages):
    for language in languages:
        src_lang_path = os.path.join(src_root, language, 'Text')
        dest_lang_path = os.path.join(dest_root, language, 'Text')

        if not os.path.exists(src_lang_path):
            print(f"Source path not found: {src_lang_path}")
            continue

        if not os.path.exists(dest_lang_path):
            os.makedirs(dest_lang_path)

        for filename in os.listdir(src_lang_path):
            src_file = os.path.join(src_lang_path, filename)
            dest_file = os.path.join(dest_lang_path, filename)

            set_file_writeable(dest_file)  # Make file writeable if it exists
            shutil.copy2(src_file, dest_file)
            print(f"Copied {filename} to {dest_lang_path}")

def main():
    languages = ["Chinese", "French", "German", "Italian", "Japanese", "Korean", "Polish", "Portuguese", "Russian", "Spanish"]

    src_root = select_directory("Select Source Root Directory")
    if not src_root:
        print("Source directory not selected. Exiting.")
        return

    dest_root = select_directory("Select Destination Root Directory")
    if not dest_root:
        print("Destination directory not selected. Exiting.")
        return

    copy_language_folders(src_root, dest_root, languages)

if __name__ == "__main__":
    main()
