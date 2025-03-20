import asyncio
import os
import logging

import typer
import uvicorn
from dotenv import load_dotenv

# from s
from backend.dispatch import JobDispatcher


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

gateway_app: typer.Typer = typer.Typer()
server_app: typer.Typer = typer.Typer()
dispatcher: JobDispatcher = JobDispatcher(connection_uri=os.getenv("MONGO_URI"), id="bsp.server.cli")


@gateway_app.command()
def up(host: str = "0.0.0.0", port: str = "3001"):
    # uvicorn.run(app, host=host, port=port)
    typer.echo(f"Starting server on {host}:{port}")


@server_app.command()
def up():
    typer.echo(f"Starting server with mongo listener at: {dispatcher.conn.connection_uri}")
    asyncio.run(dispatcher.run())


@gateway_app.command()
@server_app.command()
def jobs():
    jobs = dispatcher.conn.jobs
    typer.echo(f"Found {len(jobs)} jobs.")
    typer.echo(jobs)



