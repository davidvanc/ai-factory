#!/usr/bin/env python3
"""
Submit een taak naar de AI Factory queue.
Gebruik: python submit.py "Maak een Python script dat ..."
"""
import sys
import argparse
from redis import Redis
from rq import Queue


def main():
    parser = argparse.ArgumentParser(description="Submit AI Factory taak")
    parser.add_argument("task", help="Taakomschrijving")
    parser.add_argument("--redis-host", default="192.168.129.20")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--queue", default="factory")
    args = parser.parse_args()

    redis_conn = Redis(host=args.redis_host, port=args.redis_port)
    queue = Queue(args.queue, connection=redis_conn)

    # Importeer de pipeline-functie - we definieren die zo
    from src.workflow.pipeline import run_factory_pipeline

    job = queue.enqueue(
        run_factory_pipeline,
        args.task,
        job_timeout="30m",  # max 30 minuten per job
        result_ttl=86400,   # bewaar resultaat 24u
    )

    print(f"[submit] taak in queue gezet")
    print(f"[submit] job id: {job.id}")
    print(f"[submit] queue lengte: {len(queue)}")
    print(f"[submit] check status met: python status.py {job.id}")


if __name__ == "__main__":
    main()
