import subprocess
import os
import json
import uuid
import shutil
import time
import logging
import sys
from threading import Thread
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.DEBUG,
    format="<Computation Queuer> %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("Computation Queuer")
logger.setLevel(logging.DEBUG)

DEPLOY_ENV = os.getenv("DEPLOY_ENV", "dev")


def log_error_to_file(error_msg: str):
    """Write an error message to the log file"""
    try:
        error_log_path = "/tmp/local-queue_errors.log"
        with open(error_log_path, "a", encoding='utf-8') as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] Computation queue error: {error_msg}\n")
            f.write("=" * 80 + "\n")
    except Exception as file_error:
        logger.error(f"Failed to write error log file: {file_error}")


LOCAL_JOB_QUEUE = os.getenv("LOCAL_JOB_QUEUE")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def get_image_name(program_language: str, preset_env: str, is_v2: bool):
    # Normalize program_language to capitalized form
    program_language = program_language.capitalize() if program_language else "Python"
    if is_v2:
        if program_language == "Python":
            if preset_env == "omicairn-py-dyn-env":
                return f"py-local-v2:dyn-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-mebocost-env":
                return f"py-local-v2:mebocost-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-scvelo-env":
                return f"py-local-v2:scvelo-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-sc-env":
                return f"py-local-v2:scanpy-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-scfates-env":
                return f"py-local-v2:scfates-{DEPLOY_ENV}"
            else:
                if preset_env is not None:
                    logger.warning(f"Unsupported preset env: {preset_env}")
                return f"py-local-v2:default-{DEPLOY_ENV}"
        elif program_language == "R":
            if preset_env == "omicairn-r-metaboanalyst-env":
                return f"r-local-v2:metaboanalyst-{DEPLOY_ENV}-latest"
            return f"r-local-v2:{DEPLOY_ENV}-latest"
        elif program_language == "Bash":
            return f"bash-local-v2:{DEPLOY_ENV}-latest"
        else:
            raise ValueError(f"Unsupported program language: {program_language}")
    else:
        if program_language == "Python":
            if preset_env == "omicairn-py-dyn-env":
                return f"py-local:dyn-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-mebocost-env":
                return f"py-local:mebocost-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-scvelo-env":
                return f"py-local:scvelo-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-sc-env":
                return f"py-local:scanpy-{DEPLOY_ENV}"
            elif preset_env == "omicairn-py-scfates-env":
                return f"py-local:scfates-{DEPLOY_ENV}"
            else:
                if preset_env is not None:
                    logger.error(f"Unsupported preset env: {preset_env}")
                return f"py-local:default-{DEPLOY_ENV}"
        elif program_language == "R":
            return f"r-local:{preset_env}"
        elif program_language == "Bash":
            return f"bash-local:{preset_env}"
        else:
            raise ValueError(f"Unsupported program language: {program_language}")


def is_process_ended(process_id):
    try:
        os.kill(process_id, 0)
    except OSError:
        logger.info(
            f"Process {process_id} has ended. Exiting inspection thread.")
        return True
    return False


def is_container_ended(container_id):
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "'{{.State.Running}}'", container_id],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() == "'false'"
    except subprocess.CalledProcessError:
        logger.info(
            f"Container {container_id} has ended or does not exist. Exiting inspection thread.")
        return True


def get_first_job():
    files = os.listdir(LOCAL_JOB_QUEUE)
    logger.info(f"Before Filtering: {files}")
    files = [f for f in files if not f.endswith(".done")]
    logger.info(f"After Filtering: {files}")
    if len(files) == 0:
        return None
    files.sort(key=lambda x: os.path.getctime(
        os.path.join(LOCAL_JOB_QUEUE, x)))
    first_file = files[0]
    job = None
    with open(os.path.join(LOCAL_JOB_QUEUE, first_file), "r") as f:
        job = json.load(f)
    return job


