from urllib.request import urlopen
from datetime import datetime
import os
from typing import Set, Tuple

def get_current_tlds() -> Set[str]:
    """Read current TLDs from the repository file."""
    with open('tlds.txt', 'r') as f:
        lines = f.readlines()
    return {line.strip() for line in lines if not line.startswith('#')}

def get_new_tlds() -> Tuple[Set[str], str]:
    """Fetch new TLDs from IANA website."""
    with urlopen('https://data.iana.org/TLD/tlds-alpha-by-domain.txt') as response:
        content = response.read().decode('utf-8')
    lines = content.split('\n')
    return {line.strip() for line in lines if line.strip() and not line.startswith('#')}, ''

def ensure_readme_exists():
    """Create README.md if it doesn't exist"""
    if not os.path.exists('README.md'):
        with open('README.md', 'w') as f:
            f.write('''# TLD Monitor

This repository monitors the [IANA Top Level Domain list](https://data.iana.org/TLD/tlds-alpha-by-domain.txt) daily for changes. It automatically detects when new TLDs are added or removed and updates this README with the changes.

The script runs daily at midnight UTC to check for updates.\n\n''')

def format_number(num: int) -> str:
    """Format number with comma separators"""
    return f"{num:,}"

def update_readme(added: Set[str], removed: Set[str], total: int):
    """Update the README.md file with new statistics."""
    ensure_readme_exists()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Read existing README content
    with open('README.md', 'r') as f:
        readme_content = f.readlines()
    
    # Find where the statistics section starts
    stats_start = -1
    for i, line in enumerate(readme_content):
        if line.strip() == '## TLD Statistics':
            stats_start = i
            break
    
    new_content = []
    if stats_start == -1:
        # If no statistics section exists, create it
        new_content = readme_content + [
            '\n## TLD Statistics\n\n',
            '| Metric | Value |\n',
            '|--------|-------|\n',
            f'| Total TLDs | {format_number(total)} |\n',
            f'| Last Checked | {today} |\n\n',
            '### Changes Log\n\n',
            '| Date | Type | TLDs |\n',
            '|------|------|------|\n'
        ]
        if added:
            new_content.append(f'| {today} | Added | {", ".join(sorted(added))} |\n')
        if removed:
            new_content.append(f'| {today} | Removed | {", ".join(sorted(removed))} |\n')
    else:
        # Update existing statistics section
        new_content = readme_content[:stats_start + 1]
        new_content.extend([
            '\n',
            '| Metric | Value |\n',
            '|--------|-------|\n',
            f'| Total TLDs | {format_number(total)} |\n',
            f'| Last Checked | {today} |\n\n',
            '### Changes Log\n\n'
        ])

        # Check if changes log table exists
        table_exists = False
        for line in readme_content[stats_start:]:
            if '| Date | Type | TLDs |' in line:
                table_exists = True
                break

        if not table_exists:
            new_content.extend([
                '| Date | Type | TLDs |\n',
                '|------|------|------|\n'
            ])

        # Add new changes at the top of the existing log
        if added or removed:
            changes_lines = []
            if added:
                changes_lines.append(f'| {today} | Added | {", ".join(sorted(added))} |\n')
            if removed:
                changes_lines.append(f'| {today} | Removed | {", ".join(sorted(removed))} |\n')

            # Find where to insert the new changes
            for i, line in enumerate(readme_content[stats_start:]):
                if '|------|------|------|' in line:
                    table_start = i + stats_start + 1
                    new_content.extend(readme_content[stats_start:table_start])
                    new_content.extend(changes_lines)
                    new_content.extend(readme_content[table_start:])
                    break
            else:
                # If table header wasn't found, add it with the new changes
                new_content.extend([
                    '| Date | Type | TLDs |\n',
                    '|------|------|------|\n'
                ])
                new_content.extend(changes_lines)

    # Write updated content
    with open('README.md', 'w') as f:
        f.writelines(new_content)

def main():
    ensure_readme_exists()  # Make sure README.md exists
    current_tlds = get_current_tlds()
    new_tlds, _ = get_new_tlds()
    
    added = new_tlds - current_tlds
    removed = current_tlds - new_tlds
    
    # Always update the README with current statistics
    update_readme(added, removed, len(new_tlds))
    
    if added or removed:
        # Update the TLDs file (without the version line)
        with open('tlds.txt', 'w') as f:
            for tld in sorted(new_tlds):
                f.write(tld + '\n')
        
        # Exit with status 1 to indicate changes were made
        exit(1)
    
    # Exit with status 0 to indicate no changes
    exit(0)

if __name__ == '__main__':
    main() 