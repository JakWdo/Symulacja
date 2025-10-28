/**
 * Dashboard Header - Figma Design (Node 62:83)
 *
 * Header with title, subtitle, Settings and New Project buttons
 */

import { Button } from '@/components/ui/button';
import { Settings, Plus } from 'lucide-react';

interface DashboardHeaderProps {
  onSettingsClick?: () => void;
  onNewProjectClick?: () => void;
}

export function DashboardHeader({ onSettingsClick, onNewProjectClick }: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      {/* Left: Title + Subtitle */}
      <div>
        <h1 className="font-crimson font-semibold text-2xl leading-[33.6px] text-[#333333] dark:text-foreground">
          Panel główny
        </h1>
        <p className="font-crimson font-normal text-base leading-[25.6px] text-figma-muted dark:text-muted-foreground">
          Śledź spostrzeżenia, akcje i postęp badań w czasie rzeczywistym
        </p>
      </div>

      {/* Right: Buttons */}
      <div className="flex items-start gap-2">
        {/* Settings Button - Outline */}
        <Button
          variant="outline"
          size="sm"
          className="h-9 px-[13px] border-border rounded-figma-button font-crimson font-semibold text-sm text-[#333333] dark:text-foreground"
          onClick={onSettingsClick}
        >
          <Settings className="h-4 w-4 mr-2" />
          Ustawienia
        </Button>

        {/* New Project Button - Primary Orange */}
        <Button
          size="sm"
          className="h-9 px-[12px] bg-figma-primary hover:bg-figma-primary/90 text-white rounded-figma-button font-crimson font-semibold text-sm"
          onClick={onNewProjectClick}
        >
          <Plus className="h-4 w-4 mr-2" />
          Nowy projekt
        </Button>
      </div>
    </div>
  );
}
