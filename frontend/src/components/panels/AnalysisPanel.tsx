import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Sparkles, User, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { FloatingPanel } from '@/components/ui/floating-panel';
import { focusGroupsApi } from '@/lib/api';
import { useAppStore } from '@/store/appStore';
import { AISummaryPanel } from '@/components/analysis/AISummaryPanel';
import type { FocusGroupResponses } from '@/types';
import { formatDate, cn } from '@/lib/utils';
import { Logo } from '@/components/ui/logo';

export function AnalysisPanel() {
  // Use Zustand selectors to prevent unnecessary re-renders
  const selectedFocusGroup = useAppStore(state => state.selectedFocusGroup);
  const activePanel = useAppStore(state => state.activePanel);
  const setActivePanel = useAppStore(state => state.setActivePanel);
  const [activeView, setActiveView] = useState<'responses' | 'ai-summary'>('responses');
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set([0]));

  const { data: responses, isLoading: responsesLoading } = useQuery<FocusGroupResponses>({
    queryKey: ['focus-group-responses', selectedFocusGroup?.id],
    queryFn: () =>
      selectedFocusGroup ? focusGroupsApi.getResponses(selectedFocusGroup.id) : Promise.reject(),
    enabled: !!selectedFocusGroup && selectedFocusGroup.status === 'completed',
  });

  const toggleQuestion = (index: number) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedQuestions(newExpanded);
  };

  return (
    <FloatingPanel
      isOpen={activePanel === 'analysis'}
      onClose={() => setActivePanel(null)}
      title={selectedFocusGroup ? `Analysis: ${selectedFocusGroup.name}` : 'Analysis'}
      panelKey="analysis"
      size="xl"
    >
      {!selectedFocusGroup ? (
        <div className="flex flex-col items-center justify-center py-20 text-center px-6">
          <div className="w-20 h-20 rounded-full bg-muted/30 flex items-center justify-center mb-6">
            <MessageSquare className="w-10 h-10 text-primary-600" />
          </div>
          <h3 className="text-base font-normal text-foreground leading-[16px] mb-2">No Focus Group Selected</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            Select a completed focus group from the list to view detailed analysis and responses
          </p>
        </div>
      ) : selectedFocusGroup.status !== 'completed' ? (
        <div className="flex flex-col items-center justify-center py-20 text-center px-6">
          <div className="w-20 h-20 rounded-full bg-amber-100 flex items-center justify-center mb-6">
            <Clock className="w-10 h-10 text-amber-600" />
          </div>
          <h3 className="text-base font-normal text-foreground leading-[16px] mb-2">Focus Group In Progress</h3>
          <p className="text-sm text-muted-foreground max-w-sm">
            This focus group is currently <span className="font-semibold text-amber-600">{selectedFocusGroup.status}</span>.
            Analysis will be available once it's completed.
          </p>
        </div>
      ) : (
        <>
          {/* Header with metadata */}
          <div className="border-b border-border pb-4 mb-6">
            {selectedFocusGroup.description && (
              <p className="text-sm text-muted-foreground mb-3">{selectedFocusGroup.description}</p>
            )}
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDate(selectedFocusGroup.created_at)}
              </span>
              <span className="flex items-center gap-1">
                <User className="w-3 h-3" />
                {selectedFocusGroup.persona_ids.length} personas
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3" />
                {selectedFocusGroup.questions.length} questions
              </span>
            </div>
          </div>

          {/* View Toggle */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setActiveView('responses')}
              className={cn(
                'flex-1 py-3 px-4 rounded-figma-button font-medium text-sm transition-all',
                activeView === 'responses'
                  ? 'bg-brand text-white shadow-lg'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              )}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Responses
            </button>
            <button
              onClick={() => setActiveView('ai-summary')}
              className={cn(
                'flex-1 py-3 px-4 rounded-figma-button font-medium text-sm transition-all',
                activeView === 'ai-summary'
                  ? 'bg-brand text-white shadow-lg'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              )}
            >
              <Sparkles className="w-4 h-4 inline mr-2" />
              AI Summary
            </button>
          </div>

          {/* Content */}
          <AnimatePresence mode="wait">
            {activeView === 'responses' && (
              <motion.div
                key="responses"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ResponsesView
                  responses={responses}
                  loading={responsesLoading}
                  expandedQuestions={expandedQuestions}
                  onToggleQuestion={toggleQuestion}
                />
              </motion.div>
            )}
            {activeView === 'ai-summary' && (
              <motion.div
                key="ai-summary"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <AISummaryPanel
                  focusGroupId={selectedFocusGroup.id}
                  focusGroupName={selectedFocusGroup.name}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </FloatingPanel>
  );
}

function ResponsesView({
  responses,
  loading,
  expandedQuestions,
  onToggleQuestion,
}: {
  responses?: FocusGroupResponses;
  loading: boolean;
  expandedQuestions: Set<number>;
  onToggleQuestion: (index: number) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Logo className="w-12 h-12 mb-4" spinning />
        <p className="text-sm text-muted-foreground">Loading responses...</p>
      </div>
    );
  }

  if (!responses || responses.questions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <MessageSquare className="w-12 h-12 text-muted mb-4" />
        <p className="text-sm text-muted-foreground">No responses available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {responses.questions.map((q, qIdx) => {
        const isExpanded = expandedQuestions.has(qIdx);

        return (
          <motion.div
            key={qIdx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: qIdx * 0.1 }}
            className="border border-border rounded-figma-card overflow-hidden bg-card shadow-sm hover:shadow-lg transition-all"
          >
            {/* Question Header */}
            <button
              onClick={() => onToggleQuestion(qIdx)}
              className="w-full px-6 py-4 flex items-center justify-between bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm">
                  Q{qIdx + 1}
                </div>
                <div className="text-left">
                  <h4 className="text-base font-normal text-foreground leading-[16px]">{q.question}</h4>
                  <p className="text-xs text-muted-foreground mt-0.5">{q.responses.length} responses</p>
                </div>
              </div>
              {isExpanded ? (
                <ChevronUp className="w-5 h-5 text-muted-foreground" />
              ) : (
                <ChevronDown className="w-5 h-5 text-muted-foreground" />
              )}
            </button>

            {/* Responses */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="border-t border-border"
                >
                  <div className="p-4 space-y-3">
                    {q.responses.map((r, rIdx) => (
                      <motion.div
                        key={`${r.persona_id}-${rIdx}`}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: rIdx * 0.05 }}
                        className="p-4 rounded-figma-inner bg-muted/30 border border-border hover:border-primary-200 hover:shadow-sm transition-all"
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0">
                            <div className="w-10 h-10 rounded-full bg-brand flex items-center justify-center text-white font-bold text-sm shadow-md">
                              {rIdx + 1}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-1 rounded">
                                {r.persona_id.slice(0, 8)}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {formatDate(r.created_at)}
                              </span>
                            </div>
                            <p className="text-sm text-foreground leading-relaxed">
                              {r.response || <span className="italic text-muted-foreground">No response recorded</span>}
                            </p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
}