def run_python_job(job):
    computation_id = job["computation_id"]
    previous_computation_id = job["previous_computation_id"]
    program_language = job["program_language"]
    preset_env = job["preset_env"]
    user_id = job.get("user_id", "")
    node_id = job.get("node_id", "")
    is_v2 = job.get("is_v2", False)
    enable_code_agent = job.get("enable_code_agent", False)
    code_agent_model = job.get("code_agent_model", "gpt-4o-mini")
    code_agent_max_attempts = job.get("code_agent_max_attempts", 10)
    enable_visualizer_agent = job.get("enable_visualizer_agent", False)
    visualizer_agent_model = job.get("visualizer_agent_model", "gpt-4o-mini")
    visualizer_demand = job.get("visualizer_demand", "")
    optional_figure_counts = job.get("optional_figure_counts", 3)
    if program_language != "Python":
        raise Exception(
            "Only Python is supported for Python local computation")
    job_id = str(uuid.uuid4()) + "_py_local"

    def inspect_computation_canceled(computation_id, job_id):
        while not is_container_ended(job_id):
            time.sleep(1)
            if os.path.exists(os.path.join("/tmp/job-signal", f"{computation_id}.cancel")):
                logger.info(
                    f"Computation {computation_id} is canceled. Terminating container {job_id}.")
                launch_signal_path = os.path.join(
                    LOCAL_JOB_QUEUE, f"{computation_id}")
                if os.path.exists(launch_signal_path):
                    logger.info(
                        f"Removing job signal file: {launch_signal_path}")
                    os.remove(launch_signal_path)
                cancel_signal_path = os.path.join(
                    "/tmp/job-signal", f"{computation_id}.cancel")
                if os.path.exists(cancel_signal_path):
                    logger.info(
                        f"Removing cancel signal file: {cancel_signal_path}")
                    os.remove(cancel_signal_path)
                subprocess.call(["docker", "stop", job_id])
                break
    image_name = get_image_name(program_language, preset_env, is_v2)
    logger.info(f"Using image: {image_name} for job {job_id}")


    run_proc = subprocess.Popen([
            "docker", "run",
            "--name", job_id,
            "-e", f"COMPUTATION_ID={computation_id}",
            "-e", f"PREVIOUS_COMPUTATION_ID={previous_computation_id}",
            "-e", "PORTER_TYPE=s3-porter",
            "-e", f"BUCKET_NAME={BUCKET_NAME}",
            "-e", f"USER_ID={user_id}",
            "-e", f"NODE_ID={node_id}",
            "-e", f"ENABLE_CODE_AGENT={'1' if enable_code_agent else '0'}",
            "-e", f"CODE_AGENT_MODEL={code_agent_model}",
            "-e", f"CODE_AGENT_MAX_ATTEMPTS={code_agent_max_attempts}",
            "-e", f"ENABLE_VISUALIZER_AGENT={'1' if enable_visualizer_agent else '0'}",
            "-e", f"VISUALIZER_AGENT_MODEL={visualizer_agent_model}",
            "-e", f"VISUALIZER_DEMAND={visualizer_demand}",
            "-e", f"FIGURE_ALTERNATIVE_COUNTS={optional_figure_counts}",
            image_name
        ])

    inspection_thread = Thread(target=inspect_computation_canceled,
                               args=(computation_id, job_id))
    inspection_thread.start()
    run_proc.wait()
    inspection_thread.join()
    logger.info(f"Finished running job {job_id}")
    subprocess.call(["docker", "rm", "-f", job_id])


