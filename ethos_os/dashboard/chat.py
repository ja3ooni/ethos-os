"""Chat UI - Simple HTML/FastHTML frontend for EthosOS.

CHAT-01: Paperclip-style chat interface
CHAT-03: Agent switching
CHAT-04: Real-time updates

This provides a simple web UI for the chat interface.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/ui", tags=["ui"])


CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EthosOS Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-primary: #0f0f13;
            --bg-secondary: #1a1a24;
            --bg-tertiary: #252532;
            --text-primary: #e8e8ed;
            --text-secondary: #9898a8;
            --accent: #6366f1;
            --accent-hover: #818cf8;
            --border: #2a2a3a;
            --success: #22c55e;
            --warning: #f59e0b;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header h1 {
            font-size: 18px;
            font-weight: 600;
        }
        
        .header .logo {
            color: var(--accent);
            font-weight: 700;
        }
        
        .main {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        
        .sidebar {
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
        }
        
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border);
        }
        
        .new-chat-btn {
            width: 100%;
            padding: 10px 16px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.2s;
        }
        
        .new-chat-btn:hover {
            background: var(--accent-hover);
        }
        
        .conversations-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px;
        }
        
        .conversation-item {
            padding: 12px 16px;
            border-radius: 8px;
            cursor: pointer;
            margin-bottom: 4px;
            transition: background 0.2s;
        }
        
        .conversation-item:hover {
            background: var(--bg-tertiary);
        }
        
        .conversation-item.active {
            background: var(--accent);
            color: white;
        }
        
        .conversation-item .title {
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .conversation-item .meta {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .conversation-item.active .meta {
            color: rgba(255,255,255,0.7);
        }
        
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .agent-selector {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .agent-badge {
            padding: 6px 12px;
            background: var(--bg-tertiary);
            border-radius: 20px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .agent-badge .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }
        
        .initiative-badge {
            padding: 6px 12px;
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent);
            border-radius: 20px;
            font-size: 13px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .message {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .message.user {
            align-self: flex-end;
            background: var(--accent);
            color: white;
        }
        
        .message.assistant {
            align-self: flex-start;
            background: var(--bg-tertiary);
        }
        
        .message .meta {
            font-size: 11px;
            color: var(--text-secondary);
            margin-top: 6px;
        }
        
        .message.user .meta {
            color: rgba(255,255,255,0.6);
        }
        
        .chat-input-area {
            padding: 16px 24px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
        }
        
        .chat-input-wrapper {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px;
            color: var(--text-primary);
            font-size: 14px;
            resize: none;
            min-height: 48px;
            max-height: 120px;
            font-family: inherit;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: var(--accent);
        }
        
        .chat-input::placeholder {
            color: var(--text-secondary);
        }
        
        .send-btn {
            padding: 12px 20px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.2s;
        }
        
        .send-btn:hover {
            background: var(--accent-hover);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .empty-state {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
        }
        
        .empty-state h2 {
            font-size: 24px;
            margin-bottom: 8px;
            color: var(--text-primary);
        }
        
        .empty-state p {
            font-size: 14px;
        }
        
        .agents-dropdown {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-top: 4px;
            max-height: 300px;
            overflow-y: auto;
            display: none;
            z-index: 100;
        }
        
        .agents-dropdown.show {
            display: block;
        }
        
        .agent-option {
            padding: 12px 16px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .agent-option:hover {
            background: var(--bg-secondary);
        }
        
        .agent-option .name {
            font-size: 14px;
            font-weight: 500;
        }
        
        .agent-option .role {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .initiative-selector {
            position: relative;
        }
        
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><span class="logo">EthosOS</span> Chat</h1>
    </div>
    
    <div class="main">
        <div class="sidebar">
            <div class="sidebar-header">
                <button class="new-chat-btn" onclick="createNewConversation()">+ New Conversation</button>
            </div>
            <div class="conversations-list" id="conversationsList">
            </div>
        </div>
        
        <div class="chat-area">
            <div class="chat-header">
                <div class="agent-selector">
                    <div class="agent-badge" id="currentAgent" onclick="showAgentsDropdown()">
                        <span class="dot"></span>
                        <span id="agentName">Select Agent</span>
                    </div>
                    <div class="agents-dropdown" id="agentsDropdown"></div>
                </div>
                <div class="initiative-badge" id="initiativeBadge">
                    No initiative
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="empty-state">
                    <h2>Start a conversation</h2>
                    <p>Select an agent and send a message</p>
                </div>
            </div>
            
            <div class="chat-input-area">
                <div class="chat-input-wrapper">
                    <textarea 
                        class="chat-input" 
                        id="chatInput"
                        placeholder="Message agent..."
                        rows="1"
                        onkeydown="handleKeydown(event)"
                    ></textarea>
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentConversationId = null;
        let currentAgentId = null;
        let currentAgentName = null;
        let currentInitiativeId = null;
        let currentInitiativeType = null;
        
        async function apiCall(endpoint, options = {}) {
            const response = await fetch(endpoint, {
                headers: { 'Content-Type': 'application/json' },
                ...options
            });
            return response.json();
        }
        
        async function loadConversations() {
            const conversations = await apiCall('/api/chat/conversations');
            const list = document.getElementById('conversationsList');
            list.innerHTML = conversations.map(conv => `
                <div class="conversation-item ${conv.id === currentConversationId ? 'active' : ''}" 
                     onclick="selectConversation('${conv.id}')">
                    <div class="title">${conv.title}</div>
                    <div class="meta">${conv.message_count} messages</div>
                </div>
            `).join('');
        }
        
        async function createNewConversation() {
            const conv = await apiCall('/api/chat/conversations', {
                method: 'POST',
                body: JSON.stringify({})
            });
            currentConversationId = conv.id;
            loadConversations();
            clearMessages();
        }
        
        async function selectConversation(id) {
            currentConversationId = id;
            const conv = await apiCall(`/api/chat/conversations/${id}`);
            currentAgentId = conv.current_agent_id;
            currentAgentName = conv.current_agent_name;
            currentInitiativeId = conv.initiative_id;
            currentInitiativeType = conv.initiative_type;
            
            updateAgentDisplay();
            updateInitiativeDisplay();
            loadMessages();
            loadConversations();
        }
        
        async function loadMessages() {
            if (!currentConversationId) return;
            
            const messages = await apiCall(`/api/chat/conversations/${currentConversationId}/messages`);
            const container = document.getElementById('chatMessages');
            
            if (messages.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h2>Start a conversation</h2>
                        <p>Select an agent and send a message</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = messages.map(msg => `
                <div class="message ${msg.role}">
                    ${msg.content}
                    <div class="meta">${msg.agent_name || msg.role} · ${new Date(msg.created_at).toLocaleTimeString()}</div>
                </div>
            `).join('');
            
            container.scrollTop = container.scrollHeight;
        }
        
        function clearMessages() {
            document.getElementById('chatMessages').innerHTML = `
                <div class="empty-state">
                    <h2>Start a conversation</h2>
                    <p>Select an agent and send a message</p>
                </div>
            `;
        }
        
        async function showAgentsDropdown() {
            const dropdown = document.getElementById('agentsDropdown');
            const agents = await apiCall('/api/chat/agents');
            
            dropdown.innerHTML = agents.map(agent => `
                <div class="agent-option" onclick="selectAgent('${agent.id}', '${agent.name}')">
                    <div class="name">${agent.name}</div>
                    <div class="role">${agent.role} · ${agent.division}</div>
                </div>
            `).join('');
            
            dropdown.classList.toggle('show');
        }
        
        async function selectAgent(agentId, agentName) {
            currentAgentId = agentId;
            currentAgentName = agentName;
            
            document.getElementById('agentsDropdown').classList.remove('show');
            updateAgentDisplay();
            
            if (currentConversationId) {
                await apiCall(`/api/chat/conversations/${currentConversationId}/switch-agent`, {
                    method: 'POST',
                    body: JSON.stringify({ agent_id: agentId, agent_name: agentName })
                });
            }
        }
        
        function updateAgentDisplay() {
            document.getElementById('agentName').textContent = currentAgentName || 'Select Agent';
        }
        
        function updateInitiativeDisplay() {
            const badge = document.getElementById('initiativeBadge');
            if (currentInitiativeId) {
                badge.textContent = `${currentInitiativeType}: ${currentInitiativeId.slice(0, 8)}`;
            } else {
                badge.textContent = 'No initiative';
            }
        }
        
        async function sendMessage() {
            if (!currentConversationId) {
                await createNewConversation();
            }
            
            const input = document.getElementById('chatInput');
            const content = input.value.trim();
            if (!content) return;
            
            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            
            try {
                await apiCall(`/api/chat/conversations/${currentConversationId}/messages`, {
                    method: 'POST',
                    body: JSON.stringify({
                        content,
                        agent_id: currentAgentId,
                        agent_name: currentAgentName
                    })
                });
                
                input.value = '';
                loadMessages();
                loadConversations();
            } finally {
                sendBtn.disabled = false;
            }
        }
        
        function handleKeydown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.agent-selector')) {
                document.getElementById('agentsDropdown').classList.remove('show');
            }
        });
        
        loadConversations();
    </script>
</body>
</html>
"""


@router.get("/chat", response_class=HTMLResponse)
async def chat_ui() -> HTMLResponse:
    """Chat UI page."""
    return HTMLResponse(CHAT_HTML)


__all__ = ["router", "CHAT_HTML"]