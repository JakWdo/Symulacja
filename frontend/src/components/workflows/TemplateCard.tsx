/**
 * TemplateCard - Card component dla pojedynczego workflow template
 *
 * Prezentuje szablon workflow z ikoną, nazwą, opisem, liczbą kroków i szacowanym czasem.
 * Używany w TemplateSelectionDialog.
 */

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { WorkflowTemplate } from '@/types';
import { getTemplateMetadata, type TemplateCategory } from './templateMetadata';

interface TemplateCardProps {
  template: WorkflowTemplate;
  selected?: boolean;
  onClick?: () => void;
}

/**
 * TemplateCard Component
 *
 * @param template - Workflow template data z API
 * @param selected - Czy karta jest zaznaczona
 * @param onClick - Handler kliknięcia
 *
 * @example
 * <TemplateCard
 *   template={template}
 *   selected={selectedTemplateId === template.id}
 *   onClick={() => setSelectedTemplateId(template.id)}
 * />
 */
export function TemplateCard({ template, selected = false, onClick }: TemplateCardProps) {
  const metadata = getTemplateMetadata(template.id);

  if (!metadata) {
    // Fallback jeśli brak metadanych (nie powinno się zdarzyć dla 6 głównych szablonów)
    return (
      <Card
        className={cn(
          'cursor-pointer transition-all hover:shadow-md',
          selected && 'ring-2 ring-primary'
        )}
        onClick={onClick}
      >
        <CardHeader>
          <CardTitle>{template.name}</CardTitle>
          <CardDescription>{template.description}</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const Icon = metadata.icon;

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all hover:shadow-lg hover:scale-[1.02] border-2',
        selected && 'ring-2 ring-primary shadow-lg',
        'group relative overflow-hidden'
      )}
      style={{
        borderColor: selected ? metadata.color : 'transparent',
      }}
      onClick={onClick}
    >
      {/* Gradient background on hover */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity"
        style={{
          background: `linear-gradient(135deg, ${metadata.color}22 0%, transparent 100%)`,
        }}
      />

      <CardHeader className="relative">
        {/* Icon */}
        <div
          className="w-12 h-12 rounded-figma-inner flex items-center justify-center mb-3"
          style={{
            backgroundColor: `${metadata.color}15`,
          }}
        >
          <Icon
            className="w-6 h-6"
            style={{ color: metadata.color }}
          />
        </div>

        {/* Title & Description */}
        <CardTitle className="text-lg">{template.name}</CardTitle>
        <CardDescription className="text-sm line-clamp-2">
          {template.description}
        </CardDescription>
      </CardHeader>

      <CardContent className="relative">
        {/* Metadata badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          {/* Node Count */}
          <Badge variant="secondary" className="text-xs">
            {template.node_count} steps
          </Badge>

          {/* Estimated Time */}
          <Badge variant="secondary" className="text-xs">
            {metadata.estimatedTime}
          </Badge>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1">
          {metadata.tags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="text-xs"
              style={{
                borderColor: `${metadata.color}40`,
                color: metadata.color,
              }}
            >
              {tag}
            </Badge>
          ))}
        </div>

        {/* Category Badge (top-right corner) */}
        <div className="absolute top-0 right-0">
          <Badge
            variant="secondary"
            className="text-xs rounded-tl-none rounded-br-none"
            style={{
              backgroundColor: `${metadata.color}15`,
              color: metadata.color,
            }}
          >
            {template.category}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
