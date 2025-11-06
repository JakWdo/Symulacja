import { Search, LayoutDashboard, FolderOpen, Settings, Command, BarChart3, MessageSquare, Users, Network, Menu } from 'lucide-react';
import { Input } from './ui/input';
import { Avatar, AvatarFallback } from './ui/avatar';
import { ThemeToggle } from './ui/theme-toggle';
import { Sheet, SheetContent, SheetTrigger, SheetTitle, SheetDescription } from './ui/sheet';
import { Button } from './ui/button';
import sightIcon from 'figma:asset/f037ba4560cd7f6863b8bc139c32facab8681301.png';

interface AppSidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  isMobile?: boolean;
  sidebarOpen?: boolean;
  setSidebarOpen?: (open: boolean) => void;
}

export function AppSidebar({ currentView, onNavigate, isMobile, sidebarOpen, setSidebarOpen }: AppSidebarProps) {
  const handleNavigate = (view: string) => {
    onNavigate(view);
    if (isMobile && setSidebarOpen) {
      setSidebarOpen(false);
    }
  };

  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'projects', icon: FolderOpen, label: 'Projects', views: ['projects', 'project-detail'] },
    { id: 'personas', icon: Users, label: 'Personas' },
    { id: 'surveys', icon: BarChart3, label: 'Surveys', views: ['surveys', 'survey-builder', 'survey-results'] },
    { id: 'focus-groups', icon: MessageSquare, label: 'Focus Groups', views: ['focus-groups', 'focus-group-detail', 'focus-group-session', 'focus-group-builder'] },
    { id: 'workflow', icon: Network, label: 'Workflow' },
  ];

  const isActive = (item: typeof menuItems[0]) => {
    if (item.views) {
      return item.views.includes(currentView);
    }
    return currentView === item.id;
  };

  const sidebarContent = (
    <div className="flex flex-col h-full bg-sidebar">
      <div className="p-6">
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
      </div>

      <div className="flex-1 overflow-y-auto px-3">
        <p className="px-4 text-muted-foreground text-xs uppercase tracking-wide mb-2">
          Main Menu
        </p>
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item);
            return (
              <button
                key={item.id}
                onClick={() => handleNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all ${
                  active
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground border-l-2 shadow-sm' 
                    : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
                }`}
                style={active ? { borderLeftColor: '#F27405' } : {}}
              >
                <Icon className="w-5 h-5 shrink-0" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-6 border-t border-sidebar-border">
        <button
          onClick={() => handleNavigate('settings')}
          className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all mb-4 ${
            currentView === 'settings'
              ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm' 
              : 'text-sidebar-foreground hover:text-sidebar-accent-foreground hover:bg-sidebar-accent/50'
          }`}
        >
          <Settings className="w-5 h-5 shrink-0" />
          <span>Settings</span>
        </button>
        
        <div className="flex items-center gap-3 p-3 rounded-lg bg-sidebar-accent border border-sidebar-border shadow-sm">
          <Avatar className="w-8 h-8 shrink-0">
            <AvatarFallback className="text-white text-sm shadow-sm" style={{ backgroundColor: '#F27405' }}>
              JD
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-sidebar-accent-foreground truncate">John Doe</p>
            <p className="text-xs text-muted-foreground">Researcher</p>
          </div>
        </div>
      </div>
    </div>
  );

  if (isMobile) {
    return (
      <>
        <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
          <SheetTrigger asChild>
            <Button 
              variant="ghost" 
              size="icon"
              className="fixed top-4 left-4 z-50 bg-background border border-border shadow-lg"
              style={{ color: '#F27405' }}
            >
              <Menu className="w-5 h-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0 bg-sidebar border-r border-sidebar-border">
            <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
            <SheetDescription className="sr-only">
              Main navigation menu for the Sight application
            </SheetDescription>
            {sidebarContent}
          </SheetContent>
        </Sheet>
      </>
    );
  }

  return (
    <div className="w-64 shrink-0 border-r border-sidebar-border shadow-sm">
      {sidebarContent}
    </div>
  );
}