import re
import json
import tiktoken
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.messages import HumanMessage, SystemMessage


def get_section_slug(section_name):
    """Convert section name to slug format (3-5 chars)"""
    # Common section mappings - updated to match original sections
    slug_map = {
        "strategies_and_insights": "sai",
        "formulas_and_calculations": "calc",
        "code_snippets_and_templates": "code",
        "common_mistakes_to_avoid": "err",
        "problem_solving_heuristics": "prob",
        "context_clues_and_indicators": "ctx",
        "others": "misc",
        "meta_strategies": "meta",
    }

    # Clean and convert to snake_case
    clean_name = section_name.lower().strip().replace(" ", "_").replace("&", "and")

    if clean_name in slug_map:
        return slug_map[clean_name]

    # Generate slug from first letters
    words = clean_name.split("_")
    if len(words) == 1:
        return words[0][:4]
    else:
        return "".join(w[0] for w in words[:5])


def extract_boxed_content(text):
    """Helper function to extract content from \\boxed{} format"""
    pattern = r'\\boxed\{'
    match = re.search(pattern, text)
    if not match:
        return None

    start = match.end() - 1  # Position of opening brace
    brace_count = 0
    i = start

    while i < len(text):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return text[start + 1 : i]  # Content between braces
        i += 1
    return None


def extract_answer(response):
    """Extract final answer from model response"""
    try:
        # First try JSON parsing
        parsed = json.loads(response)
        answer = str(parsed.get("final_answer", "No final answer found"))
        return answer

    except (json.JSONDecodeError, KeyError, AttributeError):
        # JSON parsing failed, use fallback logic
        matches = re.findall(r"Finish\[(.*?)\]", response)
        if matches:
            answer = matches[-1]
            return answer

        # Try to get final answer from JSON style response with regex matching
        # Try double quotes first
        matches = re.findall(r'"final_answer"\s*:\s*"([^"]*)"', response)
        if matches:
            answer = matches[-1]
            return answer

        # Try single quotes
        matches = re.findall(r"'final_answer'\s*:\s*'([^']*)'", response)
        if matches:
            answer = matches[-1]
            return answer

        # Handle JSON format without quotes (for simple expressions)
        matches = re.findall(r'[\'"]final_answer[\'"]\s*:\s*([^,}]+)', response)
        if matches:
            answer = matches[-1].strip()
            # Clean up trailing characters
            answer = re.sub(r'[,}]*$', '', answer)
            return answer

        # Fallback for "The final answer is: X" pattern with boxed
        final_answer_pattern = r'[Tt]he final answer is:?\s*\$?\\boxed\{'
        match = re.search(final_answer_pattern, response)
        if match:
            # Extract boxed content starting from this match
            remaining_text = response[match.start() :]
            boxed_content = extract_boxed_content(remaining_text)
            if boxed_content:
                return boxed_content

        # More general pattern for "final answer is X"
        matches = re.findall(r'[Tt]he final answer is:?\s*([^\n.]+)', response)
        if matches:
            answer = matches[-1].strip()
            # Clean up common formatting
            answer = re.sub(r'^\$?\\boxed\{([^}]+)\}\$?$', r'\1', answer)
            answer = answer.replace('$', '').strip()
            if answer:
                return answer

        return "No final answer found"


enc = tiktoken.get_encoding("cl100k_base")


def count_tokens(prompt: str) -> int:
    """计算经验有多少 token，这里直接计数字符了"""
    return len(enc.encode(prompt))


def evaluate_single_test_sample(args_tuple, data_processor, logger) -> Tuple[Dict, str]:
    """
    Evaluate a single test sample - task-agnostic implementation.

    Args:
        args_tuple: Tuple of (index, task_dict, generator, playbook, max_tokens, log_dir, use_json_mode)
        data_processor: DataProcessor instance with answer_is_correct method
    """
    (i, task_dict, generator, playbook, max_tokens, log_dir, use_json_mode) = args_tuple
    try:
        question = task_dict["question"]
        target = task_dict["target"]

        from offline.ace.core.generator import Generator

        gen_response, bullet_ids, call_info = Generator(
            model=generator, max_tokens=max_tokens, logger=logger
        ).generate(
            question=question,
            playbook=playbook,
            reflection="(empty)",
            use_json_mode=use_json_mode,
            call_id=f"test_eval_{i}",
            log_dir=log_dir,
        )

        final_answer = extract_answer(gen_response)
        is_correct = data_processor.answer_is_correct(final_answer, target)

        return {
            "index": i,
            "question": question,
            "final_answer": final_answer,
            "target": target,
            "is_correct": is_correct,
            "success": True,
        }, None

    except Exception as e:
        import traceback

        logger.error(traceback.format_exc())
        return None, f"Error evaluating sample {i}: {type(e).__name__}: {str(e)}"


