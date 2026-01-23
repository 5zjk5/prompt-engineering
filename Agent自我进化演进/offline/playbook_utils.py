"""
==============================================================================
playbook.py
==============================================================================

This file contains functions for parsing and manipulating the playbook.

"""

import json
import re
from offline.utils import get_section_slug


def extract_section_identifier(section_header):
    """
    Extract section identifier from header.

    Supports two formats:
    1. "## STRATEGIES & INSIGHTS (strategies_and_insights)" → returns "strategies_and_insights"
    2. "## STRATEGIES & INSIGHTS" → returns "strategies_and_insights" (normalized)

    Args:
        section_header: Section header line (e.g., "## STRATEGIES & INSIGHTS (strategies_and_insights)")

    Returns:
        Section identifier string
    """
    header = section_header.strip()[2:].strip()

    # Check if identifier is in parentheses
    match = re.search(r'\(([^)]+)\)$', header)
    if match:
        return match.group(1)

    # Fallback: normalize the header
    return header.lower().replace(' ', '_').replace('&', 'and')


def parse_playbook_line(line):
    """Parse a single playbook line to extract components"""
    # Pattern: [id] helpful=X harmful=Y :: content
    pattern = r'\[([^\]]+)\]\s*helpful=(\d+)\s*harmful=(\d+)\s*::\s*(.*)'
    match = re.match(pattern, line.strip())

    if match:
        return {
            'id': match.group(1),
            'helpful': int(match.group(2)),
            'harmful': int(match.group(3)),
            'content': match.group(4),
            'raw_line': line,
        }
    return None


def get_next_global_id(playbook_text):
    """Extract highest global ID and return next one"""
    max_id = 0
    lines = playbook_text.strip().split('\n')

    for line in lines:
        parsed = parse_playbook_line(line)
        if parsed:
            # Extract numeric part from ID
            id_match = re.search(r'-(\d+)$', parsed['id'])
            if id_match:
                num = int(id_match.group(1))
                max_id = max(max_id, num)

    return max_id + 1


def format_playbook_line(bullet_id, helpful, harmful, content):
    """Format a bullet into playbook line format"""
    return f"[{bullet_id}] helpful={helpful} harmful={harmful} :: {content}"


def update_bullet_counts(playbook_text, bullet_tags, logger):
    """Update helpful/harmful counts based on tags (Counter layer)"""
    lines = playbook_text.strip().split('\n')
    updated_lines = []

    # Create tag lookup - handle both old and new formats
    tag_map = {}
    if isinstance(bullet_tags, list) and len(bullet_tags) > 0:
        for tag in bullet_tags:
            if isinstance(tag, dict):
                # Handle both 'id' and 'bullet' keys for backwards compatibility
                bullet_id = tag.get('id') or tag.get('bullet', '')
                tag_value = tag.get('tag', 'neutral')
                if bullet_id:
                    tag_map[bullet_id] = tag_value

    if not tag_map:
        logger.warning("Warning: No valid bullet tags found to update counts")
        return playbook_text

    for line in lines:
        if line.strip().startswith('#') or not line.strip():
            # Preserve section headers and empty lines
            updated_lines.append(line)
            continue

        parsed = parse_playbook_line(line)
        if parsed and parsed['id'] in tag_map:
            tag = tag_map[parsed['id']]
            if tag == 'helpful':
                parsed['helpful'] += 1
            elif tag == 'harmful':
                parsed['harmful'] += 1
            # neutral: no change

            # Reconstruct line with updated counts
            new_line = format_playbook_line(
                parsed['id'], parsed['helpful'], parsed['harmful'], parsed['content']
            )
            updated_lines.append(new_line)
        else:
            updated_lines.append(line)

    return '\n'.join(updated_lines)


