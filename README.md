# CavrocPebbl

A Streamlit-based input generator for geological FLAC3D models.

## Summary

CavrocPebbl provides an interactive user interface to configure FLAC3D model parameters
(project details, global settings, model construction workflows) and generate ready-to-run
`.f3dat` input files. Built on Pydantic for data validation and Streamlit for rapid web UI.

## Features

- Intuitive Streamlit UI with sidebar navigation (Project, Settings, Model Construction,
  Generate .f3dat)
- Pydantic-based data models (`models.py`, `enums.py`) for structured validation
- Configurable global settings: FLAC3D version, file format, output options (mXrap, GEM4D,
  ParaView)
- Modular model construction steps: stopping, topography, development, area of interest,
  historical mining
- Custom branding and styling with Cavroc logo and CSS
- VS Code debugger integration via `.vscode/launch.json`

## Project Structure

```
.
├── main.py              # Entry point for running the Streamlit app
├── requirements.txt     # Python dependencies
├── src/                 # Application source code
│   ├── CavrocPebbl.py   # Streamlit app definitions and UI layout
│   ├── models.py        # Pydantic data models
│   ├── enums.py         # Enumerations used across the app
│   ├── mappings.py      # Helper mappings and constants
│   ├── logging_config.py# Logging setup
│   ├── bubble_base.py   # Base classes/utilities for UI components
│   └── utils.py         # Utility functions
├── static/              # Assets (logo, project files)
├── .vscode/             # VS Code debug configuration
└── README.md            # Project overview and setup instructions
```

## Setup

Create a Python virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

Use the provided main.py entrypoint:

```bash
python main.py
```

Or run directly with Streamlit:

```bash
streamlit run src/CavrocPebbl.py
```

## Debugging in VSCode

A default debugger configuration is provided in .vscode/launch.json.
Select the "Streamlit: Run" configuration in the Run & Debug panel.