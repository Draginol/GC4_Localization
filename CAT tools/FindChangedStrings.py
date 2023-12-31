
"""
This script compares XML files in two directories and outputs the differences to a CSV file.

Functions:
- get_string_tables(directory): Reads all XML files in the directory, extracts 'Label' and 'String' from each 'StringTable', and returns a dictionary of labels and strings.

- compare_directories(dir_a, dir_b): Compares the string tables in two directories and returns a dictionary of labels and strings that exist in both directories but have different string values.

- output_to_csv(data, file_path): Writes a dictionary to a CSV file. Each row in the CSV file represents a label and its corresponding string.

- main(): Uses a tkinter GUI to ask the user to select two directories and a file path, compares the string tables in the two directories, and outputs the differences to a CSV file.

This script is designed to be run as a standalone program, and it uses a tkinter GUI to interact with the user.
"""



import os
import csv
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import html

def get_string_tables(directory):
    string_tables = {}
    for filename in os.listdir(directory):
        if filename.endswith('.xml'):
            file_path = os.path.join(directory, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag == 'StringTableList':
                for string_table in root.findall('StringTable'):
                    label = string_table.find('Label').text
                    string = string_table.find('String').text
                    string_tables[label] = string
    return string_tables

def compare_directories(dir_a, dir_b):
    a_tables = get_string_tables(dir_a)
    b_tables = get_string_tables(dir_b)

    updated_tables = {label: a_tables[label] for label in a_tables if label in b_tables and a_tables[label] != b_tables[label]}
    return updated_tables

def output_to_csv(data, file_path):
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Label', 'String'])
        for label, string in data.items():
            writer.writerow([label, string])

def main():
    root = tk.Tk()
    root.withdraw()

    dir_a = filedialog.askdirectory(title='Select Directory A (Updated Strings)')
    dir_b = filedialog.askdirectory(title='Select Directory B (Older Strings)')

    updated_tables = compare_directories(dir_a, dir_b)
    output_file = filedialog.asksaveasfilename(title='Save updated StringTables to CSV', defaultextension=".csv")
    
    if output_file:
        output_to_csv(updated_tables, output_file)
        print("Updated StringTables saved to CSV:", output_file)

if __name__ == "__main__":
    main()
