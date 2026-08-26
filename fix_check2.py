with open('site/well.html', 'rb') as f:
    content = f.read()

# Find the problematic literal </ul> in text content and replace with HTML entities
# The literal bytes are: < / u l >
# We want to replace with: & l t ; / u l & g t ;
content = content.replace(b'extra </ul>)', b'extra </ul>)')

with open('site/well.html', 'wb') as f:
    f.write(content)
print('Done')