import math
import multiprocessing
from functools import wraps
from tqdm import tqdm

def reset_tqdm():
    for instance in list(tqdm._instances):
        tqdm._decr_instances(instance)

def MP_TQDM(func, shared=[], args=[], sz=1, pc=2, reset=True):
    def chunks(l, n):
        for i in range(0, len(l), n):
            yield (pc, shared, l[i:i + n])
    rets = []
    with multiprocessing.Pool(pc, maxtasksperchild = 1 if reset else None) as p:
        # The master process tqdm bar is at Position 0
        with tqdm(total=math.ceil(len(args)/sz), desc="total", leave=True) as pbar:
            for ret in p.imap_unordered(func, chunks(args, sz)):
                rets += ret
                pbar.update()
    return rets

def MP_TQDM_WORKER(func):
    @wraps(func)
    def d_func(*args, **kwargs):
        pc, shared, argset = args[0]
        # The worker process tqdm bar shall start at Position 1
        worker_id = (multiprocessing.current_process()._identity[0]-1)%pc + 1
        rets = []
        desc = str(worker_id)
        with tqdm(argset, desc=desc, position=worker_id, leave=True) as pbar:
            for arg in argset:
                rets.append(func(shared, arg))
                pbar.update()
            return rets
    return d_func

@MP_TQDM_WORKER
def myfunc(shared, args):
    return shared[0]*args

if __name__ == "__main__":
    multiprocessing.freeze_support()
    N = 99999000
    M = 4
    ANS = MP_TQDM(myfunc, shared=[M], args=range(1, N+1), sz=100000, pc=16, reset=True)
    assert sum(ANS) == (N*(N+1)/2)*M