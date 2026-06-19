import os
import json
import argparse
import time
from Agent.Agent自我学习.offline.ace import ACE
from Agent.Agent自我学习.offline.logger import define_log_level
from dotenv import load_dotenv
from Agent.Agent自我学习.llm.ChatOpenAIModel_LangChian import ChatOpenAIModel


load_dotenv('../.env')


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='ACE System - Refactored')

    # Task configuration
    parser.add_argument(
        "--task_name",
        type=str,
        default="指代消解",
        help="Task name. The name is in data/data_process directory, that is, processed data，必填",
    )
    parser.add_argument(
        "--initial_playbook_path",
        type=str,
        default=r'C:\Users\\zhoujk2\\Desktop\\prompt-engineering\\Agent自进化\\offline\\results\\指代消解_train\\best_playbook.txt',
        # default=None,
        help="Path to initial playbook (optional)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="eval_only",
        choices=["offline", "eval_only"],
        help="Run mode: 'offline' for offline training with validation, "
        "'eval_only' for testing only with provided playbook",
    )

    # Processor for handling data preprocessing, evaluation and accuracy computation.
    from Agent.Agent自我学习.offline.data_process.data_processor_ZiRanYuYanTuiLi import DataProcessor
    parser.add_argument(
        "--data_processor",
        type=str,
        default=DataProcessor(),
        help="Processor for handling data preprocessing, evaluation and accuracy computation. 必填",
    )

    # Model configuration
    generator_model = ChatOpenAIModel(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("MODEL"),
    )
    reflector_model = ChatOpenAIModel(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("MODEL"),
    )
    curator_model = ChatOpenAIModel(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL"),
        model=os.getenv("MODEL"),
    )
    parser.add_argument(
        "--generator_model",
        default=generator_model,
        help="Model for generator",
    )
    parser.add_argument(
        "--reflector_model",
        default=reflector_model,
        help="Model for reflector",
    )
    parser.add_argument(
        "--curator_model",
        default=curator_model,
        help="Model for curator",
    )

    # Training configuration
    parser.add_argument(
        "--num_epochs",
        type=int,
        default=2,
        help="Number of training epochs. This affects efficiency，总训练轮数",
    )
    parser.add_argument(
        "--max_num_rounds",
        type=int,
        default=1,
        help="Max reflection rounds for incorrect answers. This affects efficiency，每条样本数据自我反思次数",
    )
    parser.add_argument(
        "--curator_frequency",
        type=int,
        default=1,
        help="Run curator every N steps，策展器每训练几条数据就会去更新经验（设计缺陷：假如设置5，在第五条会用当前反思去更新经验，前面四条的丢掉了）",
    )
    parser.add_argument(
        "--eval_steps",
        type=int,
        default=20,
        help="Evaluate every N steps，每训练几条数据评估一次，使用 dev 集，验证经验效果。如果设置大小大于 train 集大小，最终结果不会保存训练数据结果",
    )
    parser.add_argument(
        "--save_steps",
        type=int,
        default=15,
        help="Save intermediate playbooks every N steps，每训练多少条数据保存一次中间过程得到的经验",
    )

    # System configuration
    parser.add_argument(
        "--max_tokens", type=int, default=4096, help="Max tokens for LLM responses"
    )
    parser.add_argument(
        "--playbook_token_budget",
        type=int,
        default=80000,
        help="Total token budget for playbook",
    )
    parser.add_argument(
        "--test_workers",
        type=int,
        default=200,
        help="Number of parallel workers for testing",
    )

    # Prompt configuration
    parser.add_argument(
        "--no_ground_truth",
        action="store_true",
        default=False,
        help="Don't use ground truth in reflection，有无标签",
    )

    # Bulletpoint analyzer configuration
    parser.add_argument(
        "--use_bulletpoint_analyzer",
        action="store_true",
        default=True,
        help="Enable bulletpoint analyzer for deduplication and merging，分析经验的会使用到向量模型，使用云端模型",
    )
    parser.add_argument(
        "--bulletpoint_analyzer_threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for bulletpoint analyzer (0-1)，经验的相似度",
    )

    # Output configuration
    parser.add_argument(
        "--save_path",
        type=str,
        default="./offline/results",
        help="Directory to save results",
    )

    return parser.parse_args()


