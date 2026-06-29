/** TypeScript 类型定义 */

export type ChatMode = 'chat_excel' | 'react_agent';

export interface FileInfo {
  file_id: string;
  file_path: string;
  file_name: string;
}

export interface Conversation {
  conv_uid: string;
  chat_mode: ChatMode;
  model_name: string;
  file_path: string;
  file_name: string;
  file_paths?: string[];
  file_names?: string[];
  message_count?: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id?: number;
  conv_uid: string;
  role: 'human' | 'ai' | 'system';
  content: string;
  order_no: number;
  created_at?: string;
}

// ── Module 1 SSE Events ──────────────────────────────────

export interface ExcelSSEEvent {
  type: 'learning' | 'learning_result' | 'learning_done' | 'thought' | 'sql' | 'chart' | 'text' | 'model' | 'error' | 'done';
  content?: string;
  chart_type?: string;
  data?: { columns: string[]; rows: any[][] };
  model?: string;
}

// ── Module 3 SSE Events ──────────────────────────────────

export interface ReactSSEEvent {
  type: 'step.start' | 'step.meta' | 'step.chunk' | 'step.done' | 'context.status' | 'final' | 'model' | 'done' | 'plan.update' | 'error';
  // step.start
  step?: number;
  id?: string;
  title?: string;
  detail?: string;
  // step.meta
  thought?: string;
  action?: string;
  action_input?: any;
  action_intention?: string;
  action_reason?: string;
  // step.chunk
  output_type?: 'thought' | 'text' | 'code' | 'html' | 'image' | 'table' | 'chart' | 'json' | string;
  content?: any;
  // step.done
  status?: 'done' | 'failed';
  // context.status
  used?: number;
  budget?: number;
  ratio?: number;
  state?: string;
  compact_layer?: string | null;
  // plan.update
  todos?: Array<{ content: string; status: string; priority: string }>;
  // model
  model?: string;
}

// ── Step Card (for Module 3 rendering) ───────────────────

export interface StepState {
  id: string;
  step: number;
  title: string;
  thought: string;
  action: string;
  actionInput: any;
  output: string[];
  status: 'running' | 'completed' | 'error';
  error?: string;
}

// ── Context Status ───────────────────────────────────────

export interface ContextStatus {
  used: number;
  budget: number;
  ratio: number;
  state: 'OK' | 'WARNING' | 'ERROR';
  compactLayer?: string | null;
}
