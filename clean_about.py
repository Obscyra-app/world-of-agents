#!/usr/bin/env python3
import re

# Read the file
with open('site/about.html', 'r') as f:
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

# Now we need to fix the table structure
# The issue is duplicate table sections. Let's find and fix.

# First, let's see what we have around the stats table
# The structure should be:
# <!-- stats-table: managed by scripts/snapshot-stats.sh; re-pin via that script, not by hand -->
# <table> ... 4 rows ... </table>
# <!-- /stats-table -->
# <p class="muted">Snapshot pinned to commit ... (HEAD at refresh). Reproduce at any</p>

# But we have multiple copies. Let's use a more targeted approach:
# Find the first occurrence of the stats-table begin marker and end marker
# and keep only that block, removing duplicates.

begin_marker = '<!-- stats-table: managed by scripts/snapshot-stats.sh; re-pin via that script, not by hand -->'
end_marker = '<!-- /stats-table -->'

first_begin = cleaned.find(begin_marker)
first_end = cleaned.find(end_marker, first_begin)

if first_begin != -1 and first_end != -1:
    # Keep everything before first_begin, then the block from first_begin to first_end + len(end_marker)
    # then everything after the LAST end_marker
    last_end = cleaned.rfind(end_marker)
    if last_end != first_end:
        # There are duplicates - keep first block, remove the rest between first_end and last_end
        pre = cleaned[:first_end + len(end_marker)]
        post = cleaned[last_end + len(end_marker):]
        cleaned = pre + post

# Also fix the p.muted after the table - there should be only one
# The pattern is: </p> followed by <table> (which is wrong) or multiple <p class="muted">Snapshot pinned...
# Let's look for multiple "Snapshot pinned to commit" and keep only the first
pin_pattern = r'Snapshot pinned to commit [0-9a-f]+ \(HEAD at refresh\)'
pins = list(re.finditer(pin_pattern, cleaned))
if len(pins) > 1:
    # Remove duplicates - keep only the first occurrence
    # Find the paragraph containing the first pin
    first_pin_start = pins[0].start()
    # Find the enclosing <p> tag
    p_start = cleaned.rfind('<p class="muted">', 0, first_pin_start)
    if p_start == -1:
        p_start = cleaned.rfind('<p class=\'muted\'>', 0, first_pin_start)
    p_end = cleaned.find('</p>', first_pin_start)
    if p_start != -1 and p_end != -1:
        first_p_block = cleaned[p_start:p_end + 4]
        # Remove all other similar blocks
        for pin in pins[1:]:
            pin_start = pin.start()
            p_start2 = cleaned.rfind('<p class="muted">', 0, pin_start)
            if p_start2 == -1:
                p_start2 = cleaned.rfind('<p class=\'muted\'>', 0, pin_start)
            p_end2 = cleaned.find('</p>', pin_start)
            if p_start2 != -1 and p_end2 != -1:
                cleaned = cleaned[:p_start2] + cleaned[p_end2 + 4:]

# Also fix any orphaned <tr> tags that are not inside a table
# Look for patterns like </p>    <tr> (where <tr> follows </p> directly with whitespace)
cleaned = re.sub(r'</p>\s*<tr>', '</p>', cleaned)

# Fix any </table> followed by <table> without proper closing
# This is more complex - let's just check the final structure

# Write back
with open('site/about.html', 'w') as f:
    f.write(cleaned)

print("Cleaned about.html - removed conflict markers and attempted table structure fix")