import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { settingsApi } from '@/lib/api';
import { useTranslation } from '@/i18n/hooks';
import { ProfileSettings } from '@/components/settings/ProfileSettings';
import { BudgetSettings } from '@/components/settings/BudgetSettings';
import { AppearanceSettings } from '@/components/settings/AppearanceSettings';
import { LLMProviderSettings } from '@/components/settings/LLMProviderSettings';
import { AccountSidebar } from '@/components/settings/AccountSidebar';

export function Settings() {
  const { t } = useTranslation('settings');

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

  if (isLoadingProfile || isLoadingStats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
      </div>
    );
  }

  return (
    <div className="max-w-[1920px] w-full mx-auto space-y-6">
      <PageHeader
        title={t('header.title')}
        subtitle={t('header.subtitle')}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <ProfileSettings
            profile={profile}
            profileForm={profileForm}
            setProfileForm={setProfileForm}
          />
          <BudgetSettings
            budgetForm={budgetForm}
            setBudgetForm={setBudgetForm}
          />
          <LLMProviderSettings />
          <AppearanceSettings />
        </div>

        <AccountSidebar stats={stats} />
      </div>
    </div>
  );
}
