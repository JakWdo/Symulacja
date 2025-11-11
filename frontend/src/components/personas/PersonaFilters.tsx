/**
 * PersonaFilters - Sidebar z filtrami person (płeć, wiek, zawód)
 * Wyodrębnione z Personas.tsx (Zadanie 36)
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/components/ui/utils';
import { useTranslation } from 'react-i18next';

export interface PersonaFiltersProps {
  selectedGenders: string[];
  onGendersChange: (genders: string[]) => void;
  ageRange: [number, number];
  onAgeRangeChange: (range: [number, number]) => void;
  selectedOccupations: string[];
  onOccupationsChange: (occupations: string[]) => void;
  filtersExpanded: boolean;
  onToggleExpanded: () => void;
}

export function PersonaFilters({
  selectedGenders,
  onGendersChange,
  ageRange,
  onAgeRangeChange,
  selectedOccupations,
  onOccupationsChange,
  filtersExpanded,
  onToggleExpanded,
}: PersonaFiltersProps) {
  const { t } = useTranslation('personas');

  const handleClearFilters = () => {
    onGendersChange([]);
    onAgeRangeChange([18, 65]);
    onOccupationsChange([]);
  };

  const handleGenderToggle = (gender: string, checked: boolean) => {
    if (checked) {
      onGendersChange([...selectedGenders, gender]);
    } else {
      onGendersChange(selectedGenders.filter(g => g !== gender));
    }
  };

  return (
    <>
      {/* Mobile Toggle Button */}
      <div className="lg:hidden mb-4">
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-2"
          onClick={onToggleExpanded}
        >
          <Filter className="w-4 h-4" />
          {filtersExpanded ? 'Ukryj filtry' : 'Pokaż filtry'}
          {filtersExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </Button>
      </div>

      {/* Filters Sidebar */}
      <div className={cn(
        "lg:col-span-4",
        !filtersExpanded && "hidden lg:block"
      )}>
        <Card className="bg-card border border-border overflow-y-auto lg:sticky lg:top-6" style={{ maxHeight: '600px' }}>
          <CardHeader>
            <CardTitle className="text-card-foreground flex items-center gap-2">
              <Filter className="w-5 h-5" />
              {t('page.filters.title')}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Gender Filter */}
            <div className="space-y-3">
              <Label className="text-sm">{t('page.filters.gender')}</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="gender-female"
                    checked={selectedGenders.includes('Kobieta')}
                    onCheckedChange={(checked) => handleGenderToggle('Kobieta', !!checked)}
                  />
                  <label htmlFor="gender-female" className="text-sm text-card-foreground">
                    {t('page.filters.genderOptions.female')}
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="gender-male"
                    checked={selectedGenders.includes('Mężczyzna')}
                    onCheckedChange={(checked) => handleGenderToggle('Mężczyzna', !!checked)}
                  />
                  <label htmlFor="gender-male" className="text-sm text-card-foreground">
                    {t('page.filters.genderOptions.male')}
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="gender-other"
                    checked={selectedGenders.includes('Osoba niebinarna')}
                    onCheckedChange={(checked) => handleGenderToggle('Osoba niebinarna', !!checked)}
                  />
                  <label htmlFor="gender-other" className="text-sm text-card-foreground">
                    {t('page.filters.genderOptions.nonbinary')}
                  </label>
                </div>
              </div>
            </div>

            {/* Age Range Filter */}
            <div className="space-y-3">
              <Label className="text-sm">{t('page.filters.ageRange')}</Label>
              <div className="px-2">
                <Slider
                  value={ageRange}
                  onValueChange={(value) => onAgeRangeChange(value as [number, number])}
                  min={18}
                  max={65}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>{ageRange[0]}</span>
                  <span>{ageRange[1]}</span>
                </div>
              </div>
            </div>

            {/* Occupation Filter */}
            <div className="space-y-3">
              <Label className="text-sm">{t('page.filters.occupation')}</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Checkbox id="occupation-tech" />
                  <label htmlFor="occupation-tech" className="text-sm text-card-foreground">
                    {t('page.occupationFilter.technology')} (35%)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="occupation-healthcare" />
                  <label htmlFor="occupation-healthcare" className="text-sm text-card-foreground">
                    {t('page.occupationFilter.healthcare')} (25%)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="occupation-education" />
                  <label htmlFor="occupation-education" className="text-sm text-card-foreground">
                    {t('page.occupationFilter.education')} (20%)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox id="occupation-business" />
                  <label htmlFor="occupation-business" className="text-sm text-card-foreground">
                    {t('page.occupationFilter.business')} (20%)
                  </label>
                </div>
              </div>
            </div>

            {/* Clear Filters Button */}
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={handleClearFilters}
            >
              {t('page.filters.clearFilters')}
            </Button>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
