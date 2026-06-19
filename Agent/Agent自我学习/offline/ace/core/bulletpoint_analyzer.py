"""
BulletpointAnalyzer Component for ACE System

This component analyzes playbook bulletpoints for similarity and performs
intelligent deduplication and merging using embeddings and LLM.
"""

import re
import os
import faiss
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from collections import defaultdict
from openai import OpenAI

from Agent.Agent自我学习.offline import logger


def parse_playbook_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse playbook line format: [sec-00001] helpful=4 harmful=1 :: Actual bullet content here...

    Args:
        line: Line from playbook

    Returns:
        Dictionary with bullet information or None if not a valid bullet
    """
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('##'):
        return None

    # Match format: [id] helpful=X harmful=Y :: content
    pattern = r'\[([^\]]+)\]\s*helpful=(\d+)\s*harmful=(\d+)\s*::\s*(.*)'
    match = re.match(pattern, line)

    if match:
        bullet_id, helpful, harmful, content = match.groups()
        return {
            'id': bullet_id,
            'helpful': int(helpful),
            'harmful': int(harmful),
            'content': content.strip(),
        }

    # If not matching standard format, might be simple text line
    if '::' in line:
        parts = line.split('::', 1)
        if len(parts) == 2:
            return {
                'id': f'unknown-{hash(line) % 10000:04d}',
                'helpful': 0,
                'harmful': 0,
                'content': parts[1].strip(),
            }

    return None


class BulletpointAnalyzer:
    """
    Bulletpoint analyzer for deduplication and merging of similar playbook entries.

    Uses OpenAI embeddings for semantic similarity and LLM for intelligent merging.
    """

    def __init__(
        self,
        model: str,
        logger,
    ):
        """
        Initialize the bulletpoint analyzer.

        Args:
            model: Model object for LLM
            logger: Logger instance for logging
        """
        self.model = model
        self.logger = logger
        self.client = OpenAI(
            api_key=os.getenv("EMBEDDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_BASE_URL"),
        )

    def embed(self, text):
        # 调用 OpenAI API 获取嵌入向量
        return (
            self.client.embeddings.create(
                input=[text],
                model=os.getenv("EMBEDDING_MODEL"),
                dimensions=os.getenv("EMBEDDING_DIMS"),
            )
            .data[0]
            .embedding
        )

    def _parse_playbook(
        self, playbook: str
    ) -> Tuple[List[str], List[Dict[str, Any]], Dict[int, int]]:
        """
        Parse playbook into lines, bullets, and mapping.

        Args:
            playbook: Playbook content as string

        Returns:
            Tuple of (original_lines, bullets, bullet_line_mapping)
        """
        lines = playbook.strip().split('\n')
        bullets = []
        bullet_line_mapping = {}

        for line_idx, line in enumerate(lines):
            parsed = parse_playbook_line(line)
            if parsed:
                parsed['line_number'] = line_idx + 1
                parsed['original_line'] = line
                bullet_index = len(bullets)
                bullet_line_mapping[bullet_index] = line_idx
                bullets.append(parsed)

        return lines, bullets, bullet_line_mapping

    def _compute_embeddings(self, bullets: List[Dict[str, Any]]) -> np.ndarray:
        """
        Compute embeddings for all bullets.

        Args:
            bullets: List of bullet dictionaries

        Returns:
            Normalized embeddings array
        """
        contents = [bullet['content'] for bullet in bullets]
        embeddings = np.array([self.embed(content) for content in contents])

        # Normalize for cosine similarity
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)

        return embeddings

    def _find_similar_groups(
        self, bullets: List[Dict[str, Any]], embeddings: np.ndarray, threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Find groups of similar bullets based on embedding similarity.

        Args:
            bullets: List of bullet dictionaries
            embeddings: Normalized embeddings array
            threshold: Similarity threshold (0-1)

        Returns:
            List of duplicate groups
        """
        similarity_matrix = np.dot(embeddings, embeddings.T)

        duplicate_groups = []
        visited = set()

        for i in range(len(bullets)):
            if i in visited:
                continue

            # Find all items similar to i
            similar_indices = []
            for j in range(i + 1, len(bullets)):
                if similarity_matrix[i, j] >= threshold:
                    similar_indices.append(j)

            if similar_indices:
                # Create duplicate group
                group = [i] + similar_indices
                duplicate_groups.append(
                    {'indices': group, 'bullets': [bullets[idx] for idx in group]}
                )
                visited.update(group)

        return duplicate_groups

    def _merge_bullets_with_llm(
        self, bullets_group: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Merge a group of similar bullets using LLM.

        Args:
            bullets_group: List of similar bullets to merge

        Returns:
            Merged bullet dictionary or None if merge fails
        """
        if len(bullets_group) == 1:
            return bullets_group[0]

        # Prepare prompt for LLM
        bullets_text = "\n".join(
            [
                f"{i+1}. [{b['id']}] helpful={b['helpful']} harmful={b['harmful']} :: {b['content']}"
                for i, b in enumerate(bullets_group)
            ]
        )

        # Calculate combined helpful/harmful counts
        total_helpful = sum(b['helpful'] for b in bullets_group)
        total_harmful = sum(b['harmful'] for b in bullets_group)

        # Use first bullet's ID as base
        base_id = bullets_group[0]['id']

        prompt = f"""You are merging similar playbook bulletpoints into a single, comprehensive entry.

Given these similar bulletpoints:
{bullets_text}

Merge them into ONE bulletpoint that captures all important information while removing redundancy.

Requirements:
1. Keep the ID from the first entry: [{base_id}]
2. Use combined counts: helpful={total_helpful} harmful={total_harmful}
3. Combine the content to be comprehensive but concise
4. Output ONLY in this format: [{base_id}] helpful={total_helpful} harmful={total_harmful} :: [merged content]

Do NOT include any explanation, just output the merged bulletpoint."""

        try:
            merged_content = self.model.invoke(prompt)
            merged_content = merged_content.content
            merged_content = merged_content.strip()

            # Parse the merged bullet
            pattern = r'\[([^\]]+)\]\s+helpful=(\d+)\s+harmful=(\d+)\s+::\s+(.+)'
            match = re.match(pattern, merged_content)

            if match:
                bullet_id, helpful, harmful, content = match.groups()
                return {
                    'id': bullet_id,
                    'helpful': int(helpful),
                    'harmful': int(harmful),
                    'content': content.strip(),
                    'original_line': f"[{bullet_id}] helpful={helpful} harmful={harmful} :: {content.strip()}",
                    'is_merged': True,
                    'original_count': len(bullets_group),
                }
            else:
                self.logger.warning(
                    f"⚠️  Failed to parse merged bullet, keeping first bullet from group"
                )
                return bullets_group[0]

        except Exception as e:
            self.logger.error(f"⚠️  Error merging bullets: {e}, keeping first bullet from group")
            return bullets_group[0]

    def analyze(
        self, playbook: str, threshold: float = 0.90, merge: bool = True
    ) -> str:
        """
        Analyze and deduplicate/merge playbook bulletpoints.

        Args:
            playbook: Playbook content as string
            threshold: Similarity threshold for grouping (default: 0.90)
            merge: If True, merge similar bullets with LLM; if False, just deduplicate

        Returns:
            Processed playbook string
        """
        # Parse playbook
        original_lines, bullets, bullet_line_mapping = self._parse_playbook(playbook)

        if len(bullets) == 0:
            return playbook

        self.logger.info(
            f"Analyzing {len(bullets)} bulletpoints (threshold={threshold})..."
        )

        try:
            # Compute embeddings
            embeddings = self._compute_embeddings(bullets)
            self.logger.info(f"Use embeddings model {os.getenv('EMBEDDING_MODEL')} success! ")
            # Find similar groups
            duplicate_groups = self._find_similar_groups(bullets, embeddings, threshold)
        except Exception as e:  # embeddgin 限流之类的问题
            import traceback
            self.logger.error(traceback.format_exc())
            self.logger.error(f"Error finding similar groups: {e}")
            duplicate_groups = []

        if len(duplicate_groups) == 0:
            self.logger.info(f"No similar bulletpoints found at threshold {threshold}")
            return playbook

        self.logger.info(
            f"Found {len(duplicate_groups)} groups of similar bulletpoints"
        )

        # Create merge mapping
        merge_mapping = {}
        processed_indices = set()

        if merge:
            # Merge using LLM
            for group_idx, group in enumerate(duplicate_groups):
                indices = group['indices']
                group_bullets = group['bullets']

                self.logger.info(
                    f"  Merging group {group_idx + 1}: {len(group_bullets)} bullets -> 1"
                )
                merged_bullet = self._merge_bullets_with_llm(group_bullets)

                if merged_bullet:
                    first_bullet_idx = indices[0]
                    merge_mapping[first_bullet_idx] = merged_bullet
                    processed_indices.update(indices)
        else:
            # Simple deduplication (keep first of each group)
            for group in duplicate_groups:
                indices = group['indices']
                # Keep first, mark others for removal
                processed_indices.update(indices[1:])

        # Reconstruct playbook
        output_lines = []

        for line_idx, original_line in enumerate(original_lines):
            # Check if this line is a bullet
            current_bullet_idx = None
            for bi in bullet_line_mapping:
                if bullet_line_mapping[bi] == line_idx:
                    current_bullet_idx = bi
                    break

            if current_bullet_idx is not None:
                # This is a bullet line
                if current_bullet_idx in merge_mapping:
                    # Use merged version
                    merged_bullet = merge_mapping[current_bullet_idx]
                    output_lines.append(merged_bullet['original_line'])
                elif current_bullet_idx in processed_indices:
                    # This bullet was merged into another, skip it
                    continue
                else:
                    # Keep original
                    output_lines.append(original_line)
            else:
                # Not a bullet line (headers, empty lines, etc.)
                output_lines.append(original_line)

        # Calculate statistics
        final_bullet_count = len(bullets) - len(processed_indices) + len(merge_mapping)
        removed_count = len(bullets) - final_bullet_count

        self.logger.info(
            f"✓ Bulletpoint analysis complete: {len(bullets)} -> {final_bullet_count} "
            f"({removed_count} bullets merged/removed)"
        )

        return '\n'.join(output_lines)
