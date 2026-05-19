import os
from rq import Queue, Connection
from rq.worker import SimpleWorker
from rq.timeouts import TimerDeathPenalty

from app.core.redis_client import get_redis_connection

LISTEN_QUEUES = ["document_processing"]


def main():
    redis_conn = get_redis_connection()

    print("✅ Worker starting...")
    print(f"✅ Listening on queues: {LISTEN_QUEUES}")

    # Windows-safe:
    # - SimpleWorker (no fork)
    # - TimerDeathPenalty (no SIGALRM)
    SimpleWorker.death_penalty_class = TimerDeathPenalty

    with Connection(redis_conn):
        queues = [Queue(name, connection=redis_conn) for name in LISTEN_QUEUES]
        worker = SimpleWorker(queues, connection=redis_conn)
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()