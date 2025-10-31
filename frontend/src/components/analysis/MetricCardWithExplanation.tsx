import { useState } from 'react';
import { Info, TrendingUp, TrendingDown, AlertCircle, CheckCircle2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

interface MetricExplanation {
  name: string;
  value: string;
  interpretation: string;
  context: string;
  action: string;
  benchmark?: string | null;
}

interface MetricCardProps {
  metricKey: string;
  explanation: MetricExplanation;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  icon?: React.ReactNode;
  compact?: boolean;
}

const getVariantStyles = (variant: string) => {
  switch (variant) {
    case 'success':
      return {
        bg: 'from-green-50 to-emerald-50',
        border: 'border-green-200',
        text: 'text-green-900',
        badge: 'bg-green-100 text-green-800',
        icon: 'text-green-600',
      };
    case 'warning':
      return {
        bg: 'from-yellow-50 to-amber-50',
        border: 'border-yellow-200',
        text: 'text-yellow-900',
        badge: 'bg-yellow-100 text-yellow-800',
        icon: 'text-yellow-600',
      };
    case 'danger':
      return {
        bg: 'from-red-50 to-rose-50',
        border: 'border-red-200',
        text: 'text-red-900',
        badge: 'bg-red-100 text-red-800',
        icon: 'text-red-600',
      };
    default:
      return {
        bg: 'from-slate-50 to-gray-50',
        border: 'border-slate-200',
        text: 'text-slate-900',
        badge: 'bg-slate-100 text-slate-800',
        icon: 'text-slate-600',
      };
  }
};

const getVariantIcon = (variant: string) => {
  switch (variant) {
    case 'success':
      return <CheckCircle2 className="w-5 h-5" />;
    case 'warning':
      return <AlertCircle className="w-5 h-5" />;
    case 'danger':
      return <TrendingDown className="w-5 h-5" />;
    default:
      return <TrendingUp className="w-5 h-5" />;
  }
};

export function MetricCardWithExplanation({
  metricKey: _metricKey,
  explanation,
  variant = 'default',
  icon,
  compact = false,
}: MetricCardProps) {
  const { t } = useTranslation('analysis');
  const [isExpanded, setIsExpanded] = useState(false);
  const styles = getVariantStyles(variant);

  if (compact) {
    return (
      <div className={`relative group`}>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`w-full text-left p-4 rounded-xl border-2 bg-gradient-to-br ${styles.bg} ${styles.border} hover:shadow-md transition-all duration-200`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className={`${styles.icon}`}>
                {icon || getVariantIcon(variant)}
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500 font-semibold">
                  {explanation.name}
                </p>
                <p className={`text-xl font-bold ${styles.text} mt-1`}>
                  {explanation.value}
                </p>
              </div>
            </div>
            <button
              className={`p-1.5 rounded-lg hover:bg-white/50 transition-colors ${styles.icon}`}
            >
              <Info className="w-4 h-4" />
            </button>
          </div>

          {explanation.benchmark && (
            <div className={`mt-3 text-xs px-2 py-1 rounded-md inline-block ${styles.badge}`}>
              {explanation.benchmark}
            </div>
          )}
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="absolute z-10 mt-2 w-full min-w-[400px] p-4 bg-white rounded-xl border-2 border-slate-200 shadow-xl"
            >
              <div className="space-y-3">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 font-semibold mb-1">
                    What it means
                  </p>
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {explanation.interpretation}
                  </p>
                </div>

                <div className="border-t border-slate-200 pt-3">
                  <p className="text-xs uppercase tracking-wide text-slate-500 font-semibold mb-1">
                    Why it matters
                  </p>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    {explanation.context}
                  </p>
                </div>

                <div className="border-t border-slate-200 pt-3">
                  <p className="text-xs uppercase tracking-wide text-primary-600 font-semibold mb-1">
                    Recommended Action
                  </p>
                  <p className="text-sm text-slate-700 leading-relaxed font-medium">
                    {explanation.action}
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }

  // Full card version
  return (
    <motion.div
      layout
      className={`rounded-xl border-2 bg-gradient-to-br ${styles.bg} ${styles.border} shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden`}
    >
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-xl bg-white/70 ${styles.icon}`}>
              {icon || getVariantIcon(variant)}
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 font-semibold">
                {explanation.name}
              </p>
              <p className={`text-2xl font-bold ${styles.text} mt-1`}>
                {explanation.value}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`p-2 rounded-lg hover:bg-white/50 transition-colors ${styles.icon}`}
            aria-label={isExpanded ? t('metrics.accessibility.hideDetails') : t('metrics.accessibility.showDetails')}
          >
            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.3 }}
            >
              <Info className="w-5 h-5" />
            </motion.div>
          </button>
        </div>

        {explanation.benchmark && (
          <div className={`mt-3 text-xs px-3 py-1.5 rounded-lg inline-block ${styles.badge} font-medium`}>
            📊 {explanation.benchmark}
          </div>
        )}

        {/* Quick interpretation */}
        <p className="text-sm text-slate-700 mt-3 leading-relaxed">
          {explanation.interpretation}
        </p>
      </div>

      {/* Expandable details */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-5 space-y-4 border-t border-slate-200/50 pt-4">
              {/* Context */}
              <div className="bg-white/60 rounded-lg p-4">
                <div className="flex items-start gap-2 mb-2">
                  <Info className="w-4 h-4 text-slate-600 mt-0.5 flex-shrink-0" />
                  <p className="text-xs uppercase tracking-wide text-slate-600 font-semibold">
                    Why it matters
                  </p>
                </div>
                <p className="text-sm text-slate-700 leading-relaxed">
                  {explanation.context}
                </p>
              </div>

              {/* Action */}
              <div className="bg-primary-50 rounded-lg p-4 border border-primary-200">
                <div className="flex items-start gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-primary-600 mt-0.5 flex-shrink-0" />
                  <p className="text-xs uppercase tracking-wide text-primary-700 font-semibold">
                    Recommended Action
                  </p>
                </div>
                <p className="text-sm text-primary-900 leading-relaxed font-medium">
                  {explanation.action}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Health badge component for overall status
interface HealthBadgeProps {
  status: 'healthy' | 'good' | 'fair' | 'poor';
  score: number;
  label: string;
}

export function HealthBadge({ status, score, label }: HealthBadgeProps) {
  const getStatusStyles = () => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500 text-white';
      case 'good':
        return 'bg-blue-500 text-white';
      case 'fair':
        return 'bg-yellow-500 text-white';
      case 'poor':
        return 'bg-red-500 text-white';
    }
  };

  return (
    <div className="flex items-center gap-3">
      <div className={`px-4 py-2 rounded-full font-bold text-sm ${getStatusStyles()}`}>
        {score.toFixed(1)}/100
      </div>
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">
          Overall Health
        </p>
        <p className="text-lg font-bold text-slate-900">{label}</p>
      </div>
    </div>
  );
}
