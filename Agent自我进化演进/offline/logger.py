"""
==============================================================================
logger.py
==============================================================================

This file contains functions for logging various events and information during the training process.

"""

import os
import json
import logging
import sys
import re
from pathlib import Path
from datetime import datetime
from offline.playbook_utils import parse_playbook_line


def define_log_level(save_path, task_name, print_level="INFO", logfile_level="DEBUG"):
    """
    创建独立的 logger，支持记录模块、函数、行号
    """
    task_name = re.sub(r'[\/\\:\*\?"<>\|]', '_', task_name)

    logger = logging.getLogger(task_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    now = datetime.now()
    run_folder = f"{task_name[:30]}_{now.strftime('%Y%m%d_%H%M%S')}"
    log_dir = Path(save_path) / run_folder
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志格式包含模块、函数、行号等信息
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(print_level)
    console_handler.setFormatter(formatter)

    # 文件 handler
    file_handler = logging.FileHandler(log_dir / "log.log", encoding='utf-8')
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info(f'Log directory: {log_dir}')
    return logger, str(log_dir)


def log_llm_call(log_dir, call_info, logger):
    """Log detailed information about each LLM call"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{call_info['role']}_{call_info['call_id']}_{timestamp}.json"
    filepath = os.path.join(log_dir, filename)

    call_info['timestamp'] = timestamp
    call_info['datetime'] = datetime.now().isoformat()

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(call_info, f, indent=2, ensure_ascii=False)

    logger.info(f"[LOG] {call_info['role']} call logged to {filename}")


def log_bullet_usage(
    usage_log_path,
    epoch,
    step,
    sample_data,
    bullet_ids_used,
    playbook=None,
    reflection_content=None,
    is_correct=None,
):
    """Log which bullets were used in each training sample for future curator reference

    TODO: Future curator enhancement - when updating a bullet, the curator can:
    1. Look up all training samples that used this bullet (via this log)
    2. Review the reflection content for those samples
    3. Understand what worked/didn't work with the current bullet
    4. Write a better version based on all the usage history and feedback
    """
    # Extract bullet contents from the playbook
    bullets_with_content = []
    if playbook and bullet_ids_used:
        playbook_lines = playbook.split('\n')
        for bullet_id in bullet_ids_used:
            # Find the line containing this bullet ID
            bullet_content = None
            for line in playbook_lines:
                if f'[{bullet_id}]' in line:
                    # Extract content after the bullet ID pattern
                    # Format: [bullet_id] helpful=X harmful=Y :: content
                    if '::' in line:
                        bullet_content = line.split('::', 1)[1].strip()
                    else:
                        bullet_content = line.strip()
                    break

            bullets_with_content.append(
                {
                    "bullet_id": bullet_id,
                    "content": (
                        bullet_content if bullet_content else "Content not found"
                    ),
                }
            )
    else:
        # If no playbook provided or no bullets used, just log the IDs
        bullets_with_content = [
            {"bullet_id": bid, "content": None} for bid in bullet_ids_used
        ]

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "epoch": epoch,
        "step": step,
        "sample_id": f"epoch_{epoch}_step_{step}",
        "bullet_ids_used": bullet_ids_used,
        "bullets_with_content": bullets_with_content,
        "is_correct": is_correct,  # Only record accuracy for initial trials
        "sample_question": (
            sample_data.get("question", "")[:200] if sample_data else ""
        ),  # First 200 chars
        "reflection_summary": (
            reflection_content[:300] if reflection_content else None
        ),  # First 300 chars
        "bullet_count": len(bullet_ids_used),
    }

    with open(usage_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')


def log_curator_operation_diff(log_dir, operation, playbook_text, call_id, logger):
    """Log detailed diff for curator operations, especially MERGE operations"""
    if not log_dir:
        return

    try:
        curator_diff_log_path = os.path.join(log_dir, 'curator_operations_diff.jsonl')

        # Safely extract operation type and reason
        if isinstance(operation, dict):
            op_type = operation.get('type', 'UNKNOWN')
            reason = operation.get('reason', '')
        else:
            logger.info(f"Warning: Invalid operation format for logging: {type(operation)}")
            return

        operation_diff = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": op_type,
            "reason": reason,
        }
    except Exception as e:
        logger.error(f"Warning: Error setting up curator operation diff logging: {e}")
        return

    if op_type == 'MERGE':
        # Collect source bullet contents for diff
        source_bullets = []
        source_ids = operation.get('source_ids', [])

        lines = playbook_text.strip().split('\n')
        for source_id in source_ids:
            for line in lines:
                parsed = parse_playbook_line(line)
                if parsed and parsed['id'] == source_id:
                    source_bullets.append(
                        {
                            "bullet_id": source_id,
                            "content": parsed['content'],
                            "helpful": parsed['helpful'],
                            "harmful": parsed['harmful'],
                        }
                    )
                    break

        merged_content = operation.get('content', '')
        operation_diff.update(
            {
                "source_bullets": source_bullets,
                "merged_content": merged_content,
                "merge_summary": f"Merged {len(source_bullets)} bullets into 1 new bullet",
                "content_comparison": {
                    "total_source_length": sum(
                        len(b['content']) for b in source_bullets
                    ),
                    "merged_length": len(merged_content),
                    "compression_ratio": (
                        len(merged_content)
                        / sum(len(b['content']) for b in source_bullets)
                        if source_bullets
                        else 0
                    ),
                },
            }
        )

    elif op_type == 'UPDATE':
        bullet_id = operation.get('bullet_id', '')
        new_content = operation.get('content', '')

        # Find old content
        old_content = None
        lines = playbook_text.strip().split('\n')
        for line in lines:
            parsed = parse_playbook_line(line)
            if parsed and parsed['id'] == bullet_id:
                old_content = parsed['content']
                break

        operation_diff.update(
            {
                "bullet_id": bullet_id,
                "old_content": old_content,
                "content": new_content,
                "content_comparison": {
                    "old_length": len(old_content) if old_content else 0,
                    "new_length": len(new_content),
                    "length_change": len(new_content)
                    - (len(old_content) if old_content else 0),
                },
            }
        )

    elif op_type == 'ADD':
        section = operation.get('section', 'others')
        content = operation.get('content', '')
        operation_diff.update(
            {"section": section, "content": content, "content_length": len(content)}
        )

    elif op_type == 'CREATE_META':
        section = operation.get('section', 'meta_strategies')
        content = operation.get('content', '')
        operation_diff.update(
            {"section": section, "content": content, "meta_type": "section_creation"}
        )

    operation_diff["call_id"] = call_id
    # Write to diff log
    try:
        with open(curator_diff_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(operation_diff, ensure_ascii=False) + '\n')
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"Warning: Failed to write curator operation diff log: {e}")


def log_problematic_request(
    logger,
    call_id, prompt, model, api_params, exception, log_dir, using_key_mixer, key_mixer
):
    """Log problematic requests that cause empty responses"""
    if not log_dir:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

    # Create problematic requests log directory
    problem_log_dir = os.path.join(log_dir, "problematic_requests")
    os.makedirs(problem_log_dir, exist_ok=True)

    # Get current API key if using mixer
    current_api_key = None
    if using_key_mixer and key_mixer:
        # Get the last used key from mixer stats
        stats = key_mixer.get_usage_stats()
        if stats:
            # Find the key with the highest usage count (most recently used)
            current_api_key = max(stats.keys(), key=lambda k: stats[k])
            # Mask it for security
            current_api_key = f"{current_api_key[:8]}...{current_api_key[-8:]}"

    problem_info = {
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "call_id": call_id,
        "model": model,
        "api_params": api_params,
        "prompt": prompt,
        "prompt_length": len(prompt),
        "using_json_mode": api_params.get("response_format", {}).get("type")
        == "json_object",
        "api_key_used": current_api_key,
        "exception_info": {
            "type": type(exception).__name__,
            "message": str(exception),
            "repr": repr(exception),
            "args": list(exception.args) if hasattr(exception, 'args') else None,
        },
    }

    # Try to capture response details if available
    if hasattr(exception, 'response'):
        response_details = {"has_response_object": True}
        try:
            if hasattr(exception.response, 'status_code'):
                response_details["status_code"] = exception.response.status_code
            if hasattr(exception.response, 'headers'):
                response_details["headers"] = dict(exception.response.headers)
            if hasattr(exception.response, 'text'):
                response_details["text"] = exception.response.text
            if hasattr(exception.response, 'content'):
                response_details["content"] = str(exception.response.content)
            if hasattr(exception.response, 'json'):
                try:
                    response_details["json"] = exception.response.json()
                except:
                    response_details["json"] = "Could not parse as JSON"
        except Exception as e:
            response_details["extraction_error"] = str(e)

        problem_info["response_details"] = response_details
    else:
        problem_info["response_details"] = {"has_response_object": False}

    filename = f"empty_response_{call_id}_{timestamp}.json"
    filepath = os.path.join(problem_log_dir, filename)

    with open(filepath, 'w') as f:
        json.dump(problem_info, f, indent=2, ensure_ascii=False)

    logger.info(
        f"[PROBLEM LOG] Saved problematic request to: problematic_requests/{filename}"
    )

    # Also create a summary log
    summary_file = os.path.join(problem_log_dir, "summary.jsonl")
    summary_entry = {
        "timestamp": timestamp,
        "call_id": call_id,
        "model": model,
        "prompt_length": len(prompt),
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "json_mode": api_params.get("response_format", {}).get("type") == "json_object",
        "api_key_used": current_api_key,
    }

    with open(summary_file, 'a') as f:
        f.write(json.dumps(summary_entry, ensure_ascii=False) + '\n')


def log_curator_failure(
    save_path, step, failure_type, curator_response, epoch, logger, error_details=None,
):
    """Log curator failures to a dedicated log file for analysis"""
    curator_failure_log_path = os.path.join(save_path, "curator_failures.txt")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create log entry
    log_entry = f"""
{'='*60}
CURATOR FAILURE LOG
{'='*60}
Timestamp: {timestamp}
Epoch: {epoch}
Step: {step}
Failure Type: {failure_type}
Error Details: {error_details if error_details else 'N/A'}

Raw Curator Response (first 1000 chars):
{'-'*40}
{curator_response[:1000]}
{'-'*40}

Full Raw Curator Response:
{'-'*40}
{curator_response}
{'-'*40}

"""

    try:
        with open(curator_failure_log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        logger.info(f"📝 Curator failure logged to: {curator_failure_log_path}")
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"⚠️  Failed to write curator failure log: {e}")
