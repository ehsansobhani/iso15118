from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, validator

import iso15118  # noqa: F401 - required to demonstrate integration with the ISO 15118 package

app = FastAPI(title="EV Shared Fast Charging Simulator")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class DCCabinetConfig(BaseModel):
    num_lines: int = Field(4, ge=1, le=24)
    line_power_kw: float = Field(150.0, ge=10.0, le=2000.0)
    bus_voltage_v: float = Field(800.0, ge=200.0, le=1000.0)


class MuxConfig(BaseModel):
    num_inputs: int = Field(4, ge=1, le=24)
    num_outputs: int = Field(8, ge=1, le=64)
    switch_latency_ms: int = Field(300, ge=0, le=5000)
    outputs_enabled: List[bool] = Field(default_factory=list)

    @validator("outputs_enabled", always=True)
    def ensure_outputs_enabled(cls, value: List[bool], values: Dict) -> List[bool]:
        outputs = values.get("num_outputs", 0)
        if not value:
            return [True] * outputs
        if len(value) != outputs:
            return (value + [True] * outputs)[:outputs]
        return value


class EVFleetConfig(BaseModel):
    ev_count: int = Field(10, ge=1, le=64)
    default_dwell_min: int = Field(45, ge=1, le=240)
    initial_soc_percent: float = Field(32.0, ge=1.0, le=100.0)
    urgency_level: int = Field(2, ge=1, le=5)


class SchedulerConfig(BaseModel):
    interval_sec: int = Field(60, ge=10, le=600)
    w_soc: float = Field(0.55, ge=0.0, le=1.0)
    w_wait: float = Field(0.25, ge=0.0, le=1.0)
    w_urgency: float = Field(0.2, ge=0.0, le=1.0)


class ConfigPayload(BaseModel):
    cabinet: DCCabinetConfig
    mux: MuxConfig
    fleet: EVFleetConfig
    scheduler: SchedulerConfig


@dataclass
class EVSession:
    ev_id: int
    soc_percent: float
    urgency_level: int
    dwell_time_min: int
    status: str = "plugged"
    allocated_power_kw: float = 0.0
    last_selected_at: datetime = field(default_factory=datetime.utcnow)
    last_update: datetime = field(default_factory=datetime.utcnow)

    def wait_seconds(self) -> float:
        return max(0.0, (datetime.utcnow() - self.last_selected_at).total_seconds())


@dataclass
class DataLakeEntry:
    timestamp: datetime
    ev_id: int
    event: str
    allocated_power_kw: float
    soc_percent: float
    mux_port: Optional[int]


