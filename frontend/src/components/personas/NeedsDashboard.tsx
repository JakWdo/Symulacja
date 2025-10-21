import { useState, useMemo, useEffect } from 'react';
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

  const jobsToBeDoneRaw = data?.jobs_to_be_done;
  const painPointsRaw = data?.pain_points;
  const desiredOutcomesRaw = data?.desired_outcomes;

  const jobsToBeDone = useMemo<NeedsAndPains['jobs_to_be_done']>(() => {
    return Array.isArray(jobsToBeDoneRaw) ? jobsToBeDoneRaw : [];
  }, [jobsToBeDoneRaw]);

  const painPoints = useMemo<NeedsAndPains['pain_points']>(() => {
    return Array.isArray(painPointsRaw) ? painPointsRaw : [];
  }, [painPointsRaw]);

  const desiredOutcomes = useMemo<NeedsAndPains['desired_outcomes']>(() => {
    return Array.isArray(desiredOutcomesRaw) ? desiredOutcomesRaw : [];
  }, [desiredOutcomesRaw]);

  // Close any open dialogs when component unmounts or data changes
  useEffect(() => {
    return () => {
      setExpandedDialog(null);
    };
  }, []);

  // Also close dialogs when data changes (e.g., switching personas)
  useEffect(() => {
    setExpandedDialog(null);
  }, [data]);

  // Calculate summary metrics
  const metrics = useMemo(() => {
    const jtbdCount = jobsToBeDone.length;
    const painCount = painPoints.length;
    const outcomeCount = desiredOutcomes.length;

    const avgJtbdPriority = jtbdCount > 0
      ? jobsToBeDone.reduce((sum, job) => sum + (job.priority_score ?? 0), 0) / jtbdCount
      : 0;

    const avgPainSeverity = painCount > 0
      ? painPoints.reduce((sum, pain) => sum + (pain.severity ?? 0), 0) / painCount
      : 0;

    const avgOutcomeOpportunity = outcomeCount > 0
      ? desiredOutcomes.reduce((sum, outcome) => sum + (outcome.opportunity_score ?? 0), 0) / outcomeCount
      : 0;

    const highPriorityJtbd = jobsToBeDone.filter(job => (job.priority_score ?? 0) >= 7).length;
    const criticalPains = painPoints.filter(pain => (pain.severity ?? 0) >= 7).length;
    const highValueOutcomes = desiredOutcomes.filter(outcome => (outcome.opportunity_score ?? 0) >= 75).length;

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
  }, [jobsToBeDone, painPoints, desiredOutcomes]);

  // Sort functions for dialogs
  const sortedJtbd = useMemo(() => {
    if (jobsToBeDone.length === 0) return [];
    return [...jobsToBeDone].sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0));
  }, [jobsToBeDone]);

  const sortedPains = useMemo(() => {
    if (painPoints.length === 0) return [];
    return [...painPoints].sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));
  }, [painPoints]);

  const sortedOutcomes = useMemo(() => {
    if (desiredOutcomes.length === 0) return [];
    return [...desiredOutcomes].sort((a, b) => (b.opportunity_score ?? 0) - (a.opportunity_score ?? 0));
  }, [desiredOutcomes]);

  // Empty state
  if (!data || (
    jobsToBeDone.length === 0 &&
    painPoints.length === 0 &&
    desiredOutcomes.length === 0
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
                    <div className="flex items-center gap-2 p-3 bg-primary/10 dark:bg-primary/20 rounded-lg border border-primary">
                      <Target className="w-4 h-4 text-primary shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-primary font-medium">Jobs-to-be-Done</p>
                        <p className="text-lg font-bold text-foreground">{metrics.jtbdCount}</p>
                        {metrics.highPriorityJtbd > 0 && (
                          <p className="text-xs text-primary/80">
                            {metrics.highPriorityJtbd} wysokiego priorytetu
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Pain Points Metric */}
                  {metrics.painCount > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-secondary/10 dark:bg-secondary/20 rounded-lg border border-secondary">
                      <AlertTriangle className="w-4 h-4 text-secondary shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-secondary font-medium">Pain Points</p>
                        <p className="text-lg font-bold text-foreground">{metrics.painCount}</p>
                        {metrics.criticalPains > 0 && (
                          <p className="text-xs text-secondary/80">
                            {metrics.criticalPains} krytycznych
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Outcomes Metric */}
                  {metrics.outcomeCount > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-accent/10 dark:bg-accent/20 rounded-lg border border-accent">
                      <TrendingUp className="w-4 h-4 text-accent shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-accent font-medium">Desired Outcomes</p>
                        <p className="text-lg font-bold text-foreground">{metrics.outcomeCount}</p>
                        {metrics.highValueOutcomes > 0 && (
                          <p className="text-xs text-accent/80">
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
        {jobsToBeDone.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <Card className="border-2 border-primary bg-primary/10 dark:bg-primary/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-primary" />
                  <CardTitle className="text-sm font-bold text-foreground">
                    Jobs-to-be-Done
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-muted-foreground">
                  Top 3 najważniejsze zadania
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedJtbd.slice(0, 3).map((job, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-primary/30">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{job.job_statement}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof job.priority_score === 'number' && (
                            <Badge variant="outline" className="text-[10px] bg-primary/20 border-primary">
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

                {jobsToBeDone.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-primary text-primary hover:bg-primary/10 mt-3"
                    onClick={() => setExpandedDialog('jtbd')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({jobsToBeDone.length})
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Pain Points Dashboard Card */}
        {painPoints.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.3 }}
          >
            <Card className="border-2 border-secondary bg-secondary/10 dark:bg-secondary/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-secondary" />
                  <CardTitle className="text-sm font-bold text-foreground">
                    Pain Points
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-muted-foreground">
                  Top 3 najbardziej dotkliwe bóle
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedPains.slice(0, 3).map((pain, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-secondary/30">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{pain.pain_title}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof pain.severity === 'number' && (
                            <Badge variant="outline" className="text-[10px] bg-secondary/20 border-secondary">
                              Dotkliwość: {pain.severity}/10
                            </Badge>
                          )}
                          {pain.frequency && (
                            <Badge variant="outline" className="text-[10px]">
                              {pain.frequency}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {painPoints.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-secondary text-secondary hover:bg-secondary/10 mt-3"
                    onClick={() => setExpandedDialog('pains')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({painPoints.length})
                  </Button>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Desired Outcomes Dashboard Card */}
        {desiredOutcomes.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <Card className="border-2 border-accent bg-accent/10 dark:bg-accent/20 flex flex-col h-full">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-accent" />
                  <CardTitle className="text-sm font-bold text-foreground">
                    Desired Outcomes
                  </CardTitle>
                </div>
                <CardDescription className="text-xs text-muted-foreground">
                  Top 3 pożądane rezultaty
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 flex-1">
                {sortedOutcomes.slice(0, 3).map((outcome, idx) => (
                  <div key={idx} className="p-3 bg-white dark:bg-gray-900 rounded-lg border border-accent/30">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-foreground line-clamp-2">{outcome.outcome_statement}</p>
                        <div className="flex items-center gap-2 mt-2">
                          {typeof outcome.opportunity_score === 'number' && (
                            <Badge variant="outline" className="text-[10px] bg-accent/20 border-accent">
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

                {desiredOutcomes.length > 3 && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full border-green-300 text-green-700 hover:bg-green-100 dark:hover:bg-green-900/30 mt-3"
                    onClick={() => setExpandedDialog('outcomes')}
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Zobacz wszystkie ({desiredOutcomes.length})
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
              Wszystkie Jobs-to-be-Done ({jobsToBeDone.length})
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
              Wszystkie Pain Points ({painPoints.length})
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
              Wszystkie Desired Outcomes ({desiredOutcomes.length})
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
