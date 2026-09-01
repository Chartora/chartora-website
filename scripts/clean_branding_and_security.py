import os
import re

# Files to update branding
extensions = ('.html', '.md', '.py', '.mq5', '.json')
root_dir = '.'

patterns = [
    (r'https://t\.me/chartora_official', 'https://t.me/chartora'),
    (r'@chartora', '@chartora'),
    (r'Chartora\.in', 'CHARTORA'),
    (r'CHARTORA\.IN', 'CHARTORA'),
    (r'chartora\.in', 'chartora'),
]

modified_count = 0
for root, dirs, files in os.walk(root_dir):
    if '.git' in root or 'node_modules' in root or 'brain' in root:
        continue
    for f in files:
        if f.endswith(extensions):
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                
                new_content = content
                for pat, rep in patterns:
                    new_content = re.sub(pat, rep, new_content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as fp:
                        fp.write(new_content)
                    modified_count += 1
                    print(f"Updated branding in: {file_path}")
            except Exception as e:
                print(f"Skipping {file_path}: {e}")

print(f"\nBranding standardisation complete. {modified_count} files updated.")
