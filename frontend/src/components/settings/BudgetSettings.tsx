import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Database, Loader2 } from 'lucide-react';
import { useTranslation } from '@/i18n/hooks';
import { toast } from '@/components/ui/toastStore';
import { settingsApi } from '@/lib/api';
import type { APIError } from '@/types';

interface BudgetSettingsProps {
  budgetForm: {
    budget_limit: string;
    warning_threshold: string;
    critical_threshold: string;
  };
  setBudgetForm: (form: {
    budget_limit: string;
    warning_threshold: string;
    critical_threshold: string;
  }) => void;
}

export function BudgetSettings({ budgetForm, setBudgetForm }: BudgetSettingsProps) {
  const { t } = useTranslation('settings');
  const queryClient = useQueryClient();

  const updateBudgetMutation = useMutation({
    mutationFn: settingsApi.updateBudgetSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'budget'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'usage-budget'] });
      toast.success(t('toast.budgetUpdateSuccess'));
    },
    onError: (error: APIError) => {
      toast.error(error?.response?.data?.detail || t('budget.updateError'));
    },
  });

  const handleBudgetSubmit = () => {
    const payload = {
      budget_limit: budgetForm.budget_limit ? parseFloat(budgetForm.budget_limit) : null,
      warning_threshold: parseInt(budgetForm.warning_threshold),
      critical_threshold: parseInt(budgetForm.critical_threshold),
    };
    updateBudgetMutation.mutate(payload);
  };

  return (
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
  );
}
