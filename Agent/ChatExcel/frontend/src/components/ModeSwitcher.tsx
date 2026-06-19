/** ModeSwitcher — 模式切换，高亮+Tooltip提示 */

import { Tooltip } from 'antd';
import { TableOutlined, CodeOutlined } from '@ant-design/icons';
import type { ChatMode } from '../types';

interface Props {
  mode: ChatMode;
  onChange: (mode: ChatMode) => void | Promise<void>;
  locked?: boolean;
}

const MODE_OPTIONS = [
  {
    label: 'ChatExcel',
    value: 'chat_excel' as ChatMode,
    icon: <TableOutlined />,
    tip: '单表单sheet — DuckDB SQL 自动分析',
  },
  {
    label: 'ReAct Agent',
    value: 'react_agent' as ChatMode,
    icon: <CodeOutlined />,
    tip: '多表多sheet — 代码执行深度分析',
  },
];

export default function ModeSwitcher({ mode, onChange, locked }: Props) {
  return (
    <div className="mode-switcher">
      {MODE_OPTIONS.map((opt) => (
        <Tooltip key={opt.value} title={locked ? '对话已开始，不可切换模式' : opt.tip} placement="bottom">
          <button
            className={`mode-btn ${mode === opt.value ? 'active' : ''}`}
            onClick={() => !locked && onChange(opt.value)}
            disabled={locked}
            style={locked && mode !== opt.value ? { opacity: 0.35, cursor: 'not-allowed' } : locked && mode === opt.value ? { cursor: 'not-allowed' } : undefined}
          >
            {opt.icon} {opt.label}
          </button>
        </Tooltip>
      ))}
    </div>
  );
}
