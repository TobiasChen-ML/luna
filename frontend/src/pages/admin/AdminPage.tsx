import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Users, BookOpen, Mic, ShoppingCart,
  MessageSquare, ListTodo, Key, Settings, Coins,
  Menu, X, ChevronLeft, Loader2, ScrollText, Tags, ShieldAlert
} from 'lucide-react';
import { useAdminAuth } from '@/hooks/useAdminAuth';
import DashboardTab from './tabs/DashboardTab';
import CharactersTab from './tabs/CharactersTab';
import UserCharactersTab from './tabs/UserCharactersTab';
import StoriesTab from './tabs/StoriesTab';
import VoicesTab from './tabs/VoicesTab';
import UsersTab from './tabs/UsersTab';
import OrdersTab from './tabs/OrdersTab';
import TemplatesTab from './tabs/TemplatesTab';
import TasksTab from './tabs/TasksTab';
import ApiKeysTab from './tabs/ApiKeysTab';
import AdminSettingsPage from './AdminSettingsPage';
import CreditsTab from './tabs/CreditsTab';
import AuditLogTab from './tabs/AuditLogTab';
import TagsTab from './tabs/TagsTab';
import ScriptLibraryMatureTab from './tabs/ScriptLibraryMatureTab';

interface Tab {
  id: string;
  label: string;
  icon: React.ElementType;
  component: React.FC;
}

const tabs: Tab[] = [
  { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard, component: DashboardTab },
  { id: 'characters', label: '角色管理', icon: Users, component: CharactersTab },
  { id: 'user-characters', label: '角色用户管理', icon: Users, component: UserCharactersTab },
  { id: 'stories', label: '剧本管理', icon: BookOpen, component: StoriesTab },
  { id: 'tags', label: '标签管理', icon: Tags, component: TagsTab },
  { id: 'script-library-mature', label: '劇本庫 Mature', icon: ShieldAlert, component: ScriptLibraryMatureTab },
  { id: 'voices', label: '音色管理', icon: Mic, component: VoicesTab },
  { id: 'users', label: '用户管理', icon: Users, component: UsersTab },
  { id: 'orders', label: '订单管理', icon: ShoppingCart, component: OrdersTab },
  { id: 'credits', label: 'Credit管理', icon: Coins, component: CreditsTab },
  { id: 'prompts', label: '提示词管理', icon: MessageSquare, component: TemplatesTab },
  { id: 'tasks', label: '任务管理', icon: ListTodo, component: TasksTab },
  { id: 'api-keys', label: 'API密钥', icon: Key, component: ApiKeysTab },
  { id: 'audit-logs', label: '操作日志', icon: ScrollText, component: AuditLogTab },
  { id: 'settings', label: '系统配置', icon: Settings, component: AdminSettingsPage },
];

export default function AdminPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('tab') || 'dashboard';
  });
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAdmin, loading } = useAdminAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  const ActiveComponent = tabs.find(t => t.id === activeTab)?.component || DashboardTab;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="flex h-screen overflow-hidden">
        <div className="hidden lg:block">
          <aside className={`h-full bg-zinc-900 border-r border-zinc-800 transition-all duration-300 ${
            sidebarOpen ? 'w-64' : 'w-20'
          }`}>
            <div className="flex items-center justify-between p-4 border-b border-zinc-800">
              {sidebarOpen && (
                <h1 className="text-lg font-bold text-white">管理中心</h1>
              )}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-zinc-800 rounded-lg"
              >
                <ChevronLeft className={`w-5 h-5 transition-transform ${!sidebarOpen ? 'rotate-180' : ''}`} />
              </button>
            </div>
            <nav className="p-2 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-pink-600 text-white'
                      : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  <tab.icon className="w-5 h-5 shrink-0" />
                  {sidebarOpen && <span>{tab.label}</span>}
                </button>
              ))}
            </nav>
          </aside>
        </div>

        <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-zinc-900 border-b border-zinc-800 px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-bold text-white">管理中心</h1>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 hover:bg-zinc-800 rounded-lg"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
          {mobileMenuOpen && (
            <nav className="mt-4 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveTab(tab.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'bg-pink-600 text-white'
                      : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          )}
        </div>

        <main className="flex-1 overflow-auto pt-16 lg:pt-0">
          <div className="p-6">
            <ActiveComponent />
          </div>
        </main>
      </div>
    </div>
  );
}
