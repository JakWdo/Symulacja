/**
 * StudyDesignerView - Główny widok Study Designer Chat
 *
 * Redesigned zgodnie z Sight Design System (Figma Make Design)
 * - Brand colors z CSS variables
 * - Consistent spacing (space-y-6)
 * - Rounded corners (rounded-[8px])
 * - Icons zamiast emoji
 * - Loading states z Skeleton
 */

import React from 'react';
import { useCreateSession } from '../../hooks/useStudyDesigner';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Skeleton } from '../ui/skeleton';
import { Alert, AlertDescription } from '../ui/alert';
import {
  MessageSquare,
  ArrowLeft,
  Sparkles,
  Target,
  Users,
  FlaskConical,
  Zap,
  AlertTriangle
} from 'lucide-react';

interface Props {
  onBack: () => void;
}

export const StudyDesignerView: React.FC<Props> = ({ onBack }) => {
  const createSessionMutation = useCreateSession();

  const handleStartSession = async () => {
    try {
      await createSessionMutation.mutateAsync({});
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1920px] w-full mx-auto p-4 md:p-6">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-6 hover:bg-muted/50"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Wróć do Dashboardu
        </Button>

        {/* Main Card */}
        <Card className="max-w-4xl mx-auto border-border rounded-[8px]">
          <CardHeader className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="bg-brand/10 p-3 rounded-[8px]">
                <Sparkles className="w-6 h-6 text-brand" />
              </div>
              <CardTitle className="text-3xl font-semibold text-foreground">
                Projektowanie Badania przez Chat
              </CardTitle>
            </div>
            <CardDescription className="text-base text-muted-foreground leading-[24px]">
              AI poprowadzi Cię przez proces tworzenia badania krok po kroku.
              Sesja zajmie około 5-10 minut.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Error State */}
            {createSessionMutation.isError && (
              <Alert variant="destructive" className="rounded-[8px]">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Wystąpił błąd podczas tworzenia sesji. Spróbuj ponownie.
                </AlertDescription>
              </Alert>
            )}

            {/* How it works Section */}
            <div className="bg-brand/5 border border-brand/20 rounded-[8px] p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-brand" />
                Jak to działa?
              </h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="bg-brand/10 p-2 rounded-[6px] flex-shrink-0 mt-0.5">
                    <Target className="w-4 h-4 text-brand" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Zdefiniuj cel badania</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Zadaję pytania aby zrozumieć Twój cel i wymagania biznesowe
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="bg-brand/10 p-2 rounded-[6px] flex-shrink-0 mt-0.5">
                    <Users className="w-4 h-4 text-brand" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Określ grupę docelową</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Pomagam precyzyjnie określić demografię i charakterystykę uczestników
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="bg-brand/10 p-2 rounded-[6px] flex-shrink-0 mt-0.5">
                    <FlaskConical className="w-4 h-4 text-brand" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Wybierz metodę badawczą</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Rekomendacja najlepszej metody: persony, grupy fokusowe lub ankiety
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <div className="bg-brand/10 p-2 rounded-[6px] flex-shrink-0 mt-0.5">
                    <MessageSquare className="w-4 h-4 text-brand" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Generuj plan i wykonaj</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Profesjonalny plan badania z estymacjami i automatycznym wykonaniem
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Benefits Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-muted/50 border border-border rounded-[8px] p-4">
                <p className="text-sm font-medium text-foreground">Szybkie</p>
                <p className="text-xs text-muted-foreground mt-1">5-10 minut rozmowy</p>
              </div>
              <div className="bg-muted/50 border border-border rounded-[8px] p-4">
                <p className="text-sm font-medium text-foreground">Inteligentne</p>
                <p className="text-xs text-muted-foreground mt-1">AI dopasowuje pytania</p>
              </div>
              <div className="bg-muted/50 border border-border rounded-[8px] p-4">
                <p className="text-sm font-medium text-foreground">Automatyczne</p>
                <p className="text-xs text-muted-foreground mt-1">Workflow auto-tworzony</p>
              </div>
            </div>

            {/* CTA Button */}
            <Button
              size="lg"
              className="w-full bg-brand hover:bg-brand/90 text-white h-12 rounded-[6px]"
              onClick={handleStartSession}
              disabled={createSessionMutation.isPending}
            >
              {createSessionMutation.isPending ? (
                <>
                  <Skeleton className="w-5 h-5 mr-2 rounded-full" />
                  Rozpoczynam sesję...
                </>
              ) : (
                <>
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Rozpocznij Nowe Badanie
                </>
              )}
            </Button>

            {/* Footer Note */}
            <p className="text-sm text-muted-foreground text-center leading-[20px]">
              Możesz przerwać w dowolnym momencie i wrócić do sesji później.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
