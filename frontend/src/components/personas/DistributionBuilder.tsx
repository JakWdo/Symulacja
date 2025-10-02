/**
 * DistributionBuilder
 * Interactive distribution editor with sliders and live chart preview
 */

import { useState, useMemo, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Plus, Trash2, AlertCircle, Check } from 'lucide-react';

interface DistributionBuilderProps {
  title: string;
  distribution: Record<string, number>;
  onChange: (distribution: Record<string, number>) => void;
  allowCustomCategories?: boolean;
  suggestedCategories?: string[];
  colorScheme?: string;
}

export function DistributionBuilder({
  title,
  distribution,
  onChange,
  allowCustomCategories = false,
  suggestedCategories = [],
  colorScheme = '#8b5cf6',
}: DistributionBuilderProps) {
  const [newCategory, setNewCategory] = useState('');
  const [showAddCategory, setShowAddCategory] = useState(false);

  // Calculate total percentage
  const totalPercentage = useMemo(() => {
    return Object.values(distribution).reduce((sum, val) => sum + val, 0);
  }, [distribution]);

  // Validate distribution (should sum to 1.0 or 100%)
  const isValid = useMemo(() => {
    return Math.abs(totalPercentage - 1.0) < 0.001;
  }, [totalPercentage]);

  // Chart data
  const chartData = useMemo(() => {
    return Object.entries(distribution).map(([category, value]) => ({
      category,
      percentage: value * 100,
    }));
  }, [distribution]);

  // Handle slider change
  const handleSliderChange = useCallback(
    (category: string, newValue: number) => {
      const updated = { ...distribution };
      updated[category] = newValue / 100; // Convert from percentage to decimal
      onChange(updated);
    },
    [distribution, onChange]
  );

  // Handle category removal
  const handleRemoveCategory = useCallback(
    (category: string) => {
      const updated = { ...distribution };
      delete updated[category];
      onChange(updated);
    },
    [distribution, onChange]
  );

  // Handle add custom category
  const handleAddCategory = useCallback(() => {
    if (!newCategory.trim()) return;

    const updated = { ...distribution };
    updated[newCategory.trim()] = 0;
    onChange(updated);
    setNewCategory('');
    setShowAddCategory(false);
  }, [newCategory, distribution, onChange]);

  // Normalize distribution (make it sum to 100%)
  const handleNormalize = useCallback(() => {
    if (totalPercentage === 0) return;

    const normalized: Record<string, number> = {};
    Object.entries(distribution).forEach(([category, value]) => {
      normalized[category] = value / totalPercentage;
    });
    onChange(normalized);
  }, [distribution, totalPercentage, onChange]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-slate-700">{title}</h4>
        <div className="flex items-center gap-2">
          {!isValid && (
            <button
              onClick={handleNormalize}
              className="text-xs px-2 py-1 rounded bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
            >
              Normalize to 100%
            </button>
          )}
          <div
            className={`flex items-center gap-1 text-xs px-2 py-1 rounded ${
              isValid
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}
          >
            {isValid ? (
              <>
                <Check className="w-3 h-3" />
                {(totalPercentage * 100).toFixed(1)}%
              </>
            ) : (
              <>
                <AlertCircle className="w-3 h-3" />
                {(totalPercentage * 100).toFixed(1)}%
              </>
            )}
          </div>
        </div>
      </div>

      {/* Chart Preview */}
      <div className="bg-slate-50 rounded-lg p-2 border border-slate-200">
        <ResponsiveContainer width="100%" height={100}>
          <BarChart data={chartData}>
            <XAxis
              dataKey="category"
              tick={{ fontSize: 9 }}
              angle={-45}
              textAnchor="end"
              height={40}
            />
            <YAxis
              tick={{ fontSize: 9 }}
              label={{ value: '%', angle: -90, position: 'insideLeft', fontSize: 9 }}
            />
            <Tooltip
              formatter={(value: number) => `${value.toFixed(1)}%`}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '0.5rem',
                fontSize: '10px',
              }}
            />
            <Bar dataKey="percentage" fill={colorScheme} radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={colorScheme}
                  opacity={0.7 + (entry.percentage / 100) * 0.3}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Sliders */}
      <div className="space-y-2">
        {Object.entries(distribution).map(([category, value]) => (
          <div key={category} className="space-y-0.5">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-medium text-slate-600">
                {category}
              </label>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-semibold text-slate-700 min-w-[40px] text-right">
                  {(value * 100).toFixed(1)}%
                </span>
                {allowCustomCategories && (
                  <button
                    onClick={() => handleRemoveCategory(category)}
                    className="text-red-500 hover:text-red-700 transition-colors"
                    title="Remove category"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="0.1"
              value={value * 100}
              onChange={(e) => handleSliderChange(category, parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
              style={{
                background: `linear-gradient(to right, ${colorScheme} 0%, ${colorScheme} ${value * 100}%, #e2e8f0 ${value * 100}%, #e2e8f0 100%)`,
              }}
            />
          </div>
        ))}
      </div>

      {/* Add Custom Category */}
      {allowCustomCategories && (
        <div>
          {showAddCategory ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddCategory();
                  if (e.key === 'Escape') {
                    setShowAddCategory(false);
                    setNewCategory('');
                  }
                }}
                placeholder="Enter category name..."
                className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                autoFocus
              />
              <button
                onClick={handleAddCategory}
                disabled={!newCategory.trim()}
                className="px-3 py-2 bg-purple-600 text-white rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Add
              </button>
              <button
                onClick={() => {
                  setShowAddCategory(false);
                  setNewCategory('');
                }}
                className="px-3 py-2 bg-slate-200 text-slate-700 rounded-lg text-sm hover:bg-slate-300"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowAddCategory(true)}
              className="w-full px-3 py-2 border-2 border-dashed border-slate-300 rounded-lg text-sm text-slate-600 hover:border-purple-400 hover:text-purple-600 transition-colors flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Custom Category
            </button>
          )}
        </div>
      )}

      {/* Suggested Categories (if provided) */}
      {!showAddCategory && suggestedCategories.length > 0 && (
        <div className="pt-2 border-t border-slate-200">
          <p className="text-xs text-slate-500 mb-2">Quick add:</p>
          <div className="flex flex-wrap gap-2">
            {suggestedCategories
              .filter((cat) => !distribution[cat])
              .slice(0, 5)
              .map((cat) => (
                <button
                  key={cat}
                  onClick={() => {
                    const updated = { ...distribution };
                    updated[cat] = 0;
                    onChange(updated);
                  }}
                  className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded hover:bg-purple-100 hover:text-purple-700 transition-colors"
                >
                  + {cat}
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
