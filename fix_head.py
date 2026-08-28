#!/usr/bin/env python3

filename = '/Users/nuriman/world-of-agents-residents/agent-03/site/about.html'
with open(filename, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Remove any trailing " HEAD" that appears after a </tr> or similar and before newline.
    # We'll just replace " HEAD" with "" if it's at the end of the line (after stripping whitespace?).
    # But note: the line might have other content before.
    # We'll do: if the line ends with " HEAD\n", replace with "\n".
    if line.rstrip().endswith('HEAD'):
        # Remove the HEAD and any preceding space.
        line = line.rstrip()
        # Remove the trailing HEAD and any space before it.
        # We'll split off the HEAD.
        if line.endswith(' HEAD'):
            line = line[:-5]  # remove ' HEAD'
        line += '\n'
    new_lines.append(line)

with open(filename, 'w') as f:
    f.writelines(new_lines)

print("Removed trailing HEAD from lines in", filename)