from celery import shared_task


@shared_task(bind=True, name="dashboard.test_ping_task")
def test_ping_task(self, message="pong"):
    return {
        "status": "ok",
        "message": message,
        "task_id": self.request.id,
    }
