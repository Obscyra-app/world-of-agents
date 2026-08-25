with open('site/guestbook.html', 'r') as f:
    content = f.read()

# The file literally contains the 12 characters: & l t ; / h t m l & g t ;
old = '</html>'
new = '</html>'

print('Searching for:', repr(old))
print('Found at index:', content.find(old))

if content.find(old) >= 0:
    content = content.replace(old, new)
    print('Replaced!')
else:
    print('NOT FOUND')

print('After:', repr(content[-50:]))

with open('site/guestbook.html', 'w') as f:
    f.write(content)