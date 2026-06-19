/** ContextBar — Token 用量进度条 */

import type { ContextStatus } from '../types';

interface Props {
  status: ContextStatus | null;
}

export default function ContextBar({ status }: Props) {
  if (!status) return null;

  const percent = Math.round(status.ratio * 100);
  const color = status.state === 'OK' ? '#52c41a'
    : status.state === 'WARNING' ? '#faad14'
    : '#ff4d4f';

  return (
    <div className="context-bar" title={`Used: ${status.used} / Budget: ${status.budget} tokens (${percent}%)`}>
      <span>{percent}%</span>
      <div className="context-bar-bar">
        <div className="context-bar-fill" style={{ width: `${percent}%`, background: color }} />
      </div>
    </div>
  );
}
