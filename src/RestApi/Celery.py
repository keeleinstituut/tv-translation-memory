from celery import Celery

from Config.Config import G_CONFIG
from JobApi.SparkTaskDispatcher import SparkTaskDispatcher

redis_url = 'redis://{}:{}/0'.format(G_CONFIG.config['redis']['host'], G_CONFIG.config['redis']['port'])

main_celery = Celery('main',
                broker=redis_url,
                backend=redis_url)
main_celery.autodiscover_tasks()


@main_celery.task(bind=True)
def tm_delete_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Delete')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_import_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Import')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_export_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Export')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_generate_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Generate')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_pos_tag_task(identifier):
    SparkTaskDispatcher().run(identifier, 'PosTag')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_maintain_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Maintain')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def tm_clean_task(identifier):
    SparkTaskDispatcher().run(identifier, 'Clean')
    return {'status': 'Task completed!'}


@main_celery.task(bind=True)
def job_kill_task(job_id):
    SparkTaskDispatcher().run(job_id, 'KillTask')
    return {'status': 'Task completed!'}
