import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Users, TrendingUp, BarChart3 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { DisplayPersona } from '@/components/personas/helpers/transformers';

interface PersonasStatsProps {
  filteredPersonas: DisplayPersona[];
  ageGroups: Record<string, number>;
  sortedInterests: [string, number][];
}

export function PersonasStats({
  filteredPersonas,
  ageGroups,
  sortedInterests,
}: PersonasStatsProps) {
  const { t } = useTranslation('personas');

  return (
    <>
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{t('page.stats.allPersonas')}</p>
                <p className="text-2xl brand-orange">{filteredPersonas.length}</p>
              </div>
              <Users className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{t('page.stats.ageRange')}</p>
                <p className="text-2xl brand-orange">
                  {filteredPersonas.length > 0 ? `${Math.min(...filteredPersonas.map(p => p.age))} - ${Math.max(...filteredPersonas.map(p => p.age))}` : 'N/A'}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">{t('page.stats.topInterest')}</p>
                <p className="text-2xl brand-orange">
                  {sortedInterests[0]?.[0] || 'N/A'}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Population Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">{t('page.ageDistribution')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(ageGroups).map(([ageGroup, count]) => (
              <div key={ageGroup} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{ageGroup}</span>
                  <span className="text-card-foreground">{count} ({Math.round((count / filteredPersonas.length) * 100)}%)</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="bg-card border border-border">
          <CardHeader>
            <CardTitle className="text-foreground">{t('page.topInterests')}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sortedInterests.map(([interest, count]) => (
              <div key={interest} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{interest}</span>
                  <span className="text-card-foreground">{count} {t('page.personCount')}</span>
                </div>
                <Progress value={(count / filteredPersonas.length) * 100} className="h-2" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
