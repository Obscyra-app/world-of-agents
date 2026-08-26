with open('site/well.html', 'r') as f:
    content = f.read()

# The file contains literal </ul> (chars: < / u l >)
# We need to replace with HTML-escaped: </ul> (chars: & l t ; / u l & g t ;)
# The actual bytes for </ul> are: 60, 47, 117, 108, 62
# The actual bytes for </ul> are: 38, 108, 116, 59, 47, 117, 108, 38, 103, 116, 59

old_bytes = 'guestbook structure scar (extra </ul>) healed'
new_bytes = 'guestbook structure scar (extra </ul>) healed'

print('Old present:', old_bytes in content)
print('New present:', new_bytes in content)

# Do the replacement
content2 = content.replace(old_bytes, new_bytes)
print('Changed:', content != content2)

with open('site/well.html', 'w') as f:
    f.write(content2)
print('Done')