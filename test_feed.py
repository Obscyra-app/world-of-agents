#!/usr/bin/env python3
import xml.etree.ElementTree as ET

root = ET.parse('site/feed.xml').getroot()
ns = {'atom': 'http://www.w3.org/2005/Atom'}
title = root.find('atom:title', ns)
print(f'Feed title: {title.text if title is not None else "N/A"}')
entries = root.findall('atom:entry', ns)
print(f'Entries: {len(entries)}')
for e in entries[:3]:
    t = e.find('atom:title', ns)
    u = e.find('atom:updated', ns)
    print(f'  {t.text if t is not None else "N/A"} - {u.text if u is not None else "N/A"}')