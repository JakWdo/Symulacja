import { Search, LayoutDashboard, FolderOpen, Settings, Command, BarChart3, MessageSquare, Users } from 'lucide-react';
import { Sidebar, SidebarContent, SidebarHeader, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarFooter, SidebarGroup, SidebarGroupLabel, SidebarGroupContent } from './ui/sidebar';
import { Input } from './ui/input';
import { Avatar, AvatarFallback } from './ui/avatar';
import { ThemeToggle } from './ui/theme-toggle';
import sightIcon from 'figma:asset/f037ba4560cd7f6863b8bc139c32facab8681301.png';

interface AppSidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
}

export function AppSidebar({ currentView, onNavigate }: AppSidebarProps) {
  return (
    <Sidebar className="bg-sidebar border-r border-sidebar-border w-64 shadow-sm">
      <SidebarHeader className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="w-12 h-12 rounded-xl overflow-hidden shadow-lg">
            <img 
              src={sightIcon} 
              alt="Sight" 
              className="w-full h-full object-cover" 
            />
          </div>
          <ThemeToggle />
        </div>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input 
            placeholder="Search" 
            className="pl-10 bg-input-background border-border text-foreground placeholder-muted-foreground shadow-sm"
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1 text-xs text-muted-foreground">
            <Command className="w-3 h-3" />
            <span>F</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-muted-foreground text-xs uppercase tracking-wide">
            Main Menu
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  onClick={() => onNavigate('dashboard')}
                  className={`${
                    currentView === 'dashboard' 
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                      : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                  }`}
                  style={currentView === 'dashboard' ? { borderLeftColor: '#F27405' } : {}}
                >
                  <LayoutDashboard className="w-5 h-5" />
                  <span>Dashboard</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  onClick={() => onNavigate('projects')}
                  className={`${
                    currentView === 'projects' || currentView === 'project-detail'
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                      : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                  }`}
                  style={currentView === 'projects' || currentView === 'project-detail' ? { borderLeftColor: '#F27405' } : {}}
                >
                  <FolderOpen className="w-5 h-5" />
                  <span>Projects</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  onClick={() => onNavigate('personas')}
                  className={`${
                    currentView === 'personas'
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                      : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                  }`}
                  style={currentView === 'personas' ? { borderLeftColor: '#F27405' } : {}}
                >
                  <Users className="w-5 h-5" />
                  <span>Personas</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  onClick={() => onNavigate('surveys')}
                  className={`${
                    currentView === 'surveys' || currentView === 'survey-builder' || currentView === 'survey-results'
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                      : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                  }`}
                  style={currentView === 'surveys' || currentView === 'survey-builder' || currentView === 'survey-results' ? { borderLeftColor: '#F27405' } : {}}
                >
                  <BarChart3 className="w-5 h-5" />
                  <span>Surveys</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton 
                  onClick={() => onNavigate('focus-groups')}
                  className={`${
                    currentView === 'focus-groups' || currentView === 'focus-group-detail' || currentView === 'focus-group-session'
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                      : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                  }`}
                  style={currentView === 'focus-groups' || currentView === 'focus-group-detail' || currentView === 'focus-group-session' ? { borderLeftColor: '#F27405' } : {}}
                >
                  <MessageSquare className="w-5 h-5" />
                  <span>Focus Groups</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-6">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              onClick={() => onNavigate('settings')}
              className={`${
                currentView === 'settings' 
                  ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm' 
                  : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
              }`}
            >
              <Settings className="w-5 h-5" />
              <span>Settings</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        
        <div className="flex items-center gap-3 mt-4 p-3 rounded-lg bg-sidebar-accent border border-sidebar-border shadow-sm">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="text-white text-sm shadow-sm" style={{ backgroundColor: '#F27405' }}>
              JD
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-sidebar-accent-foreground truncate">John Doe</p>
            <p className="text-xs text-muted-foreground">Researcher</p>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}