import os
import re

def clean_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    # Remove lines that are conflict markers (after stripping)
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('<<<<<<<') or stripped.startswith('=======') or stripped.startswith('>>>>>>>'):
            continue
        cleaned.append(line)
    with open(filepath, 'w') as f:
        f.writelines(cleaned)
    print(f"Cleaned {filepath}")

if __name__ == '__main__':
    # Use the repository root of the current agent (agent-07). Resolve absolute path.
    base = os.path.abspath('.')
    files = [
        os.path.join(base, 'site/about.html'),
        os.path.join(base, 'site/feed.xml'),
        os.path.join(base, 'site/search-index.json'),
        os.path.join(base, 'sitemap.xml')
    ]
    for f in files:
        if os.path.exists(f):
            clean_file(f)
        else:
            print(f"File not found: {f}")