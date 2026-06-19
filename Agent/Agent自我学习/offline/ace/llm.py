"""
==============================================================================
llm.py
==============================================================================

This file contains the LLM class for the project.

"""

import time
import random
import json
from datetime import datetime
from Agent.Agent自我学习.offline.logger import log_llm_call, log_problematic_request


def timed_llm_call(
    model,
    prompt,
    role,
    call_id,
    logger,
    max_tokens=4096,
    log_dir=None,
    sleep_seconds=2,
    retries_on_timeout=3,
    attempt=1,
    use_json_mode=False,
):
    """
    Make a timed LLM call with error handling and retry logic.

    EMPTY RESPONSE HANDLING STRATEGY:
    - Training calls (call_id starts with 'train_'): Skip the entire training sample
    - Test calls (call_id starts with 'test_'): Mark as incorrect (return wrong answers)
    - All empty responses are logged to problematic_requests/ for SambaNova support analysis

    For test calls specifically: Returns "INCORRECT_DUE_TO_EMPTY_RESPONSE" repeated 4 times
    (comma-separated) to handle the 4-question format used in financial NER evaluation.

    Args:
        model: Model object to invoke
        prompt: Text prompt to send
        role: Role for logging (generator, reflector, curator)
        call_id: Unique identifier for this call (format: {train|test}_{role}_{details})
        logger: Logger instance for logging
        max_tokens: Maximum tokens to generate
        log_dir: Directory for detailed logging
        sleep_seconds: Base sleep time between retries
        retries_on_timeout: Maximum number of retries for timeouts/rate limits/empty responses
        attempt: Current attempt number (for recursive calls)
        use_json_mode: Whether to use JSON mode for structured output

    Returns:
        tuple: (response_text, call_info_dict)

    Special return values for empty responses:
        - Training: ("INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, ...", call_info)
        - Testing: ("INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, ...", call_info)
    """
    start_time = time.time()
    prompt_time = time.time()

    logger.info(f"[{role.upper()}] Starting call llm {call_id}...")

    while True:
        try:
            call_start = time.time()
            response = model.invoke(prompt)
            response_content = response.content
            call_end = time.time()

            if response_content is None:
                raise Exception("Model returned None content")

            response_time = time.time()
            total_time = response_time - start_time

            call_info = {
                "role": role,
                "call_id": call_id,
                "model": model.model_name,
                "prompt": prompt,
                "response": response_content,
                "prompt_time": prompt_time - start_time,
                "response_time": response_time - prompt_time,
                "total_time": total_time,
                "call_time": call_end - call_start,
                "prompt_length": len(prompt),
                "response_length": len(response_content),
                "output_token": response.response_metadata['token_usage']['completion_tokens'],
                "input_token": response.response_metadata['token_usage']['prompt_tokens'],
                "total_token": response.response_metadata['token_usage']['total_tokens'],
            }

            logger.info(
                f"[{role.upper()}] Call {call_id} completed in {total_time:.2f}s"
            )

            if log_dir:
                log_llm_call(log_dir, call_info, logger)

            return response_content, call_info

        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())

            # Check for both timeout and rate limit errors
            is_timeout = any(
                k in str(e).lower() for k in ["timeout", "timed out", "connection"]
            )
            is_rate_limit = any(
                k in str(e).lower()
                for k in ["rate limit", "429", "rate_limit_exceeded"]
            )
            is_empty_response = (
                "empty response" in str(e).lower()
                or "api returned none content" in str(e).lower()
            )

            # Check for server errors (500, 502, 503, etc.) that should be retried
            is_server_error = False
            if hasattr(e, 'response'):
                try:
                    status_code = getattr(e.response, 'status_code', None)
                    if status_code and status_code >= 500:
                        is_server_error = True
                        logger.info(
                            f"[{role.upper()}] Server error detected: HTTP {status_code}"
                        )
                except:
                    pass

            # Also check for 500 errors in the error message itself
            if any(
                k in str(e).lower()
                for k in [
                    "500 internal server error",
                    "internal server error",
                    "502 bad gateway",
                    "503 service unavailable",
                ]
            ):
                is_server_error = True
                logger.info(
                    f"[{role.upper()}] Server error detected in message: {str(e)[:100]}..."
                )

            # Debug empty response issues
            if is_empty_response:
                logger.debug(f"\n🚨 DEBUG: Empty response detected for {call_id}")
                logger.debug(f"📝 Exception type: {type(e).__name__}")
                logger.debug(f"📝 Exception message: {str(e)}")
                logger.debug(f"📝 Using JSON mode: {use_json_mode}")
                logger.debug(f"📝 Model: {model}")
                logger.debug(f"📝 Prompt length: {len(prompt)}")
                logger.debug(f"📝 Prompt preview (first 500 chars):")
                logger.debug(f"    {prompt[:500]}...")
                logger.debug(f"📝 Full exception details: {repr(e)}")
                if hasattr(e, 'response'):
                    logger.debug(f"📝 Raw response object: {e.response}")
                    if hasattr(e.response, 'text'):
                        logger.debug(f"📝 Raw response text: {e.response.text}")
                    if hasattr(e.response, 'content'):
                        logger.debug(f"📝 Raw response content: {e.response.content}")
                logger.debug("-" * 60)

                # Log problematic requests for SambaNova support
                log_problematic_request(
                    logger,
                    call_id,
                    prompt,
                    model,
                    None,
                    e,
                    log_dir,
                    False,
                    None,
                )

            # For empty responses, we handle differently based on context
            if is_empty_response:
                # Log the problematic request for SambaNova support
                log_problematic_request(
                    logger,
                    call_id,
                    prompt,
                    model,
                    None,
                    e,
                    log_dir,
                    False,
                    None,
                )

                # Check if this is a training or test call to decide behavior
                if call_id.startswith('train_'):
                    # In training: Mark as incorrect answer (same as testing)
                    logger.info(
                        f"[{role.upper()}] 🚨 Empty response in training - marking as INCORRECT for {call_id}"
                    )
                    error_time = time.time()
                    call_info = {
                        "role": role,
                        "call_id": call_id,
                        "model": model.model_name,
                        "prompt": prompt,
                        "error": "TRAINING_INCORRECT: " + str(e),
                        "total_time": error_time - start_time,
                        "prompt_length": len(prompt),
                        "response_length": 0,
                        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3],
                        "datetime": datetime.now().isoformat(),
                        "training_marked_incorrect_due_to_empty_response": True,
                    }
                    if log_dir:
                        log_llm_call(log_dir, call_info, logger)

                    # Return a response that will be marked as incorrect
                    # For the 4-question format, we return 4 wrong answers
                    incorrect_response = "INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE"
                    return incorrect_response, call_info

                elif call_id.startswith('test_'):
                    # In testing: Treat as incorrect answer
                    logger.info(
                        f"[{role.upper()}] 🚨 Empty response in testing - marking as INCORRECT for {call_id}"
                    )
                    error_time = time.time()
                    call_info = {
                        "role": role,
                        "call_id": call_id,
                        "model": model.model_name,
                        "prompt": prompt,
                        "error": "TEST_INCORRECT: " + str(e),
                        "total_time": error_time - start_time,
                        "prompt_length": len(prompt),
                        "response_length": 0,
                        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3],
                        "datetime": datetime.now().isoformat(),
                        "test_marked_incorrect_due_to_empty_response": True,
                    }
                    if log_dir:
                        log_llm_call(log_dir, call_info, logger)

                    # Return a response that will be marked as incorrect
                    # For the 4-question format, we return 4 wrong answers
                    incorrect_response = "INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE, INCORRECT_DUE_TO_EMPTY_RESPONSE"
                    return incorrect_response, call_info

            # Retry logic for timeouts, rate limits, and server errors
            if (
                is_timeout or is_rate_limit or is_server_error
            ) and attempt < retries_on_timeout:
                attempt += 1
                if is_rate_limit:
                    error_type = "rate limited"
                    base_sleep = sleep_seconds * 2
                elif is_server_error:
                    error_type = "server error (500+)"
                    base_sleep = sleep_seconds * 1.5  # Moderate delay for server errors
                elif is_empty_response:
                    error_type = "returned empty response"
                    base_sleep = sleep_seconds
                else:
                    error_type = "timed out"
                    base_sleep = sleep_seconds
                jitter = random.uniform(0.5, 1.5)  # Add jitter to avoid thundering herd
                sleep_time = base_sleep * jitter
                logger.info(
                    f"[{role.upper()}] Call {call_id} {error_type}, sleeping {sleep_time:.1f}s then retrying "
                    f"({attempt}/{retries_on_timeout})..."
                )
                time.sleep(sleep_time)
                continue

            error_time = time.time()
            call_info = {
                "role": role,
                "call_id": call_id,
                "model": model.model_name,
                "prompt": prompt,
                "error": str(e),
                "total_time": error_time - start_time,
                "prompt_length": len(prompt),
                "attempt": attempt,
            }

            logger.info(
                f"[{role.upper()}] Call {call_id} failed after {error_time - start_time:.2f}s: {e}"
            )
            logger.info(
                f"[{role.upper()}] All {retries_on_timeout} retries exhausted, returning fallback response"
            )

            if log_dir:
                log_llm_call(log_dir, call_info, logger)

            # Return fallback response based on call context instead of raising exception
            if call_id.startswith('train_'):
                # Training: Return incorrect response to allow training to continue
                fallback_response = "TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT"
                call_info["training_fallback_due_to_timeout"] = True
                logger.info(
                    f"[{role.upper()}] 🚨 All retries failed in training - returning fallback INCORRECT for {call_id}"
                )
                return fallback_response, call_info
            elif call_id.startswith('test_'):
                # Testing: Return incorrect response to allow evaluation to continue
                fallback_response = "TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT, TIMEOUT_FAILED_INCORRECT"
                call_info["test_fallback_due_to_timeout"] = True
                logger.info(
                    f"[{role.upper()}] 🚨 All retries failed in testing - returning fallback INCORRECT for {call_id}"
                )
                return fallback_response, call_info
            else:
                # Other calls (curator, etc.): Return empty response with error info
                fallback_response = json.dumps(
                    {
                        "error": "timeout_after_retries",
                        "original_error": str(e),
                        "role": role,
                    }
                )
                call_info["fallback_due_to_timeout"] = True
                logger.info(
                    f"[{role.upper()}] 🚨 All retries failed for {call_id} - returning fallback error response"
                )
                return fallback_response, call_info
