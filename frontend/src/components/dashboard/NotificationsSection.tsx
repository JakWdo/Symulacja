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
          <CardTitle>Notifications</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>Failed to load notifications</AlertDescription>
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
            <CardTitle>Notifications</CardTitle>
            <div className="flex gap-2">
              <Button
                variant={filter === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('all')}
              >
                All
              </Button>
              <Button
                variant={filter === 'unread' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter('unread')}
              >
                Unread
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Bell className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="font-medium text-lg mb-2">All caught up!</p>
            <p className="text-sm text-muted-foreground">
              No {filter === 'unread' ? 'unread' : ''} notifications
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle>Notifications</CardTitle>
            {unreadCount > 0 && (
              <Badge variant="destructive" className="rounded-full">
                {unreadCount}
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant={filter === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('all')}
            >
              All ({notifications.length})
            </Button>
            <Button
              variant={filter === 'unread' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter('unread')}
            >
              Unread ({unreadCount})
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
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
  const config = PRIORITY_CONFIG[notification.priority];
  const Icon = config.icon;

  const handleAction = () => {
    if (notification.action_url) {
      window.location.href = notification.action_url;
    }
  };

  return (
    <Card
      className={`border-l-4 ${
        notification.priority === 'high'
          ? 'border-l-red-500'
          : notification.priority === 'medium'
          ? 'border-l-yellow-500'
          : 'border-l-blue-500'
      } ${!notification.is_read ? 'bg-muted/30' : ''}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={`p-2 rounded-lg ${config.bgColor} flex-shrink-0`}>
            <Icon className={`h-4 w-4 ${config.color}`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {!notification.is_read && (
                <div className="w-2 h-2 rounded-full bg-blue-500" />
              )}
              <Badge variant="secondary" className={config.badgeClass}>
                {notification.priority}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {notification.time_ago}
              </span>
              {notification.is_done && (
                <Badge variant="outline" className="text-xs">
                  <CheckCircle className="h-3 w-3 mr-1" />
                  Done
                </Badge>
              )}
            </div>

            <p className="text-sm font-medium mb-1">{notification.title}</p>
            <p className="text-sm text-muted-foreground mb-3">
              {notification.message}
            </p>

            <div className="flex items-center gap-2">
              {notification.action_label && notification.action_url && (
                <Button size="sm" variant="outline" onClick={handleAction}>
                  {notification.action_label}
                </Button>
              )}

              {!notification.is_read && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onMarkRead(notification.id)}
                >
                  <Check className="h-4 w-4 mr-1" />
                  Mark Read
                </Button>
              )}

              {!notification.is_done && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onMarkDone(notification.id)}
                >
                  <X className="h-4 w-4 mr-1" />
                  Dismiss
                </Button>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
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
