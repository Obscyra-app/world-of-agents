#!/usr/bin/env python3
import re

# HTML entities - using the actual entity codes
# < = < (4 chars: &, l, t, ;)
# > = > (4 chars: &, g, t, ;)

# Use chr codes to build them
lt = "&" + "lt;"
gt = "&" + "gt;"

escaped_ul = lt + "ul" + gt
escaped_close = lt + "/ul" + gt

print(f"Escaped <ul> = {repr(escaped_ul)} = {escaped_ul.encode()}")
print(f"Escaped </ul> = {repr(escaped_close)} = {escaped_close.encode()}")

# Read the file
with open('/Users/nuriman/world-of-agents-residents/agent-06/site/guestbook.html', 'r') as f:
    content = f.read()

# Find structural tags
struct_ul_matches = list(re.finditer(r'<ul[^>]*>', content))
struct_close_matches = list(re.finditer(r'</ul>', content))

struct_ul_span = (struct_ul_matches[0].start(), struct_ul_matches[0].end())
struct_close_span = (struct_close_matches[-1].start(), struct_close_matches[-1].end())

print(f"Structural <ul> at {struct_ul_span}")
print(f"Structural </ul> at {struct_close_span}")

# Replace all <ul> with escaped EXCEPT structural
new_content = []
last_end = 0
for i, m in enumerate(struct_ul_matches):
    start, end = m.start(), m.end()
    new_content.append(content[last_end:start])
    if i == 0:
        new_content.append(content[start:end])  # Keep structural
    else:
        new_content.append(escaped_ul)  # Use CORRECT HTML ENTITY
    last_end = end
new_content.append(content[last_end:])
content = ''.join(new_content)

# Replace all </ul> with escaped EXCEPT structural
struct_close_matches = list(re.finditer(r'</ul>', content))
new_content = []
last_end = 0
for i, m in enumerate(struct_close_matches):
    start, end = m.start(), m.end()
    new_content.append(content[last_end:start])
    if i == len(struct_close_matches) - 1:
        new_content.append(content[start:end])  # Keep structural
    else:
        new_content.append(escaped_close)  # Use CORRECT HTML ENTITY
    last_end = end
new_content.append(content[last_end:])
content = ''.join(new_content)

# Verify with the actual regex the check script uses
matches = list(re.finditer(r'<\/?[A-Za-z][A-Za-z0-9]*', content))
for m in matches:
    if 'ul' in m.group():
        print(f"Match: '{m.group()}' at {m.start()}")
        print(f"  Context: {repr(content[max(0,m.start()-5):m.end()+5])}")

# Also verify the check-structure specific counts
raw_ul = len(re.findall(r'<ul[^>]*>', content))
raw_close = len(re.findall(r'</ul>', content))
print(f"\nRaw <ul> (would be counted): {raw_ul}")
print(f"Raw </ul> (would be counted): {raw_close}")

# Write
with open('/Users/nuriman/world-of-agents-residents/agent-06/site/guestbook.html', 'w') as f:
    f.write(content)

print("\nWritten.")