import os
import xml.etree.ElementTree as ET
from tkinter import Tk, filedialog


def combine_flavor_text_files(directory):
    """Combine XML flavor text files in the directory into a single XML."""
    
    # Create the root element for the new combined XML
    combined_root = ET.Element("FlavorTextDefs")
    
    # Go through each XML file in the directory
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            file_path = os.path.join(directory, file_name)
            
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Ensure the file has the correct structure
                if root.tag == "FlavorTextDefs":
                    for flavor_text_def in root:
                        # Append each FlavorTextDef entry to the combined XML
                        combined_root.append(flavor_text_def)
            
            except Exception as e:
                print(f"Error processing XML file {file_path}: {e}")

    return combined_root

def combine_xml_files(directory):
    """Combine XML files in the given directory into a single XML file."""
    
    # Create the root element for the new combined XML
    combined_root = ET.Element("StringTableList")
    
    # Go through each XML file in the directory
    for file_name in os.listdir(directory):
        if file_name.endswith('.xml'):
            file_path = os.path.join(directory, file_name)
            
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                # Ensure the file has the correct structure
                if root.tag == "StringTableList":
                    for string_table in root:
                        # Append each StringTable entry to the combined XML
                        combined_root.append(string_table)
            
            except Exception as e:
                print(f"Error processing XML file {file_path}: {e}")

    return combined_root

def main():
    root = Tk()
    root.withdraw()
    
    directory = filedialog.askdirectory(title="Select directory containing XML files")
    if not directory:
        return

    combined_xml_root = combine_xml_files(directory)
    combined_flavorxml_root = combine_flavor_text_files(directory)
    
    # Get parent's parent directory name
    parent_parent_dir = os.path.basename(os.path.dirname(directory))
    output_filename = os.path.join(directory, f"{parent_parent_dir}.xml")
    output_Flavorfilename = os.path.join(directory, f"{parent_parent_dir}_flavor.xml")
    
    # Save the combined XML to the output file
    combined_tree = ET.ElementTree(combined_xml_root)
    combined_flavortree = ET.ElementTree(combined_flavorxml_root)
    combined_tree.write(output_filename, encoding='utf-8', xml_declaration=True)
    combined_flavortree.write(output_Flavorfilename, encoding='utf-8', xml_declaration=True)
    print(f"Combined XML saved to {output_filename}")

if __name__ == "__main__":
    main()
