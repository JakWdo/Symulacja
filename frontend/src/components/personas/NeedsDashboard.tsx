import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import type { NeedsAndPains } from '@/types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import {
  Target,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  Eye,
  Sparkles
} from 'lucide-react';
import { JobCard, OutcomeCard, PainCard } from './NeedsSection';

interface NeedsDashboardProps {
  data?: NeedsAndPains | null;
}

type DialogType = 'jtbd' | 'pains' | 'outcomes' | null;

/**
 * NeedsDashboard - Dashboard-style view of persona needs and pains
 *
 * Features:
 * - Summary card with key metrics
 * - 3 dashboard cards showing top 3 items (JTBD, Pains, Outcomes)
 * - "Zobacz wszystkie" buttons open full list in dialogs
 * - Color-coded by category (blue/red/green)
 */
export function NeedsDashboard({ data }: NeedsDashboardProps) {
  const [expandedDialog, setExpandedDialog] = useState<DialogType>(null);

  // Calculate summary metrics
  const metrics = useMemo(() => {
    if (!data) {
      return {
        jtbdCount: 0,
        painCount: 0,
        outcomeCount: 0,
        avgJtbdPriority: 0,
        avgPainSeverity: 0,
        avgOutcomeOpportunity: 0,
        highPriorityJtbd: 0,
        criticalPains: 0,
        highValueOutcomes: 0,
      };
    }

    const jtbdCount = data.jobs_to_be_done.length;
    const painCount = data.pain_points.length;
    const outcomeCount = data.desired_outcomes.length;

    const avgJtbdPriority = jtbdCount > 0
      ? data.jobs_to_be_done.reduce((sum, job) => sum + (job.priority_score ?? 0), 0) / jtbdCount
      : 0;

    const avgPainSeverity = painCount > 0
      ? data.pain_points.reduce((sum, pain) => sum + (pain.severity ?? 0), 0) / painCount
      : 0;

    const avgOutcomeOpportunity = outcomeCount > 0
      ? data.desired_outcomes.reduce((sum, outcome) => sum + (outcome.opportunity_score ?? 0), 0) / outcomeCount
      : 0;

    const highPriorityJtbd = data.jobs_to_be_done.filter(job => (job.priority_score ?? 0) >= 7).length;
    const criticalPains = data.pain_points.filter(pain => (pain.severity ?? 0) >= 7).length;
    const highValueOutcomes = data.desired_outcomes.filter(outcome => (outcome.opportunity_score ?? 0) >= 75).length;

    return {
      jtbdCount,
      painCount,
      outcomeCount,
      avgJtbdPriority,
      avgPainSeverity,
      avgOutcomeOpportunity,
      highPriorityJtbd,
      criticalPains,
      highValueOutcomes,
    };
  }, [data]);

  // Sort functions for dialogs
  const sortedJtbd = useMemo(() => {
    if (!data) return [];
    return [...data.jobs_to_be_done].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0));
  }, [data]);

  const sortedPains = useMemo(() => {
    if (!data) return [];
    return [...data.pain_points].sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  }, [data]);

  const sortedOutcomes = useMemo(() => {
    if (!data) return [];
    return [...data.desired_outcomes].sort((a, b) => (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0));
  }, [data]);

  // Empty state
  if (!data || (
    data.jobs_to_be_done.length === 0 &&
    data.pain_points.length === 0 &&
    data.desired_outcomes.length === 0
  )) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <Card>
          <CardContent className="py-10 text-center">
            <Sparkles className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-muted-foreground">
              Brak zidentyfikowanych potrzeb lub pain pointów dla tej persony.
            </p>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Summary Card */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card className="bg-primary/5 border-l-4 border-l-primary">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary/10 rounded-lg shrink-0">
                <BarChart3 className="w-6 h-6 text-primary" />
              </div>
              <div className="flex-1 space-y-3">
                <h3 className="text-base font-bold text-foreground">Podsumowanie Potrzeb</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* JTBD Metric */}
                  {metrics.jtbdCount > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-blue-50/50 dark:bg-blue-950/30 rounded-lg border border-blue-200">
                      <Target className="w-4 h-4 text-blue-600 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-blue-700 dark:text-blue-300 font-medium">Jobs-to-be-Done</p>
                        <p className="text-lg font-bold text-blue-900 dark:text-blue-100">{metrics.jtbdCount}</p>
                        {metrics.highPriorityJtbd > 0 && (
                          <p className="text-xs text-blue-600 dark:text-blue-400">
                            {metrics.highPriorityJtbd} wysokiego priorytetu
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pain Points Metric */}
                  {metrics.painCount > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-red-50/50 dark:bg-red-950/30 rounded-lg border border-red-200">
                      <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-red-700 dark:text-red-300 font-medium">Pain Points</p>
                        <p className="text-lg font-bold text-red-900 dark:text-red-100">{metrics.painCount}</p>
                        {metrics.criticalPains > 0 && (
                          <p className="text-xs text-red-600 dark:text-red-400">
                            {metrics.criticalPains} krytycznych
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Outcomes Metric */}
                  {metrics.outcomeCount > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-green-50/50 dark:bg-green-950/30 rounded-lg border border-green-200">
                      <TrendingUp className="w-4 h-4 text-green-600 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-green-700 dark:text-green-300 font-medium">Desired Outcomes</p>
                        <p className="text-lg font-bold text-green-900 dark:text-green-100">{metrics.outcomeCount}</p>
                        {metrics.highValueOutcomes > 0 && (
                          <p className="text-xs text-green-600 dark:text-green-400">
                            {metrics.highValueOutcomes} wysokiej wartości
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* JTBD Dashboard Card */}
        {data.jobs_to_be_done.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <Card className="border-2 border-blue-200 bg-blue-50/30 dark:bg-blue-950/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-600" />
                  <CardTitle className="text-sm font-bold text-blue-900 dark:text-blue-100">
                    Jobs-to-be-Done
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-blue-700 dark:text-blue-300">
                  Top 3 najważniejsze zadania
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedJtbd.slice(0, 3).map((job, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-blue-200">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{job.job_statement}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof job.priority_score === 'number' && (
                            <Badge variant="outline" className="text-[10px] bg-blue-100 dark:bg-blue-900 border-blue-300">
                              Priorytet: {job.priority_score}/10
                            </Badge>
                          )}
                          {job.frequency && (
                            <Badge variant="secondary" className="text-[10px]">
                              {job.frequency}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {data.jobs_to_be_done.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-blue-300 text-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900/30 mt-3"
                    onClick={() => setExpandedDialog('jtbd')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({data.jobs_to_be_done.length})
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Pain Points Dashboard Card */}
        {data.pain_points.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <Card className="border-2 border-red-200 bg-red-50/30 dark:bg-red-950/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  <CardTitle className="text-sm font-bold text-red-900 dark:text-red-100">
                    Pain Points
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-red-700 dark:text-red-300">
                  Top 3 najbardziej dotkliwe bóle
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedPains.slice(0, 3).map((pain, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-red-200">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{pain.pain_title}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof pain.severity === 'number' && (
                            <Badge variant="destructive" className="text-[10px]">
                              Dotkliwość: {pain.severity}/10
                            </Badge>
                          )}
                          {pain.frequency && (
                            <Badge variant="outline" className="text-[10px] border-red-300">
                              {pain.frequency}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {data.pain_points.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-red-300 text-red-700 hover:bg-red-100 dark:hover:bg-red-900/30 mt-3"
                    onClick={() => setExpandedDialog('pains')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({data.pain_points.length})
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Desired Outcomes Dashboard Card */}
        {data.desired_outcomes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <Card className="border-2 border-green-200 bg-green-50/30 dark:bg-green-950/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <CardTitle className="text-sm font-bold text-green-900 dark:text-green-100">
                    Desired Outcomes
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-green-700 dark:text-green-300">
                  Top 3 pożądane rezultaty
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedOutcomes.slice(0, 3).map((outcome, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-green-200">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{outcome.outcome_statement}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof outcome.opportunity_score === 'number' && (
                            <Badge variant="outline" className="text-[10px] bg-green-100 dark:bg-green-900 border-green-300">
                              Opportunity: {Math.round(outcome.opportunity_score)}
                            </Badge>
                          )}
                          {typeof outcome.importance === 'number' && (
                            <Badge variant="secondary" className="text-[10px]">
                              Ważność: {outcome.importance}/10
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {data.desired_outcomes.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-green-300 text-green-700 hover:bg-green-100 dark:hover:bg-green-900/30 mt-3"
                    onClick={() => setExpandedDialog('outcomes')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({data.desired_outcomes.length})
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      {/* Expanded Dialogs */}
      {/* JTBD Dialog */}
      <Dialog open={expandedDialog === 'jtbd'} onOpenChange={(open) => !open && setExpandedDialog(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-600" />
              Wszystkie Jobs-to-be-Done ({data.jobs_to_be_done.length})
            </DialogTitle>
            <DialogDescription>
              Pełna lista zadań uporządkowana według priorytetu
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 md:grid-cols-2 mt-4">
            {sortedJtbd.map((job, idx) => (
              <JobCard key={idx} job={job} index={idx} />
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Pain Points Dialog */}
      <Dialog open={expandedDialog === 'pains'} onOpenChange={(open) => !open && setExpandedDialog(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Wszystkie Pain Points ({data.pain_points.length})
            </DialogTitle>
            <DialogDescription>
              Pełna lista pain pointów uporządkowana według dotkliwości
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 mt-4">
            {sortedPains.map((pain, idx) => (
              <PainCard key={idx} pain={pain} index={idx} />
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Desired Outcomes Dialog */}
      <Dialog open={expandedDialog === 'outcomes'} onOpenChange={(open) => !open && setExpandedDialog(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-600" />
              Wszystkie Desired Outcomes ({data.desired_outcomes.length})
            </DialogTitle>
            <DialogDescription>
              Pełna lista pożądanych rezultatów uporządkowana według opportunity score
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-3 md:grid-cols-2 mt-4">
            {sortedOutcomes.map((outcome, idx) => (
              <OutcomeCard key={idx} outcome={outcome} index={idx} />
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Metadata Footer */}
      {data.generated_at && (
        <motion.p
          className="text-xs text-muted-foreground border-t pt-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          Wygenerowano {new Date(data.generated_at).toLocaleString('pl-PL')} • {data.generated_by ?? 'LLM'}
        </motion.p>
      )}
    </motion.div>
  );
}
