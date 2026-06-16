import json
import logging
import time
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from openai import OpenAI

from config import (
    ProviderConfig,
    get_all_providers,
    get_active_provider,
    get_provider_by_model,
    set_active_provider,
    add_provider,
    update_provider,
    delete_provider,
)

logger = logging.getLogger("api_agent")

app = FastAPI(title="API Agent - OpenAI Compatible Proxy")

# ─── 请求日志 ────────────────────────────────────────────────────────────────

request_logs: list[dict] = []
MAX_LOGS = 200


def _add_log(entry: dict):
    request_logs.append(entry)
    if len(request_logs) > MAX_LOGS:
        request_logs.pop(0)


def _summarize_body(body: dict) -> dict:
    """提取请求关键信息用于日志"""
    summary = {
        "model": body.get("model", ""),
        "stream": body.get("stream", False),
        "temperature": body.get("temperature"),
        "top_p": body.get("top_p"),
        "max_tokens": body.get("max_tokens"),
    }

    # messages 概要
    messages = body.get("messages", [])
    summary["message_count"] = len(messages)
    summary["message_roles"] = [m.get("role", "?") for m in messages]
    # 最后一条消息的内容预览
    if messages:
        last = messages[-1]
        content = last.get("content", "")
        if isinstance(content, str):
            summary["last_message_preview"] = content[:200]
        elif isinstance(content, list):
            # 多模态消息
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(f"[text] {item.get('text', '')[:100]}")
                    elif item.get("type") == "image_url":
                        parts.append("[image_url]")
                    else:
                        parts.append(f"[{item.get('type', '?')}]")
            summary["last_message_preview"] = " | ".join(parts)[:200]

    # tools 信息
    tools = body.get("tools", [])
    if tools:
        summary["tool_count"] = len(tools)
        summary["tool_names"] = [t.get("function", {}).get("name", "?") for t in tools]

    tool_choice = body.get("tool_choice")
    if tool_choice:
        summary["tool_choice"] = tool_choice

    # response_format
    if "response_format" in body:
        summary["response_format"] = body["response_format"]

    return summary


# ─── OpenAI Compatible Proxy Endpoints ───────────────────────────────────────

@app.get("/v1/models")
async def list_models():
    providers = get_all_providers()
    data = []
    # 默认模型始终存在
    data.append({"id": "gpt-5.5-self", "object": "model", "owned_by": "api-agent"})
    for p in providers:
        data.append({
            "id": p.model,
            "object": "model",
            "owned_by": p.name,
        })
    return {"object": "list", "data": data}


DEFAULT_MODEL = "gpt-5.5-self"


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    model = body.get("model", "")

    # ★★★ 断点调试：打印 Trae 传入的完整请求体 ★★★
    print("=" * 80)
    print(f"[DEBUG] 完整请求体 (model={model}):")
    print(json.dumps(body, ensure_ascii=False, indent=2))
    print("=" * 80)

    # 记录请求日志
    log_entry = {
        "time": time.strftime("%H:%M:%S"),
        "direction": "in",
        "model": model,
        "summary": _summarize_body(body),
        "raw_keys": list(body.keys()),
    }
    logger.info(f"[Request] model={model}, stream={body.get('stream', False)}, "
                f"messages={len(body.get('messages', []))}, "
                f"tools={len(body.get('tools', [])) if body.get('tools') else 0}, "
                f"keys={list(body.keys())}")

    # 默认模型路由到活跃供应商
    if model == DEFAULT_MODEL:
        provider = get_active_provider()
        if not provider:
            raise HTTPException(status_code=404, detail="No active provider. Please add and activate a provider first.")
    else:
        provider = get_provider_by_model(model)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Model '{model}' not found. Please add it in the provider config.")

    stream = body.get("stream", False)

    try:
        client = OpenAI(base_url=provider.base_url, api_key=provider.api_key)

        kwargs = {
            "model": provider.model,
            "messages": body.get("messages", []),
            "stream": stream,
        }
        for key in ("temperature", "top_p", "max_tokens", "presence_penalty",
                     "frequency_penalty", "n", "stop", "response_format",
                     "tools", "tool_choice"):
            if key in body:
                kwargs[key] = body[key]

        log_entry["provider"] = provider.name
        log_entry["forward_to"] = f"{provider.base_url} -> {provider.model}"
        _add_log(log_entry)

        if stream:
            return StreamingResponse(
                _stream_response(client, kwargs, provider.name),
                media_type="text/event-stream",
            )
        else:
            response = client.chat.completions.create(**kwargs)
            result = json.loads(response.model_dump_json())
            _add_log({
                "time": time.strftime("%H:%M:%S"),
                "direction": "out",
                "provider": provider.name,
                "model": model,
                "usage": result.get("usage"),
            })
            return result

    except Exception as e:
        logger.error(f"Proxy error: {e}")
        log_entry["error"] = str(e)
        _add_log(log_entry)
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")


