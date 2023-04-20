import json
from contextlib import asynccontextmanager

import rq
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from rq.job import Job
from rq.registry import FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry

from rpl_wei.processing.worker import run_workflow_task, task_queue

# TODO: db backup of tasks and results (can be a proper db or just a file)
# TODO logging for server
# TODO consider sub-applications for different parts of the server (e.g. /job, /queue, /data, etc.)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from rpl_wei.processing import DATA_DIR

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(lifespan=lifespan)


@app.post("/job")
async def run_workflow(workflow: UploadFile = File(...), payload: str = Form("{}")):
    workflow_content = await workflow.read()
    workflow_content_str = workflow_content.decode(
        "utf-8"
    )  # Decode the bytes object to a string
    parsed_payload = json.loads(payload)
    try:
        job = task_queue.enqueue(
            run_workflow_task, workflow_content_str, parsed_payload
        )
        jobs_ahead = len(task_queue.jobs)
        return JSONResponse(
            content={
                "status": "success",
                "jobs_ahead": jobs_ahead,
                "job_id": job.get_id(),
            }
        )
    except Exception as e:
        return JSONResponse(content={"status": "failed", "error": str(e)})


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    try:
        job = Job.fetch(job_id, connection=task_queue.connection)
    except rq.exceptions.NoSuchJobError:
        return JSONResponse(content={"status": "failed", "error": "No such job"})

    job_status = job.get_status()
    result = job.result

    return JSONResponse(content={"status": job_status, "result": result})


@app.get("/queue/info")
async def queue_info():
    # TODO: what more information can we get from the queue?
    queued_jobs = task_queue.count
    started_registry = StartedJobRegistry(queue=task_queue)
    started_jobs = len(started_registry)
    finished_registry = FinishedJobRegistry(queue=task_queue)
    finished_jobs = len(finished_registry)
    failed_registry = FailedJobRegistry(queue=task_queue)
    failed_jobs = len(failed_registry)

    return JSONResponse(
        content={
            "queued_jobs": queued_jobs,
            "started_jobs": started_jobs,
            "finished_jobs": finished_jobs,
            "failed_jobs": failed_jobs,
        }
    )
