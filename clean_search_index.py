#!/usr/bin/env python3
import json

# Read the file
with open('site/search-index.json', 'r') as f:
    content = f.read()

# The file has multiple JSON blobs separated by conflict markers.
# All the JSON blobs seem to be the same. Let's extract the first valid JSON.
lines = content.split('\n')

# Find the first line that starts with { (the JSON)
json_start = None
for i, line in enumerate(lines):
    if line.strip().startswith('{'):
        json_start = i
        break

if json_start is None:
    print("No JSON found")
    exit(1)

# Now find where the first JSON ends - look for the first complete JSON object
# Since it's a large JSON, we'll just find the matching closing brace
# But simpler: just try to parse from the first { to the end, and if it fails,
# try shorter prefixes
json_text = '\n'.join(lines[json_start:])

# Try to find a valid JSON by looking for the end of the first complete object
# The structure is {"base": "...", "docs": [...]} - we need to find the matching }
brace_count = 0
in_string = False
escape_next = False
json_end = None

for i, char in enumerate(json_text):
    if escape_next:
        escape_next = False
        continue
    if char == '\\':
        escape_next = True
        continue
    if char == '"' and not escape_next:
        in_string = not in_string
        continue
    if not in_string:
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                json_end = i + 1
                break

if json_end is None:
    print("Could not find end of JSON object")
    exit(1)

valid_json = json_text[:json_end]

# Validate it parses
try:
    parsed = json.loads(valid_json)
    print(f"Valid JSON found, docs count: {len(parsed.get('docs', []))}")
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    exit(1)

# Write back the clean JSON
with open('site/search-index.json', 'w') as f:
    f.write(valid_json + '\n')

print("Cleaned search-index.json - removed all conflict markers, kept first valid JSON")