/**
 * AISummaryInsights - Sekcje z insightami AI
 *
 * Wyświetla:
 * - Key Insights (kluczowe spostrzeżenia)
 * - Surprising Findings (zaskakujące odkrycia)
 * - Recommendations (rekomendacje strategiczne)
 *
 * @example
 * <AISummaryInsights
 *   keyInsights={summary.key_insights}
 *   surprisingFindings={summary.surprising_findings}
 *   recommendations={summary.recommendations}
 *   expandedSections={expandedSections}
 *   onToggleSection={toggleSection}
 * />
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Lightbulb, AlertTriangle, Target, ChevronDown } from 'lucide-react';
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

interface AISummaryInsightsProps {
  keyInsights: string[];
  surprisingFindings: string[];
  recommendations: string[];
  expandedSections: Set<string>;
  onToggleSection: (section: string) => void;
}

/**
 * AISummaryInsights Component
 */
export function AISummaryInsights({
  keyInsights,
  surprisingFindings,
  recommendations,
  expandedSections,
  onToggleSection,
}: AISummaryInsightsProps) {
  const { t } = useTranslation('focusGroups');

  return (
    <>
      {/* Key Insights */}
      <div className="floating-panel overflow-hidden">
        <SectionHeader
          id="insights"
          icon={Lightbulb}
          title={t('analysis.keyInsights.title')}
          count={keyInsights.length}
          isExpanded={expandedSections.has('insights')}
          onToggle={() => onToggleSection('insights')}
        />
        <AnimatePresence>
          {expandedSections.has('insights') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-6 pb-6"
            >
              <div className="space-y-3">
                {keyInsights.map((insight, idx) => (
                  <div
                    key={idx}
                    className="flex gap-3 p-4 bg-primary-50 border border-primary-200 rounded-lg"
                  >
                    <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
                      {idx + 1}
                    </div>
                    <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(insight)}</ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Surprising Findings */}
      {surprisingFindings.length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="surprising"
            icon={AlertTriangle}
            title={t('analysis.surprisingFindings.title')}
            count={surprisingFindings.length}
            isExpanded={expandedSections.has('surprising')}
            onToggle={() => onToggleSection('surprising')}
          />
          <AnimatePresence>
            {expandedSections.has('surprising') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {surprisingFindings.map((finding, idx) => (
                    <div
                      key={idx}
                      className="flex gap-3 p-4 bg-accent-50 border border-accent-200 rounded-lg"
                    >
                      <AlertTriangle className="w-5 h-5 text-accent-600 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(finding)}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Strategic Recommendations */}
      {recommendations.length > 0 && (
        <div className="floating-panel overflow-hidden">
          <SectionHeader
            id="recommendations"
            icon={Target}
            title={t('analysis.recommendations.title')}
            count={recommendations.length}
            isExpanded={expandedSections.has('recommendations')}
            onToggle={() => onToggleSection('recommendations')}
          />
          <AnimatePresence>
            {expandedSections.has('recommendations') && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="px-6 pb-6"
              >
                <div className="space-y-3">
                  {recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="flex gap-3 p-4 bg-green-50 border border-green-200 rounded-lg"
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold">
                        {idx + 1}
                      </div>
                      <div className="text-sm text-slate-700 leading-relaxed flex-1 prose prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{normalizeMarkdown(rec)}</ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </>
  );
}
