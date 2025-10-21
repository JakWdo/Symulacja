import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { NeedsAndPains, JTBDJob, DesiredOutcome, PainPoint } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, Target, TrendingUp, Quote, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NeedsSectionProps {
  data?: NeedsAndPains | null;
}

/**
 * Komponent pojedynczego Job-to-be-Done
 */
export function JobCard({ job, index }: { job: JTBDJob; index: number }) {
  const priorityColor = job.priority_score
    ? job.priority_score >= 8
      ? 'bg-red-500'
      : job.priority_score >= 6
      ? 'bg-orange-500'
      : job.priority_score >= 4
      ? 'bg-yellow-500'
      : 'bg-green-500'
    : 'bg-gray-500';

  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Card className="border border-border/60 hover:border-primary/40 transition-colors">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start gap-3">
            <div className={cn('w-2 h-2 rounded-full mt-2 flex-shrink-0', priorityColor)} />
            <div className="flex-1">
              <p className="text-sm font-semibold text-foreground/90">{job.job_statement}</p>
              <div className="flex flex-wrap gap-2 mt-2 text-[11px]">
                {typeof job.priority_score === 'number' && (
                  <div className="flex items-center gap-1.5">
                    <span className="text-muted-foreground">Priorytet:</span>
                    <Progress
                      value={job.priority_score * 10}
                      className="h-1.5 w-16"
                    />
                    <Badge variant="outline" className="text-[10px]">
                      {job.priority_score}/10
                    </Badge>
                  </div>
                )}
                {job.frequency && (
                  <Badge variant="secondary" className="text-[10px]">
                    Częstotliwość: {job.frequency}
                  </Badge>
                )}
                {job.difficulty && (
                  <Badge variant="outline" className="text-[10px]">
                    Trudność: {job.difficulty}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Quotes - Collapsible */}
          {job.quotes && job.quotes.length > 0 && (
            <>
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full"
              >
                <Quote className="w-3 h-3" />
                <span>{job.quotes.length} cytat{job.quotes.length > 1 ? 'y' : ''}</span>
                <ChevronDown
                  className={cn(
                    'w-3 h-3 transition-transform ml-auto',
                    isExpanded && 'rotate-180'
                  )}
                />
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-2"
                  >
                    {job.quotes.map((quote, idx) => (
                      <blockquote
                        key={idx}
                        className="text-xs italic text-muted-foreground border-l-2 border-primary/30 pl-3 py-1"
                      >
                        "{quote}"
                      </blockquote>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * Komponent pojedynczego Desired Outcome
 */
export function OutcomeCard({ outcome, index }: { outcome: DesiredOutcome; index: number }) {
  const opportunityLevel =
    typeof outcome.opportunity_score === 'number'
      ? outcome.opportunity_score >= 75
        ? 'Bardzo wysoka'
        : outcome.opportunity_score >= 50
        ? 'Wysoka'
        : outcome.opportunity_score >= 25
        ? 'Średnia'
        : 'Niska'
      : null;

  const opportunityColor =
    typeof outcome.opportunity_score === 'number'
      ? outcome.opportunity_score >= 75
        ? 'text-green-600'
        : outcome.opportunity_score >= 50
        ? 'text-blue-600'
        : outcome.opportunity_score >= 25
        ? 'text-yellow-600'
        : 'text-red-600'
      : 'text-muted-foreground';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Card className="border border-border/60 hover:shadow-sm transition-shadow">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start gap-2">
            <Target className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
            <p className="text-sm font-semibold text-foreground/90">{outcome.outcome_statement}</p>
          </div>

          <div className="space-y-2 text-xs">
            {typeof outcome.opportunity_score === 'number' && (
              <div className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Opportunity Score:</span>
                  <span className={cn('font-bold', opportunityColor)}>
                    {opportunityLevel}
                  </span>
                </div>
                <Progress
                  value={Math.min(Math.max(outcome.opportunity_score, 0), 100)}
                  className="h-2"
                />
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-1">
              {typeof outcome.importance === 'number' && (
                <Badge variant="outline" className="text-[10px]">
                  Ważność: {outcome.importance}/10
                </Badge>
              )}
              {typeof outcome.satisfaction_current_solutions === 'number' && (
                <Badge variant="secondary" className="text-[10px]">
                  Satysfakcja: {outcome.satisfaction_current_solutions}/10
                </Badge>
              )}
              {outcome.is_measurable && (
                <Badge variant="default" className="text-[10px] bg-green-500">
                  Mierzalne
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * Komponent pojedynczego Pain Point
 */
export function PainCard({ pain, index }: { pain: PainPoint; index: number }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const severityColor =
    typeof pain.severity === 'number'
      ? pain.severity >= 8
        ? 'bg-red-500'
        : pain.severity >= 6
        ? 'bg-orange-500'
        : pain.severity >= 4
        ? 'bg-yellow-500'
        : 'bg-green-500'
      : 'bg-gray-500';

  const severityLabel =
    typeof pain.severity === 'number'
      ? pain.severity >= 8
        ? 'Krytyczny'
        : pain.severity >= 6
        ? 'Wysoki'
        : pain.severity >= 4
        ? 'Średni'
        : 'Niski'
      : 'Nieznany';

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
    >
      <Card className="border-2 border-red-200 bg-red-50/40 dark:bg-red-950/20 hover:shadow-md transition-shadow">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1">
              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-semibold text-foreground/90">{pain.pain_title}</p>
                {pain.pain_description && (
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                    {pain.pain_description}
                  </p>
                )}
              </div>
            </div>

            {typeof pain.severity === 'number' && (
              <div className="flex items-center gap-2">
                <div className={cn('w-2 h-2 rounded-full', severityColor)} />
                <Badge variant="destructive" className="text-[10px]">
                  {severityLabel} ({pain.severity}/10)
                </Badge>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2 text-[11px]">
            {pain.frequency && (
              <Badge variant="outline" className="text-[10px] border-red-300">
                Częstość: {pain.frequency}
              </Badge>
            )}
            {typeof pain.percent_affected === 'number' && (
              <Badge variant="secondary" className="text-[10px] bg-red-100 dark:bg-red-900/30">
                Dotyczy {Math.round(pain.percent_affected * 100)}% osób
              </Badge>
            )}
          </div>

          {/* Solutions - Collapsible */}
          {pain.potential_solutions && pain.potential_solutions.length > 0 && (
            <div className="border-t border-red-200 dark:border-red-800 pt-3">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full"
              >
                <TrendingUp className="w-3 h-3" />
                <span>Potencjalne rozwiązania ({pain.potential_solutions.length})</span>
                <ChevronDown
                  className={cn(
                    'w-3 h-3 transition-transform ml-auto',
                    isExpanded && 'rotate-180'
                  )}
                />
              </button>

              <AnimatePresence>
                {isExpanded && (
                  <motion.ul
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-1 mt-2"
                  >
                    {pain.potential_solutions.map((solution, idx) => (
                      <motion.li
                        key={idx}
                        className="text-xs text-foreground/80 flex items-start gap-2"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.05 }}
                      >
                        <span className="text-green-600 dark:text-green-400 mt-0.5">✓</span>
                        <span>{solution}</span>
                      </motion.li>
                    ))}
                  </motion.ul>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Quotes */}
          {pain.quotes && pain.quotes.length > 0 && (
            <div className="space-y-1">
              {pain.quotes.map((quote, idx) => (
                <blockquote
                  key={idx}
                  className="text-xs italic text-muted-foreground border-l-2 border-red-300 dark:border-red-700 pl-3 py-1"
                >
                  "{quote}"
                </blockquote>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function NeedsSection({ data }: NeedsSectionProps) {
  if (!data || (
    data.jobs_to_be_done.length === 0 &&
    data.desired_outcomes.length === 0 &&
    data.pain_points.length === 0
  )) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Brak zidentyfikowanych potrzeb lub pain pointów dla tej persony.
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
      {data.jobs_to_be_done.length > 0 && (
        <section className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <Target className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Jobs-to-be-Done ({data.jobs_to_be_done.length})
            </h3>
          </motion.div>
          <div className="grid gap-3 md:grid-cols-2">
            {data.jobs_to_be_done.map((job, idx) => (
              <JobCard key={idx} job={job} index={idx} />
            ))}
          </div>
        </section>
      )}

      {data.desired_outcomes.length > 0 && (
        <section className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="flex items-center gap-2"
          >
            <TrendingUp className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Desired Outcomes ({data.desired_outcomes.length})
            </h3>
          </motion.div>
          <div className="grid gap-3 md:grid-cols-2">
            {data.desired_outcomes.map((outcome, idx) => (
              <OutcomeCard key={idx} outcome={outcome} index={idx} />
            ))}
          </div>
        </section>
      )}

      {data.pain_points.length > 0 && (
        <section className="space-y-3">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="flex items-center gap-2"
          >
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Pain Points ({data.pain_points.length})
            </h3>
          </motion.div>
          <div className="space-y-3">
            {data.pain_points.map((pain, idx) => (
              <PainCard key={idx} pain={pain} index={idx} />
            ))}
          </div>
        </section>
      )}

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
