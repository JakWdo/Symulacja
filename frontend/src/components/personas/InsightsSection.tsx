import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, User, Circle } from 'lucide-react';
import type { PersonaAuditEntry } from '@/types';

interface InsightsSectionProps {
  auditLog: PersonaAuditEntry[];
}

/**
 * Sekcja Insights - timeline audytu zmian z animacjami.
 */
export function InsightsSection({ auditLog }: InsightsSectionProps) {
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
      {/* Audit Log Card */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Historia zmian
            </CardTitle>
          </CardHeader>
          <CardContent>
            {auditLog && auditLog.length > 0 ? (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {auditLog.map((entry, idx) => (
                  <motion.div
                    key={idx}
                    className="border-l-2 border-primary/30 pl-4 pb-3 hover:border-primary/60 transition-colors"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + idx * 0.05 }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground capitalize">
                          {entry.action.replace(/_/g, ' ')}
                        </p>
                        {entry.details && Object.keys(entry.details).length > 0 && (
                          <motion.div
                            className="mt-1 text-xs text-muted-foreground space-y-0.5"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.1 + idx * 0.05 + 0.1 }}
                          >
                            {Object.entries(entry.details).map(([key, value]) => (
                              <div key={key} className="flex items-start gap-2">
                                <Circle className="w-1 h-1 mt-1.5 flex-shrink-0 fill-current" />
                                <p>
                                  <span className="font-medium">{key}:</span>{' '}
                                  {typeof value === 'object'
                                    ? JSON.stringify(value)
                                    : String(value)}
                                </p>
                              </div>
                            ))}
                          </motion.div>
                        )}
                      </div>
                      {entry.user_id && (
                        <Badge variant="outline" className="ml-2 text-xs flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {entry.user_id.substring(0, 8)}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(entry.timestamp).toLocaleString('pl-PL')}
                    </p>
                  </motion.div>
                ))}
              </div>
            ) : (
              <motion.div
                className="text-center py-8"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
              >
                <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  Brak historii zmian dla tej persony
                </p>
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
