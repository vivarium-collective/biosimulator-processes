import datetime
import subprocess


def format_message(msg, data):
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    RESET = "\033[0m"

    print(f"{BLUE}Gateway Received:\n{RESET} {PURPLE}{data}{RESET}\n")


def spawn_workers():
    try:
        subprocess.run([
            "gunicorn",
            "-w", "4",
            "-k", "uvicorn.workers.UvicornWorker",
            "main:app"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Gunicorn failed with exit code {e.returncode}")
        
        
def timestamp() -> str:
    return str(datetime.datetime.now())

