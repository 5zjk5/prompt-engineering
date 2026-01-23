"""
Curator agent for ACE system.
Manages playbook operations (ADD, UPDATE, MERGE, DELETE).
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from offline.ace.prompts.curator import CURATOR_PROMPT, CURATOR_PROMPT_NO_GT
from offline.playbook_utils import extract_json_from_text, apply_curator_operations
from offline.logger import log_curator_operation_diff, log_curator_failure
from offline.ace.llm import timed_llm_call


class Curator:
    """
    Curator agent that manages the playbook by adding, updating,
    merging, and deleting bullets based on reflection feedback.
    """

    def __init__(self, model: str, logger, max_tokens: int = 4096):
        """
        Initialize the Curator agent.

        Args:
            api_client: OpenAI client for LLM calls
            api_provider: API provider for LLM calls
            model: Model name to use for curation
            max_tokens: Maximum tokens for curation
        """
        self.model = model
        self.max_tokens = max_tokens
        self.logger = logger

    def curate(
        self,
        current_playbook: str,
        recent_reflection: str,
        question_context: str,
        current_step: int,
        total_samples: int,
        token_budget: int,
        playbook_stats: Dict[str, Any],
        use_ground_truth: bool = True,
        use_json_mode: bool = False,
        call_id: str = "curate",
        log_dir: Optional[str] = None,
        next_global_id: int = 1,
    ) -> Tuple[str, int, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Curate the playbook based on reflection feedback.

        Args:
            current_playbook: Current playbook content
            recent_reflection: Recent reflection from reflector
            question_context: Context for the current question
            current_step: Current training step
            total_samples: Total number of training samples
            token_budget: Total token budget for playbook
            playbook_stats: Statistics about current playbook
            use_ground_truth: Whether ground truth is available
            use_json_mode: Whether to use JSON mode
            call_id: Unique identifier for this call
            log_dir: Directory for logging
            next_global_id: Next available global ID for bullets

        Returns:
            Tuple of (updated_playbook, next_global_id, operations, call_info)
        """
        # Format playbook stats as JSON string
        stats_str = json.dumps(playbook_stats, indent=2)

        # Select the appropriate prompt
        if use_ground_truth:
            prompt = CURATOR_PROMPT.format(
                current_step=current_step,
                total_samples=total_samples,
                token_budget=token_budget,
                playbook_stats=stats_str,
                recent_reflection=recent_reflection,
                current_playbook=current_playbook,
                question_context=question_context,
            )
        else:
            prompt = CURATOR_PROMPT_NO_GT.format(
                current_step=current_step,
                total_samples=total_samples,
                token_budget=token_budget,
                playbook_stats=stats_str,
                recent_reflection=recent_reflection,
                current_playbook=current_playbook,
                question_context=question_context,
            )

        # Make the LLM call
        response, call_info = timed_llm_call(
            model=self.model,
            prompt=prompt,
            logger=self.logger,
            role="curator",
            call_id=call_id,
            max_tokens=self.max_tokens,
            log_dir=log_dir,
            use_json_mode=use_json_mode,
        )

        # Check for empty response error
        if response.startswith("INCORRECT_DUE_TO_EMPTY_RESPONSE"):
            self.logger.info(f"⏭️  Skipping curator operation due to empty response")
            log_curator_failure(
                log_dir, current_step, "empty_response", response[:200], 0, self.logger
            )
            return current_playbook, next_global_id, [], call_info

        # Extract and validate operations
        try:
            operations_info = self._extract_and_validate_operations(response)

            operations = operations_info["operations"]
            self.logger.info(
                f"✅ Curator JSON schema validated successfully: {len(operations)} operations"
            )

            # Apply operations to playbook
            updated_playbook, next_global_id, operations = apply_curator_operations(
                current_playbook, operations, next_global_id, self.logger
            )

            # Log detailed diff for each operation after applying
            for op in operations:
                try:
                    log_curator_operation_diff(
                        Path(log_dir).parent, op, current_playbook, call_id, self.logger
                    )
                except Exception as e:
                    import traceback

                    self.logger.error(traceback.format_exc())
                    self.logger.error(
                        f"Warning: Failed to log curator operation diff: {e}"
                    )

            # Log operations
            for op in operations:
                try:
                    op_type = (
                        op.get('type', 'UNKNOWN') if isinstance(op, dict) else 'INVALID'
                    )
                    op_section = (
                        op.get('section', 'No section given')
                        if isinstance(op, dict)
                        else 'Invalid operation format'
                    )
                    op_content = (
                        op.get('content', 'No content given')
                        if isinstance(op, dict)
                        else 'INVALID'
                    )
                    self.logger.info(
                        f"  -operation_type={op_type} -section={op_section} -content={op_content}"
                    )
                except Exception as e:
                    import traceback

                    self.logger.error(traceback.format_exc())
                    self.logger.error(f"  - UNKNOWN: Error logging operation: {e}")

            return updated_playbook, next_global_id, operations, call_info

        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            import traceback

            self.logger.error(traceback.format_exc())

            self.logger.error(f"❌ Curator JSON parsing failed: {e}")
            self.logger.info(f"📄 Raw curator response preview: {response[:300]}...")

            log_curator_failure(
                log_dir,
                current_step,
                "json_parse_error",
                response,
                0,
                self.logger,
                str(e),
            )

            self.logger.info("⏭️  Skipping curator operation due to invalid JSON format")
            return current_playbook, next_global_id, [], call_info

        except Exception as e:
            import traceback

            self.logger.error(traceback.format_exc())
            self.logger.error(f"❌ Curator operation failed: {e}")
            self.logger.info(f"📄 Raw curator response preview: {response[:300]}...")

            log_curator_failure(
                log_dir,
                current_step,
                "operation_error",
                response,
                0,
                self.logger,
                str(e),
            )

            self.logger.info("⏭️  Skipping curator operation and continuing training")
            return current_playbook, next_global_id, [], call_info

    def _extract_and_validate_operations(self, response: str) -> Dict[str, Any]:
        """
        Extract and validate operations from curator response.

        Args:
            response: The curator's response

        Returns:
            Dictionary with 'reasoning' and 'operations' keys

        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        # Extract operations info
        operations_info = extract_json_from_text(response, self.logger, "operations", )

        # Validate JSON structure is correct
        if not operations_info:
            raise ValueError("Failed to extract valid JSON from curator response")

        # Validate required fields
        if "reasoning" not in operations_info:
            raise ValueError("JSON missing required 'reasoning' field")

        if "operations" not in operations_info:
            raise ValueError("JSON missing required 'operations' field")

        # Validate field types
        if not isinstance(operations_info["reasoning"], str):
            raise ValueError("'reasoning' field must be a string")

        if not isinstance(operations_info["operations"], list):
            raise ValueError("'operations' field must be a list")

        # Validate operations structure and filter out invalid ones
        valid_operations = []
        for i, op in enumerate(operations_info["operations"]):
            if not isinstance(op, dict):
                self.logger.warning(f"Skipping operation {i}: must be a dictionary")
                continue

            if "type" not in op:
                self.logger.warning(
                    f"Skipping operation {i}: missing required 'type' field"
                )
                continue

            op_type = op["type"]

            if op_type not in ["ADD", "UPDATE", "MERGE", "DELETE", "CREATE_META"]:
                self.logger.warning(
                    f"Skipping operation {i}: unsupported type '{op_type}'"
                )
                continue

            is_valid = True

            if op_type == "ADD":
                required_fields = {"type", "section", "content"}
                missing_fields = required_fields - set(op.keys())
                if missing_fields:
                    self.logger.warning(
                        f"Skipping ADD operation {i}: missing fields {list(missing_fields)}"
                    )
                    is_valid = False

            elif op_type == "UPDATE":
                required_fields = {"type", "bullet_id", "content"}
                missing_fields = required_fields - set(op.keys())
                if missing_fields:
                    self.logger.warning(
                        f"Skipping UPDATE operation {i}: missing fields {list(missing_fields)}"
                    )
                    is_valid = False

            elif op_type == "MERGE":
                required_fields = {"type", "source_ids", "section", "content"}
                missing_fields = required_fields - set(op.keys())
                if missing_fields:
                    self.logger.warning(
                        f"Skipping MERGE operation {i}: missing fields {list(missing_fields)}"
                    )
                    is_valid = False
                elif not isinstance(op["source_ids"], list):
                    self.logger.warning(
                        f"Skipping MERGE operation {i}: source_ids must be a list"
                    )
                    is_valid = False

            elif op_type == "DELETE":
                required_fields = {"type", "bullet_id"}
                missing_fields = required_fields - set(op.keys())
                if missing_fields:
                    self.logger.warning(
                        f"Skipping DELETE operation {i}: missing fields {list(missing_fields)}"
                    )
                    is_valid = False

            elif op_type == "CREATE_META":
                required_fields = {"type", "section_name", "content"}
                missing_fields = required_fields - set(op.keys())
                if missing_fields:
                    self.logger.warning(
                        f"Skipping CREATE_META operation {i}: missing fields {list(missing_fields)}"
                    )
                    is_valid = False

            if is_valid:
                valid_operations.append(op)

        operations_info["operations"] = valid_operations
        return operations_info
