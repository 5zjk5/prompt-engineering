import json
from pathlib import Path


def get_project_root():
    script_path = Path(__file__).resolve()
    if script_path.name == "data":
        return script_path.parent
    elif script_path.parent.name == "data":
        return script_path.parent.parent
    else:
        return script_path.parent


def process_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data_list = [json.loads(line.strip()) for line in f if line.strip()]

    processed_data = []

    for item in data_list:
        sentence1 = item.get('sentence1', '')
        sentence2 = item.get('sentence2', '')
        label = item.get('label', '')

        question = f"判断以下两个句子之间的关系（entailment/contradiction/neutral），直接说出结果：\n句子1：{sentence1}\n句子2：{sentence2}"
        target_value = label

        processed_data.append({'question': question, 'target': target_value})

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: {input_file} -> {output_file}, 共 {len(processed_data)} 条数据")


def main():
    task_name = "自然语言推理"
    project_root = get_project_root()

    ori_data_dir = project_root / "data" / "ori_data" / task_name
    data_process_dir = project_root / "data" / "data_process" / task_name

    data_process_dir.mkdir(parents=True, exist_ok=True)

    train_file = ori_data_dir / "train_few_all.json"
    dev_file = ori_data_dir / "dev_few_all.json"
    test_file = ori_data_dir / "test_public.json"

    output_train = data_process_dir / "train.jsonl"
    output_dev = data_process_dir / "dev.jsonl"
    output_test = data_process_dir / "test.jsonl"

    process_data(train_file, output_train)
    process_data(dev_file, output_dev)
    process_data(test_file, output_test)

    print(f"\n所有数据处理完成！输出目录: {data_process_dir}")


if __name__ == "__main__":
    main()
