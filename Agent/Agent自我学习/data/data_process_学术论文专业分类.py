import json
import os
from pathlib import Path


def get_project_root():
    script_path = Path(__file__).resolve()
    if script_path.name == "data":
        return script_path.parent
    elif script_path.parent.name == "data":
        return script_path.parent.parent
    else:
        return script_path.parent


def get_all_labels(data_list):
    labels = set()
    for item in data_list:
        if 'label' in item:
            labels.add(item['label'])
    return sorted(list(labels))


def process_data(input_file, output_file, all_labels, samples_per_label=None):
    with open(input_file, 'r', encoding='utf-8') as f:
        data_list = [json.loads(line.strip()) for line in f if line.strip()]

    labels_str = "、".join(all_labels)

    if samples_per_label is not None:
        data_by_label = {}
        for item in data_list:
            label = item.get('label', '')
            if label not in data_by_label:
                data_by_label[label] = []
            data_by_label[label].append(item)

        data_list = []
        for label in all_labels:
            if label in data_by_label:
                samples = data_by_label[label][:samples_per_label]
                data_list.extend(samples)
                print(
                    f"  {label}: {len(samples)} 条 (总共 {len(data_by_label[label])} 条)"
                )
            else:
                print(f"  {label}: 0 条 (无数据)")

    processed_data = []

    for item in data_list:
        content = item.get('content', '')
        label = item.get('label', '')

        question = f"有如下{labels_str}分类，判断当前内容数据什么分类。直接说出分类结果，分类结果必须是中文且跟标签对应，不要生成其他任何多余内容。\n\n{content}"
        target = label

        processed_data.append({'question': question, 'target': target})

    with open(output_file, 'w', encoding='utf-8') as f:
        for item in processed_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

    print(f"处理完成: {input_file} -> {output_file}, 共 {len(processed_data)} 条数据")


def main():
    task_name = "学术论文专业分类"
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

    with open(train_file, 'r', encoding='utf-8') as f:
        train_data = [json.loads(line.strip()) for line in f if line.strip()]

    all_labels = get_all_labels(train_data)
    print(f"所有分类标签: {all_labels}")

    print(f"\n处理训练数据 (每个类别 10 条):")
    process_data(train_file, output_train, all_labels, samples_per_label=10)

    print(f"\n处理验证数据 (每个类别 10 条):")
    process_data(dev_file, output_dev, all_labels, samples_per_label=10)

    print(f"\n处理测试数据 (全部数据):")
    process_data(test_file, output_test, all_labels, samples_per_label=None)

    print(f"\n所有数据处理完成！输出目录: {data_process_dir}")


if __name__ == "__main__":
    main()
