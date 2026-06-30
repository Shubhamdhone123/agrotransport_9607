import os
import glob

search_paths = [
    r"c:\TRANSPORT WORKING_TESTING\transport\myapp1\**\*.py",
    r"c:\TRANSPORT WORKING_TESTING\transport\templates\*.html",
]

files_to_process = []
for pattern in search_paths:
    for file in glob.glob(pattern, recursive=True):
        files_to_process.append(file)

count = 0
for filepath in files_to_process:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "Transport Pro" in content:
        new_content = content.replace("Transport Pro", "AgroTransport")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        count += 1
        print(f"Updated {filepath}")

print(f"Successfully replaced 'Transport Pro' with 'AgroTransport' in {count} files.")
