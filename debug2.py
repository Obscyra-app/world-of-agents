with open('site/well.html', 'rb') as f:
    content = f.read()

idx = content.find(b'extra')
print('Bytes at idx+11 to idx+16:')
for i in range(11, 17):
    c = content[idx+i]
    if 32 <= c < 127:
        char = chr(c)
    else:
        char = '\\x{:02x}'.format(c)
    print('  {}: {} ({})'.format(i, char, c))