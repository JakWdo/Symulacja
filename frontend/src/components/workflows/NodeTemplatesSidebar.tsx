/**
 * NodeTemplatesSidebar - Lewy sidebar z dostępnymi node templates
 *
 * Wyświetla node templates pogrupowane według kategorii:
 * - Planning
 * - Data Collection
 * - Analysis
 * - Logic
 *
 * @example
 * <NodeTemplatesSidebar onAddNode={(template) => addNode(template)} />
 */

import { nodeTemplates, NodeTemplate } from './nodeTemplates';

interface NodeTemplatesSidebarProps {
  onAddNode: (template: NodeTemplate) => void;
}

/**
 * NodeTemplatesSidebar Component
 */
export function NodeTemplatesSidebar({
  onAddNode,
}: NodeTemplatesSidebarProps) {
  const categories = ['Planning', 'Data Collection', 'Analysis', 'Logic'] as const;

  return (
    <div className="w-64 border-r border-border bg-background p-4 overflow-y-auto">
      <h3 className="text-sm font-semibold text-foreground mb-4">
        Add Activities
      </h3>

      {categories.map((category) => {
        const categoryNodes = nodeTemplates.filter(
          (t) => t.category === category
        );
        if (categoryNodes.length === 0) return null;

        return (
          <div key={category} className="mb-6">
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wide">
              {category}
            </p>
            <div className="space-y-2">
              {categoryNodes.map((template) => (
                <button
                  key={template.type}
                  onClick={() => onAddNode(template)}
                  className="w-full text-left px-3 py-2 rounded-lg border border-border bg-card hover:bg-accent transition-colors group"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <template.icon className="w-4 h-4 text-foreground group-hover:text-brand-orange transition-colors" />
                    <span className="text-sm font-medium text-foreground group-hover:text-brand-orange transition-colors">
                      {template.label}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {template.description}
                  </p>
                  {template.estimatedTime && (
                    <p className="text-xs text-muted-foreground mt-1">
                      ~{template.estimatedTime}
                    </p>
                  )}
                </button>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
