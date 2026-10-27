"""Backtest module for StockChoice."""
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import calculate_metrics
from src.backtest.signal_evaluator import evaluate_signal_status, EvaluationResult

__all__ = ["BacktestEngine", "calculate_metrics", "evaluate_signal_status", "EvaluationResult"]

