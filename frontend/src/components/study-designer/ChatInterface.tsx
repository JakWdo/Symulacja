/**
 * ChatInterface - Główny komponent Study Designer Chat
 *
 * Zarządza całą konwersacją z AI, wyświetla wiadomości, input, plan.
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useSession, useSendMessage } from '../../hooks/useStudyDesigner';
import { MessageList } from './MessageList';
import { UserInput } from './UserInput';
import { PlanPreview } from './PlanPreview';
import { ProgressIndicator } from './ProgressIndicator';
import { Alert, AlertDescription } from '../ui/alert';
import { Loader2 } from 'lucide-react';

export const ChatInterface: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [userMessage, setUserMessage] = useState('');

  // Queries
  const { data: session, isLoading, error } = useSession(sessionId);
  const sendMessageMutation = useSendMessage(sessionId!);

  // Auto-scroll effect
  useEffect(() => {
    if (session?.messages) {
      // Scroll to bottom when new messages arrive
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  }, [session?.messages?.length]);

  // Handle send message
  const handleSendMessage = async () => {
    if (!userMessage.trim()) return;

    try {
      await sendMessageMutation.mutateAsync(userMessage);
      setUserMessage(''); // Clear input
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="ml-3 text-lg">Ładowanie sesji...</span>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertDescription>
            Błąd ładowania sesji: {(error as Error).message}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  const isPlanReady = session.status === 'plan_ready';
  const isExecuting = session.status === 'executing';
  const isCompleted = session.status === 'completed';
  const isCancelled = session.status === 'cancelled';

  const canSendMessage =
    session.status === 'active' || session.status === 'plan_ready';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with Progress */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Projektowanie Badania przez Chat
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Sesja: {sessionId?.slice(0, 8)}...
              </p>
            </div>

            <ProgressIndicator currentStage={session.current_stage} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Status Alerts */}
        {isExecuting && (
          <Alert className="mb-4 bg-blue-50 border-blue-200">
            <AlertDescription>
              🚀 Badanie jest wykonywane... Trwa generacja person i analiza.
            </AlertDescription>
          </Alert>
        )}

        {isCompleted && (
          <Alert className="mb-4 bg-green-50 border-green-200">
            <AlertDescription>
              ✅ Badanie zakończone! Wyniki są dostępne w projekcie.
            </AlertDescription>
          </Alert>
        )}

        {isCancelled && (
          <Alert className="mb-4 bg-gray-50 border-gray-200">
            <AlertDescription>
              ❌ Sesja została anulowana.
            </AlertDescription>
          </Alert>
        )}

        {/* Messages */}
        <MessageList
          messages={session.messages || []}
          isLoading={sendMessageMutation.isPending}
        />

        {/* Plan Preview (if generated) */}
        {isPlanReady && session.generated_plan && (
          <div className="mt-6">
            <PlanPreview
              plan={session.generated_plan}
              sessionId={session.id}
            />
          </div>
        )}

        {/* User Input */}
        {canSendMessage && !isPlanReady && (
          <div className="mt-6 sticky bottom-0 bg-white p-4 rounded-lg shadow-lg border border-gray-200">
            <UserInput
              value={userMessage}
              onChange={setUserMessage}
              onSend={handleSendMessage}
              onKeyPress={handleKeyPress}
              disabled={sendMessageMutation.isPending}
              isLoading={sendMessageMutation.isPending}
            />
          </div>
        )}
      </div>
    </div>
  );
};
