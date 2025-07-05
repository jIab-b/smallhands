"""Local executor using multiprocessing."""
from multiprocessing import Pool
from .base_executor import BaseExecutor

class LocalExecutor(BaseExecutor):
    def __init__(self, workers=4):
        self.pool = Pool(workers)
        self.tasks = []

    def submit(self, fn, *args, **kwargs):
        async_result = self.pool.apply_async(fn, args, kwargs)
        self.tasks.append(async_result)
        return async_result

    def shutdown(self):
        self.pool.close()
        self.pool.join()
