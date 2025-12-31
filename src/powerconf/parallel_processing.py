import multiprocessing

def mkmsg(t,p):
    return {'type':t,'payload':p}


class BatchJobController:
    """
    A class for managing batch jobs.
    
    target should be a 'job server', a function that runs indefinatly while listening
    for messages and stops when it recieves a "stop" message (i.e. a string with the text stop).

    Jobs are sent to the job server from the `run_jobs(self,jobs)` method. Each item in the `jobs`
    list is sent to the job server as "as is". The job server and the caller of `run_jobs(self,jobs)`
    are responsile for coordinating message types.
    """
    def __init__(self,target,njobs=None):
        self.njobs = njobs if njobs is not None else multiprocessing.cpu_count()
        self.procs = []
        self.links = []
        for i in range(self.njobs):
            parent_link,child_link = multiprocessing.Pipe()
            self.links.append(parent_link)
            p = multiprocessing.Process(target=target, args=(child_link,))
            p.start()
            self.procs.append(p)

    def run_jobs(self,jobs):
      '''Submit jobs to the task server, collect results, and return them in a list.'''
      running = [-1]*len(self.procs)
      results = [None]*len(jobs)
      while len(jobs) > 0 or sum(running) > -len(running):
          for i,link in enumerate(self.links):
              if len(jobs) > 0 and running[i] < 0:
                  link.send( jobs.pop())
                  running[i] = len(jobs)
              if link.poll():
                  msg = link.recv()
                  results[running[i]] = msg
                  running[i] = -1
      return results
    
    def stop(self):
      for link in self.links:
          link.send("stop")

    def wait(self):
      for p in self.procs:
          p.join()
