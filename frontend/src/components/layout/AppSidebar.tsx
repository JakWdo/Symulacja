import { Search, LayoutDashboard, FolderOpen, Settings, Command, Users, MessageSquare, BarChart3, LogOut, Workflow } from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Logo } from '@/components/ui/logo';
import { useTheme } from '@/hooks/use-theme';
import { useAuth } from '@/contexts/AuthContext';
import { getAvatarUrl, getInitials } from '@/lib/avatar';
import { useTranslation } from 'react-i18next';

interface AppSidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export function AppSidebar({ currentView, onNavigate }: AppSidebarProps) {
  const { theme } = useTheme();
  const { user, logout } = useAuth();
  const { t } = useTranslation('common');

  return (
    <Sidebar className="bg-sidebar border-r border-sidebar-border w-64 h-screen sticky top-0">
      <SidebarHeader className="h-[164px] p-0 flex-shrink-0">
        <div className="flex items-center justify-between h-12 px-6 pt-6">
          <div key={theme} className="w-12 h-12 rounded-[14px] shadow-[0px_10px_15px_-3px_rgba(0,0,0,0.1),0px_4px_6px_-4px_rgba(0,0,0,0.1)] overflow-hidden">
            <Logo className="w-full h-full object-cover" />
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
          </div>
        </div>

        <div className="relative px-6 mt-8">
          <Search className="absolute left-9 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <input
            placeholder={t('sidebar.search')}
            className="w-full h-9 pl-10 pr-3 py-1 bg-sidebar-accent border border-sidebar-border rounded-[8px] text-[14px] text-muted-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <div className="absolute right-9 top-1/2 transform -translate-y-1/2 flex items-center gap-1 text-xs text-muted-foreground">
            <Command className="w-3 h-3" />
            <span className="text-[12px]">F</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent className="bg-sidebar">
        <SidebarGroup className="px-2 py-2">
          <SidebarGroupLabel className="h-8 px-2 text-muted-foreground text-[12px] font-medium uppercase tracking-[0.3px]">
            {t('sidebar.mainMenu')}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('dashboard')}
                  className={`h-8 gap-2 pl-[10px] pr-0 rounded-[8px] ${
                    currentView === 'dashboard'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.dashboard')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('projects')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'projects' || currentView === 'project-detail'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <FolderOpen className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.projects')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('personas')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'personas'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <Users className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.personas')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('surveys')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'surveys' || currentView === 'survey-builder' || currentView === 'survey-results'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <BarChart3 className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.surveys')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('focus-groups')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'focus-groups' || currentView === 'focus-group-builder' || currentView === 'focus-group-detail'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.focusGroups')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('workflows')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'workflows' || currentView === 'workflow-editor'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <Workflow className="w-4 h-4" />
                  <span className="text-[14px]">{t('sidebar.workflows')}</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="h-[166px] p-6 bg-sidebar flex-shrink-0">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={() => onNavigate('settings')}
              className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                currentView === 'settings'
                  ? 'bg-sidebar-accent text-foreground'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent'
              }`}
            >
              <Settings className="w-4 h-4" />
              <span className="text-[14px]">{t('sidebar.settings')}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <div className="flex items-center gap-3 mt-6 p-3 rounded-[10px] bg-sidebar-accent border border-sidebar-border min-h-[62px]">
          <Avatar className="w-8 h-8 flex-shrink-0">
            {user?.avatar_url && <AvatarImage src={getAvatarUrl(user.avatar_url)} />}
            <AvatarFallback className="text-white text-[14px] bg-brand-orange rounded-full shadow-[0px_1px_3px_0px_rgba(0,0,0,0.1),0px_1px_2px_-1px_rgba(0,0,0,0.1)]">
              {getInitials(user?.full_name)}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 overflow-hidden">
            <p className="text-[14px] leading-5 text-foreground truncate">{user?.full_name || t('sidebar.userFallback')}</p>
            <p className="text-[12px] leading-4 text-muted-foreground truncate">{user?.role || user?.email || t('sidebar.roleFallback')}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 hover:bg-sidebar-accent-foreground/10 rounded transition-colors"
            title={t('sidebar.logout')}
          >
            <LogOut className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