async def _stream_response(client: OpenAI, kwargs: dict, provider_name: str) -> AsyncIterator[str]:
    try:
        response = client.chat.completions.create(**kwargs)
        for chunk in response:
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
        _add_log({
            "time": time.strftime("%H:%M:%S"),
            "direction": "out",
            "provider": provider_name,
            "model": kwargs.get("model", ""),
            "note": "stream completed",
        })
    except Exception as e:
        logger.error(f"Stream error: {e}")
        error_data = json.dumps({"error": {"message": str(e), "type": "upstream_error"}})
        yield f"data: {error_data}\n\n"
        yield "data: [DONE]\n\n"


# ─── Provider Config API ─────────────────────────────────────────────────────

@app.get("/api/providers")
async def api_list_providers():
    from config import _load_config
    config = _load_config()
    providers = get_all_providers()
    active_name = config.get("active_name")
    return {"providers": [p.model_dump() for p in providers], "active_name": active_name}


@app.post("/api/providers")
async def api_add_provider(provider: ProviderConfig):
    if not add_provider(provider):
        raise HTTPException(status_code=409, detail=f"供应商 '{provider.name}' 已存在")
    return {"ok": True}


@app.put("/api/providers/{name}")
async def api_update_provider(name: str, provider: ProviderConfig):
    if not update_provider(name, provider):
        raise HTTPException(status_code=404, detail=f"供应商 '{name}' 不存在")
    return {"ok": True}


@app.delete("/api/providers/{name}")
async def api_delete_provider(name: str):
    if not delete_provider(name):
        raise HTTPException(status_code=404, detail=f"供应商 '{name}' 不存在")
    return {"ok": True}


@app.post("/api/providers/{name}/activate")
async def api_activate_provider(name: str):
    if not set_active_provider(name):
        raise HTTPException(status_code=404, detail=f"供应商 '{name}' 不存在")
    return {"ok": True}


@app.get("/api/logs")
async def api_get_logs():
    return request_logs


@app.delete("/api/logs")
async def api_clear_logs():
    request_logs.clear()
    return {"ok": True}


# ─── Web UI ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_CONTENT


HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>API Agent</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f0f2f5; color: #1f2937; min-height: 100vh;
  }
  .container { max-width: 960px; margin: 0 auto; padding: 32px 20px; }
  h1 { font-size: 24px; margin-bottom: 4px; color: #111827; font-weight: 700; }
  .subtitle { color: #6b7280; margin-bottom: 28px; font-size: 14px; }

  /* Tab */
  .tabs { display: flex; gap: 0; margin-bottom: 24px; border-bottom: 2px solid #e5e7eb; }
  .tab {
    padding: 10px 24px; cursor: pointer; font-size: 14px; font-weight: 500;
    color: #6b7280; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s;
  }
  .tab:hover { color: #2563eb; }
  .tab.active { color: #2563eb; border-bottom-color: #2563eb; }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Endpoint Info */
  .endpoint-box {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 20px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .endpoint-box .label { color: #6b7280; font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
  .endpoint-box .value { color: #2563eb; font-size: 15px; font-family: 'Cascadia Code', 'Fira Code', monospace; word-break: break-all; }
  .endpoint-box .hint { color: #9ca3af; font-size: 12px; margin-top: 10px; line-height: 1.5; }
  .endpoint-row { display: flex; gap: 24px; flex-wrap: wrap; }
  .endpoint-row > div { flex: 1; min-width: 200px; }

  /* Card */
  .card {
    background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
    padding: 18px 20px; margin-bottom: 12px; transition: all 0.2s;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  }
  .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
  .card.active-card { border-color: #2563eb; background: #f0f5ff; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
  .card-title { font-size: 15px; font-weight: 600; color: #111827; }
  .card-model { color: #2563eb; font-family: monospace; font-size: 13px; }
  .card-detail { color: #6b7280; font-size: 13px; margin-top: 3px; word-break: break-all; }
  .card-detail span { color: #9ca3af; }
  .card-badge {
    display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 11px; font-weight: 600;
  }
  .badge-active { background: #dcfce7; color: #166534; }
  .badge-inactive { background: #f3f4f6; color: #9ca3af; }

  /* Buttons */
  .btn {
    padding: 6px 14px; border-radius: 8px; border: none; cursor: pointer;
    font-size: 13px; font-weight: 500; transition: all 0.15s;
  }
  .btn-primary { background: #2563eb; color: #fff; }
  .btn-primary:hover { background: #1d4ed8; }
  .btn-danger { background: #fee2e2; color: #dc2626; }
  .btn-danger:hover { background: #fecaca; }
  .btn-outline { background: transparent; border: 1px solid #d1d5db; color: #374151; }
  .btn-outline:hover { background: #f9fafb; border-color: #9ca3af; }
  .btn-success { background: #dcfce7; color: #166534; }
  .btn-success:hover { background: #bbf7d0; }
  .actions { display: flex; gap: 6px; align-items: center; }

  .add-btn {
    width: 100%; padding: 14px; border-radius: 12px; border: 2px dashed #d1d5db;
    background: #fff; color: #6b7280; font-size: 14px; cursor: pointer;
    transition: all 0.2s; margin-bottom: 24px;
  }
  .add-btn:hover { border-color: #2563eb; color: #2563eb; background: #f0f5ff; }

  /* Modal */
  .modal-overlay {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.3); z-index: 100; justify-content: center; align-items: center;
  }
  .modal-overlay.active { display: flex; }
  .modal {
    background: #fff; border-radius: 16px; padding: 28px; width: 480px; max-width: 90vw;
    box-shadow: 0 20px 60px rgba(0,0,0,0.15);
  }
  .modal h2 { font-size: 18px; margin-bottom: 20px; color: #111827; }
  .form-group { margin-bottom: 14px; }
  .form-group label { display: block; color: #374151; font-size: 13px; font-weight: 500; margin-bottom: 5px; }
  .form-group input {
    width: 100%; padding: 9px 12px; border-radius: 8px; border: 1px solid #d1d5db;
    background: #fff; color: #1f2937; font-size: 14px; outline: none;
  }
  .form-group input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }
  .form-group .hint { color: #9ca3af; font-size: 12px; margin-top: 3px; }
  .modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; }

  .empty-state { text-align: center; padding: 48px 20px; color: #9ca3af; }
  .empty-state p { margin-top: 8px; font-size: 14px; }

  /* Logs */
  .log-container {
    background: #1e293b; border-radius: 12px; padding: 16px; font-family: 'Cascadia Code', 'Fira Code', monospace;
    font-size: 12px; max-height: 500px; overflow-y: auto; color: #e2e8f0;
  }
  .log-entry { padding: 6px 0; border-bottom: 1px solid #334155; }
  .log-entry:last-child { border-bottom: none; }
  .log-time { color: #64748b; }
  .log-in { color: #38bdf8; }
  .log-out { color: #4ade80; }
  .log-err { color: #f87171; }
  .log-key { color: #94a3b8; }
  .log-val { color: #e2e8f0; }
  .log-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .log-header span { color: #6b7280; font-size: 13px; }
</style>
</head>
<body>
<div class="container">
  <h1>API Agent</h1>
  <p class="subtitle">LLM API 代理 - 兼容 OpenAI 接口格式</p>

  <div class="endpoint-box">
    <div class="endpoint-row">
      <div>
        <div class="label">代理端点</div>
        <div class="value" id="endpointUrl"></div>
      </div>
      <div>
        <div class="label">默认模型 ID</div>
        <div class="value">gpt-5.5-self</div>
      </div>
    </div>
    <div class="hint">在 Trae 中：API Base URL 填上方端点地址，模型名填 gpt-5.5-self（或下方自定义模型名）</div>
  </div>

  <div class="tabs">
    <div class="tab active" onclick="switchTab('providers')">供应商管理</div>
    <div class="tab" onclick="switchTab('logs')">请求日志</div>
  </div>

  <div id="tab-providers" class="tab-content active">
    <div id="providerList"></div>
    <button class="add-btn" onclick="openModal()">+ 添加供应商</button>
  </div>

  <div id="tab-logs" class="tab-content">
    <div class="log-header">
      <span id="logCount">0 条记录</span>
      <button class="btn btn-outline" onclick="clearLogs()">清空日志</button>
    </div>
    <div class="log-container" id="logContainer">
      <div class="empty-state" style="color:#64748b"><p>暂无请求日志，发送请求后将在此显示</p></div>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal">
  <div class="modal">
    <h2 id="modalTitle">添加供应商</h2>
    <div class="form-group">
      <label>供应商名称</label>
      <input id="fName" placeholder="例如: DeepSeek, 智谱, 月之暗面">
    </div>
    <div class="form-group">
      <label>Base URL</label>
      <input id="fUrl" placeholder="例如: https://api.deepseek.com/v1">
      <div class="hint">供应商的 API 地址，需包含 /v1 路径</div>
    </div>
    <div class="form-group">
      <label>API Key</label>
      <input id="fKey" type="password" placeholder="sk-xxxx">
    </div>
    <div class="form-group">
      <label>模型名称</label>
      <input id="fModel" placeholder="例如: deepseek-chat">
      <div class="hint">客户端请求时的 model 参数，需与供应商实际模型名一致</div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-outline" onclick="closeModal()">取消</button>
      <button class="btn btn-primary" onclick="saveProvider()">保存</button>
    </div>
  </div>
</div>

<script>
const BASE = location.origin;
let editingName = null;
let logRefreshTimer = null;

document.getElementById('endpointUrl').textContent = BASE + '/v1';

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelector(`.tab:nth-child(${name==='providers'?1:2})`).classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'logs') { loadLogs(); startLogRefresh(); }
  else { stopLogRefresh(); }
}

async function loadProviders() {
  const res = await fetch('/api/providers');
  const data = await res.json();
  const providers = data.providers || [];
  const activeName = data.active_name;
  const list = document.getElementById('providerList');
  if (!providers.length) {
    list.innerHTML = '<div class="empty-state"><p>暂无供应商配置，点击下方按钮添加</p></div>';
    return;
  }
  list.innerHTML = providers.map(p => {
    const isActive = p.name === activeName;
    return `
    <div class="card ${isActive ? 'active-card' : ''}">
      <div class="card-header">
        <div>
          <span class="card-title">${esc(p.name)}</span>
          <span class="card-badge ${isActive ? 'badge-active' : 'badge-inactive'}">${isActive ? '使用中' : '未启用'}</span>
          <div class="card-model">${esc(p.model)}</div>
        </div>
        <div class="actions">
          ${!isActive ? `<button class="btn btn-success" onclick="activateProvider('${esc(p.name)}')">启用</button>` : ''}
          <button class="btn btn-outline" onclick="editProvider('${esc(p.name)}')">编辑</button>
          <button class="btn btn-danger" onclick="delProvider('${esc(p.name)}')">删除</button>
        </div>
      </div>
      <div class="card-detail"><span>URL: </span>${esc(p.base_url)}</div>
      <div class="card-detail"><span>Key: </span>${p.api_key.slice(0,8)}...${p.api_key.slice(-4)}</div>
    </div>`;
  }).join('');
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function openModal(provider = null) {
  editingName = provider ? provider.name : null;
  document.getElementById('modalTitle').textContent = provider ? '编辑供应商' : '添加供应商';
  document.getElementById('fName').value = provider ? provider.name : '';
  document.getElementById('fUrl').value = provider ? provider.base_url : '';
  document.getElementById('fKey').value = provider ? provider.api_key : '';
  document.getElementById('fModel').value = provider ? provider.model : '';
  document.getElementById('fName').disabled = !!provider;
  document.getElementById('modal').classList.add('active');
}

function closeModal() {
  document.getElementById('modal').classList.remove('active');
  editingName = null;
}

async function saveProvider() {
  const data = {
    name: document.getElementById('fName').value.trim(),
    base_url: document.getElementById('fUrl').value.trim(),
    api_key: document.getElementById('fKey').value.trim(),
    model: document.getElementById('fModel').value.trim(),
  };
  if (!data.name || !data.base_url || !data.api_key || !data.model) {
    alert('请填写所有字段'); return;
  }
  if (editingName) {
    await fetch('/api/providers/' + encodeURIComponent(editingName), {
      method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
  } else {
    const res = await fetch('/api/providers', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    if (res.status === 409) { alert('该供应商名称已存在'); return; }
  }
  closeModal();
  loadProviders();
}

async function activateProvider(name) {
  await fetch('/api/providers/' + encodeURIComponent(name) + '/activate', { method: 'POST' });
  loadProviders();
}

async function editProvider(name) {
  const res = await fetch('/api/providers');
  const data = await res.json();
  const p = (data.providers || []).find(x => x.name === name);
  if (p) openModal(p);
}

async function delProvider(name) {
  if (!confirm('确定删除 ' + name + ' ?')) return;
  await fetch('/api/providers/' + encodeURIComponent(name), { method: 'DELETE' });
  loadProviders();
}

// ─── Logs ────────────────────────────────────────────────────────────────────

async function loadLogs() {
  const res = await fetch('/api/logs');
  const logs = await res.json();
  const container = document.getElementById('logContainer');
  document.getElementById('logCount').textContent = logs.length + ' 条记录';
  if (!logs.length) {
    container.innerHTML = '<div class="empty-state" style="color:#64748b"><p>暂无请求日志</p></div>';
    return;
  }
  container.innerHTML = logs.map(log => {
    const dir = log.direction === 'in' ? 'IN' : 'OUT';
    const dirClass = log.direction === 'in' ? 'log-in' : (log.error ? 'log-err' : 'log-out');
    let detail = '';
    if (log.direction === 'in' && log.summary) {
      const s = log.summary;
      detail = `<span class="log-key">model:</span> <span class="log-val">${esc(s.model||'')}</span> `;
      detail += `<span class="log-key">stream:</span> <span class="log-val">${s.stream}</span> `;
      detail += `<span class="log-key">messages:</span> <span class="log-val">${s.message_count||0}条 [${(s.message_roles||[]).join(', ')}]</span><br>`;
      if (s.last_message_preview) detail += `<span class="log-key">  末条:</span> <span class="log-val">${esc(s.last_message_preview)}</span><br>`;
      if (s.tool_count) detail += `<span class="log-key">  tools:</span> <span class="log-val">${s.tool_count}个 [${(s.tool_names||[]).join(', ')}]</span><br>`;
      if (s.tool_choice) detail += `<span class="log-key">  tool_choice:</span> <span class="log-val">${JSON.stringify(s.tool_choice)}</span><br>`;
      if (s.temperature !== undefined && s.temperature !== null) detail += `<span class="log-key">  temperature:</span> <span class="log-val">${s.temperature}</span> `;
      if (s.max_tokens) detail += `<span class="log-key">  max_tokens:</span> <span class="log-val">${s.max_tokens}</span> `;
      if (s.response_format) detail += `<span class="log-key">  response_format:</span> <span class="log-val">${JSON.stringify(s.response_format)}</span><br>`;
      detail += `<span class="log-key">  请求字段:</span> <span class="log-val">[${(log.raw_keys||[]).join(', ')}]</span>`;
      if (log.forward_to) detail += `<br><span class="log-key">  转发至:</span> <span class="log-val">${esc(log.forward_to)}</span>`;
    } else if (log.direction === 'out') {
      if (log.usage) detail = `<span class="log-key">usage:</span> <span class="log-val">prompt=${log.usage.prompt_tokens||0} completion=${log.usage.completion_tokens||0} total=${log.usage.total_tokens||0}</span>`;
      else if (log.note) detail = `<span class="log-val">${esc(log.note)}</span>`;
    }
    if (log.error) detail += `<br><span class="log-err">ERROR: ${esc(log.error)}</span>`;
    return `<div class="log-entry"><span class="log-time">${log.time}</span> <span class="${dirClass}">[${dir}]</span> <span class="log-key">${esc(log.provider||'')}</span> <span class="log-key">${esc(log.model||'')}</span><br>${detail}</div>`;
  }).reverse().join('');
}

async function clearLogs() {
  await fetch('/api/logs', { method: 'DELETE' });
  loadLogs();
}

function startLogRefresh() {
  stopLogRefresh();
  logRefreshTimer = setInterval(loadLogs, 2000);
}
function stopLogRefresh() {
  if (logRefreshTimer) { clearInterval(logRefreshTimer); logRefreshTimer = null; }
}

loadProviders();
</script>
</body>
</html>
"""
