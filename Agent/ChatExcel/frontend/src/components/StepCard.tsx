/** StepCard — ReAct 步骤卡片，支持多种 output_type 渲染 */

import { useState } from 'react';
import {
  CheckCircleOutlined,
  LoadingOutlined,
  CloseCircleOutlined,
  DownOutlined,
  UpOutlined,
  CodeOutlined,
  PictureOutlined,
  TableOutlined,
  BarChartOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { StepState } from '../types';

interface Props {
  step: StepState;
}

/** 根据 output_type 判断内容类型并渲染 */
function renderOutputItem(item: string, index: number) {
  // 尝试解析为结构化 chunk
  let parsed: { output_type?: string; content?: any; title?: string } | null = null;
  try {
    const obj = JSON.parse(item);
    if (obj && typeof obj === 'object' && obj.output_type) {
      parsed = obj;
    }
  } catch {}

  // 如果是结构化 chunk
  if (parsed) {
    switch (parsed.output_type) {
      case 'text':
        return (
          <div key={index} style={{ margin: '2px 0', fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {typeof parsed.content === 'string' ? parsed.content : JSON.stringify(parsed.content, null, 2)}
          </div>
        );
      case 'code':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              <CodeOutlined /> Code:
            </div>
            <pre style={{
              background: '#1e1e1e', color: '#d4d4d4', padding: 8, borderRadius: 4,
              fontSize: 11, overflowX: 'auto', maxHeight: 200,
            }}>
              {typeof parsed.content === 'string' ? parsed.content : JSON.stringify(parsed.content, null, 2)}
            </pre>
          </div>
        );
      case 'html':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              <FileTextOutlined /> HTML Report: {parsed.title || 'Report'}
            </div>
            <iframe
              srcDoc={typeof parsed.content === 'string' ? parsed.content : ''}
              style={{ width: '100%', height: 300, border: '1px solid #e8e8e8', borderRadius: 4 }}
              title={parsed.title || 'Report'}
              sandbox="allow-scripts"
            />
          </div>
        );
      case 'image':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              <PictureOutlined /> Image
            </div>
            <img
              src={typeof parsed.content === 'string' ? parsed.content : ''}
              alt="chart"
              style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }}
            />
          </div>
        );
      case 'table':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              <TableOutlined /> Table
            </div>
            <div style={{ fontSize: 11, color: '#666' }}>
              {typeof parsed.content === 'object' && parsed.content?.rows
                ? `${parsed.content.rows.length} rows`
                : 'Table data'}
            </div>
          </div>
        );
      case 'chart':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              <BarChartOutlined /> Chart
            </div>
          </div>
        );
      case 'json':
        return (
          <div key={index} style={{ marginBottom: 8 }}>
            <div style={{ color: '#888', fontWeight: 500, fontSize: 11, marginBottom: 2 }}>
              JSON:
            </div>
            <pre style={{ fontSize: 11, background: '#f5f5f5', padding: 4, borderRadius: 4, maxHeight: 120, overflow: 'auto' }}>
              {typeof parsed.content === 'string' ? parsed.content : JSON.stringify(parsed.content, null, 2)}
            </pre>
          </div>
        );
    }
  }

  // 默认文本渲染
  // 检测是否包含图片 URL
  if (typeof item === 'string' && item.startsWith('/images/')) {
    return (
      <div key={index} style={{ marginBottom: 8 }}>
        <img src={item} alt="chart" style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 4 }} />
      </div>
    );
  }

  // 检测是否包含 HTML 内容标记
  if (typeof item === 'string' && item.startsWith('[HTML Report')) {
    return (
      <div key={index} style={{ marginBottom: 8, color: '#1677ff', fontSize: 11 }}>
        <FileTextOutlined /> {item}
      </div>
    );
  }

  return (
    <pre key={index} style={{ margin: '2px 0', fontSize: 11, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
      {typeof item === 'string' ? item : JSON.stringify(item, null, 2)}
    </pre>
  );
}

export default function StepCard({ step }: Props) {
  return <StepCardContent key={`${step.id}-${step.status}`} step={step} />;
}

function StepCardContent({ step }: Props) {
  const [expanded, setExpanded] = useState(step.status === 'running');

  const statusIcon = step.status === 'completed'
    ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
    : step.status === 'error'
    ? <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
    : <LoadingOutlined style={{ color: '#1677ff' }} spin />;

  return (
    <div className="step-card">
      <div className="step-card-header" onClick={() => setExpanded(!expanded)}>
        {statusIcon}
        <strong style={{ fontSize: 12 }}>Step {step.step}</strong>
        <span style={{ color: '#1677ff', fontSize: 12 }}>{step.action || '...'}</span>
        {expanded ? <UpOutlined style={{ fontSize: 10, marginLeft: 'auto', color: '#aaa' }} />
                  : <DownOutlined style={{ fontSize: 10, marginLeft: 'auto', color: '#aaa' }} />}
      </div>
      {expanded && (
        <div className="step-card-body">
          {step.thought && (
            <div style={{ marginBottom: 6 }}>
              <span style={{ color: '#888', fontWeight: 500 }}>Thought: </span>
              {step.thought}
            </div>
          )}
          {step.action && (
            <div style={{ marginBottom: 6 }}>
              <span style={{ color: '#888', fontWeight: 500 }}>Action: </span>
              <span style={{ color: '#1677ff' }}>{step.action}</span>
              {step.actionInput && (
                <pre style={{ margin: '4px 0', fontSize: 11 }}>
                  {typeof step.actionInput === 'string'
                    ? step.actionInput
                    : JSON.stringify(step.actionInput, null, 2)}
                </pre>
              )}
            </div>
          )}
          {step.output.length > 0 && (
            <div>
              <span style={{ color: '#888', fontWeight: 500 }}>Observation:</span>
              {step.output.map((item, idx) => renderOutputItem(item, idx))}
            </div>
          )}
          {step.error && (
            <div style={{ color: '#ff4d4f' }}>{step.error}</div>
          )}
        </div>
      )}
    </div>
  );
}
