with open('site/well.html', 'r') as f:
    content = f.read()

# The problem: the text "guestbook structure scar (extra </ul>) healed" 
# contains a literal </ul> which the structure checker counts as a closing tag
# We need to escape it to </ul> in the HTML content
content = content.replace('guestbook structure scar (extra </ul>) healed', 'guestbook structure scar (extra </ul>) healed')

with open('site/well.html', 'w') as f:
    f.write(content)
print('Done')