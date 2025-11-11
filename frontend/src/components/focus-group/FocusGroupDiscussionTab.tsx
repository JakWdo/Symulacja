import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { MessageSquare, Play, Clock, Info } from 'lucide-react';
import { SpinnerLogo } from '@/components/ui/spinner-logo';
import { Logo } from '@/components/ui/logo';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { formatDuration as formatFGDuration } from '@/lib/focusGroupGeneration';

interface ChatMessage {
  id: number;
  persona: string;
  message: string;
  timestamp: string;
}

interface FocusGroupDiscussionTabProps {
  isRunning: boolean;
  discussionComplete: boolean;
  status: string;
  personaCount: number;
  questionsCount: number;
  discussionProgress: number;
  chatMessages: ChatMessage[];
  progressMeta: {
    duration: number;
    targetResponses: number;
  } | null;
  responsesCount: number;
  aiSummaryGenerated: boolean;
  summaryProcessing: boolean;
  onRunDiscussion: () => void;
  onGenerateAiSummary: () => void;
  onViewResults: () => void;
  isRunPending: boolean;
}

export function FocusGroupDiscussionTab({
  isRunning,
  discussionComplete,
  status,
  personaCount,
  questionsCount,
  discussionProgress,
  chatMessages,
  progressMeta,
  responsesCount,
  aiSummaryGenerated,
  summaryProcessing,
  onRunDiscussion,
  onGenerateAiSummary,
  onViewResults,
  isRunPending,
}: FocusGroupDiscussionTabProps) {
  const { t } = useTranslation('focusGroups');

  return (
    <Card className="bg-card border border-border shadow-sm">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-card-foreground">{t('view.discussion.runTitle')}</CardTitle>
            <p className="text-muted-foreground">{t('view.discussion.runDescription')}</p>
          </div>

          {!discussionComplete && !isRunning && status === 'pending' && (
            <Button
              onClick={onRunDiscussion}
              className="bg-brand hover:bg-brand/90 text-brand-foreground"
              disabled={isRunPending}
            >
              <Play className="w-4 h-4 mr-2" />
              {t('view.discussion.startButton')}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!isRunning && !discussionComplete && status === 'pending' && (
          <div className="text-center py-8">
            <MessageSquare className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-card-foreground mb-2">{t('view.discussion.readyTitle')}</h3>
            <p className="text-muted-foreground">
              {t('view.discussion.readyDescription', { count: personaCount })}
            </p>
          </div>
        )}

        {(isRunning || status === 'running') && (
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="rounded-lg border border-border bg-card/80 p-4 space-y-3 shadow-sm">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <SpinnerLogo className="w-4 h-4" />
                  <span className="font-medium text-card-foreground">
                    {t('view.discussion.simulationInProgress')}
                  </span>
                </div>

                {progressMeta && (
                  <div className="text-xs text-muted-foreground tabular-nums">
                    Czas: ~{formatFGDuration(progressMeta.duration)}
                    {responsesCount > 0 && progressMeta.targetResponses > 0 && (
                      <span className="ml-2 text-primary font-medium">
                        {responsesCount}/{progressMeta.targetResponses}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <Progress value={Math.min(discussionProgress, 100)} className="h-2" />

              <div className="flex items-start gap-2 text-xs text-muted-foreground bg-muted/30 rounded p-2">
                <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
                <p className="leading-tight">
                  <strong>Generowanie Focus Group trwa długo</strong> gdy masz wiele person
                  i pytań (każda persona odpowiada na każde pytanie).
                  {progressMeta && progressMeta.targetResponses > 0 && (
                    <> {progressMeta.targetResponses} odpowiedzi ≈ {formatFGDuration(progressMeta.duration)}.</>
                  )}
                </p>
              </div>
            </div>

            {/* Current Status */}
            <div className="bg-muted rounded-lg p-4 border border-border">
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Clock className="w-4 h-4 text-primary" />
                  <span className="text-muted-foreground">{t('view.discussion.currentStatus')}</span>
                </div>
                <p className="text-card-foreground">
                  {discussionProgress < 30 && t('view.discussion.statusIntroduction')}
                  {discussionProgress >= 30 && discussionProgress < 60 && t('view.discussion.statusDiscussing', { current: 1, total: questionsCount })}
                  {discussionProgress >= 60 && discussionProgress < 90 && t('view.discussion.statusFollowUp')}
                  {discussionProgress >= 90 && t('view.discussion.statusWrapping')}
                </p>
              </div>
            </div>

            {/* Live Chat Messages */}
            {chatMessages.length > 0 && (
              <div className="bg-card border border-border rounded-lg p-4">
                <h4 className="text-card-foreground font-medium mb-3">{t('view.discussion.liveDiscussionTitle')}</h4>
                <div className="space-y-3 max-h-48 overflow-y-auto">
                  {chatMessages.map((message) => (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="flex gap-3"
                    >
                      <div className="w-8 h-8 bg-gradient-to-br from-[#F27405] to-[#F29F05] rounded-full flex items-center justify-center shrink-0">
                        <span className="text-white text-xs font-medium">
                          {message.persona.split(' ').map(n => n[0]).join('')}
                        </span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-card-foreground font-medium text-sm">{message.persona}</span>
                          <span className="text-muted-foreground text-xs">{message.timestamp}</span>
                        </div>
                        <div className="bg-muted/50 rounded-lg p-3 border border-border/50">
                          <p className="text-card-foreground text-sm">{message.message}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {discussionComplete && !aiSummaryGenerated && (
          <div className="text-center py-8">
            <img
              src="/sight-logo-przezroczyste.png"
              alt="Sight Logo"
              className="w-16 h-16 mx-auto mb-4 object-contain"
            />
            <h3 className="text-lg font-medium text-brand mb-2">{t('view.discussion.completeTitle')}</h3>
            <p className="text-muted-foreground mb-4">
              {t('view.discussion.completeDescription')}
            </p>
            <Button
              onClick={onGenerateAiSummary}
              disabled={summaryProcessing}
              className="bg-brand hover:bg-brand/90 text-brand-foreground"
            >
              {summaryProcessing ? (
                <>
                  <Logo className="w-4 h-4 mr-2" spinning />
                  {t('view.discussion.generatingButton')}
                </>
              ) : (
                <>
                  <MessageSquare className="w-4 h-4 mr-2" />
                  {t('view.discussion.generateButton')}
                </>
              )}
            </Button>
          </div>
        )}

        {discussionComplete && aiSummaryGenerated && (
          <div className="text-center py-8">
            <img
              src="/sight-logo-przezroczyste.png"
              alt="Sight Logo"
              className="w-16 h-16 mx-auto mb-4 object-contain"
            />
            <h3 className="text-lg font-medium text-brand mb-2">{t('view.discussion.summaryGeneratedTitle')}</h3>
            <p className="text-muted-foreground mb-4">
              {t('view.discussion.summaryGeneratedDescription')}
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                variant="outline"
                onClick={onViewResults}
                className="border-border text-card-foreground hover:text-card-foreground"
              >
                {t('view.discussion.viewResultsButton')}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
