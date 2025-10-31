import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { LanguageSelector } from '@/components/ui/language-selector';
import { useTheme } from '@/hooks/use-theme';
import { useTranslation } from '@/i18n/hooks';
import { toast } from '@/components/ui/toastStore';
import { settingsApi } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { PageHeader } from '@/components/layout/PageHeader';
import { getAvatarUrl, getInitials } from '@/lib/avatar';
import {
  User,
  Database,
  Palette,
  Loader2,
  Upload,
  X,
  AlertTriangle,
} from 'lucide-react';
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

export function Settings() {
  const { t } = useTranslation('settings');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { theme, setTheme } = useTheme();
  const queryClient = useQueryClient();
  const { logout } = useAuth();

  // === QUERIES ===
  const { data: profile, isLoading: isLoadingProfile } = useQuery({
    queryKey: ['settings', 'profile'],
    queryFn: settingsApi.getProfile,
  });

  const { data: stats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['settings', 'stats'],
    queryFn: settingsApi.getStats,
  });

  const { data: budgetSettings } = useQuery({
    queryKey: ['settings', 'budget'],
    queryFn: settingsApi.getBudgetSettings,
  });

  // Local state for forms
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    role: '',
    company: '',
  });

  const [budgetForm, setBudgetForm] = useState({
    budget_limit: '',
    warning_threshold: '80',
    critical_threshold: '90',
  });

  // Update forms when data loads from API
  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name || '',
        role: profile.role || '',
        company: profile.company || '',
      });
    }
  }, [profile]);

  useEffect(() => {
    if (budgetSettings) {
      setBudgetForm({
        budget_limit: budgetSettings.budget_limit?.toString() || '',
        warning_threshold: budgetSettings.warning_threshold.toString(),
        critical_threshold: budgetSettings.critical_threshold.toString(),
      });
    }
  }, [budgetSettings]);

  // === MUTATIONS ===
  const updateProfileMutation = useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success(t('toast.profileUpdateSuccess'));
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t('profile.updateError'));
    },
  });

  const uploadAvatarMutation = useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return settingsApi.uploadAvatar(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success(t('toast.avatarUploadSuccess'));
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t('profile.avatar.uploadError'));
    },
  });

  const deleteAvatarMutation = useMutation({
    mutationFn: settingsApi.deleteAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success(t('toast.avatarDeleteSuccess'));
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t('profile.avatar.deleteError'));
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: settingsApi.deleteAccount,
    onSuccess: () => {
      toast.info(t('toast.accountDeleteSuccess'));
      logout();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t('toast.accountDeleteError'));
    },
  });

  const updateBudgetMutation = useMutation({
    mutationFn: settingsApi.updateBudgetSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'budget'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'usage-budget'] });
      toast.success(t('toast.budgetUpdateSuccess'));
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || t('budget.updateError'));
    },
  });

  // === HANDLERS ===
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      toast.error(t('profile.avatar.invalidType'));
      return;
    }

    // Validate file size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error(t('profile.avatar.tooLarge'));
      return;
    }

    uploadAvatarMutation.mutate(file);
  };

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(profileForm);
  };

  const handleBudgetSubmit = () => {
    const payload = {
      budget_limit: budgetForm.budget_limit ? parseFloat(budgetForm.budget_limit) : null,
      warning_threshold: parseInt(budgetForm.warning_threshold),
      critical_threshold: parseInt(budgetForm.critical_threshold),
    };
    updateBudgetMutation.mutate(payload);
  };


  if (isLoadingProfile || isLoadingStats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    );
  }

  return (
    <div className="max-w-[1920px] w-full mx-auto space-y-6">
      {/* Header */}
      <PageHeader
        title={t('header.title')}
        subtitle={t('header.subtitle')}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-chart-2" />
                <CardTitle className="text-card-foreground">{t('profile.title')}</CardTitle>
              </div>
              <p className="text-muted-foreground">{t('profile.description')}</p>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleProfileSubmit} className="space-y-4">
                <div className="flex items-center gap-4 mb-6">
                  <Avatar className="w-16 h-16">
                    {profile?.avatar_url && (
                      <AvatarImage src={getAvatarUrl(profile.avatar_url)} alt={profile.full_name} />
                    )}
                    <AvatarFallback className="text-white text-xl bg-brand-orange">
                      {getInitials(profile?.full_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex gap-2">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={handleFileSelect}
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadAvatarMutation.isPending}
                    >
                      {uploadAvatarMutation.isPending ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Upload className="w-4 h-4 mr-2" />
                      )}
                      {t('profile.avatar.change')}
                    </Button>
                    {profile?.avatar_url && (
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => deleteAvatarMutation.mutate()}
                        disabled={deleteAvatarMutation.isPending}
                      >
                        {deleteAvatarMutation.isPending ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{t('profile.avatar.hint')}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">{t('profile.fields.fullName')}</Label>
                    <Input
                      id="name"
                      value={profileForm.full_name}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, full_name: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">{t('profile.fields.email')}</Label>
                    <Input id="email" type="email" value={profile?.email} disabled />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="role">{t('profile.fields.role')}</Label>
                    <Input
                      id="role"
                      value={profileForm.role}
                      onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label htmlFor="company">{t('profile.fields.company')}</Label>
                    <Input
                      id="company"
                      value={profileForm.company}
                      onChange={(e) =>
                        setProfileForm({ ...profileForm, company: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    disabled={updateProfileMutation.isPending}
                  >
                    {updateProfileMutation.isPending && (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    )}
                    {t('profile.saveButton')}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Budget & Limits Settings */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-chart-3" />
                <CardTitle className="text-card-foreground">{t('budget.title')}</CardTitle>
              </div>
              <p className="text-muted-foreground">{t('budget.description')}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="budget_limit">{t('budget.fields.limit.label')}</Label>
                  <Input
                    id="budget_limit"
                    type="number"
                    min="0"
                    step="10"
                    placeholder={t('budget.fields.limit.placeholder')}
                    value={budgetForm.budget_limit}
                    onChange={(e) =>
                      setBudgetForm({ ...budgetForm, budget_limit: e.target.value })
                    }
                  />
                  <p className="text-xs text-muted-foreground">
                    {t('budget.fields.limit.hint')}
                  </p>
                </div>

                <Separator className="bg-border" />

                <div className="space-y-4">
                  <h4 className="text-sm font-semibold text-card-foreground">{t('budget.alertsTitle')}</h4>

                  <div className="space-y-2">
                    <Label htmlFor="warning_threshold">{t('budget.fields.warning.label')}</Label>
                    <Input
                      id="warning_threshold"
                      type="number"
                      min="1"
                      max="100"
                      placeholder={t('budget.fields.warning.placeholder')}
                      value={budgetForm.warning_threshold}
                      onChange={(e) =>
                        setBudgetForm({ ...budgetForm, warning_threshold: e.target.value })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {t('budget.fields.warning.hint')}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="critical_threshold">{t('budget.fields.critical.label')}</Label>
                    <Input
                      id="critical_threshold"
                      type="number"
                      min="1"
                      max="100"
                      placeholder={t('budget.fields.critical.placeholder')}
                      value={budgetForm.critical_threshold}
                      onChange={(e) =>
                        setBudgetForm({ ...budgetForm, critical_threshold: e.target.value })
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      {t('budget.fields.critical.hint')}
                    </p>
                  </div>
                </div>

                <div className="flex justify-end">
                  <Button
                    type="button"
                    className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                    onClick={handleBudgetSubmit}
                    disabled={updateBudgetMutation.isPending}
                  >
                    {updateBudgetMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                    {t('budget.saveButton')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Appearance Settings */}
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
        </div>

        {/* Sidebar */}
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
      </div>
    </div>
  );
}
