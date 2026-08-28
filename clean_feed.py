#!/usr/bin/env python3
import re
import xml.etree.ElementTree as ET

# Read the file
with open('site/feed.xml', 'r') as f:
    content = f.read()

# Remove all conflict marker lines
lines = content.split('\n')
cleaned_lines = []
for line in lines:
    stripped = line.strip()
    if stripped.startswith('<<<<<<<') or stripped.startswith('=======') or stripped.startswith('>>>>>>>'):
        continue
    cleaned_lines.append(line)

cleaned = '\n'.join(cleaned_lines)

# Now we might have duplicate <updated> tags in some places
# Let's parse and see if it's valid
try:
    # Try to parse to validate
    root = ET.fromstring(cleaned)
    print("XML is valid after removing markers!")
    
    # Write back
    with open('site/feed.xml', 'w') as f:
        f.write(cleaned)
    print("Cleaned feed.xml - removed all conflict markers")
except ET.ParseError as e:
    print(f"XML parse error: {e}")
    # Try a more aggressive approach - fix duplicate <updated> tags
    # The issue is likely duplicate <updated> tags on the same line or adjacent lines
    # Let's look for patterns like "<updated>...</updated>  <updated>...</updated>"
    fixed = re.sub(r'(<updated>[^<]*</updated>)\s+(<updated>[^<]*</updated>)', r'\1', cleaned)
    fixed = re.sub(r'(<updated>[^<]*</updated>)\s+(<updated>[^<]*</updated>)', r'\1', fixed)  # run twice for triple
    
    # Also fix <content> duplicates
    fixed = re.sub(r'(<content type="text">[^<]*</content>)\s+(<content type="text">[^<]*</content>)', r'\1', fixed)
    
    try:
        root = ET.fromstring(fixed)
        print("XML is valid after removing duplicate tags!")
        with open('site/feed.xml', 'w') as f:
            f.write(fixed)
        print("Cleaned feed.xml - removed conflict markers and duplicate tags")
    except ET.ParseError as e2:
        print(f"Still invalid: {e2}")
        # Save for inspection
        with open('site/feed.xml.debug', 'w') as f:
            f.write(cleaned)
        print("Saved debug version to feed.xml.debug")