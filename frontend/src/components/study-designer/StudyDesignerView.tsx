/**
 * StudyDesignerView - Główny widok Study Designer Chat
 * 
 * Simplified version bez React Router - używa state-based routing.
 */

import React, { useState } from 'react';
import { useCreateSession } from '../../hooks/useStudyDesigner';
import { Button } from '../ui/button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { MessageSquare, ArrowLeft } from 'lucide-react';

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
    <div className="container mx-auto p-6">
      <Button
        variant="ghost"
        onClick={onBack}
        className="mb-4"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Wróć do Dashboardu
      </Button>

      <Card className="max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle className="text-3xl">Projektowanie Badania przez Chat 💬</CardTitle>
          <CardDescription className="text-lg">
            AI poprowadzi Cię przez proces tworzenia badania krok po kroku
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-3">Jak to działa?</h3>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Zadaję pytania aby zrozumieć Twój cel i wymagania</li>
              <li>Pomagam wybrać najlepszą metodę badawczą</li>
              <li>Generuję profesjonalny plan badania z estymacjami</li>
              <li>Po Twoim zatwierdzeniu - automatycznie wykonuję badanie</li>
            </ol>
          </div>

          <Button
            size="lg"
            className="w-full"
            onClick={handleStartSession}
            disabled={createSessionMutation.isPending}
          >
            <MessageSquare className="w-5 h-5 mr-2" />
            {createSessionMutation.isPending ? 'Rozpoczynam...' : 'Rozpocznij Nowe Badanie'}
          </Button>

          <p className="text-sm text-gray-500 text-center">
            Sesja zajmie ~5-10 minut. Możesz przerwać w dowolnym momencie.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};