def apply_curator_operations(playbook_text, operations, next_id, logger):
    """
    Apply curator operations to playbook

    Supported Operations:
    - ADD: Create new bullet points with fresh IDs
    - UPDATE: Update the content of an existing bullet point
    - MERGE: Combine related bullets into stronger ones
    - DELETE: Remove outdated or incorrect bullets
    - CREATE_META: Add high-level strategy sections
    """
    lines = playbook_text.strip().split('\n')

    # Build section map and bullet ID map
    sections = {}
    current_section = "general"
    section_line_map = {}  # Track which line each section header is on
    bullet_id_map = {}  # Map bullet_id to its line index and parsed data

    for i, line in enumerate(lines):
        if line.strip().startswith('##'):
            current_section = extract_section_identifier(line)
            section_line_map[current_section] = i
            if current_section not in sections:
                sections[current_section] = []
        elif line.strip():
            sections[current_section].append((i, line))
            parsed = parse_playbook_line(line)
            if parsed:
                bullet_id_map[parsed['id']] = (i, parsed)

    # Process operations
    bullets_to_add = []
    bullets_to_update = {}
    bullets_to_delete = set()
    sections_to_create = []
    valid_operations = []

    for op in operations:
        op_type = op['type']

        if op_type == 'ADD':
            section_raw = op.get('section', 'general')
            section = section_raw

            # Check if section exists, if not use 'others'
            if section not in sections and section != 'general':
                logger.warning(
                    f"Warning: Section '{section_raw}' not found, adding to OTHERS"
                )
                section = 'others'

            slug = get_section_slug(section)
            new_id = f"{slug}-{next_id:05d}"
            next_id += 1

            content = op.get('content', '')

            new_line = format_playbook_line(new_id, 0, 0, content)
            bullets_to_add.append((section, new_line))
            valid_operations.append(op)
            logger.info(f"  Added bullet {new_id} to section {section}")

        elif op_type == 'UPDATE':
            bullet_id = op.get('bullet_id', '')
            if bullet_id not in bullet_id_map:
                logger.warning(
                    f"  Skipping UPDATE: bullet_id '{bullet_id}' not found in playbook"
                )
                continue
            new_content = op.get('content', '')
            bullets_to_update[bullet_id] = new_content
            valid_operations.append(op)
            logger.info(f"  Update bullet {bullet_id}")

        elif op_type == 'MERGE':
            source_ids = op.get('source_ids', [])
            valid_source_ids = []
            for source_id in source_ids:
                if source_id not in bullet_id_map:
                    logger.warning(
                        f"  Skipping MERGE: source_id '{source_id}' not found in playbook"
                    )
                else:
                    valid_source_ids.append(source_id)
            if len(valid_source_ids) < 2:
                logger.warning(
                    f"  Skipping MERGE: need at least 2 valid source_ids, got {len(valid_source_ids)}"
                )
                continue
            bullets_to_delete.update(valid_source_ids)
            # Create new merged bullet
            section_raw = op.get('section', 'general')
            section = section_raw
            if section not in sections and section != 'general':
                logger.info(
                    f"Warning: Section '{section_raw}' not found, adding to OTHERS"
                )
                section = 'others'
            slug = get_section_slug(section)
            new_id = f"{slug}-{next_id:05d}"
            next_id += 1
            content = op.get('content', '')
            new_line = format_playbook_line(new_id, 0, 0, content)
            bullets_to_add.append((section, new_line))
            valid_operations.append(op)
            logger.info(f"  Merged bullets {valid_source_ids} into {new_id}")

        elif op_type == 'DELETE':
            bullet_id = op.get('bullet_id', '')
            if bullet_id not in bullet_id_map:
                logger.warning(
                    f"  Skipping DELETE: bullet_id '{bullet_id}' not found in playbook"
                )
                continue
            bullets_to_delete.add(bullet_id)
            valid_operations.append(op)
            logger.info(f"  Delete bullet {bullet_id}")

        elif op_type == 'CREATE_META':
            section_name = op.get('section_name', 'META_STRATEGIES')
            content = op.get('content', '')
            section_header = f"## {section_name}"
            section_normalized = extract_section_identifier(section_header)

            # Check if section already exists
            existing_sections = [
                extract_section_identifier(line)
                for line in lines
                if line.strip().startswith('##')
            ]
            if section_normalized in existing_sections:
                logger.warning(
                    f"  Skipping CREATE_META: section '{section_name}' already exists"
                )
                continue
            sections_to_create.append((section_name, content))
            logger.info(f"  Create new section {section_name}")
            valid_operations.append(op)

    # Rebuild playbook
    new_lines = []
    for line in lines:
        parsed = parse_playbook_line(line)
        if parsed:
            if parsed['id'] in bullets_to_delete:
                continue
            if parsed['id'] in bullets_to_update:
                new_content = bullets_to_update[parsed['id']]
                new_line = format_playbook_line(
                    parsed['id'], parsed['helpful'], parsed['harmful'], new_content
                )
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add new sections from CREATE_META operations
    for section_name, content in sections_to_create:
        section_header = f"## {section_name}"
        if section_header not in new_lines:
            new_lines.append("")
            new_lines.append(section_header)
            new_lines.append("")
            slug = get_section_slug(extract_section_identifier(section_header))
            new_id = f"{slug}-{next_id:05d}"
            next_id += 1
            new_line = format_playbook_line(new_id, 0, 0, content)
            new_lines.append(new_line)

    # Add new bullets to appropriate sections
    final_lines = []
    current_section = None

    for line in new_lines:
        if line.strip().startswith('##'):
            # Before moving to new section, add any bullets for current section
            if current_section:
                section_adds = [b for s, b in bullets_to_add if s == current_section]
                final_lines.extend(section_adds)
                # Clear added bullets
                bullets_to_add = [
                    (s, b) for s, b in bullets_to_add if s != current_section
                ]

            current_section = extract_section_identifier(line)
        final_lines.append(line)

    # Add remaining bullets to current section
    if current_section:
        section_adds = [b for s, b in bullets_to_add if s == current_section]
        final_lines.extend(section_adds)
        bullets_to_add = [(s, b) for s, b in bullets_to_add if s != current_section]

    # If there are still bullets to add (for sections that don't exist), add them to OTHERS
    if bullets_to_add:
        logger.info(
            f"Warning: {len(bullets_to_add)} bullets have no matching section, adding to OTHERS"
        )
        others_bullets = [b for s, b in bullets_to_add]
        # Find OTHERS section
        others_idx = -1
        for i, line in enumerate(final_lines):
            if line.strip() == "## OTHERS":
                others_idx = i
                break

        if others_idx >= 0:
            # Insert after OTHERS header
            for i, bullet in enumerate(others_bullets):
                final_lines.insert(others_idx + 1 + i, bullet)
        else:
            # Append to end
            final_lines.extend(others_bullets)

    return '\n'.join(final_lines), next_id, valid_operations


