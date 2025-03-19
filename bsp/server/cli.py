import asyncio
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional
from warnings import warn

import typer
from dotenv import load_dotenv

from bsp.server.main import JobDispatcher


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

app: typer.Typer = typer.Typer()
dispatcher: JobDispatcher = JobDispatcher(connection_uri=os.getenv("MONGO_URI"), id="bsp.server.cli")


@app.command()
def up():
    typer.echo(f"Starting server with mongo listener at: {dispatcher.conn.connection_uri}")
    asyncio.run(dispatcher.run())


@app.command()
def jobs():
    jobs = dispatcher.conn.get_jobs()
    typer.echo(f"Found {len(jobs)} jobs.")
    typer.echo(jobs)



