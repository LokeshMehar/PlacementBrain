import React, { useState, useEffect } from 'react';
import {
  Brain,
  MessageSquare,
  Database,
  ChevronLeft,
  ChevronRight,
  Upload as UploadIcon,
  Trash2,
  X,
} from 'lucide-react';
import ChatWindow from './components/Chat/ChatWindow';
import KnowledgeBase from './components/Dashboard/KnowledgeBase';
import FileUpload from './components/Upload/FileUpload';
import RepoInput from './components/Upload/RepoInput';
import { listChats, createChat, deleteChat, ChatSession } from './api/chat';

type Tab = 'chat' | 'knowledge';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Chats state
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  
  // Custom Create Chat Modal State
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState('New Chat');

  const loadChats = async () => {
    try {
      const data = await listChats();
      setChats(data);
      if (data.length > 0 && !activeChatId) {
        setActiveChatId(data[0].id);
      } else if (data.length === 0) {
        const newChat = await createChat('General Placement Prep');
        setChats([newChat]);
        setActiveChatId(newChat.id);
      }
    } catch (err) {
      console.error('Failed to load chats:', err);
    }
  };

  useEffect(() => {
    loadChats();
  }, []);

  const handleCreateChatSubmit = async () => {
    if (!newChatTitle.trim()) return;
    try {
      const newChat = await createChat(newChatTitle.trim());
      setChats((prev) => [newChat, ...prev]);
      setActiveChatId(newChat.id);
      setShowNewChatModal(false);
      setNewChatTitle('New Chat');
    } catch (err) {
      console.error('Failed to create chat:', err);
    }
  };

  const handleDeleteChat = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this chat thread?')) return;
    try {
      await deleteChat(id);
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (activeChatId === id) {
        const remaining = chats.filter((c) => c.id !== id);
        if (remaining.length > 0) {
          setActiveChatId(remaining[0].id);
        } else {
          const newChat = await createChat('General Placement Prep');
          setChats([newChat]);
          setActiveChatId(newChat.id);
        }
      }
    } catch (err) {
      console.error('Failed to delete chat:', err);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-900/80 backdrop-blur-lg flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center shadow-lg shadow-brand-500/25">
            <Brain size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-100 tracking-tight">
              PlacementBrain
            </h1>
            <p className="text-[10px] text-gray-500 -mt-0.5">AI Knowledge Base</p>
          </div>
        </div>

        {/* Tab switches */}
        <div className="flex items-center gap-1 bg-gray-800/50 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('chat')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              activeTab === 'chat'
                ? 'bg-brand-500/20 text-brand-400 shadow-sm'
                : 'text-gray-400 hover:text-gray-300'
            }`}
            id="tab-chat"
          >
            <MessageSquare size={16} />
            Chat
          </button>
          <button
            onClick={() => setActiveTab('knowledge')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
              activeTab === 'knowledge'
                ? 'bg-brand-500/20 text-brand-400 shadow-sm'
                : 'text-gray-400 hover:text-gray-300'
            }`}
            id="tab-knowledge"
          >
            <Database size={16} />
            Knowledge Base
          </button>
        </div>

        {/* Sidebar toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-gray-500 hover:text-gray-300 p-2 rounded-lg hover:bg-gray-800 transition-colors lg:block hidden"
          id="sidebar-toggle"
        >
          {sidebarOpen ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
        </button>
      </header>

      {/* Main content area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside
          className={`${
            sidebarOpen ? 'w-80' : 'w-0'
          } transition-all duration-300 border-r border-gray-800 bg-gray-900/50 overflow-hidden flex-shrink-0`}
        >
          <div className="w-80 h-full flex flex-col p-4 space-y-6 overflow-y-auto">
            {/* Conversations list */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300">
                  <MessageSquare size={14} className="text-brand-400" />
                  Conversations
                </h3>
                <button
                  onClick={() => setShowNewChatModal(true)}
                  className="text-xs text-brand-400 hover:text-brand-300 font-medium px-2 py-0.5 rounded border border-brand-500/30 hover:border-brand-500/50 bg-brand-500/5 transition-all"
                >
                  + New
                </button>
              </div>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {chats.map((c) => (
                  <div
                    key={c.id}
                    onClick={() => setActiveChatId(c.id)}
                    className={`group flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-all ${
                      activeChatId === c.id
                        ? 'bg-brand-500/10 border border-brand-500/20 text-brand-300'
                        : 'border border-transparent text-gray-400 hover:bg-gray-800/40 hover:text-gray-300'
                    }`}
                  >
                    <span className="text-xs truncate font-medium max-w-[180px]">{c.title}</span>
                    <button
                      onClick={(e) => handleDeleteChat(c.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 p-0.5 transition-opacity"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-gray-800 pt-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-3">
                <UploadIcon size={14} className="text-brand-400" />
                Upload Files
              </h3>
              <FileUpload />
            </div>

            <div className="border-t border-gray-800 pt-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-300 mb-3">
                <UploadIcon size={14} className="text-purple-400" />
                Clone Repository
              </h3>
              <RepoInput />
            </div>
          </div>
        </aside>

        {/* Main area */}
        <main className="flex-1 overflow-hidden">
          {activeTab === 'chat' ? <ChatWindow activeChatId={activeChatId || ''} /> : <KnowledgeBase />}
        </main>
      </div>

      {/* New Chat Modal */}
      {showNewChatModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
          <div className="glass-card p-6 max-w-sm w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-100">
                New Conversation
              </h3>
              <button
                onClick={() => setShowNewChatModal(false)}
                className="text-gray-400 hover:text-gray-200"
              >
                <X size={16} />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-gray-400 mb-1">
                  Conversation Title
                </label>
                <input
                  type="text"
                  value={newChatTitle}
                  onChange={(e) => setNewChatTitle(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateChatSubmit()}
                  className="input-field w-full text-xs py-1.5"
                  placeholder="e.g. C++ Practice, Resume Prep..."
                  autoFocus
                />
              </div>
              <button
                onClick={handleCreateChatSubmit}
                disabled={!newChatTitle.trim()}
                className="btn-primary w-full text-xs py-2"
              >
                Create Conversation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
