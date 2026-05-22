"""Diagnostics and performance monitoring."""
import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import os


class MetricType(Enum):
    """Type of metric."""

    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR = "error"
    RESOURCE = "resource"


@dataclass
class Metric:
    """A performance metric."""

    name: str
    value: float
    timestamp: float
    metric_type: MetricType


class DiagnosticsCollector:
    """Collects performance metrics and diagnostics."""

    def __init__(self, max_metrics: int = 1000):
        """
        Initialize diagnostics collector.

        Args:
            max_metrics: Maximum metrics to store
        """
        self.max_metrics = max_metrics
        self.metrics: List[Metric] = []
        self.lock = asyncio.Lock()
        self.start_time = time.time()
        self.error_log: List[Dict[str, Any]] = []

    async def record_metric(self, name: str, value: float, metric_type: MetricType) -> None:
        """
        Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
        """
        metric = Metric(name=name, value=value, timestamp=time.time(), metric_type=metric_type)

        async with self.lock:
            self.metrics.append(metric)
            # Keep only recent metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics :]

    async def record_latency(self, operation: str, duration_ms: float) -> None:
        """Record operation latency."""
        await self.record_metric(f"latency_{operation}", duration_ms, MetricType.LATENCY)

    async def record_error(self, error_type: str, message: str) -> None:
        """Record an error."""
        async with self.lock:
            self.error_log.append(
                {
                    "type": error_type,
                    "message": message,
                    "timestamp": time.time(),
                }
            )
            # Keep only recent errors
            if len(self.error_log) > 100:
                self.error_log = self.error_log[-100:]

    async def get_metrics(self, name_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get metrics, optionally filtered by name."""
        async with self.lock:
            result = []
            for metric in self.metrics:
                if name_filter is None or name_filter in metric.name:
                    result.append(
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "type": metric.metric_type.value,
                            "timestamp": metric.timestamp,
                        }
                    )
            return result

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall diagnostics statistics."""
        async with self.lock:
            uptime = time.time() - self.start_time
            latency_metrics = [m for m in self.metrics if m.metric_type == MetricType.LATENCY]

            latencies = [m.value for m in latency_metrics]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            max_latency = max(latencies) if latencies else 0
            min_latency = min(latencies) if latencies else 0

            return {
                "uptime_seconds": uptime,
                "total_metrics": len(self.metrics),
                "total_errors": len(self.error_log),
                "latency_stats": {
                    "average": avg_latency,
                    "min": min_latency,
                    "max": max_latency,
                },
                "recent_errors": self.error_log[-10:],
            }

    async def clear(self) -> None:
        """Clear all metrics."""
        async with self.lock:
            self.metrics.clear()
            self.error_log.clear()
            logger.info("Diagnostics cleared")

    async def export_to_file(self, filepath: str) -> bool:
        """Export metrics to JSON file."""
        try:
            import json

            async with self.lock:
                data = {
                    "uptime": time.time() - self.start_time,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": m.value,
                            "type": m.metric_type.value,
                            "timestamp": m.timestamp,
                        }
                        for m in self.metrics
                    ],
                    "errors": self.error_log,
                }

            # Write to file in thread
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, lambda: open(filepath, "w").write(json.dumps(data, indent=2))
            )
            logger.info(f"Diagnostics exported to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to export diagnostics: {e}")
            return False


class PerformanceTimer:
    """Context manager for measuring performance."""

    def __init__(self, operation_name: str, collector: Optional[DiagnosticsCollector] = None):
        """
        Initialize timer.

        Args:
            operation_name: Name of operation being timed
            collector: Optional diagnostics collector
        """
        self.operation_name = operation_name
        self.collector = collector
        self.start_time = 0.0

    async def __aenter__(self):
        """Start timer."""
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop timer and record."""
        duration_ms = (time.time() - self.start_time) * 1000

        if self.collector:
            await self.collector.record_latency(self.operation_name, duration_ms)

        logger.debug(f"{self.operation_name} took {duration_ms:.2f}ms")

        if exc_type:
            logger.error(f"{self.operation_name} failed: {exc_type.__name__}")


def setup_logging(log_dir: str = "logs") -> None:
    """
    Setup logging configuration.

    Args:
        log_dir: Directory for log files
    """
    # Create log directory
    os.makedirs(log_dir, exist_ok=True)

    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        os.path.join(log_dir, "friday.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="500 MB",
        retention="7 days",
    )
    logger.add(
        os.path.join(log_dir, "errors.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="500 MB",
        retention="7 days",
    )
    logger.add(
        lambda msg: None,  # Console output
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:{function} - <level>{message}</level>",
        level="INFO",
    )

    logger.info("Logging initialized")


# Global diagnostics collector
_diagnostics: Optional[DiagnosticsCollector] = None


async def get_diagnostics() -> DiagnosticsCollector:
    """Get or create the global diagnostics collector."""
    global _diagnostics
    if _diagnostics is None:
        _diagnostics = DiagnosticsCollector()
    return _diagnostics
