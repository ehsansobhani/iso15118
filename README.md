# iso15118

EV shared fast charging simulator using the `iso15118` Python package. The web UI models the
DC cabinet, MUX switching matrix, EV fleet, ISO 15118 server scheduler, and data lake logging
shown in the provided diagram.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://localhost:8000>.

## Features

- **DC cabinet**: Configure the number of DC lines, per-line power, and DC bus voltage.
- **MUX**: Adjust switch latency, inputs/outputs, and output enable states.
- **EV fleet**: Set fleet size, initial SOC, dwell time, and urgency level.
- **ISO 15118 server**: Scheduler picks EVs every interval based on SOC, wait time, and urgency.
- **Data lake**: Query and download session history as CSV.
