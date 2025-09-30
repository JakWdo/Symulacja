import { useMemo } from 'react';
import type { Persona, GraphData, GraphNode, GraphLink } from '@/types';

export function useGraphData(personas: Persona[]) {
  const graphData = useMemo<GraphData | null>(() => {
    if (!personas || personas.length === 0) return null;

    const nodes: GraphNode[] = personas.map((persona) => ({
      id: persona.id,
      label: `${persona.gender}, ${persona.age}`,
      type: 'persona',
      data: persona,
      color: getPersonaColor(persona),
      size: 0.8,
    }));

    const links: GraphLink[] = [];

    for (let i = 0; i < personas.length; i++) {
      for (let j = i + 1; j < personas.length; j++) {
        const similarity = calculateSimilarity(personas[i], personas[j]);
        if (similarity > 0.5) {
          links.push({
            source: personas[i].id,
            target: personas[j].id,
            value: similarity,
            type: 'similarity',
          });
        }
      }
    }

    return { nodes, links };
  }, [personas]);

  return graphData;
}


// Helper functions
function calculateSimilarity(p1: Persona, p2: Persona): number {
    let score = 0;
    let factors = 0;
  
    if (p1.age && p2.age) {
      const ageDiff = Math.abs(p1.age - p2.age);
      score += 1 - ageDiff / 100;
      factors++;
    }
  
    if (p1.gender === p2.gender) {
      score += 1;
      factors++;
    }
  
    if (p1.education_level === p2.education_level) {
      score += 1;
      factors++;
    }
  
    if (p1.income_bracket === p2.income_bracket) {
      score += 1;
      factors++;
    }
  
    if (p1.location === p2.location) {
      score += 1;
      factors++;
    }
  
    if (p1.openness !== null && p2.openness !== null) {
      score += 1 - Math.abs(p1.openness - p2.openness);
      factors++;
    }
  
    if (p1.conscientiousness !== null && p2.conscientiousness !== null) {
      score += 1 - Math.abs(p1.conscientiousness - p2.conscientiousness);
      factors++;
    }
    
    if (p1.extraversion !== null && p2.extraversion !== null) {
      score += 1 - Math.abs(p1.extraversion - p2.extraversion);
      factors++;
    }
  
    if (p1.agreeableness !== null && p2.agreeableness !== null) {
      score += 1 - Math.abs(p1.agreeableness - p2.agreeableness);
      factors++;
    }
  
    if (p1.neuroticism !== null && p2.neuroticism !== null) {
      score += 1 - Math.abs(p1.neuroticism - p2.neuroticism);
      factors++;
    }
  
    return factors > 0 ? score / factors : 0;
  }
  
  function getPersonaColor(persona: Persona): string {
    if (persona.openness !== null && persona.openness > 0.7) {
      return '#8b5cf6'; // Purple - high openness
    }
  
    if (persona.extraversion !== null && persona.extraversion > 0.7) {
      return '#f59e0b'; // Amber - high extraversion
    }
  
    if (persona.conscientiousness !== null && persona.conscientiousness > 0.7) {
      return '#10b981'; // Green - high conscientiousness
    }
  
    if (persona.agreeableness !== null && persona.agreeableness > 0.7) {
      return '#06b6d4'; // Cyan - high agreeableness
    }
  
    return '#0ea5e9'; // Default blue
  }