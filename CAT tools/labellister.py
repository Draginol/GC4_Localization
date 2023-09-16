import xml.etree.ElementTree as ET
from tkinter import filedialog, Tk

def extract_labels_from_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    labels = []
    for elem in root.findall(".//StringTable/Label"):
        labels.append(elem.text)

    return labels

def main():
    # Initialize Tkinter root window (it won't be shown)
    root = Tk()
    root.withdraw()

    # Open file dialog to select the XML file
    file_path = filedialog.askopenfilename(title="Select XML file", filetypes=[("XML Files", "*.xml"), ("All files", "*.*")])
    if not file_path:
        print("No file selected. Exiting.")
        return

    labels = extract_labels_from_xml(file_path)

    # Write the labels to a text file
    with open("labels_output.txt", "w") as f:
        for label in labels:
            f.write(f"{label}\n")

    print(f"Labels have been written to labels_output.txt")

if __name__ == "__main__":
    main()
