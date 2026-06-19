import { useState, useEffect, useRef } from 'react';
import { Modal } from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  TableOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import ChatPanel from './components/ChatPanel';
import ExcelPreview from './components/ExcelPreview';
import { listConversations, createConversation, deleteConversation, updateConversation } from './api/client';
import type { ChatMode, Conversation, FileInfo } from './types';

function getConversationFilePaths(conv: Conversation): string[] {
  if (Array.isArray(conv.file_paths) && conv.file_paths.length > 0) {
    return conv.file_paths.filter(Boolean);
  }
  return conv.file_path ? [conv.file_path] : [];
}

function isEmptyConversation(conv: Conversation): boolean {
  return getConversationFilePaths(conv).length === 0 && (conv.message_count || 0) === 0;
}

function isBlankNewConversation(conv: Conversation): boolean {
  return isEmptyConversation(conv) && (!conv.title || conv.title.startsWith('新对话'));
}

function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvUid, setActiveConvUid] = useState<string>('');
  const [mode, setMode] = useState<ChatMode>('chat_excel');
  const [activeFilePath, setActiveFilePath] = useState<string>('');
  const [activeFilePaths, setActiveFilePaths] = useState<string[]>([]);
  const [previewCollapsed, setPreviewCollapsed] = useState(true);
  const [editingConvUid, setEditingConvUid] = useState('');
  const [editingTitle, setEditingTitle] = useState('');
  const initDone = useRef(false);

  const activateConversation = (conv: Conversation) => {
    const filePaths = getConversationFilePaths(conv);
    const fp = filePaths[0] || '';
    setActiveConvUid(conv.conv_uid);
    setMode(conv.chat_mode as ChatMode);
    setActiveFilePath(fp);
    setActiveFilePaths(filePaths);
    setPreviewCollapsed(!(conv.chat_mode === 'chat_excel' && fp));
  };

  const loadConversations = async () => {
    try {
      const data = await listConversations();
      setConversations(data);
      return data;
    } catch (err) {
      console.error('Failed to load conversations:', err);
      return [];
    }
  };

  const handleNewConversation = async (source?: Conversation[], reuseEmpty = false) => {
    const currentConversations = source || conversations;
    const activeConversation = currentConversations.find(item => item.conv_uid === activeConvUid);
    if (!reuseEmpty && activeConversation && isBlankNewConversation(activeConversation)) {
      return;
    }
    const empty = reuseEmpty ? currentConversations.find(isEmptyConversation) : null;
    if (empty) {
      const nextEmpty = { ...empty, chat_mode: mode };
      activateConversation(nextEmpty);
      setConversations(items => items.map(item => (
        item.conv_uid === empty.conv_uid ? nextEmpty : item
      )));
      try {
        await updateConversation(empty.conv_uid, { chat_mode: mode });
      } catch (err) {
        console.error('Failed to update empty conversation mode:', err);
      }
      return;
    }

    const convUid = `conv_${Date.now()}`;
    const title = `新对话 ${currentConversations.length + 1}`;
    const now = new Date().toISOString();
    const newConversation = {
      conv_uid: convUid,
      chat_mode: mode,
      model_name: '',
      file_path: '',
      file_name: '',
      file_paths: [],
      file_names: [],
      message_count: 0,
      title,
      created_at: now,
      updated_at: now,
    } as Conversation;

    activateConversation(newConversation);
    setPreviewCollapsed(true);
    setConversations(prev => [newConversation, ...prev]);

    try {
      await createConversation({
        conv_uid: convUid,
        chat_mode: mode,
        title,
      });
      await loadConversations();
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  useEffect(() => {
    const init = async () => {
      if (initDone.current) return;
      initDone.current = true;
      const data = await loadConversations();
      await handleNewConversation(data, true);
    };
    init();
  }, []);

  const handleDeleteConversation = async (convUid: string) => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后不可恢复，确认删除此对话？',
      okText: '删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        await deleteConversation(convUid);
        const remaining = conversations.filter(c => c.conv_uid !== convUid);
        if (activeConvUid === convUid) {
          if (remaining.length > 0) {
            activateConversation(remaining[0]);
          } else {
            setActiveConvUid('');
            setActiveFilePath('');
            setActiveFilePaths([]);
            setPreviewCollapsed(true);
          }
        }
        await loadConversations();
      },
    });
  };

  const startRenameConversation = (item: Conversation) => {
    setEditingConvUid(item.conv_uid);
    setEditingTitle(item.title || item.conv_uid);
  };

  const cancelRenameConversation = () => {
    setEditingConvUid('');
    setEditingTitle('');
  };

  const saveRenameConversation = async (item: Conversation) => {
    const title = editingTitle.trim();
    if (!title || title === item.title) {
      cancelRenameConversation();
      return;
    }
    setConversations(items => items.map(conv => (
      conv.conv_uid === item.conv_uid ? { ...conv, title } : conv
    )));
    cancelRenameConversation();
    try {
      await updateConversation(item.conv_uid, { title });
      await loadConversations();
    } catch (err) {
      console.error('Failed to rename conversation:', err);
      await loadConversations();
    }
  };

  const handleModeChange = async (newMode: ChatMode) => {
    setMode(newMode);
    setConversations(items => items.map(item => (
      item.conv_uid === activeConvUid ? { ...item, chat_mode: newMode } : item
    )));
    if (activeConvUid) {
      try {
        await updateConversation(activeConvUid, { chat_mode: newMode });
      } catch (err) {
        console.error('Failed to update conversation mode:', err);
      }
    }
  };

  const handleTitleUpdate = async (hasMessage = false) => {
    if (hasMessage) {
      setConversations(items => items.map(item => (
        item.conv_uid === activeConvUid ? { ...item, message_count: Math.max(item.message_count || 0, 1) } : item
      )));
    }
    await loadConversations();
  };

  const handleFilePathUpdate = (fileInfo: FileInfo) => {
    const filePath = fileInfo.file_path;
    const fileName = fileInfo.file_name;
    setActiveFilePath(filePath);
    setActiveFilePaths(prev => {
      const next = filePath && !prev.includes(filePath) ? [...prev, filePath] : prev;
      setConversations(items => items.map(item => {
        if (item.conv_uid !== activeConvUid) return item;
        const fileNames = Array.isArray(item.file_names)
          ? item.file_names.filter(Boolean)
          : (item.file_name ? [item.file_name] : []);
        const nextFileNames = fileName && !fileNames.includes(fileName)
          ? [...fileNames, fileName]
          : fileNames;
        return {
          ...item,
          file_path: next[0] || '',
          file_name: nextFileNames[0] || '',
          file_paths: next,
          file_names: nextFileNames,
        };
      }));
      return next;
    });
    if (filePath) setPreviewCollapsed(false);
    loadConversations();
  };

  const handleConvClick = (item: Conversation) => {
    activateConversation(item);
  };

  const showPreview = mode === 'chat_excel' && !!activeFilePath;

  return (
    <>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1><span>ChatExcel</span></h1>
          <p>Data Analysis Agent</p>
        </div>

        <button className="sidebar-new-btn" onClick={() => handleNewConversation()}>
          <PlusOutlined /> 新建对话
        </button>

        <div className="sidebar-conversations">
          {conversations.length === 0 && (
            <div style={{ color: 'var(--sidebar-text-secondary)', fontSize: 12, textAlign: 'center', padding: 24 }}>
              暂无对话
            </div>
          )}
          {conversations.map((item) => (
            <div
              key={item.conv_uid}
              className={`sidebar-conv-item ${activeConvUid === item.conv_uid ? 'active' : ''}`}
              onClick={() => handleConvClick(item)}
            >
              <MessageOutlined style={{ fontSize: 14, color: 'var(--sidebar-text-secondary)' }} />
              {editingConvUid === item.conv_uid ? (
                <input
                  className="conv-title-input"
                  value={editingTitle}
                  autoFocus
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                  onBlur={() => saveRenameConversation(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveRenameConversation(item);
                    if (e.key === 'Escape') cancelRenameConversation();
                  }}
                />
              ) : (
                <span
                  className="conv-title"
                  title="双击重命名"
                  onDoubleClick={(e) => {
                    e.stopPropagation();
                    startRenameConversation(item);
                  }}
                >
                  {item.title || item.conv_uid}
                </span>
              )}
              <span className="conv-mode">
                {item.chat_mode === 'chat_excel' ? 'SQL' : 'Agent'}
              </span>
              <button
                className="conv-edit"
                title="重命名"
                onClick={(e) => {
                  e.stopPropagation();
                  startRenameConversation(item);
                }}
              >
                <EditOutlined />
              </button>
              <button
                className="conv-delete"
                title="删除"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(item.conv_uid);
                }}
              >
                <DeleteOutlined />
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-user">
          <div className="user-avatar">D</div>
          <span className="user-name">default</span>
        </div>
      </aside>

      <div className="main-area">
        {activeConvUid ? (
          <div className="main-content-wrapper">
            <div className={`chat-area ${showPreview && !previewCollapsed ? 'with-preview' : ''}`}>
              <ChatPanel
                key={activeConvUid}
                convUid={activeConvUid}
                mode={mode}
                onModeChange={handleModeChange}
                onTitleUpdate={handleTitleUpdate}
                onFilePathUpdate={handleFilePathUpdate}
              />
            </div>

            {showPreview && (
              <ExcelPreview
                filePaths={activeFilePaths}
                collapsed={previewCollapsed}
                onToggle={() => setPreviewCollapsed(!previewCollapsed)}
              />
            )}
          </div>
        ) : (
          <div className="welcome-page">
            <div className="welcome-icon">
              <TableOutlined style={{ color: '#60a5fa' }} />
            </div>
            <h2>ChatExcel</h2>
            <p>上传 Excel 文件，用 AI 分析你的数据</p>
            <p style={{ fontSize: 12, color: '#aaa' }}>
              <span style={{ marginRight: 16 }}>
                <TableOutlined style={{ marginRight: 4 }} /> SQL模式 - 单表单Sheet
              </span>
              <span>
                <CodeOutlined style={{ marginRight: 4 }} /> ReAct模式 - 多表多Sheet
              </span>
            </p>
          </div>
        )}
      </div>
    </>
  );
}

export default App;
