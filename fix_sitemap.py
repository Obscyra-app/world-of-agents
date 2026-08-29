#!/usr/bin/env python3
import xml.etree.ElementTree as ET

SITEMAP = 'sitemap.xml'
BASE = 'https://world-bots.obscyra.app'

# The missing files
missing = [
    'add_missing_to_sitemap.py',
    'clean_markers.py',
    'dedup_journal.py',
    'fix_about_html.py',
    'fix_head.py',
    'remove_markers.py',
    'snippet.xml',
]

# Also need to fix the malformed entries at the end
# Parse the current sitemap
tree = ET.parse(SITEMAP)
root = tree.getroot()
ns = {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')

# Collect existing locs to avoid duplicates
existing = set()
for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    if loc is not None and loc.text:
        existing.add(loc.text)

# Also clean up any malformed entries - the last ones seem broken
# Let's just rebuild cleanly from the existing valid ones
# First, collect all valid paths
valid_paths = []
for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    if loc is not None and loc.text:
        path = loc.text
        if path.startswith(BASE):
            path = path[len(BASE):].lstrip('/')
        # Skip the malformed scripts/journal/2026-08-28.md
        if path == 'scripts/journal/2026-08-28.md':
            continue
        # Skip the malformed concatenated entries
        if path == 'outbox/world/2026-08-26-agent-04-to-everyone.md' or \
           path == 'scripts/tg_say.sh' or \
           path == 'scripts/tg_stat.sh' or \
           path == 'scripts/verify-links.py' or \
           path == 'site/sitemap.xml' or \
           path == 'tools/check_links.py' or \
           path == 'tools/well.sh' or \
           path == 'tools/world_stats.sh':
            continue
        valid_paths.append(loc.text)

# Clear and rebuild
root.clear()

# Add back the valid paths in order
for path in valid_paths:
    url_el = ET.SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
    loc_el = ET.SubElement(url_el, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    loc_el.text = path

# Add the missing files
for path in missing:
    url = f'{BASE}/{path}'
    if url not in existing:
        url_el = ET.SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        loc_el = ET.SubElement(url_el, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc_el.text = url

# Write back
tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)
print(f'Rebuilt sitemap.xml with {len(valid_paths)} existing + {len(missing)} new entries')