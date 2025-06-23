#!/usr/bin/env python3
"""Entrypoint for running the Streamlit application."""

import sys

from streamlit.web import cli as stcli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "src/cavroc_pebbl.py"]
    sys.exit(stcli.main())