from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime
from collections import defaultdict
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

class Scheduler:
    _instance = None
    d = defaultdict(int)
    jobs = {}
    def __init__(self):
        self.cnt = 0
        self.sched = BackgroundScheduler()
        self.sched.add_listener(self.listener_notification_sent, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        self.sched.start()
        self.job_id = ''

    def __new__(class_):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_)
        return class_._instance

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.sched.shutdown()

    def kill_scheduler(self, job_id):
        try:
            # self.sched.remove_job(job_id)
            self.jobs[job_id].remove()
            self.jobs[job_id] = None
            print(f'@kill_scheduler - scheduler {job_id} has been removed')
        except JobLookupError as err:
            print("fail to stop Scheduler: {err}".format(err=err))
            return

    def setup_ticketing(self, func, args, seconds, next_run_time, job_id):
        print(f"@Scheduler:setup_ticketing - Job '{job_id}' is added to the scheduler")
        self.jobs[job_id] = self.sched.add_job(func, seconds=seconds, trigger="interval", id=job_id, args=args, next_run_time=next_run_time)

    def setup_scanning(self, func, args, seconds, next_run_time, job_id):
        print(f"@Scheduler:setup_scanning - Job '{job_id}' is added to the scheduler")
        self.jobs[job_id] = self.sched.add_job(func, seconds=seconds, trigger="interval", id=job_id, args=args, next_run_time=next_run_time)
    
    def listener_notification_sent(self, event):
        if not event.exception:
            print(f"@listener_notification_sent - listens to event on '{event.job_id}', return value is {event.retval}")
            if event.retval:
                print(f"@listener_notification_sent - ends the task '{event.job_id}' as seats open and it sent the update {datetime.now()}")
                self.kill_scheduler(event.job_id)
        else:
            print(event.exception)
            
if __name__ == '__main__':
    # scheduler.scheduler('cron', "1")
    sc = Scheduler()
    sc.sched.add_listener(sc.listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    while True:
        pass