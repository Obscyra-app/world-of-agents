
import re
with open('site/guestbook.html', 'r') as f:
    content = f.read()
# Count opening and closing tags (ignoring attributes for simplicity)
tags = ['html', 'head', 'body', 'ul', 'li']
opens = {}
closes = {}
for tag in tags:
    opens[tag] = len(re.findall(f'<{tag}[^>]*>', content))
    closes[tag] = len(re.findall(f'</{tag}>', content))
    print(f'{tag}: opens={opens[tag]}, closes={closes[tag]}')
# We'll assume extra closing tags are at the end and remove them.
# We'll work from the end of the string.
# We'll create a list of tags to remove (closing tags) in reverse order.
to_remove = []
for tag in tags:
    if closes[tag] > opens[tag]:
        to_remove.extend([f'</{tag}>'] * (closes[tag] - opens[tag]))
print(f'Tags to remove from end: {to_remove}')
# Now remove from the end.
for tag in to_remove:
    # Find the last occurrence of this tag, ignoring trailing whitespace.
    # We'll search for the tag followed by optional whitespace and then the end of string.
    pattern = re.escape(tag) + r'\s*$'
    if re.search(pattern, content):
        # Remove the tag and any trailing whitespace after it.
        content = re.sub(pattern, '', content)
    else:
        # If not found at the end, we remove the last occurrence anywhere.
        last_pos = content.rfind(tag)
        if last_pos != -1:
            content = content[:last_pos] + content[last_pos+len(tag):]
        else:
            print(f'Warning: could not find {tag} to remove')
# Now write back.
with open('site/guestbook.html', 'w') as f:
    f.write(content)
print('Fixed extra closing tags.')
