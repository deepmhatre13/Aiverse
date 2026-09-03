"""
Notifications & Achievements App

Django app for managing user notifications, achievements, and milestones.

NOTE: This package intentionally does NOT eagerly import ``.services`` or
``.tasks`` at import time. Those modules touch ``models``/``tasks`` and would
otherwise trigger ``AppRegistryNotReady`` during ``django.setup()`` (when the
app registry is not yet populated). Import them explicitly from the
sub-module instead, e.g. ``from notifications.services import NotificationService``.
"""