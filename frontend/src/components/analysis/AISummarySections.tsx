/**
 * AISummarySections - Sekcje tematyczne AI Summary
 *
 * Wyświetla:
 * - Executive Summary (podsumowanie wykonawcze)
 * - Segment Analysis (analiza segmentów)
 * - Sentiment Narrative (narracja sentymentu)
 *
 * @example
 * <AISummarySections
 *   executiveSummary={summary.executive_summary}
 *   segmentAnalysis={summary.segment_analysis}
 *   sentimentNarrative={summary.sentiment_narrative}
 *   expandedSections={expandedSections}
 *   onToggleSection={toggleSection}
 * />
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Users, TrendingUp, ChevronDown } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTranslation } from 'react-i18next';
import { normalizeMarkdown } from '@/lib/markdown';

interface SectionHeaderProps {
  id: string;
  icon: React.ElementType;
  title: string;
  count?: number;
  isExpanded: boolean;
  onToggle: () => void;
}

function SectionHeader({
  id: _id,
  icon: Icon,
  title,
  count,
  isExpanded,
  onToggle,
}: SectionHeaderProps) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-4 hover:bg-slate-50 rounded-lg transition-colors"
    >
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 text-primary-600" />
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        {count !== undefined && (
          <span className="text-xs px-2 py-1 rounded-full bg-primary-100 text-primary-700 font-medium">
            {count}
          </span>
        )}
      </div>
      <motion.div
        animate={{ rotate: isExpanded ? 180 : 0 }}
        transition={{ duration: 0.2 }}
      >
        <ChevronDown className="w-5 h-5 text-slate-400" />
      </motion.div>
    </button>
  );
}

interface AISummarySectionsProps {
  executiveSummary: string;
  segmentAnalysis: Record<string, string>;
  sentimentNarrative: string;
  expandedSections: Set<string>;
  onToggleSection: (section: string) => void;
}

/**
 * AISummarySections Component
 */
export function AISummarySections({
  executiveSummary,
  segmentAnalysis,
  sentimentNarrative,
  expandedSections,
  onToggleSection,
}: AISummarySectionsProps) {
  const { t } = useTranslation('focusGroups');

  return (
    <>
      {/* Executive Summary */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader
          id="executive"
          icon={Sparkles}
          title={t('analysis.executiveSummary.title')}
          isExpanded={expandedSections.has('executive')}
          onToggle={() => onToggleSection('executive')}
        />
        <AnimatePresence>
          {expandedSections.has('executive') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(executiveSummary)}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Segment Analysis */}
      {Object.keys(segmentAnalysis).length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="segments"
            icon={Users}
            title={t('analysis.segments.title')}
            count={Object.keys(segmentAnalysis).length}
            isExpanded={expandedSections.has('segments')}
            onToggle={() => onToggleSection('segments')}
          />
          <AnimatePresence>
            {expandedSections.has('segments') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {Object.entries(segmentAnalysis).map(([segment, analysis]) => (
                    <div key={segment} className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
                      <h4 className="text-sm font-semibold text-slate-900 mb-2">{segment}</h4>
                      <div className="text-sm text-slate-700 leading-relaxed prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(analysis)}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Sentiment Narrative */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader
          id="sentiment"
          icon={TrendingUp}
          title={t('analysis.aiSummary.sentimentNarrative')}
          isExpanded={expandedSections.has('sentiment')}
          onToggle={() => onToggleSection('sentiment')}
        />
        <AnimatePresence>
          {expandedSections.has('sentiment') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(sentimentNarrative)}</ReactMarkdown>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
