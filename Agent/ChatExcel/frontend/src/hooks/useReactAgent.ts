/** 模块3 ReAct Agent Hook — SSE 流式对话 */

import { useCallback, useRef, useState } from 'react';
import { readSSEStream } from '../api/sse-parser';
import type { ReactSSEEvent, StepState, ContextStatus } from '../types';

export interface ReactChatState {
  steps: StepState[];
  finalContent: string;
  isWorking: boolean;
  error: string | null;
  contextStatus: ContextStatus | null;
}

const initialState: ReactChatState = {
  steps: [],
  finalContent: '',
  isWorking: false,
  error: null,
  contextStatus: null,
};

export function useReactAgent() {
  const [state, setState] = useState<ReactChatState>(initialState);
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
      const res = await fetch('/api/chat/react-agent', {
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

      await readSSEStream(res, (event: ReactSSEEvent) => {
        setState(prev => {
          const steps = [...prev.steps];

          switch (event.type) {
            case 'step.start': {
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
              return { ...prev, steps };
            }
            case 'step.meta': {
              const step = steps.find(s => s.id === event.id);
              if (step) {
                step.thought = event.thought || step.thought;
                step.action = event.action || step.action;
                step.actionInput = event.action_input ?? step.actionInput;
              }
              return { ...prev, steps };
            }
            case 'step.chunk': {
              const step = steps.find(s => s.id === event.id);
              if (step) {
                if (event.output_type === 'thought') {
                  step.thought += event.content || '';
                } else {
                  const content = typeof event.content === 'string' ? event.content : JSON.stringify(event.content, null, 2);
                  step.output.push(content);
                }
              }
              return { ...prev, steps };
            }
            case 'step.done': {
              const step = steps.find(s => s.id === event.id);
              if (step) {
                step.status = event.status === 'done' ? 'completed' : 'error';
                if (event.status === 'failed') step.error = 'Step failed';
              }
              return { ...prev, steps };
            }
            case 'context.status': {
              if (!Number.isFinite(event.budget) || (event.budget ?? 0) <= 0) return prev;
              const stateMap: Record<string, 'OK' | 'WARNING' | 'ERROR'> = {
                normal: 'OK', warning: 'WARNING', error: 'ERROR',
                critical: 'ERROR', overflow: 'ERROR',
              };
              return {
                ...prev,
                contextStatus: {
                  used: event.used || 0,
                  budget: event.budget || 0,
                  ratio: event.ratio || 0,
                  state: stateMap[event.state || 'normal'] || 'OK',
                  compactLayer: event.compact_layer,
                },
              };
            }
            case 'final': {
              return { ...prev, finalContent: event.content || '' };
            }
            case 'error': {
              return { ...prev, error: event.content || '服务端异常', finalContent: `❌ ${event.content || '服务端异常'}` };
            }
            case 'done': {
              return { ...prev, isWorking: false };
            }
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