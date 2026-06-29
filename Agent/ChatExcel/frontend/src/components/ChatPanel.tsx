/** ChatPanel — 主聊天面板，现代大模型对话风格 */

import { useState, useRef, useEffect } from 'react';
import ModeSwitcher from './ModeSwitcher';
import ModelSelector from './ModelSelector';
import ContextBar from './ContextBar';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { readSSEStream } from '../api/sse-parser';
import { getMessages, updateConversation } from '../api/client';
import type { ChatMode, FileInfo, StepState, ExcelSSEEvent, ReactSSEEvent } from '../types';

function stripApiCall(content: string): string {
  return content.replace(/<api-call>[\s\S]*?<\/api-call>/g, '').trim();
}

function normalizeLearningTitle(content: string): string {
  return content.replace(/(### \*\*表：[^\n]*?)\s*\/\s*data_analysis_[^*\n]+(\*\*)/g, '$1$2');
}

function hasAiVisibleContent(msg: ChatMessage): boolean {
  return !!(
    msg.content?.trim()
    || msg.sql?.trim()
    || msg.finalContent?.trim()
    || (msg.steps && msg.steps.length > 0)
    || msg.chartData
  );
}

function isDuplicateMessage(prev: ChatMessage | undefined, next: ChatMessage): boolean {
  if (!prev || prev.role !== next.role) return false;
  if (prev.role === 'human') return prev.content === next.content;
  return prev.content === next.content
    && (prev.finalContent || '') === (next.finalContent || '')
    && (prev.sql || '') === (next.sql || '')
    && JSON.stringify(prev.steps || []) === JSON.stringify(next.steps || []);
}

export interface ChatMessage {
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
  convUid: string;
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void | Promise<void>;
  onTitleUpdate: (hasMessage?: boolean) => void;  // 通知 App 刷新侧边栏标题
  onFilePathUpdate?: (fileInfo: FileInfo) => void;  // 通知 App 文件变化（用于预览栏）
  initialFilePaths?: string[];  // 从会话恢复的文件路径列表
  initialFileNames?: string[];  // 从会话恢复的文件名列表
  selectedModel: string;  // 用户选择的模型名称
  onModelChange: (model: string) => void;  // 模型切换回调（含后端自动切换通知）
}

export default function ChatPanel({ convUid, mode, onModeChange, onTitleUpdate, onFilePathUpdate, initialFilePaths = [], initialFileNames = [], selectedModel, onModelChange }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isWorking, setIsWorking] = useState(false);
  const [contextStatus, setContextStatus] = useState<any>(null);
  const [hasHistory, setHasHistory] = useState(false);  // 是否有对话历史（用于锁死模式）
  const messageAreaRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);  // 追踪最新消息用于持久化

  // 加载历史消息
  useEffect(() => {
    let cancelled = false;
    setMessages([]);
    messagesRef.current = [];
    setHasHistory(false);
    const loadHistory = async () => {
      try {
        const dbMessages = await getMessages(convUid);
        if (dbMessages && dbMessages.length > 0) {
          const loaded: ChatMessage[] = [];
          for (const msg of dbMessages) {
            if (msg.role === 'human') {
              const humanMsg: ChatMessage = { role: 'human', content: msg.content, mode };
              if (!isDuplicateMessage(loaded[loaded.length - 1], humanMsg)) loaded.push(humanMsg);
            } else if (msg.role === 'ai') {
              // 从 metadata 恢复完整消息结构
              const base: ChatMessage = { role: 'ai', content: normalizeLearningTitle(stripApiCall(msg.content || '')), mode };
              if (msg.metadata) {
                try {
                  const meta = JSON.parse(msg.metadata);
                  if (meta.sql) base.sql = meta.sql;
                  if (meta.chartType) base.chartType = meta.chartType;
                  if (meta.chartData) base.chartData = meta.chartData;
                  if (meta.steps) base.steps = meta.steps;
                  if (meta.finalContent) base.finalContent = meta.finalContent;
                  if (typeof meta.elapsedMs === 'number') base.elapsedMs = meta.elapsedMs;
                  if (meta.content) base.content = normalizeLearningTitle(stripApiCall(meta.content));  // metadata中的content更准确
                } catch {}
              }
              if (hasAiVisibleContent(base) && !isDuplicateMessage(loaded[loaded.length - 1], base)) {
                loaded.push(base);
              }
            }
          }
          if (cancelled) return;
          setMessages(loaded);
          messagesRef.current = loaded;  // 同步 ref，否则 learningMsgIdx 会算错
          setHasHistory(true);
        }
      } catch {}
    };
    loadHistory();
    return () => { cancelled = true; };
  }, [convUid, mode]);

  // 自动滚动到底部
  useEffect(() => {
    if (messageAreaRef.current) {
      messageAreaRef.current.scrollTop = messageAreaRef.current.scrollHeight;
    }
  }, [messages, isWorking]);


  const handleSend = async (input: string, fileInfo: FileInfo | null, fileList?: (FileInfo & { size?: number })[]) => {
    const startedAt = performance.now();
    const hasQuestion = !!input.trim();

    // 在添加用户消息之前捕获当前消息数量，确保索引计算不受 setMessages 时序影响
    const baseMsgCount = messagesRef.current.length;

    // 添加用户消息（有输入时才显示用户气泡）
    if (hasQuestion) {
      const userMsg: ChatMessage = { role: 'human', content: input, mode };
      setMessages(prev => { const next = [...prev, userMsg]; messagesRef.current = next; return next; });
    }
    setIsWorking(true);

    // react_agent 模式：使用文件列表中的路径；chat_excel 模式：使用单个文件
    let filePath = fileInfo?.file_path || '';
    let fileName = fileInfo?.file_name || '';
    let filePaths: string[] = [];
    let fileNames: string[] = [];
    if (mode === 'react_agent' && fileList && fileList.length > 0) {
      filePaths = fileList.map(f => f.file_path).filter(Boolean);
      fileNames = fileList.map(f => f.file_name).filter(Boolean);
      // 主文件路径取第一个
      if (!filePath && filePaths.length > 0) {
        filePath = filePaths[0];
        fileName = fileNames[0];
      }
    }

    const endpoint = mode === 'chat_excel' ? '/api/chat/excel' : '/api/chat/react-agent';

    // 创建学习阶段的 AI 消息
    // 索引 = 原始消息数 + (有用户提问时占1位) = 新 AI 消息在数组中的位置
    const learningMsgIdx = baseMsgCount + (hasQuestion ? 1 : 0);
    const emptyAiMsg: ChatMessage = {
      role: 'ai',
      content: '',
      mode,
      sql: '',
      chartType: '',
      chartData: null,
      steps: [],
      finalContent: '',
    };
    setMessages(prev => { const next = [...prev, emptyAiMsg]; messagesRef.current = next; return next; });

    // 用可变对象追踪当前活跃 AI 消息索引（learning_done 时可能切换到新消息）
    const activeIdx = { current: learningMsgIdx };
    const createdAiIndexes = new Set<number>([learningMsgIdx]);

    abortRef.current = new AbortController();

    // 更新对话标题（首次发送时）
    if (!hasHistory) {
      const displayName = fileName ? fileName.replace(/\.[^.]+$/, '') : '';
      const newTitle = displayName
        ? `${displayName} - ${input.slice(0, 20)}`
        : input.slice(0, 30) || '数据学习';
      try {
        await updateConversation(convUid, {
          title: newTitle.length > 30 ? newTitle.slice(0, 30) + '...' : newTitle,
          chat_mode: mode,
          file_path: filePath,
          file_name: fileName,
        });
        onTitleUpdate(hasQuestion);  // 刷新侧边栏
      } catch {}
      setHasHistory(true);
    }

    // 记录对话已关联文件
    if (fileInfo) {
      onTitleUpdate();
      // 通知 App 更新文件路径（用于预览栏）
      onFilePathUpdate?.(fileInfo);
    }

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({
          user_input: input,
          conv_uid: convUid,
          file_path: filePath,
          file_name: fileName,
          file_paths: filePaths,
          file_names: fileNames,
          model_name: selectedModel,
        }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      if (mode === 'chat_excel') {
        // 模块1: 逐事件更新 AI 消息
        await readSSEStream(res, (event: ExcelSSEEvent) => {
          setMessages(prev => {
            const updated = [...prev];
            const idx = activeIdx.current;
            if (idx >= updated.length || !updated[idx]) {
              console.warn(`SSE event index ${idx} out of bounds (length ${updated.length}), skipping`, event.type);
              return prev;
            }
            const msg = { ...updated[idx] } as ChatMessage;

            switch (event.type) {
              case 'model':
                if (event.model) onModelChange(event.model);
                break;
              case 'learning':
                msg.content = event.content || '正在分析数据结构...';
                break;
              case 'learning_result':
                msg.content = normalizeLearningTitle(event.content || '');
                break;
              case 'learning_done':
                // 有用户问题：学完后再创建一条 AI 消息用于分析阶段
                if (hasQuestion) {
                  updated[idx] = msg;
                  const analysisMsg: ChatMessage = {
                    role: 'ai', content: '', mode,
                    sql: '', chartType: '', chartData: null,
                  };
                  updated.push(analysisMsg);
                  activeIdx.current = idx + 1;
                  createdAiIndexes.add(idx + 1);
                  messagesRef.current = updated;
                  return updated;
                }
                break;
              case 'thought':
                break;
              case 'sql':
                msg.sql = event.content || '';
                break;
              case 'chart':
                msg.chartType = event.chart_type || '';
                msg.chartData = event.data || null;
                break;
              case 'text':
                msg.content = (msg.content || '') + (event.content || '');
                break;
              case 'error':
                msg.content = (msg.content || '') + '\n❌ ' + (event.content || 'Error');
                break;
              case 'done': {
                const elapsedMs = Math.round(performance.now() - startedAt);
                for (const aiIdx of createdAiIndexes) {
                  if (updated[aiIdx]?.role === 'ai') updated[aiIdx] = { ...updated[aiIdx], elapsedMs };
                }
                msg.elapsedMs = elapsedMs;
                break;
              }
            }
            updated[idx] = msg;
            messagesRef.current = updated;
            return updated;
          });
        });
      } else {
        // 模块3: 逐事件更新 AI 消息
        await readSSEStream(res, (event: ReactSSEEvent) => {
          setMessages(prev => {
            const updated = [...prev];
            if (learningMsgIdx >= updated.length || !updated[learningMsgIdx]) {
              console.warn(`ReAct SSE index ${learningMsgIdx} out of bounds (length ${updated.length}), skipping`);
              return prev;
            }
            const msg = { ...updated[learningMsgIdx] } as ChatMessage;
            const steps = (msg.steps || []).map(step => ({
              ...step,
              output: [...(step.output || [])],
            }));

            switch (event.type) {
              case 'model':
                if (event.model) onModelChange(event.model);
                break;
              case 'step.start':
                steps.push({
                  id: event.id || `step_${steps.length}`,
                  step: event.step || steps.length + 1,
                  title: event.title || '',
                  thought: '',
                  action: '',
                  actionInput: null,
                  output: [],
                  status: 'running',
                });
                msg.steps = steps;
                break;
              case 'step.meta': {
                const step = steps.find(s => s.id === event.id);
                if (step) {
                  step.thought = event.thought || step.thought;
                  step.action = event.action || step.action;
                  step.actionInput = event.action_input ?? step.actionInput;
                }
                msg.steps = steps;
                break;
              }
              case 'step.chunk': {
                const step = steps.find(s => s.id === event.id);
                if (step) {
                  if (event.output_type === 'thought') {
                    step.thought = event.content || step.thought;
                  } else if ((event.output_type || 'text') === 'text') {
                    const lastIdx = step.output.length - 1;
                    const last = step.output[lastIdx];
                    if (last && last.startsWith('{"output_type":"text"')) {
                      try {
                        const parsed = JSON.parse(last);
                        parsed.content = `${parsed.content || ''}${event.content || ''}`;
                        step.output[lastIdx] = JSON.stringify(parsed);
                      } catch {
                        step.output.push(JSON.stringify({ output_type: 'text', content: event.content || '' }));
                      }
                    } else {
                      step.output.push(JSON.stringify({ output_type: 'text', content: event.content || '' }));
                    }
                  } else {
                    // 将结构化 chunk 序列化为 JSON 字符串，供 StepCard 解析渲染
                    const chunkData = {
                      output_type: event.output_type || 'text',
                      content: event.content,
                      title: (event as any).title,
                    };
                    step.output.push(JSON.stringify(chunkData));
                  }
                }
                msg.steps = steps;
                break;
              }
              case 'step.done': {
                const step = steps.find(s => s.id === event.id);
                if (step) {
                  step.status = event.status === 'done' ? 'completed' : 'error';
                  if (event.status === 'failed') step.error = 'Step failed';
                }
                msg.steps = steps;
                break;
              }
              case 'context.status':
                setContextStatus({
                  used: event.used || 0,
                  budget: event.budget || 0,
                  ratio: event.ratio || 0,
                  state: event.state === 'normal' ? 'OK' : event.state === 'warning' ? 'WARNING' : 'ERROR',
                  compactLayer: event.compact_layer,
                });
                break;
              case 'plan.update':
                // 任务计划更新 — 暂存到 msg 上供后续渲染
                (msg as any).planTodos = event.todos || [];
                break;
              case 'final':
                msg.finalContent = event.content || '';
                break;
              case 'error':
                msg.finalContent = `❌ ${event.content || '服务端异常'}`;
                steps.forEach(step => {
                  if (step.status === 'running') {
                    step.status = 'error';
                    step.error = event.content || '服务端异常';
                  }
                });
                msg.steps = steps;
                break;
              case 'done':
                msg.elapsedMs = Math.round(performance.now() - startedAt);
                break;
            }
            updated[learningMsgIdx] = msg;
            messagesRef.current = updated;
            return updated;
          });
        });
      }

    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages(prev => {
          const updated = [...prev];
          updated[activeIdx.current] = { ...updated[activeIdx.current], content: '❌ 请求失败: ' + err.message } as ChatMessage;
          messagesRef.current = updated;
          return updated;
        });
      }
    }

    setIsWorking(false);
  };

  // 文件上传完成回调
  const handleFileUploaded = (fileInfo: FileInfo) => {
    // 标记对话已关联文件
    onFilePathUpdate?.(fileInfo);
    onTitleUpdate();
    // chat_excel 模式：自动触发学习
    if (mode === 'chat_excel') {
      handleSend('', fileInfo);
    }
  };

  // ChatExcel 和 ReAct 都允许在同一会话继续上传文件。
  const disableUpload = false;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 顶部栏 */}
      <div className="chat-topbar">
        <ModelSelector value={selectedModel} onChange={onModelChange} />
        <ModeSwitcher mode={mode} onChange={onModeChange} locked={hasHistory} />
        {mode === 'react_agent' && <ContextBar status={contextStatus} />}
      </div>

      {/* 消息列表 */}
      <div className="message-area" ref={messageAreaRef}>
        <div className="message-container">
          <MessageList messages={messages} isWorking={isWorking} />
        </div>
      </div>

      {/* 输入区 */}
      <div className="input-area">
        <ChatInput onSend={handleSend} disabled={isWorking} disableUpload={disableUpload} chatMode={mode} onFileUploaded={handleFileUploaded} convUid={convUid} initialFilePaths={initialFilePaths} initialFileNames={initialFileNames} />
      </div>
    </div>
  );
}
