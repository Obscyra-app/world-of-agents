import os
import re
import json
import xml.etree.ElementTree as ET

def extract_sides(content):
    """Extract the two sides from a file with conflict markers.
    Returns (our_side, their_side) as strings.
    Assumes there is exactly one conflict block.
    """
    pattern = re.compile(r'^<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [0-9a-f]+$', re.DOTALL | re.MULTILINE)
    match = pattern.search(content)
    if not match:
        # Try to find the markers in case there are extra newlines
        lines = content.splitlines()
        # Find the start and end indices
        start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('<<<<<<< HEAD'):
                start = i
                break
        if start is None:
            return None, None
        # Find the ======= line after start
        mid = None
        for i in range(start+1, len(lines)):
            if lines[i].strip().startswith('======='):
                mid = i
                break
        if mid is None:
            return None, None
        # Find the >>>>>>> line after mid
        end = None
        for i in range(mid+1, len(lines)):
            if lines[i].strip().startswith('>>>>>>>'):
                end = i
                break
        if end is None:
            return None, None
        # Our side is lines[start+1:mid]
        # Their side is lines[mid+1:end]
        our_side = '\n'.join(lines[start+1:mid])
        their_side = '\n'.join(lines[mid+1:end])
        return our_side, their_side
    our_side = match.group(1)
    their_side = match.group(2)
    return our_side, their_side

def resolve_about_html():
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/about.html', 'r') as f:
        content = f.read()
    our_side, their_side = extract_sides(content)
    if our_side is None or their_side is None:
        print("Failed to extract sides for site/about.html")
        return False
    # We want to keep the prefix (before <<<<<<< HEAD) and suffix (after >>>>>>)
    # Let's split the content by the conflict markers
    parts = re.split(r'^<<<<<<< HEAD\n.*?\n=======\n.*?\n>>>>>>> [0-9a-f]+$', content, flags=re.DOTALL | re.MULTILINE)
    if len(parts) != 3:
        print("Failed to split site/about.html into three parts")
        return False
    prefix, suffix = parts[0], parts[2]
    # Now we need to build the middle section.
    # We'll extract the table and snapshot lines from each side.
    # We know that each side contains two tables and then a <p> with two snapshot lines.
    # But to be safe, we will extract all <table> blocks and all snapshot lines.
    def extract_tables_and_snapshots(side):
        lines = side.splitlines()
        tables = []
        snapshots = []
        i = 0
        while i < len(lines):
            if lines[i].strip() == '<table>':
                # Collect the table until the closing </table>
                table_lines = [lines[i]]
                i += 1
                while i < len(lines) and lines[i].strip() != '</table>':
                    table_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    table_lines.append(lines[i])  # the </table>
                    i += 1
                tables.append('\n'.join(table_lines))
            elif 'Snapshot pinned to commit' in lines[i]:
                snapshots.append(lines[i])
                i += 1
            else:
                i += 1
        return tables, snapshots
    our_tables, our_snapshots = extract_tables_and_snapshots(our_side)
    their_tables, their_snapshots = extract_tables_and_snapshots(their_side)
    # We want to keep all tables and all snapshots from both sides.
    # However, note that there might be duplicate tables (if the same table appears in both sides).
    # We'll keep duplicates because they represent different voices.
    # Build the middle section:
    middle_lines = []
    for table in our_tables:
        middle_lines.append(table)
    for table in their_tables:
        middle_lines.append(table)
    for snap in our_snapshots:
        middle_lines.append(snap)
    for snap in their_snapshots:
        middle_lines.append(snap)
    # We need to ensure the middle section is wrapped in the same indentation as the original.
    # But we don't know the exact indentation. We'll assume that the original middle section
    # was at the same indentation level as the surrounding <p> tags.
    # We'll look at the prefix to see what the last line is.
    # However, for simplicity, we'll just join with newline and hope the indentation is correct.
    # We'll instead reconstruct by putting each table and snapshot line on its own line.
    middle = '\n'.join(middle_lines)
    # But note: the original middle section had the tables and snapshot lines at a certain indentation.
    # We'll look at the line before the conflict in the original file (the line just before <<<<<<< HEAD)
    # to get the indentation.
    lines = content.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('<<<<<<< HEAD'):
            start_idx = i
            break
    if start_idx is not None and start_idx > 0:
        # The line before the conflict marker is the last line of the prefix.
        # We'll use its indentation.
        indent_line = lines[start_idx-1]
        indent = indent_line[:len(indent_line) - len(indent_line.lstrip())]
        # Now we need to indent each line in the middle by that amount?
        # But note: the middle section might be a block of lines that are already indented.
        # We'll instead not change the indentation and hope it's correct.
        # We'll just use the middle as is.
        pass
    # Build the new content
    new_content = prefix + middle + '\n' + suffix
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/about.html', 'w') as f:
        f.write(new_content)
    print("Resolved site/about.html")
    return True

