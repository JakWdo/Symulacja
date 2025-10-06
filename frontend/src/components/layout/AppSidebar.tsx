import { Search, LayoutDashboard, FolderOpen, Settings, Plus, Command } from 'lucide-react';
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
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { Logo } from '@/components/ui/Logo';
import { useTheme } from '@/hooks/use-theme';

interface AppSidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export function AppSidebar({ currentView, onNavigate }: AppSidebarProps) {
  const { theme } = useTheme();

  return (
    <Sidebar className="bg-sidebar border-r border-sidebar-border w-64">
      <SidebarHeader className="h-[164px] p-0">
        <div className="flex items-center justify-between h-12 px-6 pt-6">
          <div key={theme} className="w-12 h-12 rounded-[14px] shadow-[0px_10px_15px_-3px_rgba(0,0,0,0.1),0px_4px_6px_-4px_rgba(0,0,0,0.1)] overflow-hidden">
            <Logo className="w-full h-full object-cover" />
          </div>
          <ThemeToggle />
        </div>

        <div className="relative px-6 mt-8">
          <Search className="absolute left-9 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <input
            placeholder="Search"
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
            Main Menu
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
                  <span className="text-[14px]">Dashboard</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('projects')}
                  className={`h-8 gap-2 pl-2 pr-0 rounded-[8px] ${
                    currentView === 'projects'
                      ? 'bg-sidebar-accent border-l-2 border-l-primary text-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent'
                  }`}
                >
                  <FolderOpen className="w-4 h-4" />
                  <span className="text-[14px]">Projects</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup className="px-2 py-2">
          <SidebarGroupLabel className="h-8 px-2 text-muted-foreground text-[12px] font-medium uppercase tracking-[0.3px]">
            Workflows
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  onClick={() => onNavigate('projects')}
                  className="h-8 gap-2 pl-2 pr-0 rounded-[8px] text-sidebar-foreground hover:bg-sidebar-accent"
                >
                  <Plus className="w-4 h-4" />
                  <span className="text-[14px]">New Project</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="h-[166px] p-6 bg-sidebar">
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
              <span className="text-[14px]">Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <div className="flex items-center gap-3 mt-6 p-3 rounded-[10px] bg-sidebar-accent border border-sidebar-border h-[62px]">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="text-white text-[14px] bg-primary rounded-full shadow-[0px_1px_3px_0px_rgba(0,0,0,0.1),0px_1px_2px_-1px_rgba(0,0,0,0.1)]">
              JD
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-[14px] leading-5 text-foreground truncate">John Doe</p>
            <p className="text-[12px] leading-4 text-muted-foreground">Researcher</p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
