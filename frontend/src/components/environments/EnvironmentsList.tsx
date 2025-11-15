import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Plus,
  Search,
  Folder,
  Calendar,
  Check,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { Logo } from '@/components/ui/logo';
import { CreateEnvironmentDialog } from './CreateEnvironmentDialog';
import { listEnvironments, type Environment } from '@/api/environments';
import { formatDate } from '@/lib/utils';
import { useAppStore } from '@/store/appStore';

interface EnvironmentsListProps {
  onSelectEnvironment?: (environment: Environment) => void;
}

export function EnvironmentsList({ onSelectEnvironment }: EnvironmentsListProps) {
  const { t } = useTranslation('common');
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const currentTeamId = useAppStore((state) => state.currentTeamId);
  const currentEnvironmentId = useAppStore((state) => state.currentEnvironmentId);
  const setCurrentEnvironmentId = useAppStore((state) => state.setCurrentEnvironmentId);

  // Fetch environments
  const { data: environments = [], isLoading } = useQuery({
    queryKey: ['environments', currentTeamId],
    queryFn: () => listEnvironments(currentTeamId ?? undefined),
  });

  const filteredEnvironments = environments.filter((env: Environment) =>
    env.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (env.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full p-6">
        <Logo className="w-8 h-8" spinning />
      </div>
    );
  }

  return (
    <div className="w-full h-full overflow-y-auto">
      <div className="max-w-[1920px] w-full mx-auto space-y-6 p-6">
        {/* Header */}
        <PageHeader
          title={t('environments.title')}
          subtitle={t('environments.subtitle')}
          actions={
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              {t('environments.newEnvironment')}
            </Button>
          }
        />

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            type="text"
            placeholder={t('environments.searchPlaceholder')}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Environments Grid */}
        {filteredEnvironments.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Folder className="w-12 h-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {searchTerm ? t('environments.noResults') : t('environments.noEnvironments')}
              </h3>
              <p className="text-muted-foreground text-center mb-4">
                {searchTerm
                  ? t('environments.tryDifferentSearch')
                  : t('environments.createFirstEnvironment')}
              </p>
              {!searchTerm && (
                <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                  <Plus className="w-4 h-4" />
                  {t('environments.createEnvironment')}
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEnvironments.map((env) => (
              <Card
                key={env.id}
                className={`hover:shadow-md transition-shadow cursor-pointer ${
                  env.id === currentEnvironmentId ? 'border-primary/60 shadow-md' : ''
                }`}
                onClick={() => {
                  setCurrentEnvironmentId(env.id);
                  onSelectEnvironment?.(env);
                }}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Folder className="w-5 h-5 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-lg truncate">{env.name}</CardTitle>
                      </div>
                    </div>
                    {env.id === currentEnvironmentId && (
                      <Badge variant="default" className="gap-1">
                        <Check className="w-3 h-3" />
                        {t('environments.currentEnvironment')}
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {env.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {env.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Calendar className="w-3 h-3" />
                    <span>{t('environments.created')} {formatDate(env.created_at)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Create Dialog */}
        <CreateEnvironmentDialog
          open={showCreateDialog}
          onOpenChange={setShowCreateDialog}
        />
      </div>
    </div>
  );
}
