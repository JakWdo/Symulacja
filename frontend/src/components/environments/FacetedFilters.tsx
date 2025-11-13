/**
 * Faceted Filters Component
 *
 * UI do filtrowania zasobów w environment używając faceted tags i DSL.
 * Wspiera:
 * - Chips dla wybranych tagów
 * - DSL query input (advanced mode)
 * - Zapisywanie filtrów
 * - Preview wyników
 */

import React, { useState, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  filterEnvironmentResources,
  createSavedFilter,
  listSavedFilters,
  type FilterResourcesRequest,
  type SavedFilter,
} from '../../api/environments';

interface FacetedFiltersProps {
  environmentId: string;
  resourceType: 'persona' | 'workflow';
  onResultsChange?: (resourceIds: string[]) => void;
  className?: string;
}

// Facety dostępne dla tagów
const FACETS = {
  dem: { label: 'Demografia', color: 'blue' },
  geo: { label: 'Geografia', color: 'green' },
  psy: { label: 'Psychologia', color: 'purple' },
  biz: { label: 'Biznes', color: 'orange' },
  ctx: { label: 'Kontekst', color: 'pink' },
  custom: { label: 'Niestandardowe', color: 'gray' },
};

export const FacetedFilters: React.FC<FacetedFiltersProps> = ({
  environmentId,
  resourceType,
  onResultsChange,
  className = '',
}) => {
  const [dslQuery, setDslQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [advancedMode, setAdvancedMode] = useState(false);
  const [filterName, setFilterName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Fetch saved filters
  const { data: savedFilters = [] } = useQuery({
    queryKey: ['savedFilters', environmentId],
    queryFn: () => listSavedFilters(environmentId),
    enabled: !!environmentId,
  });

  // Filter resources mutation
  const filterMutation = useMutation({
    mutationFn: (request: FilterResourcesRequest) =>
      filterEnvironmentResources(environmentId, request),
    onSuccess: (data) => {
      onResultsChange?.(data.resource_ids);
    },
  });

  // Save filter mutation
  const saveFilterMutation = useMutation({
    mutationFn: (data: { name: string; dsl: string }) =>
      createSavedFilter({
        environment_id: environmentId,
        name: data.name,
        dsl: data.dsl,
      }),
    onSuccess: () => {
      setShowSaveDialog(false);
      setFilterName('');
    },
  });

  // Build DSL from selected tags
  const buildDSL = () => {
    if (advancedMode) {
      return dslQuery;
    }
    // Simple mode: AND all selected tags
    return selectedTags.join(' AND ');
  };

  // Handle filter apply
  const handleApplyFilter = () => {
    const dsl = buildDSL();
    if (!dsl) return;

    filterMutation.mutate({
      dsl,
      resource_type: resourceType,
      limit: 100,
    });
  };

  // Handle tag add
  const handleAddTag = (tag: string) => {
    if (!selectedTags.includes(tag)) {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  // Handle tag remove
  const handleRemoveTag = (tag: string) => {
    setSelectedTags(selectedTags.filter((t) => t !== tag));
  };

  // Handle saved filter load
  const handleLoadSavedFilter = (filter: SavedFilter) => {
    setDslQuery(filter.dsl);
    setAdvancedMode(true);
    handleApplyFilter();
  };

  // Handle save filter
  const handleSaveFilter = () => {
    const dsl = buildDSL();
    if (!dsl || !filterName) return;

    saveFilterMutation.mutate({ name: filterName, dsl });
  };

  // Auto-apply when tags change (simple mode)
  useEffect(() => {
    if (!advancedMode && selectedTags.length > 0) {
      handleApplyFilter();
    }
  }, [selectedTags, advancedMode]);

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Filtry</h3>
          <button
            onClick={() => setAdvancedMode(!advancedMode)}
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            {advancedMode ? 'Tryb prosty' : 'Tryb zaawansowany (DSL)'}
          </button>
        </div>

        {/* Simple Mode - Tag Chips */}
        {!advancedMode && (
          <div className="space-y-3">
            {/* Tag input */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dodaj tag (format: facet:key)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="np. dem:age-25-34"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value) {
                      handleAddTag(e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>

            {/* Selected tags as chips */}
            {selectedTags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {selectedTags.map((tag) => {
                  const [facet] = tag.split(':');
                  const facetConfig = FACETS[facet as keyof typeof FACETS] || FACETS.custom;

                  return (
                    <span
                      key={tag}
                      className={`
                        inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm
                        bg-${facetConfig.color}-100 text-${facetConfig.color}-800
                      `}
                    >
                      <span className="font-medium">{facetConfig.label}:</span>
                      <span>{tag.split(':')[1]}</span>
                      <button
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-1 hover:text-red-600"
                      >
                        ×
                      </button>
                    </span>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Advanced Mode - DSL Query */}
        {advancedMode && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              DSL Query
            </label>
            <textarea
              value={dslQuery}
              onChange={(e) => setDslQuery(e.target.value)}
              placeholder="np. dem:age-25-34 AND geo:warsaw OR psy:high-openness"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              Składnia: facet:key AND/OR/NOT + nawiasy ( )
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleApplyFilter}
            disabled={filterMutation.isPending}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {filterMutation.isPending ? 'Filtrowanie...' : 'Zastosuj filtr'}
          </button>

          <button
            onClick={() => setShowSaveDialog(!showSaveDialog)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Zapisz filtr
          </button>

          {/* Clear button */}
          <button
            onClick={() => {
              setSelectedTags([]);
              setDslQuery('');
              onResultsChange?.([]);
            }}
            className="px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            Wyczyść
          </button>
        </div>

        {/* Save Filter Dialog */}
        {showSaveDialog && (
          <div className="border-t pt-4 mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nazwa filtra
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={filterName}
                onChange={(e) => setFilterName(e.target.value)}
                placeholder="np. Młodzi profesjonaliści z Warszawy"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={handleSaveFilter}
                disabled={!filterName || saveFilterMutation.isPending}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
              >
                Zapisz
              </button>
            </div>
          </div>
        )}

        {/* Saved Filters */}
        {savedFilters.length > 0 && (
          <div className="border-t pt-4 mt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Zapisane filtry</h4>
            <div className="space-y-2">
              {savedFilters.map((filter) => (
                <button
                  key={filter.id}
                  onClick={() => handleLoadSavedFilter(filter)}
                  className="w-full text-left px-3 py-2 bg-gray-50 rounded-md hover:bg-gray-100 text-sm"
                >
                  <div className="font-medium text-gray-900">{filter.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{filter.dsl}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {filterMutation.data && (
          <div className="border-t pt-4 mt-4">
            <div className="text-sm text-gray-600">
              Znaleziono <span className="font-semibold">{filterMutation.data.count}</span> zasobów
            </div>
          </div>
        )}

        {/* Error */}
        {filterMutation.error && (
          <div className="border-t pt-4 mt-4">
            <div className="text-sm text-red-600">
              Błąd: {(filterMutation.error as Error).message}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
