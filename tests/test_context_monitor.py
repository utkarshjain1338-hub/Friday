import asyncio
from system_state.context_monitor import ContextMonitor


def test_context_monitor_returns_context():
    monitor = ContextMonitor()
    context = asyncio.run(monitor.get_context())
    assert isinstance(context, dict)
    assert "clipboard" in context
