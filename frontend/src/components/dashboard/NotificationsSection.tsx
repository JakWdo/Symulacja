/**
 * Notifications Section - Displays notifications with read/done actions
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertTriangle,
  Bell,
  CheckCircle,
  AlertCircle,
  Info,
  X,
  Check,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNotifications } from '@/hooks/dashboard/useNotifications';
import { useMarkNotificationRead, useMarkNotificationDone } from '@/hooks/dashboard/useNotificationActions';
import type { Notification } from '@/types/dashboard';

const PRIORITY_CONFIG = {
  high: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-500/10',
    badgeClass: 'bg-red-500 text-white',
  },
  medium: {
    icon: Info,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-500/10',
    badgeClass: 'bg-yellow-500 text-white',
  },
  low: {
    icon: Info,
    color: 'text-blue-600',
    bgColor: 'bg-blue-500/10',
    badgeClass: 'bg-blue-500 text-white',
  },
};

export function NotificationsSection() {
  const { t } = useTranslation('dashboard');
  const [filter, setFilter] = useState<'all' | 'unread'>('unread');
  const { data: notifications, isLoading, error } = useNotifications(
    filter === 'unread',
    20
  );
  const markAsRead = useMarkNotificationRead();
  const markAsDone = useMarkNotificationDone();

  if (isLoading) {
    return <NotificationsSkeleton />;
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t('notifications.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{t('errors.loadNotifications')}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (!notifications || notifications.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{t('notifications.title')}</CardTitle>
            <div className="flex gap-2">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                {t('notifications.filters.all')}
              </Button>
              <Button
                variant={filter === 'unread' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('unread')}
              >
                {t('notifications.filters.unread')}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Bell className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="font-medium text-lg mb-2">{t('notifications.allRead')}</p>
            <p className="text-sm text-muted-foreground">
              {t('notifications.emptyState.description')}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <Card className="border-border rounded-[12px]">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-foreground" />
          <CardTitle className="text-base font-normal text-foreground">{t('notifications.title')}</CardTitle>
        </div>
        <p className="text-base text-muted-foreground">{t('notifications.subtitle')}</p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {notifications.map((notification) => (
            <NotificationCard
              key={notification.id}
              notification={notification}
              onMarkRead={(id) => markAsRead.mutate(id)}
              onMarkDone={(id) => markAsDone.mutate(id)}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function NotificationCard({
  notification,
  onMarkRead,
  onMarkDone,
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onMarkDone: (id: string) => void;
}) {
  const { t } = useTranslation('dashboard');

  // Figma design: border-2 + background colors
  const cardStyles =
    notification.priority === 'high'
      ? 'border-2 border-orange-500/20 dark:border-orange-500/30 bg-orange-500/5 dark:bg-orange-500/10'
      : 'border-2 border-border bg-card';

  const iconBg =
    notification.priority === 'high'
      ? 'bg-red-500/10 dark:bg-red-500/20'
      : 'bg-muted/50';

  return (
    <div className={`${cardStyles} rounded-[8px] p-[13px] flex items-start justify-between gap-4`}>
      {/* Left: Icon + Content */}
      <div className="flex items-start gap-2 flex-1 min-w-0">
        {/* Icon in colored background (24x24px) */}
        <div className={`${iconBg} rounded-[8px] p-[6px] flex-shrink-0`}>
          <AlertCircle className="h-3 w-3 text-foreground" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0 space-y-1">
          <h4 className="text-sm font-normal text-foreground leading-tight">
            {notification.title}
          </h4>
          <p className="text-sm text-muted-foreground leading-tight">
            {notification.message}
          </p>
          <p className="text-xs text-muted-foreground">
            {notification.time_ago}
          </p>
        </div>
      </div>

      {/* Right: Mark Done Button */}
      {!notification.is_done && (
        <Button
          onClick={() => onMarkDone(notification.id)}
          size="sm"
          variant="outline"
          className="border-border h-8 px-3 flex-shrink-0 rounded-[6px]"
        >
          {t('notifications.markDone')}
        </Button>
      )}
    </div>
  );
}

function NotificationsSkeleton() {
  return (
    <Card>
      <CardHeader>
        <Skeleton className="h-6 w-32" />
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
