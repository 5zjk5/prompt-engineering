/** 模块1 ChatExcel Hook — SSE 流式对话 */

import { useCallback, useRef, useState } from 'react';
import { readSSEStream } from '../api/sse-parser';
import type { ExcelSSEEvent } from '../types';

export interface ExcelChatState {
  thought: string;
  sql: string;
  chartType: string;
  chartData: { columns: string[]; rows: any[][] } | null;
  text: string;
  isWorking: boolean;
  error: string | null;
}

const initialState: ExcelChatState = {
  thought: '',
  sql: '',
  chartType: '',
  chartData: null,
  text: '',
  isWorking: false,
  error: null,
};

export function useChatExcel() {
  const [state, setState] = useState<ExcelChatState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const cancel = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState(prev => ({ ...prev, isWorking: false }));
  }, []);

  const sendMessage = useCallback(async (
    userInput: string,
    convUid: string,
    filePath: string,
    fileName: string,
  ) => {
    cancel();
    abortRef.current = new AbortController();
    setState({ ...initialState, isWorking: true });

    try {
      const res = await fetch('/api/chat/excel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({
          user_input: userInput,
          conv_uid: convUid,
          file_path: filePath,
          file_name: fileName,
        }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await readSSEStream(res, (event: ExcelSSEEvent) => {
        setState(prev => {
          switch (event.type) {
            case 'learning_done':
              return prev;  // 学习完成信号，不需要更新状态
            case 'thought':
              return { ...prev, thought: prev.thought + (prev.thought ? '\n' : '') + (event.content || '') };
            case 'sql':
              return { ...prev, sql: event.content || '' };
            case 'chart':
              return { ...prev, chartType: event.chart_type || '', chartData: event.data || null };
            case 'text':
              return { ...prev, text: prev.text + (event.content || '') };
            case 'error':
              return { ...prev, error: event.content || 'Error' };
            case 'done':
              return { ...prev, isWorking: false };
            default:
              return prev;
          }
        });
      });

      setState(prev => ({ ...prev, isWorking: false }));
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setState(prev => ({ ...prev, isWorking: false, error: err.message }));
      }
    }
  }, [cancel]);

  const reset = useCallback(() => {
    cancel();
    setState(initialState);
  }, [cancel]);

  return { state, sendMessage, cancel, reset };
}