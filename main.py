#!/usr/bin/env python3
"""Entrypoint for running the Streamlit application."""

import argparse
import os
import sys
from dotenv import load_dotenv
from src.logging_config import get_logger
from streamlit.web import cli as stcli

# Ensure the application source directory is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

# Load environment variables from .env
load_dotenv()

# Parse --prod flag to set application mode
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--prod", action="store_true", help="Run in production mode")
args, remaining_args = parser.parse_known_args()
app_env = "prod" if args.prod else "dev"
os.environ["APP_ENV"] = app_env

logger = get_logger(__name__)
logger.info(f"Starting CavrocPebbl in {app_env} mode")

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "src/cavroc_pebbl.py"] + remaining_args
    sys.exit(stcli.main())