import { useState, useMemo, useRef } from 'react'
import './App.css'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [searchVisible, setSearchVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadedImages, setUploadedImages] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  // 用户相关状态
  const [users, setUsers] = useState([
    { value: 'langgraph', label: 'LangGraph' },
    { value: 'user1', label: '用户1' },
    { value: 'user2', label: '用户2' }
  ]);
  const [selectedUser, setSelectedUser] = useState('langgraph');
  const [showNewUserModal, setShowNewUserModal] = useState(false);
  const [newUserName, setNewUserName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // 用于图片上传的隐藏input
  const fileInputRef = useRef(null);
  // 用于自动滚动到底部
  const messagesEndRef = useRef(null);

  // 模拟历史对话数据
  const [conversations, setConversations] = useState([
    {
      id: 1,
      title: 'Python字符串处理技巧',
      preview: '你好，我想了解一下Python字符串处理的最佳实践...',
      content: 'Python字符串处理技巧包括使用strip()去除空白字符，使用split()分割字符串，使用join()连接字符串等。'
    },
    {
      id: 2,
      title: 'React组件设计模式',
      preview: '什么是React的高阶组件？如何使用...',
      content: 'React高阶组件是一种复用组件逻辑的技术，它接受一个组件并返回一个新组件。'
    },
    {
      id: 3,
      title: '数据库优化',
      preview: '如何优化MySQL查询性能？...',
      content: '数据库优化包括添加索引、优化查询语句、使用缓存等方法。'
    },
    {
      id: 4,
      title: 'VS Code Git配置',
      preview: '如何在VS Code中配置Git自动获取更新？...',
      content: '在VS Code中，可以通过设置git.autofetch为true来自动获取远程更新。'
    },
    {
      id: 5,
      title: 'PyCharm vs VS Code',
      preview: 'PyCharm和VS Code哪个更适合Python开发？...',
      content: 'PyCharm是专门为Python开发设计的IDE，功能强大但资源消耗较大；VS Code是轻量级编辑器，通过插件扩展功能。'
    }
  ]);
  
  // 编辑状态
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState('');

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleSearch = () => {
    setSearchVisible(!searchVisible);
    if (!searchVisible) {
      setSearchTerm('');
    }
  };

  // 搜索功能
  const filteredConversations = useMemo(() => {
    if (!searchTerm.trim()) {
      return conversations;
    }
    const term = searchTerm.toLowerCase();
    return conversations.filter(conv => 
      conv.title.toLowerCase().includes(term) || 
      conv.preview.toLowerCase().includes(term) ||
      conv.content.toLowerCase().includes(term)
    );
  }, [searchTerm, conversations]);
  
  // 删除对话
  const deleteConversation = (id) => {
    setConversations(conversations.filter(conv => conv.id !== id));
  };
  
  // 开始编辑对话标题
  const startEditing = (conversation) => {
    setEditingId(conversation.id);
    setEditingTitle(conversation.title);
  };
  
  // 保存编辑的对话标题
  const saveEditing = () => {
    if (editingId && editingTitle.trim()) {
      setConversations(conversations.map(conv => 
        conv.id === editingId ? { ...conv, title: editingTitle } : conv
      ));
      setEditingId(null);
      setEditingTitle('');
    }
  };
  
  // 取消编辑
  const cancelEditing = () => {
    setEditingId(null);
    setEditingTitle('');
  };

  // 图片上传功能
  const handleImageUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files);
    const newImages = files.map(file => ({
      id: Date.now() + Math.random(),
      file: file,
      url: URL.createObjectURL(file)
    }));
    setUploadedImages([...uploadedImages, ...newImages]);
    // 清空input，允许重复选择相同文件
    e.target.value = '';
  };

  // 删除上传的图片
  const removeImage = (id) => {
    setUploadedImages(uploadedImages.filter(img => img.id !== id));
  };

  // 发送消息功能
  const sendMessage = () => {
    if (!inputValue.trim() && uploadedImages.length === 0) return;

    // 创建新消息
    const newMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      images: [...uploadedImages],
      timestamp: new Date()
    };

    // 添加到消息列表
    setMessages([...messages, newMessage]);

    // 清空输入框和图片
    setInputValue('');
    setUploadedImages([]);

    // 模拟AI回复
    setTimeout(() => {
      const aiReply = {
        id: Date.now() + 1,
        type: 'ai',
        content: `收到您的消息：${inputValue || '（仅图片）'}，这是我的回复。`,
        images: [],
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiReply]);
    }, 1000);
  };

  // 处理键盘事件
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        // Shift+Enter 只允许换一行
        e.preventDefault();
        // 计算当前换行符数量
        const newlineCount = (inputValue.match(/\n/g) || []).length;
        // 只允许一行换行
        if (newlineCount < 1) {
          setInputValue(prev => prev + '\n');
        }
      } else {
        // Enter 发送消息
        e.preventDefault();
        sendMessage();
      }
    }
  };

  // 从后端数据库获取用户列表（模拟）
  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      // 模拟API请求延迟
      await new Promise(resolve => setTimeout(resolve, 500));
      // 模拟从数据库获取的用户数据
      const mockUsers = [
        { value: 'langgraph', label: 'LangGraph' },
        { value: 'user1', label: '用户1' },
        { value: 'user2', label: '用户2' },
        { value: 'user3', label: '用户3' },
        { value: 'admin', label: '管理员' }
      ];
      setUsers(mockUsers);
    } catch (error) {
      console.error('获取用户列表失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 新建用户
  const handleCreateUser = async () => {
    if (!newUserName.trim()) return;
    
    setIsLoading(true);
    try {
      // 模拟API请求延迟
      await new Promise(resolve => setTimeout(resolve, 500));
      // 模拟创建新用户
      const newUser = {
        value: newUserName.toLowerCase().replace(/\s+/g, '_'),
        label: newUserName
      };
      setUsers([...users, newUser]);
      setSelectedUser(newUser.value);
      setShowNewUserModal(false);
      setNewUserName('');
    } catch (error) {
      console.error('创建用户失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 当消息更新时自动滚动
  useMemo(() => {
    scrollToBottom();
  }, [messages]);
  
  // 组件挂载时获取用户列表
  useMemo(() => {
    fetchUsers();
  }, []);

  return (
    <div className="app-container">
      {/* 左侧历史对话列表 */}
      <div className={`sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-title">
            {!sidebarCollapsed && <div className="logo-title">LangGraph</div>}
            <div className="header-buttons">
              <button className="header-btn" title="搜索对话" onClick={toggleSearch}>
                🔍
              </button>
              <button className="header-btn" title="折叠" onClick={toggleSidebar}>
                {sidebarCollapsed ? '▶️' : '◀️'}
              </button>
            </div>
          </div>
          
          {/* 搜索框 */}
          {!sidebarCollapsed && searchVisible && (
            <div className="search-container">
              <input
                type="text"
                className="search-input"
                placeholder="搜索对话..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                autoFocus
              />
            </div>
          )}
          
          {!sidebarCollapsed && !searchVisible && <button className="new-chat-btn">+ 新建对话</button>}
        </div>
        
        {!sidebarCollapsed && (
          <div className="conversation-list">
            {filteredConversations.map((conv) => (
              <div key={conv.id} className="conversation-item">
                {editingId === conv.id ? (
                  <div className="conversation-edit">
                    <input
                      type="text"
                      className="conversation-edit-input"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          saveEditing();
                        } else if (e.key === 'Escape') {
                          cancelEditing();
                        }
                      }}
                      autoFocus
                    />
                    <div className="conversation-edit-buttons">
                      <button className="edit-save-btn" onClick={saveEditing} title="保存">
                        ✅
                      </button>
                      <button className="edit-cancel-btn" onClick={cancelEditing} title="取消">
                        ❌
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="conversation-title">{conv.title}</div>
                    <div className="conversation-preview">{conv.preview}</div>
                  </>
                )}
                <div className="conversation-actions">
                  <button 
                    className="conversation-action-btn" 
                    onClick={() => startEditing(conv)}
                    title="修改命名"
                  >
                    ✏️
                  </button>
                  <button 
                    className="conversation-action-btn" 
                    onClick={() => deleteConversation(conv.id)}
                    title="删除"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            ))}
            
            {/* 搜索结果为空时显示 */}
            {searchTerm && filteredConversations.length === 0 && (
              <div className="no-results">
                <div className="no-results-text">未找到匹配的对话</div>
              </div>
            )}
          </div>
        )}
        
        {!sidebarCollapsed && !searchVisible && (
          <div className="sidebar-footer">
            <div className="user-select-container">
              <div className="user-select">
                <span className="user-select-label">用户选择：</span>
                <select 
                  className="user-dropdown"
                  value={selectedUser}
                  onChange={(e) => setSelectedUser(e.target.value)}
                  disabled={isLoading}
                >
                  {users.map(user => (
                    <option key={user.value} value={user.value}>
                      {user.label}
                    </option>
                  ))}
                </select>
              </div>
              <button 
                className="new-user-btn"
                onClick={() => setShowNewUserModal(true)}
                disabled={isLoading}
                title="新建用户"
              >
                + 新建用户
              </button>
            </div>
          </div>
        )}
        
        {/* 新建用户模态框 */}
        {showNewUserModal && (
          <div className="modal-overlay">
            <div className="modal">
              <div className="modal-header">
                <h3>新建用户</h3>
                <button 
                  className="modal-close-btn"
                  onClick={() => setShowNewUserModal(false)}
                  disabled={isLoading}
                >
                  ×
                </button>
              </div>
              <div className="modal-body">
                <label htmlFor="new-user-name" className="modal-label">
                  用户名：
                </label>
                <input
                  type="text"
                  id="new-user-name"
                  className="modal-input"
                  value={newUserName}
                  onChange={(e) => setNewUserName(e.target.value)}
                  placeholder="请输入用户名"
                  disabled={isLoading}
                  autoFocus
                />
              </div>
              <div className="modal-footer">
                <button 
                  className="modal-cancel-btn"
                  onClick={() => {
                    setShowNewUserModal(false);
                    setNewUserName('');
                  }}
                  disabled={isLoading}
                >
                  取消
                </button>
                <button 
                  className="modal-create-btn"
                  onClick={handleCreateUser}
                  disabled={isLoading || !newUserName.trim()}
                >
                  {isLoading ? '创建中...' : '确定'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 中间聊天区域 */}
      <div className={`chat-container ${sidebarCollapsed ? 'expanded' : ''}`}>
        {/* 聊天内容区域 */}
        <div className="chat-messages">
          {/* 聊天消息 */}
          {messages.map(message => (
            <div key={message.id} className={`message ${message.type}`}>
              <div className="message-avatar">
                {message.type === 'user' ? '👤' : '🤖'}
              </div>
              <div className="message-bubble">
                {message.content && <div className="message-content">{message.content}</div>}
                {message.images.length > 0 && (
                  <div className="message-images">
                    {message.images.map(img => (
                      <img key={img.id} src={img.url} alt="Message image" className="message-image" />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {/* 自动滚动到底部的标记 */}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入框区域 */}
        <div className="input-container">
          {/* 上传图片预览 - 移到对话框上方 */}
          {uploadedImages.length > 0 && (
            <div className="image-preview-container">
              {uploadedImages.map(img => (
                <div key={img.id} className="image-preview-item">
                  <img src={img.url} alt="Upload preview" className="image-preview" />
                  <button 
                    className="image-remove-btn"
                    onClick={() => removeImage(img.id)}
                    title="删除图片"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className="input-wrapper short-input">
            <textarea
              className="message-input"
              placeholder="向 LangGraph Agent 提问"
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                // 自动调整文本域高度
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
              }}
              onKeyDown={handleKeyDown}
              rows={1}
              style={{ height: 'auto' }}
            />
            <div className="input-buttons">
              <button 
                className="input-btn"
                onClick={handleImageUploadClick}
                title="上传图片"
              >
                🖼️
              </button>
              <button className="send-btn" onClick={sendMessage}>
                发送
              </button>
            </div>
            {/* 隐藏的文件输入 */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              multiple
              style={{ display: 'none' }}
              onChange={handleImageChange}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
