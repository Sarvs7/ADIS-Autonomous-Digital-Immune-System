\# ADIS — Autonomous Digital Immune System



ADIS is a Windows-based endpoint behaviour-monitoring prototype built with Python.



\## Features



\- Process, network, and configured file-activity monitoring

\- Event collection and processing

\- Behaviour-based rule detection and risk scoring

\- Anomaly-detection pipeline

\- Risk assessment and response-policy handling

\- SQLite storage for events and assessments

\- PySide6 desktop GUI with Start/Stop controls

\- Command console for status, events, and alerts

\- Separate supervised-learning experiment using synthetic data



\## Requirements



\- Windows

\- Python

\- Git



\## Installation



Clone this repository and open its directory in PowerShell.



Create a virtual environment:



```powershell

py -m venv .venv

```



Install dependencies:



```powershell

.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

```



Configure a local `.env` file according to the project's configuration requirements.



\## Run ADIS



```powershell

.\\.venv\\Scripts\\python.exe .\\dashboard\\adis\_gui.py

```



\## Testing



```powershell

.\\.venv\\Scripts\\python.exe -m pytest -q

```



\## Project Structure



\- `sensors/` — Endpoint activity sensors

\- `engine/` — Event processing, detection, risk assessment, and response logic

\- `memory/` — SQLite persistence

\- `dashboard/` — Desktop GUI

\- `models/` — Saved model artifacts

\- `scripts/` — Training, validation, and utility scripts

\- `tests/` — Automated tests

\- `docs/` — Project documentation

\- `data/` — Local data and watched files



\## Safety and Limitations



ADIS is a prototype, not a replacement for commercial antivirus or endpoint detection software.



The current response system uses dry-run behaviour and does not actually terminate processes. The separate 18-feature supervised model is not integrated into the live detection pipeline. Results from synthetic data do not establish real-world malware-detection accuracy.

