import os
import tkinter as tk
from tkinter import filedialog

def replace_line_endings(directory):
    for subdir, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(subdir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace CRLF with CR to ensure no double carriage returns
                content = content.replace('\r\n', '\r')
                # Then replace CR with CRLF
                content = content.replace('\r', '\r\n')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

def select_directory():
    directory = filedialog.askdirectory(title="Select Directory")
    if directory:
        replace_line_endings(directory)
        label.config(text=f"Processed XML files in: {directory}")

app = tk.Tk()
app.title("Line Ending Converter")

label = tk.Label(app, text="Click the button to select a directory of XML files.")
label.pack(pady=20)

button = tk.Button(app, text="Select Directory", command=select_directory)
button.pack(pady=20)

app.mainloop()
