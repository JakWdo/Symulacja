import { useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Database, Loader2, AlertTriangle } from 'lucide-react';
import { useTranslation } from '@/i18n/hooks';
import { toast } from '@/components/ui/toastStore';
import { settingsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import type { APIError } from '@/types';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

interface AccountStats {
  plan: string;
  projects_count: number;
  personas_count: number;
  focus_groups_count: number;
  surveys_count: number;
}

interface AccountSidebarProps {
  stats: AccountStats | undefined;
}

export function AccountSidebar({ stats }: AccountSidebarProps) {
  const { t } = useTranslation('settings');
  const { logout } = useAuth();

  const deleteAccountMutation = useMutation({
    mutationFn: settingsApi.deleteAccount,
    onSuccess: () => {
      toast.info(t('toast.accountDeleteSuccess'));
      logout();
    },
    onError: (error: APIError) => {
      toast.error(error?.response?.data?.detail || t('toast.accountDeleteError'));
    },
  });

  return (
    <div className="space-y-6">
      {/* Account Status */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-card-foreground">{t('account.title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t('account.plan')}</span>
            <Badge
              className="bg-gradient-to-r from-chart-2/10 to-chart-5/10 text-chart-2 border-chart-2/20 capitalize"
            >
              {stats?.plan || 'free'}
            </Badge>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t('account.stats.projects')}</span>
            <span className="text-card-foreground">{stats?.projects_count || 0}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t('account.stats.personas')}</span>
            <span className="text-card-foreground">{stats?.personas_count || 0}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t('account.stats.focusGroups')}</span>
            <span className="text-card-foreground">{stats?.focus_groups_count || 0}</span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">{t('account.stats.surveys')}</span>
            <span className="text-card-foreground">{stats?.surveys_count || 0}</span>
          </div>

          <Separator className="bg-border" />

          <Button variant="outline" className="w-full" disabled>
            {t('account.upgradeButton')}
          </Button>
        </CardContent>
      </Card>

      {/* Data & Privacy */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-chart-4" />
            <CardTitle className="text-card-foreground">{t('privacy.title')}</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button variant="outline" className="w-full justify-start" disabled>
            {t('privacy.export')}
          </Button>

          <Button variant="outline" className="w-full justify-start" disabled>
            {t('privacy.settings')}
          </Button>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-start border-destructive/50 text-destructive hover:text-destructive hover:border-destructive"
              >
                <AlertTriangle className="w-4 h-4 mr-2" />
                {t('privacy.deleteAccount.button')}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t('privacy.deleteAccount.dialog.title')}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t('privacy.deleteAccount.dialog.description')}
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>{t('privacy.deleteAccount.dialog.items.projects')}</li>
                    <li>{t('privacy.deleteAccount.dialog.items.focusGroups')}</li>
                    <li>{t('privacy.deleteAccount.dialog.items.profile')}</li>
                  </ul>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{t('privacy.deleteAccount.dialog.cancel')}</AlertDialogCancel>
                <AlertDialogAction
                  onClick={() => deleteAccountMutation.mutate()}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  disabled={deleteAccountMutation.isPending}
                >
                  {deleteAccountMutation.isPending && (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  )}
                  {t('privacy.deleteAccount.dialog.confirm')}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>

      {/* Support */}
      <Card className="bg-card border border-border shadow-sm">
        <CardHeader>
          <CardTitle className="text-card-foreground">{t('support.title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button variant="outline" className="w-full justify-start" disabled>
            {t('support.helpCenter')}
          </Button>

          <Button variant="outline" className="w-full justify-start" disabled>
            {t('support.contact')}
          </Button>

          <Button variant="outline" className="w-full justify-start" disabled>
            {t('support.features')}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
