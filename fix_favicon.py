import os
import sys

SITE_DIR = 'site'

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find the index of </head>
    try:
        head_end = next(i for i, line in enumerate(lines) if line.strip() == '</head>')
    except StopIteration:
        print(f"Warning: {filepath} has no </head> tag", file=sys.stderr)
        return False

    # Determine the correct favicon href based on file's depth relative to site/
    rel_path = os.path.relpath(filepath, SITE_DIR)
    # Count how many levels up we need to go to reach site/ from the file's directory
    # Actually we want the href such that when resolved from the file's directory, it points to site/favicon.svg
    file_dir = os.path.dirname(filepath)
    target = os.path.join(SITE_DIR, 'favicon.svg')
    # Compute relative path from file_dir to target
    href = os.path.relpath(target, file_dir)
    # Ensure it uses forward slash
    href = href.replace(os.sep, '/')

    # We'll rebuild the head section, keeping all lines except any existing favicon links.
    new_head_lines = []
    for line in lines[:head_end]:
        stripped = line.strip()
        # Check if this line is a link tag with rel="icon" (case-insensitive)
        if stripped.lower().startswith('<link') and 'rel="icon"' in stripped.lower():
            # Skip this line; we'll add our own later
            continue
        new_head_lines.append(line)
    # Add the favicon tag (we'll add it before the closing head, but we can add it now)
    new_head_lines.append(f'  <link rel="icon" href="{href}">\n')
    # The tail (from head_end onward) remains the same.
    new_tail = lines[head_end:]

    new_lines = new_head_lines + new_tail

    if new_lines == lines:
        return False  # no change

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return True

def main():
    updated = []
    for fname in os.listdir(SITE_DIR):
        if fname.endswith('.html'):
            filepath = os.path.join(SITE_DIR, fname)
            if process_file(filepath):
                updated.append(filepath)

    if updated:
        print(f"Updated favicon in {len(updated)} file(s):")
        for f in updated:
            print(f"  {f}")
    else:
        print("All site/*.html files already have correct favicon href.")

if __name__ == '__main__':
    main()