#!/usr/bin/env python3
import os

# Use the current repository's about.html path.
filename = os.path.join(os.path.abspath('.'), 'site', 'about.html')
with open(filename, 'r') as f:
    lines = f.readlines()

# Find the first table open and close
first_open = None
first_close = None
for i, line in enumerate(lines):
    if '<table>' in line:
        first_open = i
        break
if first_open is not None:
    for i in range(first_open+1, len(lines)):
        if '</table>' in lines[i]:
            first_close = i
            break

if first_open is None or first_close is None:
    print("Could not find first table boundaries")
    exit(1)

# Now find the second table's rows: look for a <tr> that is not inside a table (i.e., after first_close)
# We'll assume that the second table starts at the first <tr> after first_close that is not preceded by a <table> tag without a closing.
# Simpler: look for the pattern where we have a <tr> and the previous line is not a <table> line (but we already have a closing table tag).
# Actually, after the first table's closing, we have:
# line first_close+1: '  <!-- /stats-table -->\n'
# line first_close+2: '  <p class=\"muted\">\n'
# line first_close+3: '    Snapshot pinned to commit af1ee20 (HEAD at refresh). Reproduce at any\n'
# line first_close+4: '  </p>    <tr>...'   <-- this is the line where the second table's rows start, but it's missing the opening <table> tag.
# We need to insert a <table> tag before this line, at the same indentation as the surrounding block.

# Let's find the line that contains the first <tr> of the second table's rows.
second_table_start = None
for i in range(first_close+1, len(lines)):
    if '<tr>' in lines[i] and '<table>' not in lines[i]:
        second_table_start = i
        break

if second_table_start is None:
    print("Could not find start of second table rows")
    exit(1)

# Determine indentation: look at the line before second_table_start
prev_line = lines[second_table_start-1]
# If the previous line is empty or just whitespace, look further back
indent = 0
if prev_line.strip() == '':
    for j in range(second_table_start-2, -1, -1):
        if lines[j].strip():
            indent = len(lines[j]) - len(lines[j].lstrip())
            break
else:
    indent = len(prev_line) - len(prev_line.lstrip())

# Insert the <table> tag with the same indentation
lines.insert(second_table_start, ' ' * indent + '<table>\n')

# Now write back
with open(filename, 'w') as f:
    f.writelines(lines)

print(f"Inserted <table> tag at line {second_table_start+1} (0-index {second_table_start})")