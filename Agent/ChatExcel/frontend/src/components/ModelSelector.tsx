/** ModelSelector — 大模型选择器，从后端获取可用模型列表供用户选择 */

import { useState, useEffect } from 'react';
import { Select } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { getLlmModels } from '../api/client';

interface Props {
  value: string;
  onChange: (model: string) => void;
}

export default function ModelSelector({ value, onChange }: Props) {
  const [models, setModels] = useState<{ name: string; model: string }[]>([]);

  useEffect(() => {
    getLlmModels()
      .then(data => {
        setModels(data);
        // 未选择模型时自动选中第一个，让用户知道当前默认使用哪个模型
        if (!value && data.length > 0) {
          onChange(data[0].name);
        }
      })
      .catch(err => console.error('Failed to load LLM models:', err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="model-selector">
      <RobotOutlined style={{ fontSize: 13, color: '#888' }} />
      <Select
        size="small"
        value={value || undefined}
        placeholder="选择模型"
        onChange={onChange}
        style={{ width: 170 }}
        options={models.map(m => ({ label: m.name, value: m.name }))}
        popupMatchSelectWidth={false}
      />
    </div>
  );
}