def run_r_job(job):
    computation_id = job["computation_id"]
    previous_computation_id = job["previous_computation_id"]
    program_language = job["program_language"]
    preset_env = job["preset_env"]
    is_v2 = job.get("is_v2", False)
    user_id = job.get("user_id", "")
    node_id = job.get("node_id", "")
    enable_code_agent = job.get("enable_code_agent", False)
    code_agent_model = job.get("code_agent_model", "gpt-4o-mini")
    code_agent_max_attempts = job.get("code_agent_max_attempts", 10)
    enable_visualizer_agent = job.get("enable_visualizer_agent", False)
    visualizer_agent_model = job.get("visualizer_agent_model", "gpt-4o-mini")
    visualizer_demand = job.get("visualizer_demand", "")
    optional_figure_counts = job.get("optional_figure_counts", 3)

    if program_language != "R":
        raise Exception("Only R is supported for R local computation")
    job_id = str(uuid.uuid4()) + "_r_local"

    def inspect_computation_canceled(computation_id, job_id):
        while not is_container_ended(job_id):
            time.sleep(1)
            if os.path.exists(os.path.join("/tmp/job-signal", f"{computation_id}.cancel")):
                logger.info(
                    f"Computation {computation_id} is canceled. Terminating container {job_id}.")
                launch_signal_path = os.path.join(
                    LOCAL_JOB_QUEUE, f"{computation_id}")
                if os.path.exists(launch_signal_path):
                    logger.info(
                        f"Removing job signal file: {launch_signal_path}")
                    os.remove(launch_signal_path)
                cancel_signal_path = os.path.join(
                    "/tmp/job-signal", f"{computation_id}.cancel")
                if os.path.exists(cancel_signal_path):
                    logger.info(
                        f"Removing cancel signal file: {cancel_signal_path}")
                    os.remove(cancel_signal_path)
                subprocess.call(["docker", "stop", job_id])
                break

    image_name = get_image_name(program_language, preset_env, is_v2)
    logger.info(f"Using image: {image_name} for job {job_id}")

    run_proc = subprocess.Popen([
            "docker", "run",
            "--name", job_id,
            "-e", f"COMPUTATION_ID={computation_id}",
            "-e", f"PREVIOUS_COMPUTATION_ID={previous_computation_id}",
            "-e", "PORTER_TYPE=s3-porter",
            "-e", f"BUCKET_NAME={BUCKET_NAME}",
            "-e", f"USER_ID={user_id}",
            "-e", f"NODE_ID={node_id}",
            "-e", f"ENABLE_CODE_AGENT={'1' if enable_code_agent else '0'}",
            "-e", f"CODE_AGENT_MODEL={code_agent_model}",
            "-e", f"CODE_AGENT_MAX_ATTEMPTS={code_agent_max_attempts}",
            "-e", f"ENABLE_VISUALIZER_AGENT={'1' if enable_visualizer_agent else '0'}",
            "-e", f"VISUALIZER_AGENT_MODEL={visualizer_agent_model}",
            "-e", f"VISUALIZER_DEMAND={visualizer_demand}",
            "-e", f"FIGURE_ALTERNATIVE_COUNTS={optional_figure_counts}",
            image_name
        ])
    inspection_thread = Thread(target=inspect_computation_canceled,
                               args=(computation_id, job_id))
    inspection_thread.start()
    run_proc.wait()
    inspection_thread.join()
    logger.info(f"Finished running job {job_id}")

    subprocess.call(["docker", "rm", "-f", job_id])


