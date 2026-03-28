from celery import shared_task

from playground.services.ml_engine import run_training


@shared_task
def run_training_task(experiment_id: int):
    return run_training(experiment_id)
