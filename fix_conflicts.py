import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    # Pattern for conflict block
    pattern = re.compile(r'^<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [0-9a-f]+$', re.DOTALL | re.MULTILINE)
    def replace(match):
        our = match.group(1)
        their = match.group(2)
        # For about.html, we want to keep both tables and both snapshot lines.
        # We'll simply return our + '\n' + their (but note that our and their already include the newlines at the end?)
        # We'll just return our + their
        return our + their
    new_content = pattern.sub(replace, content)
    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Processed {filepath}")

# List of files to process
files = [
    'site/about.html',
    'site/feed.xml',
    'site/search-index.json',
    'sitemap.xml'
]

for f in files:
    if os.path.exists(f):
        process_file(f)
    else:
        print(f"File not found: {f}")

