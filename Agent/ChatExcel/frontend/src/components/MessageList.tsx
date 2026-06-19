/** MessageList — 消息列表，左右气泡，Markdown渲染 */

import {
  UserOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import TableRenderer from './TableRenderer';
import ChartRenderer from './ChartRenderer';
import StepCard from './StepCard';
import ResultTabs from './ResultTabs';
import type { ChatMode, StepState } from '../types';

interface ChatMessage {
  role: 'human' | 'ai';
  content: string;
  mode: ChatMode;
  sql?: string;
  chartType?: string;
  chartData?: { columns: string[]; rows: any[][] } | null;
  steps?: StepState[];
  finalContent?: string;
  elapsedMs?: number;
}

interface Props {
  messages: ChatMessage[];
  isWorking: boolean;
}

/** Markdown 组件样式覆盖 */
const formatElapsed = (elapsedMs: number) => {
  if (elapsedMs < 1000) return `${elapsedMs}ms`;
  return `${(elapsedMs / 1000).toFixed(1)}s`;
};

/** 清洗 finalContent：如果后端返回的是 {"result": "..."} 这样的 JSON 字符串，提取纯文本 */
const cleanFinalContent = (raw: string): string => {
  const trimmed = raw.trim();
  if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed && typeof parsed.result === 'string') return parsed.result;
      if (parsed && typeof parsed.output === 'string') return parsed.output;
    } catch {
      // 不是合法 JSON，原样返回
    }
  }
  return raw;
};

const markdownComponents = {
  h1: ({ children }: any) => <h3 style={{ fontSize: 18, margin: '8px 0 4px', fontWeight: 600 }}>{children}</h3>,
  h2: ({ children }: any) => <h4 style={{ fontSize: 16, margin: '8px 0 4px', fontWeight: 600 }}>{children}</h4>,
  h3: ({ children }: any) => <h5 style={{ fontSize: 14, margin: '6px 0 2px', fontWeight: 600 }}>{children}</h5>,
  p: ({ children }: any) => <p style={{ margin: '4px 0' }}>{children}</p>,
  ul: ({ children }: any) => <ul style={{ margin: '4px 0', paddingLeft: 20 }}>{children}</ul>,
  ol: ({ children }: any) => <ol style={{ margin: '4px 0', paddingLeft: 20 }}>{children}</ol>,
  li: ({ children }: any) => <li style={{ margin: '2px 0' }}>{children}</li>,
  code: ({ className, children }: any) => {
    const isBlock = className?.includes('language-');
    if (isBlock) {
      return <pre className="sql-block">{children}</pre>;
    }
    return <code style={{ background: '#f0f0f0', padding: '1px 4px', borderRadius: 3, fontSize: 13 }}>{children}</code>;
  },
  pre: ({ children }: any) => <div>{children}</div>,
  table: ({ children }: any) => (
    <div style={{ overflowX: 'auto', margin: '8px 0' }}>
      <table style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}>{children}</table>
    </div>
  ),
  th: ({ children }: any) => <th style={{ border: '1px solid #ddd', padding: '4px 8px', background: '#f5f5f5', textAlign: 'left' }}>{children}</th>,
  td: ({ children }: any) => <td style={{ border: '1px solid #ddd', padding: '4px 8px' }}>{children}</td>,
};

export default function MessageList({ messages, isWorking }: Props) {
  if (messages.length === 0 && !isWorking) {
    return (
      <div style={{ textAlign: 'center', color: '#aaa', padding: 60, fontSize: 14 }}>
        上传 Excel 文件，输入问题开始分析
      </div>
    );
  }

  return (
    <>
      {messages.map((msg, idx) => {
        const isLastAi = idx === messages.length - 1 && msg.role === 'ai';
        const showSpinner = isLastAi && isWorking && !msg.content && !msg.sql && !msg.finalContent;

        return (
          <div key={idx} className={`message-row ${msg.role === 'human' ? 'user' : 'ai'}`}>
            {/* 头像 */}
            <div className={`message-avatar ${msg.role === 'human' ? 'human' : 'ai'}`}>
              {msg.role === 'human' ? <UserOutlined /> : <RobotOutlined />}
            </div>

            {/* 气泡内容 */}
            <div className="message-bubble">
              {msg.role === 'human' ? (
                <div>{msg.content}</div>
              ) : (
                <>
                  {/* 加载中转圈 */}
                  {showSpinner && (
                    <div className="typing-indicator">
                      <span /><span /><span />
                    </div>
                  )}

                  {/* 模块1渲染 */}
                  {msg.mode === 'chat_excel' && (
                    <>
                      {msg.content && (
                        <div className="markdown-body">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}
                      {msg.sql && msg.chartData && msg.chartType && msg.chartData.columns && msg.chartData.rows ? (
                        <ResultTabs
                          sql={msg.sql}
                          chartType={msg.chartType}
                          chartData={msg.chartData}
                        />
                      ) : (
                        <>
                          {msg.sql && (
                            <pre className="sql-block">{msg.sql}</pre>
                          )}
                          {msg.chartData && msg.chartType && msg.chartData.columns && msg.chartData.rows && (
                            <div style={{ marginTop: 8 }}>
                              {msg.chartType === 'response_table' ? (
                                <TableRenderer columns={msg.chartData.columns} rows={msg.chartData.rows} />
                              ) : (
                                <ChartRenderer chartType={msg.chartType} data={msg.chartData} />
                              )}
                            </div>
                          )}
                        </>
                      )}
                    </>
                  )}

                  {/* 模块3渲染 */}
                  {msg.mode === 'react_agent' && (
                    <>
                      {msg.steps && msg.steps.map((step, sIdx) => (
                        <StepCard key={sIdx} step={step} />
                      ))}
                      {msg.finalContent && (
                        <div className="final-answer">
                          <strong>结论: </strong>
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {cleanFinalContent(msg.finalContent)}
                          </ReactMarkdown>
                        </div>
                      )}
                    </>
                  )}
                  {msg.elapsedMs ? (
                    <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                      用时 {formatElapsed(msg.elapsedMs)}
                    </div>
                  ) : null}
                </>
              )}
            </div>
          </div>
        );
      })}

      {/* 全局加载指示器（非空 AI 消息时不再显示） */}
      {isWorking && messages.length > 0 && messages[messages.length - 1].role === 'human' && (
        <div className="message-row ai">
          <div className="message-avatar ai"><RobotOutlined /></div>
          <div className="message-bubble">
            <div className="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
