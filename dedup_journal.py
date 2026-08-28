#!/usr/bin/env python3

filename = '/Users/nuriman/world-of-agents-residents/agent-03/journal/2026-08-28.md'
with open(filename, 'r') as f:
    lines = f.readlines()

seen = set()
unique_lines = []
for line in lines:
    if line not in seen:
        unique_lines.append(line)
        seen.add(line)

with open(filename, 'w') as f:
    f.writelines(unique_lines)

print(f"Removed {len(lines) - len(unique_lines)} duplicate lines from {filename}")