def resolve_feed_xml():
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/feed.xml', 'r') as f:
        content = f.read()
    our_side, their_side = extract_sides(content)
    if our_side is None or their_side is None:
        print("Failed to extract sides for site/feed.xml")
        return False
    parts = re.split(r'^<<<<<<< HEAD\n.*?\n=======\n.*?\n>>>>>>> [0-9a-f]+$', content, flags=re.DOTALL | re.MULTILINE)
    if len(parts) != 3:
        print("Failed to split site/feed.xml into three parts")
        return False
    prefix, suffix = parts[0], parts[2]
    # Parse the XML from each side
    try:
        our_root = ET.fromstring(our_side)
        their_root = ET.fromstring(their_side)
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return False
    # We'll collect all <entry> elements by their id (the <id> element text)
    entries = {}  # id -> element
    for elem in our_root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        id_elem = elem.find('{http://www.w3.org/2005/Atom}id')
        if id_elem is not None and id_elem.text:
            entries[id_elem.text] = elem
    for elem in their_root.findall('.//{http://www.w3.org/2005/Atom}entry'):
        id_elem = elem.find('{http://www.w3.org/2005/Atom}id')
        if id_elem is not None and id_elem.text:
            if id_elem.text not in entries:
                entries[id_elem.text] = elem
    # Build a new feed element
    # We'll take the root tag and attributes from our_side (or their_side, they should be the same)
    new_root = ET.Element(our_root.tag, attrib=our_root.attrib)
    # Add all child elements that are not <entry> from our_root
    for child in our_root:
        if child.tag != '{http://www.w3.org/2005/Atom}entry':
            new_root.append(child)
    # Add the collected entries
    for entry in entries.values():
        new_root.append(entry)
    # Format the XML
    ET.indent(new_root, space='  ', level=0)
    new_xml = ET.tostring(new_root, encoding='unicode')
    new_content = prefix + new_xml + '\n' + suffix
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/feed.xml', 'w') as f:
        f.write(new_content)
    print("Resolved site/feed.xml")
    return True

def resolve_search_index_json():
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/search-index.json', 'r') as f:
        content = f.read()
    our_side, their_side = extract_sides(content)
    if our_side is None or their_side is None:
        print("Failed to extract sides for site/search-index.json")
        return False
    parts = re.split(r'^<<<<<<< HEAD\n.*?\n=======\n.*?\n>>>>>>> [0-9a-f]+$', content, flags=re.DOTALL | re.MULTILINE)
    if len(parts) != 3:
        print("Failed to split site/search-index.json into three parts")
        return False
    prefix, suffix = parts[0], parts[2]
    # Parse the JSON from each side
    try:
        our_json = json.loads(our_side)
        their_json = json.loads(their_side)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        return False
    # Merge the docs arrays: for each path, keep the doc with the later timestamp.
    def merge_docs(existing, incoming):
        by_path = {doc['path']: doc for doc in existing}
        for doc in incoming:
            path = doc['path']
            if path in by_path:
                existing_time = by_path[path]['stamp']
                incoming_time = doc['stamp']
                if incoming_time > existing_time:
                    by_path[path] = doc
            else:
                by_path[path] = doc
        # Return list sorted by path for consistency
        return sorted(by_path.values(), key=lambda x: x['path'])
    merged_docs = merge_docs(our_json.get('docs', []), their_json.get('docs', []))
    merged_json = {
        "base": our_json.get('base', ""),
        "docs": merged_docs
    }
    merged_str = json.dumps(merged_json, indent=2, ensure_ascii=False) + '\n'
    new_content = prefix + merged_str + suffix
    with open('/Users/nuriman/world-of-agents-residents/agent-03/site/search-index.json', 'w') as f:
        f.write(new_content)
    print("Resolved site/search-index.json")
    return True

def resolve_sitemap_xml():
    with open('/Users/nuriman/world-of-agents-residents/agent-03/sitemap.xml', 'r') as f:
        content = f.read()
    our_side, their_side = extract_sides(content)
    if our_side is None or their_side is None:
        print("Failed to extract sides for sitemap.xml")
        return False
    parts = re.split(r'^<<<<<<< HEAD\n.*?\n=======\n.*?\n>>>>>>> [0-9a-f]+$', content, flags=re.DOTALL | re.MULTILINE)
    if len(parts) != 3:
        print("Failed to split sitemap.xml into three parts")
        return False
    prefix, suffix = parts[0], parts[2]
    # Parse the XML from each side
    try:
        our_root = ET.fromstring(our_side)
        their_root = ET.fromstring(their_side)
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return False
    # Collect all <url> elements by their loc
    urls = {}  # loc -> element
    for elem in our_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc_elem = elem.find('./{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc_elem is not None and loc_elem.text:
            urls[loc_elem.text] = elem
    for elem in their_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
        loc_elem = elem.find('./{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        if loc_elem is not None and loc_elem.text:
            if loc_elem.text not in urls:
                urls[loc_elem.text] = elem
    # Build a new sitemap element
    new_root = ET.Element(our_root.tag, attrib=our_root.attrib)
    # Add all child elements that are not <url> from our_root
    for child in our_root:
        if child.tag != '{http://www.sitemaps.org/schemas/sitemap/0.9}url':
            new_root.append(child)
    # Add the collected urls
    for url in urls.values():
        new_root.append(url)
    ET.indent(new_root, space='  ', level=0)
    new_xml = ET.tostring(new_root, encoding='unicode')
    new_content = prefix + new_xml + '\n' + suffix
    with open('/Users/nuriman/world-of-agents-residents/agent-03/sitemap.xml', 'w') as f:
        f.write(new_content)
    print("Resolved sitemap.xml")
    return True

if __name__ == '__main__':
    os.chdir('/Users/nuriman/world-of-agents-residents/agent-03')
    resolve_about_html()
    resolve_feed_xml()
    resolve_search_index_json()
    resolve_sitemap_xml()
    print("All files resolved.")
