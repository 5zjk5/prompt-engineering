/** SSE 解析器 — 解析后端 SSE data: 行为事件对象 */

export function parseSSELine(line: string): any | null {
  const prefix = 'data: ';
  if (!line.startsWith(prefix)) return null;
  const jsonStr = line.slice(prefix.length).trim();
  if (!jsonStr) return null;
  try {
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

/** 从 ReadableStream 读取 SSE 事件 */
export async function readSSEStream(
  response: Response,
  onEvent: (event: any) => void,
  onError?: (error: string) => void,
): Promise<void> {
  if (!response.body) throw new Error('Response body is null');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // 处理剩余 buffer
        if (buffer.trim()) {
          for (const line of buffer.split('\n')) {
            const trimmed = line.trim();
            if (trimmed) {
              const event = parseSSELine(trimmed);
              if (event) onEvent(event);
            }
          }
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed) {
          const event = parseSSELine(trimmed);
          if (event) onEvent(event);
        }
      }
    }
  } catch (err: any) {
    if (err.name !== 'AbortError' && onError) {
      onError(err.message || 'Stream error');
    }
  }
}