def evaluate_test_set(
    data_processor,
    generator,
    playbook,
    test_samples,
    logger,
    max_tokens=4096,
    log_dir=None,
    max_workers=20,
    use_json_mode=False,
) -> Tuple[Dict, Dict]:
    """
    Parallel evaluation of test set - task-agnostic implementation.
    （for dev）

    Args:
        data_processor: DataProcessor instance with answer_is_correct and evaluate_accuracy methods
        generator: Generator instance
        playbook: Current playbook string
        test_samples: List of test samples
        max_tokens: Max tokens for generation
        log_dir: Directory for logs
        max_workers: Number of parallel workers
        use_json_mode: Whether to use JSON mode

    Returns:
        Tuple of (results_dict, error_logs_dict)
    """
    logger.info(f"{'='*40}")
    logger.info(
        f"EVALUATING TEST SET - {len(test_samples)} samples, {max_workers} workers"
    )
    logger.info(f"{'='*40}")

    args_list = [
        (i, sample, generator, playbook, max_tokens, log_dir, use_json_mode)
        for i, sample in enumerate(test_samples)
    ]

    results = {
        "correct": 0,
        "total": 0,
        "no_answer": 0,
        "samples": [],
        "errors": [],
    }

    # Use a wrapper to pass data_processor to the evaluation function
    def eval_wrapper(args_tuple):
        return evaluate_single_test_sample(args_tuple, data_processor, logger)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_args = {
            executor.submit(eval_wrapper, args): args for args in args_list
        }

        for i, future in enumerate(as_completed(future_to_args), 1):
            result, error = future.result()

            if error:
                logger.error(error)
                continue

            if result and result["success"]:
                results["correct"] += 1 if result["is_correct"] else 0
                results["total"] += 1

                sample_info = {
                    "index": result["index"],
                    "question": result["question"],
                    "prediction": result["final_answer"],
                    "ground_truth": result["target"],
                    "is_correct": result["is_correct"],
                }
                results["samples"].append(sample_info)

                if not result["is_correct"]:
                    results["errors"].append(
                        {
                            "index": result["index"],
                            "prediction": result["final_answer"],
                            "ground_truth": result["target"],
                            "question": result["question"],
                        }
                    )

                if result["final_answer"] == "No final answer found":
                    results["no_answer"] += 1

            if i % 50 == 0:
                curr_acc = (
                    results["correct"] / results["total"] if results["total"] > 0 else 0
                )
                logger.info(f"Progress: {i}/{len(args_list)}, Accuracy: {curr_acc:.3f}")

    if results["samples"]:
        # Extract answers and targets for accuracy calculation
        answers = [s["prediction"] for s in results["samples"]]
        targets = [s["ground_truth"] for s in results["samples"]]

        accuracy = data_processor.evaluate_accuracy(answers, targets)

        final_results = {
            "accuracy": accuracy,
            "correct": results["correct"],
            "total": results["total"],
            "no_answer": results["no_answer"],
            "samples": results["samples"],
        }

        error_logs = {"accuracy": accuracy, "errors": results["errors"]}

        logger.info(
            f"📊 Final Accuracy: {accuracy:.3f} ({results['correct']}/{results['total']})"
        )
    else:
        results = {"accuracy": 0.0, "correct": 0, "total": 0}
        error_logs = {}
        logger.info(f"📊 No valid results!")

    return final_results, error_logs


