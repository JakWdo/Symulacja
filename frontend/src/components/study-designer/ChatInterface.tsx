/**
 * ChatInterface - Główny komponent Study Designer Chat
 *
 * Redesigned zgodnie z Sight Design System:
 * - Brand colors z CSS variables
 * - Consistent spacing i borders
 * - Icons zamiast emoji
 * - Skeleton loading states
 * - Proper alert variants (info, success, warning)
 */

import React, { useState, useEffect } from 'react';
import { useSession, useSendMessageStream } from '../../hooks/useStudyDesigner';
import { MessageList } from './MessageList';
import { UserInput } from './UserInput';
import { PlanPreview } from './PlanPreview';
import { ProgressIndicator } from './ProgressIndicator';
import { Alert, AlertDescription } from '../ui/alert';
import { Skeleton } from '../ui/skeleton';
import { Loader2, Rocket, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface ChatInterfaceProps {
  sessionId: string;
  onBack?: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId, onBack }) => {
  const [userMessage, setUserMessage] = useState('');

  // Queries
  const { data: session, isLoading, error } = useSession(sessionId);

  // NOWY: Streaming hook (zamiast mutation)
  const {
    sendMessage,
    isStreaming,
    streamedMessage,
    error: streamError,
  } = useSendMessageStream(sessionId!);

  // Auto-scroll effect
  useEffect(() => {
    if (session?.messages || streamedMessage) {
      // Scroll to bottom when new messages arrive or streaming
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }
  }, [session?.messages?.length, streamedMessage]);

  // Handle send message
  const handleSendMessage = async () => {
    if (!userMessage.trim() || isStreaming) return;

    const messageToSend = userMessage;
    setUserMessage(''); // Clear input immediately

    try {
      await sendMessage(messageToSend);
    } catch (err) {
      console.error('Failed to send message:', err);
      // Restore message on error
      setUserMessage(messageToSend);
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
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-brand" />
          <p className="text-base text-muted-foreground">Ładowanie sesji...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <div className="max-w-[1920px] w-full mx-auto p-4 md:p-6">
          <Alert variant="destructive" className="rounded-[8px]">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Błąd ładowania sesji: {(error as Error).message}
            </AlertDescription>
          </Alert>
        </div>
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
    <div className="min-h-screen bg-background">
      {/* Header with Progress */}
      <div className="bg-background border-b border-border sticky top-0 z-10 shadow-sm">
        <div className="max-w-[1920px] w-full mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-xl md:text-2xl font-semibold text-foreground">
                Projektowanie Badania przez Chat
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                Sesja: {sessionId?.slice(0, 8)}...
              </p>
            </div>

            <ProgressIndicator currentStage={session.current_stage} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1920px] w-full mx-auto px-4 py-6">
        <div className="max-w-5xl mx-auto space-y-6">
          {/* Status Alerts */}
          {isExecuting && (
            <Alert className="rounded-[8px] bg-info/10 border-info/20">
              <Rocket className="h-4 w-4 text-info" />
              <AlertDescription className="text-info-foreground">
                Badanie jest wykonywane... Trwa tworzenie workflow i przygotowanie zasobów.
              </AlertDescription>
            </Alert>
          )}

          {isCompleted && (
            <Alert className="rounded-[8px] bg-success/10 border-success/20">
              <CheckCircle className="h-4 w-4 text-success" />
              <AlertDescription className="text-success-foreground">
                Badanie zakończone! Wyniki są dostępne w projekcie.
              </AlertDescription>
            </Alert>
          )}

          {isCancelled && (
            <Alert className="rounded-[8px] bg-muted border-border">
              <XCircle className="h-4 w-4 text-muted-foreground" />
              <AlertDescription className="text-muted-foreground">
                Sesja została anulowana.
              </AlertDescription>
            </Alert>
          )}

          {/* Messages */}
          <MessageList
            messages={session.messages || []}
            isLoading={isStreaming}
            streamingMessage={streamedMessage}
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
            <div className="mt-6 sticky bottom-4 bg-background p-4 rounded-[8px] border border-border shadow-sm">
              <UserInput
                value={userMessage}
                onChange={setUserMessage}
                onSend={handleSendMessage}
                onKeyPress={handleKeyPress}
                disabled={isStreaming}
                isLoading={isStreaming}
                placeholder={isStreaming ? "AI odpowiada..." : "Wpisz wiadomość..."}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