def load_data(data_path: str, mode, logger):
    """
    Load and process data from a JSONL file.

    Args:
        data_path: Path to directory containing train.jsonl, dev.jsonl, and test.jsonl

    Returns:
        Tuple of (train_samples, val_samples, test_samples)
    """
    # Ensure data_path exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    # Load train data
    train_samples = []
    if mode == "offline":
        train_path = os.path.join(data_path, "train.jsonl")
        if not os.path.exists(train_path):
            raise FileNotFoundError(
                f"The mode is offline. Train data file not found: {train_path}"
            )
        with open(train_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    train_samples.append(json.loads(line))
        logger.info(f"Loaded {len(train_samples)} train samples from {train_path}")

    # Load dev data
    val_samples = []
    if mode == "offline":
        dev_path = os.path.join(data_path, "dev.jsonl")
        if not os.path.exists(dev_path):
            logger.warning(
                f"The mode is offline. Dev data file not found: {dev_path}. No verification is conducted."
            )
        else:
            with open(dev_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        val_samples.append(json.loads(line))
            logger.info(f"Loaded {len(val_samples)} dev samples from {dev_path}")

    # Load test data
    test_samples = []
    test_path = os.path.join(data_path, "test.jsonl")
    if mode == "eval_only":
        if not os.path.exists(test_path):
            raise FileNotFoundError(
                f"The mode is eval_only. Test data file not found: {test_path}"
            )
        with open(test_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    test_samples.append(json.loads(line))
        logger.info(f"Loaded {len(test_samples)} test samples from {test_path}")
    elif mode == "offline" and os.path.exists(test_path):
        with open(test_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    test_samples.append(json.loads(line))
        logger.info(f"Loaded {len(test_samples)} test samples from {test_path}")

    return train_samples, val_samples, test_samples


def load_initial_playbook(path):
    """Load initial playbook if provided."""
    if path and os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return None


def calc_token(log_dir, elapsed_time):
    """
    计算花费 token，同时保存耗时
    """
    detailed_llm_logs_dir = os.path.join(log_dir, "detailed_llm_logs")

    total_output_token = 0
    total_input_token = 0
    total_token = 0

    if os.path.exists(detailed_llm_logs_dir):
        for filename in os.listdir(detailed_llm_logs_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(detailed_llm_logs_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_output_token += data.get('output_token', 0)
                    total_input_token += data.get('input_token', 0)
                    total_token += data.get('total_token', 0)

    result = {
        "total_output_token": total_output_token,
        "total_input_token": total_input_token,
        "total_token": total_token,
        "elapsed_time": elapsed_time,
    }

    output_path = os.path.join(log_dir, "train_cost_stats.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def main():
    """Main execution function."""
    args = parse_args()

    # 初始化日志
    logger, log_dir = define_log_level(
        save_path=args.save_path,
        task_name=args.task_name,
        print_level="INFO",
        logfile_level="DEBUG",
    )

    logger.info(f"{'='*60}")
    logger.info(f"ACE SYSTEM")
    logger.info(f"{'='*60}")
    logger.info(f"Task: {args.task_name}")
    logger.info(f"Mode: {args.mode.upper().replace('_', ' ')}")
    logger.info(f"{'='*60}")

    # Load data
    task_data_path = os.path.join('./data/data_process', args.task_name)
    train_samples, val_samples, test_samples = load_data(
        task_data_path, args.mode, logger
    )

    # Load initial playbook (or use empty if None provided)
    initial_playbook = load_initial_playbook(args.initial_playbook_path)
    if initial_playbook:
        logger.info(f"Loaded initial playbook from {args.initial_playbook_path}")
    else:
        logger.info("Using empty playbook as initial playbook")

    # 参数验证和警告
    if args.mode == "offline":
        # 检查 eval_steps 是否合理
        if args.eval_steps > len(train_samples):
            logger.warning(
                f"⚠️  WARNING: eval_steps ({args.eval_steps}) is greater than the number of training samples ({len(train_samples)})"
            )
            logger.warning(
                f"⚠️  This means NO evaluation will be performed during training!"
            )
            logger.warning(
                f"⚠️  train_results.json will be empty. Please set eval_steps <= {len(train_samples)}"
            )

        # 检查 curator_frequency 是否合理
        if args.curator_frequency > len(train_samples):
            logger.warning(
                f"⚠️  WARNING: curator_frequency ({args.curator_frequency}) is greater than the number of training samples ({len(train_samples)})"
            )
            logger.warning(f"⚠️  This means the curator will NEVER run during training!")
            logger.warning(
                f"⚠️  The playbook will not be updated. Please set curator_frequency <= {len(train_samples)}"
            )

    # Create ACE system
    ace_system = ACE(
        generator_model=args.generator_model,
        reflector_model=args.reflector_model,
        curator_model=args.curator_model,
        max_tokens=args.max_tokens,
        initial_playbook=initial_playbook,
        use_bulletpoint_analyzer=args.use_bulletpoint_analyzer,
        bulletpoint_analyzer_threshold=args.bulletpoint_analyzer_threshold,
        logger=logger,
    )

    # Prepare configuration
    config = {
        'num_epochs': args.num_epochs,
        'max_num_rounds': args.max_num_rounds,
        'curator_frequency': args.curator_frequency,
        'eval_steps': args.eval_steps,
        'save_steps': args.save_steps,
        'playbook_token_budget': args.playbook_token_budget,
        'task_name': args.task_name,
        'mode': args.mode,
        'no_ground_truth': args.no_ground_truth,
        'save_dir': log_dir,
        'test_workers': args.test_workers,
        'initial_playbook_path': args.initial_playbook_path,
        'use_bulletpoint_analyzer': args.use_bulletpoint_analyzer,
        'bulletpoint_analyzer_threshold': args.bulletpoint_analyzer_threshold,
    }
    logger.info(f"Config: {config}")

    # Execute using the unified run method
    start_time = time.time()
    results = ace_system.run(
        mode=args.mode,
        train_samples=train_samples,
        val_samples=val_samples,
        test_samples=test_samples,
        data_processor=args.data_processor,
        config=config,
    )
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(
        f"ACE system execution completed. Total time: {elapsed_time:.2f} seconds"
    )

    # 计算花费训练提取经验 token 消耗，同时保存耗时
    calc_token(log_dir, elapsed_time)


if __name__ == "__main__":
    main()
