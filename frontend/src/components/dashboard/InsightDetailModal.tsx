/**
 * Insight Detail Modal - Shows detailed insight with evidence trail and provenance
 */

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  CheckCircle,
  Share2,
  Download,
  ThumbsUp,
  Quote,
  FileText,
  Tag,
} from 'lucide-react';
import { useInsightDetail } from '@/hooks/dashboard/useInsightDetail';
import type { InsightEvidenceItem } from '@/types/dashboard';

interface InsightDetailModalProps {
  insightId: string;
  isOpen: boolean;
  onClose: () => void;
}

export function InsightDetailModal({
  insightId,
  isOpen,
  onClose,
}: InsightDetailModalProps) {
  const { data: insight, isLoading, error } = useInsightDetail(insightId);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleAction = async (action: 'share' | 'export' | 'adopt') => {
    setActionLoading(action);
    // TODO: Implement actions (API calls)
    setTimeout(() => {
      setActionLoading(null);
    }, 1000);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        {isLoading ? (
          <InsightDetailSkeleton />
        ) : error ? (
          <div>
            <DialogHeader>
              <DialogTitle>Insight Details</DialogTitle>
            </DialogHeader>
            <Alert variant="destructive" className="mt-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Failed to load insight details</AlertDescription>
            </Alert>
          </div>
        ) : insight ? (
          <>
            <DialogHeader>
              <DialogTitle>Insight Details</DialogTitle>
            </DialogHeader>

            {/* Insight Overview */}
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary">{insight.insight_type}</Badge>
                    <span className="text-xs text-muted-foreground">
                      {insight.time_ago}
                    </span>
                    {insight.is_adopted && (
                      <Badge variant="outline">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Adopted
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    {insight.project_name}
                  </p>
                  <p className="text-base">{insight.insight_text}</p>
                </div>
              </div>

              {/* Metrics */}
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-muted-foreground">Confidence:</span>{' '}
                  <strong>{(insight.confidence_score * 100).toFixed(0)}%</strong>
                </div>
                <div>
                  <span className="text-muted-foreground">Impact:</span>{' '}
                  <strong>{insight.impact_score}/10</strong>
                </div>
                <div>
                  <span className="text-muted-foreground">Evidence:</span>{' '}
                  <strong>{insight.evidence_count} items</strong>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleAction('share')}
                  disabled={!!actionLoading}
                >
                  <Share2 className="h-4 w-4 mr-1" />
                  Share
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleAction('export')}
                  disabled={!!actionLoading}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </Button>
                {!insight.is_adopted && (
                  <Button
                    size="sm"
                    onClick={() => handleAction('adopt')}
                    disabled={!!actionLoading}
                  >
                    <ThumbsUp className="h-4 w-4 mr-1" />
                    Mark as Adopted
                  </Button>
                )}
              </div>

              <Separator />

              {/* Concepts */}
              {insight.concepts && insight.concepts.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Tag className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-semibold text-sm">Key Concepts</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {insight.concepts.map((concept, index) => (
                      <Badge key={index} variant="outline">
                        {concept}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Sentiment */}
              {insight.sentiment && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-sm">Sentiment</h3>
                  </div>
                  <Badge
                    variant="secondary"
                    className={
                      insight.sentiment === 'positive'
                        ? 'bg-green-500/10 text-green-700'
                        : insight.sentiment === 'negative'
                        ? 'bg-red-500/10 text-red-700'
                        : insight.sentiment === 'mixed'
                        ? 'bg-yellow-500/10 text-yellow-700'
                        : 'bg-gray-500/10 text-gray-700'
                    }
                  >
                    {insight.sentiment.charAt(0).toUpperCase() + insight.sentiment.slice(1)}
                  </Badge>
                </div>
              )}

              <Separator />

              {/* Evidence Trail */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Quote className="h-4 w-4 text-muted-foreground" />
                  <h3 className="font-semibold text-sm">Evidence Trail</h3>
                  <span className="text-xs text-muted-foreground">
                    ({insight.evidence.length} items)
                  </span>
                </div>
                <div className="space-y-3">
                  {insight.evidence.map((evidence, index) => (
                    <EvidenceItem key={index} evidence={evidence} />
                  ))}
                </div>
              </div>

              <Separator />

              {/* Provenance */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <h3 className="font-semibold text-sm">Provenance</h3>
                </div>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <div>
                    <span className="font-medium">Model:</span>{' '}
                    {insight.provenance.model_version}
                  </div>
                  <div>
                    <span className="font-medium">Generated:</span>{' '}
                    {new Date(insight.provenance.created_at).toLocaleString()}
                  </div>
                  <div>
                    <span className="font-medium">Prompt Hash:</span>{' '}
                    <code className="text-xs bg-muted px-1 py-0.5 rounded">
                      {insight.provenance.prompt_hash?.slice(0, 16)}...
                    </code>
                  </div>
                  <div>
                    <span className="font-medium">Sources:</span>{' '}
                    {insight.provenance.sources.length} references
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function EvidenceItem({ evidence }: { evidence: InsightEvidenceItem }) {
  const getIcon = () => {
    switch (evidence.type) {
      case 'quote':
        return <Quote className="h-4 w-4" />;
      case 'snippet':
        return <FileText className="h-4 w-4" />;
      case 'concept':
        return <Tag className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex gap-3 p-3 border rounded-lg bg-muted/30">
      <div className="flex-shrink-0 text-muted-foreground mt-0.5">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="outline" className="text-xs">
            {evidence.type}
          </Badge>
          <span className="text-xs text-muted-foreground">{evidence.source}</span>
        </div>
        <p className="text-sm text-foreground/90">{evidence.text}</p>
      </div>
    </div>
  );
}

function InsightDetailSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-48" />
      <Skeleton className="h-20 w-full" />
      <Skeleton className="h-10 w-full" />
      <Separator />
      <Skeleton className="h-32 w-full" />
      <Separator />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}
