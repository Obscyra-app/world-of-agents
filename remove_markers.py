#!/usr/bin/env python3

filename = '/Users/nuriman/world-of-agents-residents/agent-03/site/about.html'
with open(filename, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Remove conflict marker strings
    newline = line.replace('<<<<<<<', '').replace('=======', '').replace('>>>>>>>', '')
    new_lines.append(newline)

with open(filename, 'w') as f:
    f.writelines(new_lines)

print("Removed conflict marker strings from", filename)