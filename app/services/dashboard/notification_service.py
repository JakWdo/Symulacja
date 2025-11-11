"""
Notification Service - System notifications & alerts

Zarządzanie notyfikacjami:
- Tworzenie notyfikacji (insights ready, focus idle, budget alerts, etc.)
- Oznaczanie jako przeczytane/wykonane
- Pobieranie pending notifications
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserNotification


class NotificationService:
    """Serwis do zarządzania notyfikacjami użytkowników"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: UUID,
        notification_type: str,
        priority: str,
        title: str,
        message: str,
        project_id: UUID | None = None,
        focus_group_id: UUID | None = None,
        action_url: str | None = None,
        action_label: str | None = None,
        expires_at: datetime | None = None,
    ) -> UserNotification:
        """
        Utwórz notyfikację dla użytkownika

        Args:
            user_id: UUID użytkownika
            notification_type: Typ notyfikacji ('insights_ready', 'focus_idle_48h', etc.)
            priority: Priorytet ('high', 'medium', 'low')
            title: Tytuł notyfikacji
            message: Treść notyfikacji
            project_id: UUID projektu (optional)
            focus_group_id: UUID focus group (optional)
            action_url: URL akcji (optional)
            action_label: Label akcji (optional)
            expires_at: Data wygaśnięcia (optional)

        Returns:
            UserNotification: Utworzona notyfikacja
        """
        notification = UserNotification(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            project_id=project_id,
            focus_group_id=focus_group_id,
            action_url=action_url,
            action_label=action_label,
            expires_at=expires_at,
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def mark_as_read(
        self, notification_id: UUID, user_id: UUID
    ) -> UserNotification:
        """
        Oznacz notyfikację jako przeczytaną

        Args:
            notification_id: UUID notyfikacji
            user_id: UUID użytkownika (security check)

        Returns:
            UserNotification: Zaktualizowana notyfikacja
        """
        stmt = select(UserNotification).where(
            and_(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one()

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_as_done(
        self, notification_id: UUID, user_id: UUID
    ) -> UserNotification:
        """
        Oznacz notyfikację jako wykonaną (dismissed)

        Args:
            notification_id: UUID notyfikacji
            user_id: UUID użytkownika (security check)

        Returns:
            UserNotification: Zaktualizowana notyfikacja
        """
        stmt = select(UserNotification).where(
            and_(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one()

        if not notification.is_done:
            notification.is_done = True
            notification.done_at = datetime.utcnow()

            # Auto-mark as read
            if not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 20,
    ) -> list[UserNotification]:
        """
        Pobierz notyfikacje użytkownika

        Args:
            user_id: UUID użytkownika
            unread_only: Tylko nieprzeczytane (default False)
            limit: Maksymalna liczba wyników

        Returns:
            Lista UserNotification
        """
        stmt = (
            select(UserNotification)
            .where(
                and_(
                    UserNotification.user_id == user_id,
                    UserNotification.is_done.is_(False),  # Nie pokazuj dismissed
                )
            )
            .order_by(UserNotification.created_at.desc())
            .limit(limit)
        )

        if unread_only:
            stmt = stmt.where(UserNotification.is_read.is_(False))

        # Filter expired
        now = datetime.utcnow()
        stmt = stmt.where(
            (UserNotification.expires_at.is_(None))
            | (UserNotification.expires_at > now)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_count(self, user_id: UUID) -> int:
        """
        Pobierz liczbę nieprzeczytanych notyfikacji

        Args:
            user_id: UUID użytkownika

        Returns:
            Liczba nieprzeczytanych notyfikacji
        """
        from sqlalchemy import func

        stmt = select(func.count(UserNotification.id)).where(
            and_(
                UserNotification.user_id == user_id,
                UserNotification.is_read.is_(False),
                UserNotification.is_done.is_(False),
            )
        )

        # Filter expired
        now = datetime.utcnow()
        stmt = stmt.where(
            (UserNotification.expires_at.is_(None))
            | (UserNotification.expires_at > now)
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def cleanup_expired(self) -> int:
        """
        Usuń wygasłe notyfikacje (background job)

        Returns:
            Liczba usuniętych notyfikacji
        """
        from sqlalchemy import delete

        now = datetime.utcnow()

        stmt = delete(UserNotification).where(
            and_(
                UserNotification.expires_at.isnot(None),
                UserNotification.expires_at < now,
            )
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount
