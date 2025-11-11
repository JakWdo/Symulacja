import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { LanguageSelector } from '@/components/ui/language-selector';
import { Palette } from 'lucide-react';
import { useTheme } from '@/hooks/use-theme';
import { useTranslation } from '@/i18n/hooks';

export function AppearanceSettings() {
  const { t } = useTranslation('settings');
  const { theme, setTheme } = useTheme();

  return (
    <Card className="bg-card border border-border shadow-sm">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Palette className="w-5 h-5 text-chart-1" />
          <CardTitle className="text-card-foreground">{t('appearance.title')}</CardTitle>
        </div>
        <p className="text-muted-foreground">{t('appearance.description')}</p>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Theme Selection */}
        <div className="space-y-3">
          <div>
            <Label className="text-card-foreground">
              {t('appearance.theme.label')}
            </Label>
            <p className="text-sm text-muted-foreground">
              {t('appearance.theme.description')}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Button
              variant={theme === 'light' ? 'default' : 'outline'}
              onClick={() => setTheme('light')}
              className="justify-start h-auto p-4"
            >
              <div className="flex flex-col items-start gap-2">
                <div className="w-6 h-4 rounded border bg-white border-gray-300"></div>
                <span>{t('appearance.theme.light')}</span>
              </div>
            </Button>

            <Button
              variant={theme === 'dark' ? 'default' : 'outline'}
              onClick={() => setTheme('dark')}
              className="justify-start h-auto p-4"
            >
              <div className="flex flex-col items-start gap-2">
                <div className="w-6 h-4 rounded border bg-gray-800 border-gray-600"></div>
                <span>{t('appearance.theme.dark')}</span>
              </div>
            </Button>
          </div>
        </div>

        <Separator className="bg-border" />

        {/* Language Selection */}
        <div className="space-y-3">
          <div>
            <Label className="text-card-foreground">
              {t('appearance.language.label')}
            </Label>
            <p className="text-sm text-muted-foreground">
              {t('appearance.language.description')}
            </p>
          </div>
          <LanguageSelector />
        </div>
      </CardContent>
    </Card>
  );
}
