with open('site/well.html', 'rb') as f:
    content = f.read()

idx = content.find(b'extra')
# Print more context
segment = content[idx-5:idx+30]
print("Bytes around 'extra':")
for i, c in enumerate(segment):
    if 32 <= c < 127:
        char = chr(c)
    else:
        char = f'\\x{c:02x}'
    print(f"  {i}: {char} ({c})")

# Search for the literal </ul> pattern
print("\nSearching for </ul> pattern:")
for i in range(len(content) - 4):
    if content[i:i+4] == b'</ul>':
        print(f"  Found at offset {i}: context = {content[i-20:i+20]}")