def get_playbook_stats(playbook_text):
    """Generate statistics about the playbook"""
    lines = playbook_text.strip().split('\n')
    stats = {
        'total_bullets': 0,
        'high_performing': 0,  # helpful > 5, harmful < 2
        'problematic': 0,  # harmful >= helpful
        'unused': 0,  # helpful + harmful = 0
        'by_section': {},
    }

    current_section = 'general'

    for line in lines:
        if line.strip().startswith('##'):
            current_section = extract_section_identifier(line)
            continue

        parsed = parse_playbook_line(line)
        if parsed:
            stats['total_bullets'] += 1

            if parsed['helpful'] > 5 and parsed['harmful'] < 2:
                stats['high_performing'] += 1
            elif parsed['harmful'] >= parsed['helpful'] and parsed['harmful'] > 0:
                stats['problematic'] += 1
            elif parsed['helpful'] + parsed['harmful'] == 0:
                stats['unused'] += 1

            if current_section not in stats['by_section']:
                stats['by_section'][current_section] = {
                    'count': 0,
                    'helpful': 0,
                    'harmful': 0,
                }

            stats['by_section'][current_section]['count'] += 1
            stats['by_section'][current_section]['helpful'] += parsed['helpful']
            stats['by_section'][current_section]['harmful'] += parsed['harmful']

    return stats


def extract_json_from_text(text, logger, json_key=None):
    """Extract JSON object from text, handling various formats"""
    try:
        # First, try to parse the entire response as JSON (JSON mode)
        try:
            result = json.loads(text.strip())
            return result
        except json.JSONDecodeError:
            pass

        # Fallback: Look for ```json blocks
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, text, re.DOTALL | re.IGNORECASE)

        if matches:
            # Try each match until we find valid JSON
            for match in matches:
                try:
                    json_str = match.strip()
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    continue

        # Improved JSON extraction using balanced brace counting
        # This handles deeply nested structures better
        def find_json_objects(text):
            """Find JSON objects using balanced brace counting"""
            json_objects = []
            i = 0
            while i < len(text):
                if text[i] == '{':
                    # Found start of potential JSON object
                    brace_count = 1
                    start = i
                    i += 1

                    while i < len(text) and brace_count > 0:
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                        elif text[i] == '"':
                            # Handle quoted strings to avoid counting braces inside strings
                            i += 1
                            while i < len(text) and text[i] != '"':
                                if text[i] == '\\':
                                    i += 1  # Skip escaped character
                                i += 1
                        i += 1

                    if brace_count == 0:
                        # Found complete JSON object
                        json_candidate = text[start:i]
                        json_objects.append(json_candidate)
                else:
                    i += 1

            return json_objects

        # Find all potential JSON objects
        json_objects = find_json_objects(text)

        for json_str in json_objects:
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                continue

    except Exception as e:
        import traceback

        logger.error(traceback.format_exc())
        logger.error(f"Failed to extract JSON: {e}")
        if len(text) > 500:
            logger.info(f"Raw content preview:\n{text[:500]}...")
        else:
            logger.info(f"Raw content:\n{text}")

    return None


def extract_playbook_bullets(playbook_text, bullet_ids):
    """
    Extract specific bullet points from playbook based on bullet_ids.

    Args:
        playbook_text (str): The full playbook text
        bullet_ids (list): List of bullet IDs to extract

    Returns:
        str: Formatted playbook content containing only the specified bullets
    """
    if not bullet_ids:
        return "(No bullets used by generator)"

    lines = playbook_text.strip().split('\n')
    found_bullets = []

    for line in lines:
        if line.strip():  # Skip empty lines
            parsed = parse_playbook_line(line)
            if parsed and parsed['id'] in bullet_ids:
                found_bullets.append(
                    {
                        'id': parsed['id'],
                        'content': parsed['content'],
                        'helpful': parsed['helpful'],
                        'harmful': parsed['harmful'],
                    }
                )

    if not found_bullets:
        return "(Generator referenced bullet IDs but none were found in playbook)"

    # Format the bullets for reflector input
    formatted_bullets = []
    for bullet in found_bullets:
        formatted_bullets.append(
            f"[{bullet['id']}] helpful={bullet['helpful']} harmful={bullet['harmful']} :: {bullet['content']}"
        )

    return '\n'.join(formatted_bullets)
