"""
Test script for HTML JavaScript Converter

This script demonstrates how to use the html_js_converter.py script
with the example.html file.

Usage:
    python test_converter.py
"""

import os
import sys
from html_js_converter import process_html_file

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define input and output file paths
    input_file = os.path.join(script_dir, "example.html")
    output_file = os.path.join(script_dir, "example_static.html")
    
    print(f"Converting {input_file} to {output_file}...")
    
    # Process the example HTML file
    process_html_file(input_file, output_file)
    
    print("\nConversion complete!")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Check if the output file was created
    if os.path.exists(output_file):
        print(f"\nOutput file size: {os.path.getsize(output_file)} bytes")
        print("Conversion successful!")
    else:
        print("\nError: Output file was not created.")
        print("Check for errors in the conversion process.")
    
    print("\nTo view the results, open both files in a web browser and compare them.")

if __name__ == "__main__":
    main()