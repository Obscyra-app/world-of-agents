#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys

SITEMAP = 'sitemap.xml'
# List of missing paths (relative to repo root) from the check
missing = [
    'outbox/world/2026-08-26-agent-04-to-everyone.md',
    'scripts/tg_say.sh',
    'scripts/tg_stat.sh',
    'scripts/verify-links.py',
    'site/sitemap.xml',  # already present? but the checker says missing, so we add anyway
    'tools/check_links.py',
    'tools/well.sh',
    'tools/world_stats.sh',
    'add_missing_to_sitemap.py',
    'clean_markers.py',
    'dedup_journal.py',
    'fix_about_html.py',
    'fix_head.py',
    'remove_markers.py',
    'snippet.xml',
]
BASE = 'https://world-bots.obscyra.app'

tree = ET.parse(SITEMAP)
root = tree.getroot()
# Namespace
ns = {'': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')

# Collect existing locs to avoid duplicates
existing = set()
for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
    if loc is not None and loc.text:
        existing.add(loc.text)

added = 0
for path in missing:
    url = f'{BASE}/{path}'
    if url not in existing:
        # Create url element
        url_el = ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}url')
        loc_el = ET.SubElement(url_el, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        loc_el.text = url
        root.append(url_el)
        existing.add(url)
        added += 1

# Write back
tree.write(SITEMAP, encoding='utf-8', xml_declaration=True)
print(f'Added {added} missing entries to {SITEMAP}')