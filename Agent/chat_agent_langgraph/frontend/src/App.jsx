import { useState, useMemo, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

function App() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [searchVisible, setSearchVisible] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [uploadedImages, setUploadedImages] = useState([]);
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    // 用户相关状态
    const [users, setUsers] = useState([]);
    const [selectedUser, setSelectedUser] = useState(null);
    const [selectedUserId, setSelectedUserId] = useState(null);
    const [showNewUserModal, setShowNewUserModal] = useState(false);
    const [newUserName, setNewUserName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [dropdownExpanded, setDropdownExpanded] = useState(false);
    // 会话相关状态
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [hasCreatedSession, setHasCreatedSession] = useState(false);

    // 点击外部关闭下拉框
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownExpanded && !event.target.closest('.custom-dropdown')) {
                setDropdownExpanded(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [dropdownExpanded]);

    // 用于图片上传的隐藏input
    const fileInputRef = useRef(null);
    // 用于自动滚动到底部
    const messagesEndRef = useRef(null);
    // 用于获取消息输入框
    const textareaRef = useRef(null);

    // 模拟历史对话数据 - 默认为空，只有点击新建对话后才添加
    const [conversations, setConversations] = useState([]);

    // 编辑状态
    const [editingId, setEditingId] = useState(null);
    const [editingTitle, setEditingTitle] = useState('');

    // 流式输出状态
    const [isStreaming, setIsStreaming] = useState(false);
    const [readerController, setReaderController] = useState(null);

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
    const deleteConversation = async (id) => {
        // 调用后端API删除会话
        try {
            await fetch('http://localhost:8000/update_session_title', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: selectedUserId || 'default',
                    user_name: selectedUser || 'default',
                    session_id: id,
                    title: '', // 删除时title可以为空
                    mode: 'delete'
                })
            });

            // 删除成功后，从前端会话列表中移除
            setConversations(conversations.filter(conv => conv.id !== id));
        } catch (error) {
            console.error('删除会话失败:', error);
        }
    };

    // 开始编辑对话标题
    const startEditing = (conversation) => {
        setEditingId(conversation.id);
        setEditingTitle(conversation.title);
    };

    // 保存编辑的对话标题
    const saveEditing = async () => {
        if (editingId && editingTitle.trim()) {
            // 找到要编辑的会话
            const conversation = conversations.find(conv => conv.id === editingId);
            if (!conversation) return;

            // 更新本地会话标题
            setConversations(conversations.map(conv =>
                conv.id === editingId ? { ...conv, title: editingTitle } : conv
            ));

            // 调用后端API更新数据库中的会话标题
            try {
                await fetch('http://localhost:8000/update_session_title', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: selectedUserId || 'default',
                        user_name: selectedUser || 'default',
                        session_id: conversation.session_id, // 使用session_id而不是id
                        title: editingTitle,
                        mode: 'update'
                    })
                });
            } catch (error) {
                console.error('更新会话标题失败:', error);
            }

            // 结束编辑状态
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

        // 检查图片数量限制
        if (uploadedImages.length + files.length > 5) {
            alert('最多只能上传5张图片');
            // 清空input，允许重复选择相同文件
            e.target.value = '';
            return;
        }

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

    // 将图片转换为base64编码
    const convertImageToBase64 = (file) => {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                // 移除base64前缀，只保留编码部分
                const base64String = reader.result.split(',')[1];
                resolve(base64String);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    };

    // 停止流式输出
    const stopStreaming = () => {
        if (readerController) {
            readerController.abort();
        }
    };

    // 发送消息功能
    const sendMessage = async () => {
        if (!inputValue.trim() && uploadedImages.length === 0) return;

        // 检查用户是否已选择
        // selectedUser 为 null、undefined 或空字符串时都表示未选择用户
        if (!selectedUser || selectedUser === null || selectedUser === undefined || selectedUser === '') {
            alert('请先选择一个用户，然后再发送消息');
            return;
        }

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

        // 保存输入内容用于设置标题
        const tempInputValue = inputValue;

        // 清空输入框和图片
        setInputValue('');
        setUploadedImages([]);

        // 重置输入框高度和滚动条状态
        if (textareaRef.current) {
            // 先设置为auto，让浏览器自动计算合适的高度
            textareaRef.current.style.height = 'auto';
            // 重置为默认的动态高度设置，不固定为24px
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 100) + 'px';
            // 确保滚动条在顶部
            textareaRef.current.scrollTop = 0;
            // 确保overflow-y正确设置
            textareaRef.current.style.overflowY = 'hidden';
        }

        try {
            // 1. 检查是否有当前会话ID，如果没有则创建新会话
            let sessionId = currentSessionId;
            let isFirstMessage = false;

            if (!sessionId) {
                // 使用默认标题创建会话
                const sessionResponse = await fetch('http://localhost:8000/create_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: selectedUserId || 'default',
                        user_name: selectedUser || 'default'
                    })
                });

                if (!sessionResponse.ok) {
                    throw new Error('创建会话失败');
                }

                const sessionData = await sessionResponse.json();
                sessionId = sessionData.session_id;
                setCurrentSessionId(sessionId);

                // 设置已创建会话标志，用于隐藏欢迎提示
                setHasCreatedSession(true);

                // 更新对话列表，添加新创建的会话
                setConversations(prevConversations => [
                    {
                        id: sessionId,
                        session_id: sessionId,
                        title: '新建对话',
                        preview: newMessage.content.substring(0, 50) || '',
                        content: newMessage.content || ''
                    },
                    ...prevConversations
                ]);

                isFirstMessage = true;
            } else {
                // 检查当前会话是否有消息，如果没有则是第一条消息
                const currentConversation = conversations.find(conv => conv.session_id === sessionId);
                if (currentConversation && currentConversation.title === '新建对话') {
                    isFirstMessage = true;
                }
            }

            // 使用第一条消息作为标题，截取前10个字符，超出部分用省略号表示
            if (isFirstMessage && tempInputValue) {
                const title = tempInputValue.length > 10
                    ? tempInputValue.substring(0, 10) + '...'
                    : tempInputValue;

                // 更新对话列表中的标题
                setConversations(prevConversations =>
                    prevConversations.map(conv =>
                        conv.session_id === sessionId
                            ? { ...conv, title: title }
                            : conv
                    )
                );

                // 调用后端API更新会话标题
                try {
                    await fetch('http://localhost:8000/update_session_title', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_name: selectedUser || 'default',
                            session_id: sessionId,
                            title: title,
                            mode: 'update'
                        })
                    });
                } catch (error) {
                    console.error('更新会话标题失败:', error);
                }
            }

            // 2. 创建AI回复消息占位符
            const aiReplyId = Date.now() + 1;
            const aiReply = {
                id: aiReplyId,
                type: 'ai',
                content: '',
                images: [],
                timestamp: new Date(),
                streaming: true
            };
            setMessages(prev => [...prev, aiReply]);

            // 3. 转换图片为base64编码
            const filesData = [];
            for (const img of uploadedImages) {
                try {
                    const img_base64 = await convertImageToBase64(img.file);
                    filesData.push({
                        img_name: img.file.name,
                        img_base64: img_base64
                    });
                } catch (error) {
                    console.error('图片转换为base64失败:', error);
                }
            }

            // 4. 调用后端/chat接口，处理流式响应
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: selectedUserId || 'default',
                    user_name: selectedUser || 'default',
                    session_id: sessionId,
                    query: newMessage.content || '',
                    files: filesData
                })
            });

            if (!response.ok) {
                throw new Error('发送消息失败');
            }

            // 4. 处理流式响应
            setIsStreaming(true);
            const decoder = new TextDecoder();
            let accumulatedContent = '';

            // 使用AbortController来控制取消流式响应
            const controller = new AbortController();
            const signal = controller.signal;
            setReaderController(controller);

            try {
                const reader = response.body.getReader();

                while (true) {
                    // 检查是否被取消
                    if (signal.aborted) {
                        console.log('流式响应已被取消');
                        await reader.cancel();
                        break;
                    }

                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.trim() === '') continue;
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                if (data.content) {
                                    accumulatedContent += data.content;
                                    // 更新AI回复消息内容
                                    setMessages(prev => prev.map(msg =>
                                        msg.id === aiReplyId
                                            ? { ...msg, content: accumulatedContent }
                                            : msg
                                    ));
                                }
                            } catch (e) {
                                console.error('解析流式数据失败:', e);
                            }
                        }
                    }
                }

                // 5. 流式响应完成，更新消息状态和时间戳
                setMessages(prev => prev.map(msg =>
                    msg.id === aiReplyId
                        ? { ...msg, streaming: false, timestamp: new Date() }
                        : msg
                ));
            } catch (error) {
                if (error.name === 'AbortError') {
                    console.log('流式响应被中断');
                    // 更新AI回复消息状态为已停止
                    setMessages(prev => prev.map(msg =>
                        msg.id === aiReplyId
                            ? { ...msg, streaming: false, timestamp: new Date() }
                            : msg
                    ));
                } else {
                    console.error('处理流式响应失败:', error);
                }
            } finally {
                setIsStreaming(false);
                setReaderController(null);
            }

        } catch (error) {
            console.error('发送消息失败:', error);
            // 当后端不可用时，使用本地模拟回复
            setTimeout(() => {
                const aiReply = {
                    id: Date.now() + 1,
                    type: 'ai',
                    content: `收到您的消息：${newMessage.content || '（仅图片）'}，这是我的回复（本地模式）。`,
                    images: [],
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, aiReply]);
            }, 1000);
        }
    };

    // 处理键盘事件
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            if (e.shiftKey) {
                // Shift+Enter 允许多行换行
                // 不阻止默认行为，允许自然换行
            } else {
                // Enter 发送消息
                e.preventDefault();
                sendMessage();
            }
        }
    };

    // 从后端数据库获取用户列表
    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            // 调用后端API获取用户列表
            const response = await fetch('http://localhost:8000/user_select');
            if (!response.ok) {
                throw new Error('获取用户列表失败');
            }
            const data = await response.json();
            // 检查是否有错误
            if (data.error) {
                throw new Error(data.error);
            }
            // 转换为前端需要的格式
            const formattedUsers = data.users.map(user => ({
                value: user,
                label: user
            }));
            setUsers(formattedUsers);

            // 不再自动选择用户，需要用户手动选择
            // 如果用户列表中有default用户，则默认选择它
            // if (formattedUsers.some(user => user.value === 'default')) {
            //     setSelectedUser('default');
            // } else if (formattedUsers.length > 0) {
            //     // 如果没有default用户，则选择第一个用户
            //     setSelectedUser(formattedUsers[0].value);
            // }
        } catch (error) {
            console.error('获取用户列表失败:', error);
            // 当后端不可用时，提供默认用户选项
            const defaultUsers = [
                { value: 'default', label: 'default' }
            ];
            setUsers(defaultUsers);
            // 不再自动选择用户，需要用户手动选择
            // setSelectedUser('default');
        } finally {
            setIsLoading(false);
        }
    };

    // 新建用户
    const handleCreateUser = async () => {
        if (!newUserName.trim()) return;

        setIsLoading(true);
        try {
            // 调用后端API创建用户
            const response = await fetch(`http://localhost:8000/create_user?username=${encodeURIComponent(newUserName)}`);
            if (!response.ok) {
                throw new Error('创建用户请求失败');
            }
            const data = await response.json();

            // 检查后端返回的结果
            if (data.error) {
                // 如果后端返回错误，显示错误信息
                alert(data.error);
            } else {
                // 创建成功，刷新用户列表
                await fetchUsers();
                // 选择新创建的用户
                setSelectedUser(newUserName);
                // 获取用户会话，同时获取用户ID
                await fetchUserSessions(newUserName);
                // 关闭模态框并清空输入
                setShowNewUserModal(false);
                setNewUserName('');
            }
        } catch (error) {
            console.error('创建用户失败:', error);
            // 当后端不可用时，仍然添加用户到本地列表
            const newUser = {
                value: newUserName.trim(),
                label: newUserName.trim()
            };
            setUsers([...users, newUser]);
            setSelectedUser(newUserName.trim());
            // 尝试获取用户会话，即使后端不可用也可能有本地缓存
            try {
                await fetchUserSessions(newUserName.trim());
            } catch (e) {
                console.warn('获取用户会话失败:', e);
            }
            setShowNewUserModal(false);
            setNewUserName('');
        } finally {
            setIsLoading(false);
        }
    };

    // 自动滚动到底部
    const scrollToBottom = () => {
        // 使用 requestAnimationFrame 确保 DOM 已经更新
        requestAnimationFrame(() => {
            if (messagesEndRef.current) {
                // 使用 auto 行为确保立即滚动到底部，避免平滑滚动的动画冲突
                messagesEndRef.current.scrollIntoView({ behavior: 'auto', block: 'end', inline: 'nearest' });
            }
        });
    };

    // 新建对话
    const handleNewConversation = async (event) => {
        // 忽略React自动传入的event对象
        console.log('=== handleNewConversation 被调用 ===');
        console.log('selectedUser 状态:', selectedUser);
        console.log('selectedUser 类型:', typeof selectedUser);
        console.log('selectedUser === null:', selectedUser === null);
        console.log('selectedUser === undefined:', selectedUser === undefined);
        console.log('!selectedUser:', !selectedUser);

        // 直接使用当前选中的用户
        const userToUse = selectedUser;
        console.log('userToUse:', userToUse);
        console.log('userToUse 类型:', typeof userToUse);

        // 检查用户是否选择了具体用户
        if (!userToUse) {
            console.log('检查失败，阻止创建对话');
            alert('请先选择一个用户，然后再点击新建对话');
            return;
        }

        console.log('检查通过，继续创建对话');

        try {
            // 调用后端API创建新会话
            // 确保请求体只包含必要的数据，避免循环引用
            const requestBody = {
                user_id: selectedUserId || 'default',
                user_name: String(userToUse || '').trim()
                // 不传递title参数，让后端使用默认值"新建对话"
            };

            const response = await fetch('http://localhost:8000/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            // 检查是否有错误返回
            if (data.error) {
                // 如果后端返回错误，显示错误信息
                throw new Error(data.error + (data.details ? ': ' + data.details : ''));
            }

            console.log('新会话创建成功:', data);

            // 更新当前会话ID
            setCurrentSessionId(data.session_id);

            // 设置已创建会话标志，用于隐藏欢迎提示
            setHasCreatedSession(true);

            // 更新对话列表，添加新创建的会话
            // 使用后端返回的标题
            setConversations(prevConversations => [
                {
                    id: data.session_id,
                    session_id: data.session_id,
                    title: data.title || '新建对话',
                    preview: '',
                    content: ''
                },
                ...prevConversations
            ]);
        } catch (error) {
            console.error('创建会话失败:', error);
        }

        // 清空当前消息列表
        setMessages([]);
    };

    // 当消息更新时自动滚动
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // 获取用户的所有会话
    const fetchUserSessions = async (userName) => {
        if (!userName) return;

        try {
            const response = await fetch('http://localhost:8000/user_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_name: userName })
            });

            const data = await response.json();

            if (data.error) {
                console.error('获取用户会话失败:', data.error);
                return;
            }

            // 保存用户ID
            setSelectedUserId(data.user_id);

            // 更新对话列表
            if (data.sessions && Array.isArray(data.sessions)) {
                const formattedConversations = data.sessions.map(session => ({
                    id: session.session_id,
                    session_id: session.session_id,
                    title: session.title || '新建对话', // 确保标题为空时显示"新建对话"
                    preview: '',
                    content: ''
                }));
                setConversations(formattedConversations);
            }
        } catch (error) {
            console.error('获取用户会话失败:', error);
        }
    };

    // 组件挂载时获取用户列表
    useEffect(() => {
        fetchUsers();
    }, []);

    // 加载历史消息
    const loadHistoryMessages = async (sessionId) => {
        if (!sessionId) return;

        try {
            const response = await fetch('http://localhost:8000/session_messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    user_id: selectedUserId || 'default',
                    user_name: selectedUser || 'default'
                })
            });
            if (!response.ok) {
                throw new Error('获取历史消息失败');
            }
            const data = await response.json();

            if (data.error) {
                console.error('获取历史消息失败:', data.error);
                return;
            }

            // 如果有历史消息，格式化并设置到消息列表
            if (data.messages && Array.isArray(data.messages)) {
                const formattedMessages = [];
                let messageIndex = 0;

                // 处理每一轮问答，创建两条消息：用户消息和AI消息
                data.messages.forEach((msg, turnIndex) => {
                    // 创建用户消息
                    if (msg.query) {
                        formattedMessages.push({
                            id: `history-${messageIndex++}`,
                            type: 'user',
                            content: msg.query,
                            timestamp: msg.timestamp || new Date().toISOString(),
                            streaming: false,
                            images: []
                        });
                    }

                    // 创建AI消息
                    if (msg.answer) {
                        formattedMessages.push({
                            id: `history-${messageIndex++}`,
                            type: 'ai',
                            content: msg.answer,
                            timestamp: msg.timestamp || new Date().toISOString(),
                            streaming: false,
                            images: []
                        });
                    }
                });

                setMessages(formattedMessages);
            } else {
                setMessages([]);
            }
        } catch (error) {
            console.error('加载历史消息失败:', error);
            setMessages([]);
        }
    };

    // 切换会话
    const handleConversationClick = (conversation) => {
        // 更新当前会话ID
        setCurrentSessionId(conversation.session_id);
        // 设置已创建会话标志
        setHasCreatedSession(true);
        // 清空当前消息列表
        setMessages([]);
        // 加载历史消息
        loadHistoryMessages(conversation.session_id);
    };

    // 当selectedUser变化时，获取该用户的所有会话
    useEffect(() => {
        if (selectedUser) {
            fetchUserSessions(selectedUser);
        }
    }, [selectedUser]);

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

                    {!sidebarCollapsed && !searchVisible && <button className="new-chat-btn" onClick={handleNewConversation}>+ 新建对话</button>}
                </div>

                {!sidebarCollapsed && (
                    <div className="conversation-list">
                        {filteredConversations.map((conv) => (
                            <div
                                key={conv.id}
                                className={`conversation-item ${conv.session_id && conv.session_id === currentSessionId ? 'active' : ''}`}
                                onClick={() => handleConversationClick(conv)}
                            >
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
                                            <button className="edit-save-btn" onClick={(e) => { e.stopPropagation(); saveEditing(); }} title="保存">
                                                ✅
                                            </button>
                                            <button className="edit-cancel-btn" onClick={(e) => { e.stopPropagation(); cancelEditing(); }} title="取消">
                                                ❌
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="conversation-title">
                                            {conv.title.length > 10 ? conv.title.substring(0, 10) + '...' : (conv.title || '新建对话')}
                                        </div>
                                        <div className="conversation-preview">{conv.preview}</div>
                                    </>
                                )}
                                <div className="conversation-actions">
                                    <button
                                        className="conversation-action-btn"
                                        onClick={(e) => { e.stopPropagation(); startEditing(conv); }}
                                        title="修改命名"
                                    >
                                        ✏️
                                    </button>
                                    <button
                                        className="conversation-action-btn"
                                        onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id); }}
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
                                <div className="custom-dropdown">
                                    <div
                                        className={`dropdown-header ${dropdownExpanded && users.length > 5 ? 'expanded' : ''}`}
                                        onClick={() => setDropdownExpanded(!dropdownExpanded)}
                                    >
                                        {users.find(user => user.value === selectedUser)?.label || '选择用户'}
                                        <span className="dropdown-arrow">▼</span>
                                    </div>
                                    {dropdownExpanded && (
                                        <div className={`dropdown-options ${users.length > 5 ? 'scrollable' : ''}`}>
                                            {users.map(user => (
                                                <div
                                                    key={user.value}
                                                    className={`dropdown-option ${user.value === selectedUser ? 'selected' : ''}`}
                                                    onClick={() => {
                                                        setSelectedUser(user.value);
                                                        setDropdownExpanded(false);
                                                        // 获取用户会话，同时获取用户ID
                                                        fetchUserSessions(user.value);
                                                    }}
                                                >
                                                    {user.label}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
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
                    {/* 欢迎提示 - 当消息列表为空且未创建会话时显示 */}
                    {messages.length === 0 && !hasCreatedSession && !selectedUser && (
                        <div className="welcome-message">
                            <div className="welcome-icon">👋</div>
                            <div className="welcome-text">请先选择用户，然后点击新建对话开启对话</div>
                        </div>
                    )}

                    {/* 欢迎提示 - 当用户已选择但未创建会话时显示 */}
                    {messages.length === 0 && !hasCreatedSession && selectedUser && (
                        <div className="welcome-message">
                            <div className="welcome-icon">👋</div>
                            <div className="welcome-text">点击新建对话开启对话</div>
                        </div>
                    )}

                    {/* 聊天消息 */}
                    {messages.map(message => (
                        <div key={message.id} className={`message ${message.type}`}>
                            <div className="message-avatar">
                                {message.type === 'user' ? '👤' : '🤖'}
                            </div>
                            <div className="message-content-wrapper">
                                <div className="message-bubble">
                                    {message.content && <div className="message-content"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown></div>}
                                    {message.streaming && (
                                        <div className="streaming-indicator">
                                            <span className="typing-dot"></span>
                                            <span className="typing-dot"></span>
                                            <span className="typing-dot"></span>
                                        </div>
                                    )}
                                    {message.images.length > 0 && (
                                        <div className="message-images">
                                            {message.images.map(img => {
                                                // 获取图片名称，处理不同情况
                                                let fileName = '未知图片';
                                                if (img.file && img.file.name) {
                                                    fileName = img.file.name;
                                                } else if (img.name) {
                                                    fileName = img.name;
                                                } else if (img.url) {
                                                    // 从URL中提取文件名
                                                    const urlParts = img.url.split('/');
                                                    fileName = urlParts[urlParts.length - 1];
                                                    // 去除可能的查询参数
                                                    fileName = fileName.split('?')[0];
                                                }

                                                // 处理图片名称，显示更合理的长度
                                                const ext = fileName.substring(fileName.lastIndexOf('.'));
                                                const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'));

                                                // 调整截断规则：名称部分最多显示5个字符，加上扩展名
                                                let displayName;
                                                if (nameWithoutExt.length > 5) {
                                                    displayName = nameWithoutExt.substring(0, 5) + '...' + ext;
                                                } else {
                                                    displayName = fileName;
                                                }

                                                return (
                                                    <div key={img.id} className="message-image-wrapper">
                                                        <img src={img.url} alt="Message image" className="message-image" />
                                                        <div className="image-name">{displayName}</div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                                {message.timestamp && (
                                    <div className="message-timestamp">
                                        {new Date(message.timestamp).toLocaleString('zh-CN', {
                                            year: 'numeric',
                                            month: 'numeric',
                                            day: 'numeric',
                                            hour: '2-digit',
                                            minute: '2-digit',
                                            second: '2-digit',
                                            hour12: false
                                        })}
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
                            {uploadedImages.map(img => {
                                // 处理图片名称，显示更合理的长度
                                const fileName = img.file.name;
                                const ext = fileName.substring(fileName.lastIndexOf('.'));
                                const nameWithoutExt = fileName.substring(0, fileName.lastIndexOf('.'));

                                // 调整截断规则：名称部分最多显示5个字符（考虑中文字符），加上扩展名
                                let displayName;
                                if (nameWithoutExt.length > 5) {
                                    displayName = nameWithoutExt.substring(0, 5) + '...' + ext;
                                } else {
                                    displayName = fileName;
                                }

                                return (
                                    <div key={img.id} className="image-preview-item">
                                        <img src={img.url} alt="Upload preview" className="image-preview" />
                                        <div className="image-name">{displayName}</div>
                                        <button
                                            className="image-remove-btn"
                                            onClick={() => removeImage(img.id)}
                                            title="删除图片"
                                        >
                                            ×
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div className="input-wrapper short-input">
                        <textarea
                            className="message-input"
                            placeholder="向 LangGraph Agent 提问"
                            value={inputValue}
                            onChange={(e) => {
                                setInputValue(e.target.value);
                                // 自动调整文本域高度，最多显示5行（约100px）
                                e.target.style.height = 'auto';
                                const newHeight = Math.min(e.target.scrollHeight, 100);
                                e.target.style.height = newHeight + 'px';
                                // 根据内容高度动态设置overflow-y
                                e.target.style.overflowY = (e.target.scrollHeight > newHeight) ? 'auto' : 'hidden';
                                // 确保滚动条在顶部
                                e.target.scrollTop = 0;
                            }}
                            onKeyDown={handleKeyDown}
                            rows={1}
                            ref={textareaRef}
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
                            {isStreaming ? (
                                <button className="send-btn stop-btn" onClick={stopStreaming}>
                                    <div className="loading-spinner"></div>
                                </button>
                            ) : (
                                <button className="send-btn" onClick={sendMessage}>
                                    发送
                                </button>
                            )}
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