class SimulationState:
    def __init__(self) -> None:
        self.cabinet = DCCabinetConfig()
        self.mux = MuxConfig()
        self.fleet = EVFleetConfig()
        self.scheduler = SchedulerConfig()
        self.sessions: Dict[int, EVSession] = {}
        self.data_lake: List[DataLakeEntry] = []
        self._initialize_sessions()

    def _initialize_sessions(self) -> None:
        self.sessions = {}
        for ev_id in range(self.fleet.ev_count):
            self.sessions[ev_id] = EVSession(
                ev_id=ev_id,
                soc_percent=max(5.0, min(100.0, self.fleet.initial_soc_percent - ev_id * 1.5)),
                urgency_level=self.fleet.urgency_level,
                dwell_time_min=self.fleet.default_dwell_min,
            )

    def update_config(self, payload: ConfigPayload) -> None:
        self.cabinet = payload.cabinet
        self.mux = payload.mux
        self.fleet = payload.fleet
        self.scheduler = payload.scheduler
        self._initialize_sessions()

    def schedule_tick(self) -> Dict[str, List[int]]:
        now = datetime.utcnow()
        active_sessions = list(self.sessions.values())
        scores = []
        for session in active_sessions:
            wait_score = min(1.0, session.wait_seconds() / self.scheduler.interval_sec)
            soc_score = max(0.0, (100.0 - session.soc_percent) / 100.0)
            urgency_score = session.urgency_level / 5.0
            score = (
                self.scheduler.w_soc * soc_score
                + self.scheduler.w_wait * wait_score
                + self.scheduler.w_urgency * urgency_score
            )
            scores.append((score, session))

        scores.sort(key=lambda item: item[0], reverse=True)
        selected = scores[: self.cabinet.num_lines]
        selected_ids = {session.ev_id for _, session in selected}

        mux_map: Dict[int, Optional[int]] = {}
        for idx in range(self.cabinet.num_lines):
            mux_map[idx] = None

        for line_index, (_, session) in enumerate(selected):
            mux_map[line_index] = session.ev_id

        for session in active_sessions:
            is_selected = session.ev_id in selected_ids
            session.allocated_power_kw = self.cabinet.line_power_kw if is_selected else 0.0
            session.status = "charging" if is_selected else "plugged"
            if is_selected:
                session.last_selected_at = now
                session.soc_percent = min(100.0, session.soc_percent + 1.5)
            session.last_update = now
            self.data_lake.append(
                DataLakeEntry(
                    timestamp=now,
                    ev_id=session.ev_id,
                    event="power_delivery",
                    allocated_power_kw=session.allocated_power_kw,
                    soc_percent=session.soc_percent,
                    mux_port=next(
                        (port for port, ev_id in mux_map.items() if ev_id == session.ev_id),
                        None,
                    ),
                )
            )

        return {"selected": sorted(selected_ids), "mux_map": mux_map}

    def as_dict(self) -> Dict:
        return {
            "cabinet": self.cabinet.dict(),
            "mux": self.mux.dict(),
            "fleet": self.fleet.dict(),
            "scheduler": self.scheduler.dict(),
            "sessions": [
                {
                    "ev_id": session.ev_id,
                    "soc_percent": session.soc_percent,
                    "urgency_level": session.urgency_level,
                    "dwell_time_min": session.dwell_time_min,
                    "status": session.status,
                    "allocated_power_kw": session.allocated_power_kw,
                    "wait_seconds": session.wait_seconds(),
                }
                for session in self.sessions.values()
            ],
        }

    def query_data_lake(self, ev_id: Optional[int] = None) -> List[DataLakeEntry]:
        if ev_id is None:
            return self.data_lake
        return [entry for entry in self.data_lake if entry.ev_id == ev_id]


state = SimulationState()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/state")
async def get_state() -> JSONResponse:
    return JSONResponse(state.as_dict())


@app.post("/api/config")
async def update_config(payload: ConfigPayload) -> JSONResponse:
    state.update_config(payload)
    return JSONResponse({"status": "ok"})


@app.post("/api/schedule")
async def run_scheduler() -> JSONResponse:
    result = state.schedule_tick()
    return JSONResponse(result)


@app.get("/api/datalake")
async def get_datalake(ev_id: Optional[int] = None) -> JSONResponse:
    entries = state.query_data_lake(ev_id)
    data = [
        {
            "timestamp": entry.timestamp.isoformat(),
            "ev_id": entry.ev_id,
            "event": entry.event,
            "allocated_power_kw": entry.allocated_power_kw,
            "soc_percent": entry.soc_percent,
            "mux_port": entry.mux_port,
        }
        for entry in entries
    ]
    return JSONResponse({"entries": data})


@app.get("/api/datalake/download")
async def download_datalake(ev_id: Optional[int] = None) -> StreamingResponse:
    entries = state.query_data_lake(ev_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["timestamp", "ev_id", "event", "allocated_power_kw", "soc_percent", "mux_port"])
    for entry in entries:
        writer.writerow(
            [
                entry.timestamp.isoformat(),
                entry.ev_id,
                entry.event,
                entry.allocated_power_kw,
                entry.soc_percent,
                entry.mux_port,
            ]
        )
    buffer.seek(0)
    headers = {"Content-Disposition": "attachment; filename=ev_sessions.csv"}
    return StreamingResponse(buffer, media_type="text/csv", headers=headers)
