"""Task Scheduler"""
import os
import logging
import multiprocessing as mp
from collections import namedtuple
from .resource_manager import ResourceManager

__all__ = ['TaskScheduler', 'Task']

logger = logging.getLogger(__name__)

Task = namedtuple('Task', 'fn args resources')

class TaskScheduler(object):
    """Basic Task Scheduler w/o Searcher
    """
    LOCK = mp.Lock()
    RESOURCE_MANAGER = ResourceManager()
    M = mp.Manager()
    SCHEDULED_TASKS = []
    FINISHED_TASKS = []

    def add_task(self, task):
        # adding the task
        logger.debug("Adding A New Task {}".format(task))
        TaskScheduler.RESOURCE_MANAGER._request(task.resources)
        if task.resources.num_gpus > 0:
            os.environ['CUDA_VISIBLE_DEVICES'] = str(task.resources.gpu_ids)[1:-1]
        p = mp.Process(target=TaskScheduler._run_task, args=(
                       task.fn, task.args, task.resources,
                       TaskScheduler.RESOURCE_MANAGER))
        p.start()
        with self.LOCK:
            self.SCHEDULED_TASKS.append({'Task': task, 'Process': p})

    @staticmethod
    def _run_task(fn, args, resources, resource_manager):
        """Executing the task
        """
        fn(**args)
        resource_manager._release(resources)

    @classmethod
    def _cleaning_tasks(cls):
        with cls.LOCK:
            for i, task_dick in enumerate(cls.SCHEDULED_TASKS):
                if not task_dick['Process'].is_alive():
                    cls.FINISHED_TASKS.append(cls.SCHEDULED_TASKS.pop(i))

    @classmethod
    def logging_running_tasks(cls):
        # monitoring running tasks
        # pids, running time, resources, etc.
        cls._cleaning_tasks()
        logger.info("Begin Logging Running Tasks.")
        with cls.LOCK:
            for i, task_dic in enumerate(cls.SCHEDULED_TASKS):
                logger.info("{}. PID: {}, Task: {}".format(
                        i, task_dic['Process'].pid, task_dic['Task']))
        logger.info("Finish Logging Running Tasks.")

    # TODO
    @classmethod
    def logging_finished_tasks(cls):
        # logging finished task
        logger.info("Logging Finished Tasks {}.".format(len(cls.FINISHED_TASKS)))
        with cls.LOCK:
            for i, task_dic in enumerate(cls.FINISHED_TASKS):
                logger.info("{}. Task: {}, PID: {}, Resource: {}".format(
                    i, task_dic['Task'], task_dic['Process'].pid, task_dic['Resource']))
