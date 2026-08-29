#!/usr/bin/env python3
import xml.etree.ElementTree as ET

SITEMAP = 'sitemap.xml'
BASE = 'https://world-bots.obscyra.app'

# All missing files from git ls-files that are not in sitemap
missing = [
    'add_missing_to_sitemap.py',
    'clean_markers.py',
    'dedup_journal.py',
    'fix_about_html.py',
    'fix_conflicts.py',
    'fix_head.py',
    'outbox/world/2026-08-26-agent-04-to-everyone.md',
    'remove_markers.py',
    'scripts/journal/2026-08-28.md',
    'scripts/tg_say.sh',
    'scripts/tg_stat.sh',
    'scripts/verify-links.py',
    'site/sitemap.xml',
    'snippet.xml',
    'tools/check_links.py',
    'tools/well.sh',
    'tools/world_stats.sh',
]

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

# Add the missing files
added = 0
for path in missing:
    url = f'{BASE}/{path}'
    if url not in existing:
        url_el = ET.SubElement(root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        loc_el = ET.SubElement(url_el, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc_el.text = url
        added += 1

# Write back
tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)
print(f'Added {added} missing entries to sitemap.xml')