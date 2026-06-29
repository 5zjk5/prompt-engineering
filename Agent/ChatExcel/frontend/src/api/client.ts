/** API 客户端 — fetch 封装 */

const API_BASE = '/api';

export async function uploadFile(file: File, chatMode: string = 'chat_excel', userNo: string = 'default', convUid: string = ''): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('chat_mode', chatMode);
  formData.append('user_no', userNo);
  if (convUid) formData.append('conv_uid', convUid);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
  if (!res.ok) {
    // 解析后端返回的错误详情，给用户展示可读的提示
    let detail = '';
    try {
      const errBody = await res.json();
      detail = errBody?.detail || errBody?.message || '';
    } catch {}
    if (res.status === 413 || detail.includes('超过')) {
      throw new Error(detail || '文件超过大小限制');
    }
    throw new Error(detail || `上传失败 (${res.status})`);
  }
  return res.json();
}

export async function listConversations(limit = 50): Promise<any[]> {
  const res = await fetch(`${API_BASE}/conversations?limit=${limit}`);
  return res.json();
}

export async function createConversation(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function updateConversation(convUid: string, data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/conversations/${convUid}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteConversation(convUid: string): Promise<any> {
  const res = await fetch(`${API_BASE}/conversations/${convUid}`, { method: 'DELETE' });
  return res.json();
}

export async function addMessage(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getMessages(convUid: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/messages/${convUid}`);
  return res.json();
}

export async function getExcelPreview(filePath: string): Promise<any> {
  const res = await fetch(`${API_BASE}/excel-preview?file_path=${encodeURIComponent(filePath)}`);
  if (!res.ok) {
    let detail = '';
    try {
      const errBody = await res.json();
      detail = errBody?.detail || errBody?.message || '';
    } catch {}
    throw new Error(detail || `预览失败 (${res.status})`);
  }
  return res.json();
}

export async function getLlmModels(): Promise<{ name: string; model: string }[]> {
  const res = await fetch(`${API_BASE}/llm/models`);
  return res.json();
}