def run_bash_job(job):
    computation_id = job["computation_id"]
    previous_computation_id = job["previous_computation_id"]
    program_language = job["program_language"]
    if program_language != "Bash":
        raise Exception("Only Bash is supported for Bash local computation")
    job_id = str(uuid.uuid4()) + "_bash_local"

    def inspect_computation_canceled(computation_id, job_id):
        while not is_container_ended(job_id):
            time.sleep(1)
            if os.path.exists(os.path.join("/tmp/job-signal", f"{computation_id}.cancel")):
                logger.info(
                    f"Computation {computation_id} is canceled. Terminating container {job_id}.")
                launch_signal_path = os.path.join(
                    LOCAL_JOB_QUEUE, f"{computation_id}")
                if os.path.exists(launch_signal_path):
                    logger.info(
                        f"Removing job signal file: {launch_signal_path}")
                    os.remove(launch_signal_path)
                cancel_signal_path = os.path.join(
                    "/tmp/job-signal", f"{computation_id}.cancel")
                if os.path.exists(cancel_signal_path):
                    logger.info(
                        f"Removing cancel signal file: {cancel_signal_path}")
                    os.remove(cancel_signal_path)
                subprocess.call(["docker", "stop", job_id])
                break

    run_proc = subprocess.Popen([
            "docker", "run",
            "--name", job_id,
            "-e", f"COMPUTATION_ID={computation_id}",
            "-e", f"PREVIOUS_COMPUTATION_ID={previous_computation_id}",
            "-e", "PORTER_TYPE=s3-porter",
            "-e", f"BUCKET_NAME={BUCKET_NAME}",
            f"bash-local:{DEPLOY_ENV}"
        ])
    inspection_thread = Thread(target=inspect_computation_canceled,
                               args=(computation_id, job_id))
    inspection_thread.start()
    run_proc.wait()
    inspection_thread.join()
    logger.info(f"Finished running job {job_id}")

    subprocess.call(["docker", "rm", "-f", job_id])


def run_notebook_job(job):
    computation_id = job["computation_id"]
    previous_computation_id = job["previous_computation_id"]
    program_language = job["program_language"]
    user_id = job.get("user_id", "")
    node_id = job.get("node_id", "")
    job_id = str(uuid.uuid4()) + "_notebook_local"

    def inspect_computation_canceled(computation_id, job_id):
        while not is_container_ended(job_id):
            time.sleep(1)
            if os.path.exists(os.path.join("/tmp/job-signal", f"{computation_id}.cancel")):
                logger.info(
                    f"Computation {computation_id} is canceled. Terminating container {job_id}.")
                launch_signal_path = os.path.join(
                    LOCAL_JOB_QUEUE, f"{computation_id}")
                if os.path.exists(launch_signal_path):
                    logger.info(
                        f"Removing job signal file: {launch_signal_path}")
                    os.remove(launch_signal_path)
                cancel_signal_path = os.path.join(
                    "/tmp/job-signal", f"{computation_id}.cancel")
                if os.path.exists(cancel_signal_path):
                    logger.info(
                        f"Removing cancel signal file: {cancel_signal_path}")
                    os.remove(cancel_signal_path)
                subprocess.call(["docker", "stop", job_id])
                break
    image_name = f"ntbk-local-v2:default-{DEPLOY_ENV}"
    logger.info(f"Using image: {image_name} for job {job_id}")


    run_proc = subprocess.Popen([
            "docker", "run",
            "--name", job_id,
            "-e", f"COMPUTATION_ID={computation_id}",
            "-e", f"PREVIOUS_COMPUTATION_ID={previous_computation_id}",
            "-e", "PORTER_TYPE=s3-porter",
            "-e", f"BUCKET_NAME={BUCKET_NAME}",
            "-e", f"USER_ID={user_id}",
            "-e", f"NODE_ID={node_id}",
            image_name
        ])

    inspection_thread = Thread(target=inspect_computation_canceled,
                               args=(computation_id, job_id))
    inspection_thread.start()
    run_proc.wait()
    inspection_thread.join()
    logger.info(f"Finished running job {job_id}")
    subprocess.call(["docker", "rm", "-f", job_id])

def run_job(job):
    logger.info(f"Running job: {job}")
    if job.get("is_notebook", False):
        run_notebook_job(job)
    elif job["program_language"] == "Python":
        run_python_job(job)
    elif job["program_language"] == "R":
        run_r_job(job)
    elif job["program_language"] == "Bash":
        run_bash_job(job)
    else:
        logger.error(
            f"Unsupported program language: {job['program_language']}")
        run_python_job(job)
    logger.info(f"Finished running job: {job}")


