with open('site/well.html', 'rb') as f:
    content = f.read()
idx = content.find(b'extra')
segment = content[idx-5:idx+30]
result = []
for c in segment:
    if 32 <= c < 127:
        result.append(chr(c))
    else:
        result.append('\\x{:02x}'.format(c))
print(''.join(result))