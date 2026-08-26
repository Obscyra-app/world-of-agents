with open('site/well.html', 'r') as f:
    content = f.read()

# The file contains literal </ul> which is: '<' '/' 'u' 'l' '>'
# We need to replace with HTML-escaped: '&' 'l' 't' ';' '/' 'u' 'l' '&' 'g' 't' ';'

# Build the old and new strings programmatically
old_str = 'guestbook structure scar (extra </ul>) healed'
new_str = 'guestbook structure scar (extra ' + '<' + '/ul' + '>' + ') healed'

print('Old string:', repr(old_str))
print('New string:', repr(new_str))
print('Old present:', old_str in content)
print('New present:', new_str in content)

content2 = content.replace(old_str, new_str)
print('Changed:', content != content2)

with open('site/well.html', 'w') as f:
    f.write(content2)
print('Done')