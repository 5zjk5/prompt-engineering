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


def get_span_with_context(text, span_text, span_index, context_length=10):
    end_index = span_index + len(span_text)
    context = text[end_index : end_index + context_length]
    if context:
        return f"[{span_text}]{context}"
    return f"[{span_text}]"


def process_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data_list = [json.loads(line.strip()) for line in f if line.strip()]

    processed_data = []

    for item in data_list:
        text = item.get('text', '')
        label = item.get('label', '')
        target = item.get('target', {})

        span1_text = target.get('span1_text', '')
        span2_text = target.get('span2_text', '')
        span1_index = target.get('span1_index', 0)
        span2_index = target.get('span2_index', 0)

        span1_with_context = get_span_with_context(text, span1_text, span1_index)
        span2_with_context = get_span_with_context(text, span2_text, span2_index)

        question = f"判断句子中的'{span1_with_context}'和'{span2_with_context}'是否指代同一对象，直接回答true或false。句子内容：{text}"
        target_value = label

        processed_data.append({'question': question, 'target': target_value})

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: {input_file} -> {output_file}, 共 {len(processed_data)} 条数据")


def main():
    task_name = "指代消解"
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
