import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { PersonaDetailsResponse } from '@/types';

interface ProfileSectionProps {
  persona: PersonaDetailsResponse;
}

/**
 * Sekcja profilu persony - demografia, wartości i zainteresowania, historia
 *
 * Wyświetla:
 * - Podstawowe dane demograficzne (wiek, płeć, lokalizacja, wykształcenie, dochód)
 * - Wartości i zainteresowania
 * - Background story
 */
export function ProfileSection({ persona }: ProfileSectionProps) {

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
      },
    },
  };

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      {/* Demographics Card */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dane demograficzne</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Wiek</p>
                <p className="text-foreground font-medium">{persona.age} lat</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Płeć</p>
                <p className="text-foreground font-medium">{persona.gender || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Lokalizacja</p>
                <p className="text-foreground font-medium">{persona.location || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Wykształcenie</p>
                <p className="text-foreground font-medium">{persona.education_level || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Dochód</p>
                <p className="text-foreground font-medium">{persona.income_bracket || 'Nie podano'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Zawód</p>
                <p className="text-foreground font-medium">{persona.occupation || 'Nie podano'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Values & Interests Card */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Wartości i zainteresowania</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Values */}
            {persona.values && persona.values.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <p className="text-sm text-muted-foreground mb-2">Wartości</p>
                <div className="flex flex-wrap gap-2">
                  {persona.values.map((value, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.2 + idx * 0.05 }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <Badge
                        variant="outline"
                        className="border-primary text-primary hover:bg-primary/10 transition-colors cursor-default"
                      >
                        {value}
                      </Badge>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Interests */}
            {persona.interests && persona.interests.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <p className="text-sm text-muted-foreground mb-2">Zainteresowania</p>
                <div className="flex flex-wrap gap-2">
                  {persona.interests.map((interest, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.3 + idx * 0.05 }}
                      whileHover={{ scale: 1.05 }}
                    >
                      <Badge
                        variant="secondary"
                        className="bg-secondary/50 hover:bg-secondary transition-colors cursor-default"
                      >
                        {interest}
                      </Badge>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Background Story Card */}
      {persona.background_story && (
        <motion.div variants={itemVariants}>
          <Card className="border-l-4 border-l-primary">
            <CardHeader>
              <CardTitle className="text-base">Historia</CardTitle>
            </CardHeader>
            <CardContent>
              <motion.p
                className="text-sm text-foreground leading-relaxed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                {persona.background_story}
              </motion.p>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