def rm_job(job):
    job_path = os.path.join(LOCAL_JOB_QUEUE, str(job["computation_id"]))
    if os.path.exists(job_path):
        shutil.move(job_path, os.path.join(
            LOCAL_JOB_QUEUE, f"{job['computation_id']}.done"))


def handle_canceled_signals(canceled_signals):
    canceled_computation_ids = [
        signal.split(".")[0] for signal in canceled_signals]
    logger.info(f"Canceled computation ids: {canceled_computation_ids}")
    for computation_id in canceled_computation_ids:
        logger.info(f"Handling canceled computation: {computation_id}")
        launch_signal_path = os.path.join(LOCAL_JOB_QUEUE, f"{computation_id}")
        if os.path.exists(launch_signal_path):
            logger.info(f"Removing job signal file: {launch_signal_path}")
            os.remove(launch_signal_path)
        cancel_signal_path = os.path.join(
            "/tmp/job-signal", f"{computation_id}.cancel")
        if os.path.exists(cancel_signal_path):
            logger.info(f"Removing cancel signal file: {cancel_signal_path}")
            os.remove(cancel_signal_path)


def handle_signals():
    signals_folder = "/tmp/job-signal"
    signals = os.listdir(signals_folder)
    canceled_signals = []
    other_signals = []
    for signal in signals:
        if signal.endswith(".cancel"):
            canceled_signals.append(signal)
        else:
            other_signals.append(signal)
    if len(canceled_signals) > 0:
        handle_canceled_signals(canceled_signals)
    # TODO: Handle other signals if needed


def process_job_queue():
    """Scheduled job: process the job queue"""
    try:
        # Handle cancellation signals
        try:
            handle_signals()
        except Exception as e:
            error_msg = f"When Handling Signals. Error handling signals: {e}"
            logger.error(error_msg)
            log_error_to_file(error_msg)

        # Fetch the first job
        try:
            first_job = get_first_job()
        except Exception as e:
            error_msg = f"When Getting First Job. Error getting first job: {e}"
            logger.error(error_msg)
            log_error_to_file(error_msg)
            return

        if first_job is None:
            logger.debug("No jobs in queue")
            return

        logger.info(f"Got first job: {first_job}")

        # Run the job
        try:
            run_job(first_job)
        except Exception as e:
            error_msg = f"When Running Job. Error running job: {e}"
            logger.error(error_msg)
            log_error_to_file(error_msg)

        # Remove the job
        try:
            rm_job(first_job)
        except Exception as e:
            error_msg = f"When Removing Job. Error removing job: {e}"
            logger.error(error_msg)
            log_error_to_file(error_msg)
            
    except Exception as e:
        error_msg = f"Unexpected error in process_job_queue: {e}"
        logger.error(error_msg, exc_info=True)
        log_error_to_file(error_msg)


def main():
    logger.info("Computation Queuer Daemon starting...")
    
    # Wait for system initialization
    logger.info("Waiting for system initialization...")
    time.sleep(20)
    
    # Create the scheduler
    logger.info("=" * 60)
    logger.info("Initializing APScheduler for job queue processing:")
    logger.info("  - Interval: every 2 seconds")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler(
        timezone=os.environ.get('SCHEDULER_TIMEZONE', 'UTC'),
        job_defaults={
            'coalesce': True,  # Merge missed runs
            'max_instances': 1,  # At most one running instance per job
            'misfire_grace_time': 5  # Grace period for a missed run (5 seconds)
        }
    )
    
    # Add the job-queue processing job (every 2 seconds)
    scheduler.add_job(
        func=process_job_queue,
        trigger=IntervalTrigger(seconds=2),
        id='process_job_queue',
        name='Process Job Queue',
        replace_existing=True
    )
    logger.info("✓ Added job queue processing task (every 2 seconds)")
    
    # Start the scheduler (blocking)
    try:
        logger.info("=" * 60)
        logger.info("APScheduler started successfully")
        logger.info("Computation Queuer Daemon is now running...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Computation Queuer Daemon stopped by user")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
