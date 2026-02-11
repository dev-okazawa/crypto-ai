from pydantic import BaseModel
from typing import List


class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class PredictionPoint(BaseModel):
    time: int
    value: float


class Prediction(BaseModel):
    future: List[PredictionPoint]
    direction: int
    confidence: float
    model_version: str


class Meta(BaseModel):
    symbol: str
    interval: str
    timezone: str
    last_update: int


class ChartResponse(BaseModel):
    meta: Meta
    data: dict