def evaluate_test_set_for_eval_only(
    data_processor,
    generator,
    playbook,
    test_samples,
    logger,
    max_tokens=4096,
    log_dir=None,
    max_workers=20,
    use_json_mode=False,
) -> Tuple[Dict, Dict]:
    """
    Parallel evaluation of test set - task-agnostic implementation.
    （for dev）

    Args:
        data_processor: DataProcessor instance with answer_is_correct and evaluate_accuracy methods
        generator: Generator instance
        playbook: Current playbook string
        test_samples: List of test samples
        max_tokens: Max tokens for generation
        log_dir: Directory for logs
        max_workers: Number of parallel workers
        use_json_mode: Whether to use JSON mode

    Returns:
        Tuple of (results_dict, error_logs_dict)
    """
    system_prompt_template = """
你是一个具备自我进化能力的智能助手，通过持续学习和经验积累不断提升性能。

【核心能力】
- 自我进化：从每次交互中学习，不断优化自身的回答策略
- 策略调整：根据不同任务特点，灵活运用已有经验进行调整
- 持续改进：通过策略经验，持续提升回答的准确性和效率

【策略经验】
{playbook}

【任务要求】
根据给定的问题和上下文，解析出问题的答案。在回答时，充分利用上述策略经验，结合具体问题特点进行策略的参考使用。
    """.strip()
    logger.info(f"system_prompt_template: \n{system_prompt_template}")

    logger.info(f"{'='*40}")
    logger.info(
        f"EVALUATING TEST SET - {len(test_samples)} samples, {max_workers} workers"
    )
    logger.info(f"{'='*40}")

    # 处理playbook，去掉id，统计
    exp = []
    for pb in playbook.split("\n"):
        if pb.startswith('##'):
            exp.append(pb)
            continue
        _exp = pb.split('::')[-1].strip()
        exp.append(_exp)
    playbook = "\n".join(exp)

    results = {
        "correct": 0,
        "total": 0,
        "no_answer": 0,
        "samples": [],
        "errors": [],
    }

    for i in range(0, len(test_samples), max_workers):
        batch_sample = test_samples[i : i + max_workers]

        messages = []
        questions = []
        targets = []
        for b in batch_sample:
            question = b["question"]
            target = b["target"]
            questions.append(question)
            targets.append(target)
            messages.append(
                [
                    SystemMessage(
                        content=system_prompt_template.format(playbook=playbook)
                    ),
                    HumanMessage(content=question),
                ]
            )
        batch_result = generator.batch(messages)

        for idx, response in enumerate(batch_result):
            final_answer = response.content
            target = targets[idx]
            question = questions[idx]
            is_correct = data_processor.answer_is_correct(final_answer, target)

            results["correct"] += 1 if is_correct else 0
            results["total"] += 1

            sample_info = {
                "index": i + idx,
                "question": question,
                "prediction": final_answer,
                "ground_truth": target,
                "is_correct": is_correct,
            }
            results["samples"].append(sample_info)

            if not is_correct:
                results["errors"].append(
                    {
                        "index": i + idx,
                        "prediction": final_answer,
                        "ground_truth": target,
                        "question": question,
                    }
                )

            if final_answer == "No final answer found":
                results["no_answer"] += 1

        curr_acc = results["correct"] / results["total"] if results["total"] > 0 else 0
        logger.info(
            f"Progress: {results['total']}/{len(test_samples)}, Accuracy: {curr_acc:.3f}"
        )

    if results["samples"]:
        # Extract answers and targets for accuracy calculation
        answers = [s["prediction"] for s in results["samples"]]
        targets = [s["ground_truth"] for s in results["samples"]]

        accuracy = data_processor.evaluate_accuracy(answers, targets)

        final_results = {
            "accuracy": accuracy,
            "correct": results["correct"],
            "total": results["total"],
            "no_answer": results["no_answer"],
            "samples": results["samples"],
        }

        error_logs = {"accuracy": accuracy, "errors": results["errors"]}

        logger.info(
            f"📊 Final Accuracy: {accuracy:.3f} ({results['correct']}/{results['total']})"
        )
    else:
        results = {"accuracy": 0.0, "correct": 0, "total": 0}
        error_logs = {}
        logger.info(f"📊 No valid results!")

    return final_results, error_logs
