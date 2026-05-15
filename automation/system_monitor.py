import psutil


def get_cpu_usage() -> float:
    return psutil.cpu_percent(interval=0.5)


def get_memory_usage() -> float:
    return psutil.virtual_memory().percent


def get_battery_status() -> str:
    battery = psutil.sensors_battery()
    if not battery:
        return "No battery information is available."

    status = "charging" if battery.power_plugged else "discharging"
    return f"Battery is {status} at {battery.percent:.0f}%"


def get_temperature_report() -> str:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return "Temperature sensors are not available."

        lines = []
        for name, entries in temps.items():
            for entry in entries:
                if entry.current is not None:
                    lines.append(f"{name} {entry.label or ''}: {entry.current:.1f}°C")
        return "\n".join(lines) if lines else "Temperature data is unavailable."
    except Exception:
        return "Temperature sensors are unavailable on this system."


def get_network_stats() -> str:
    counters = psutil.net_io_counters()
    sent = counters.bytes_sent / 1024 / 1024
    recv = counters.bytes_recv / 1024 / 1024
    return f"Network sent: {sent:.2f} MB, received: {recv:.2f} MB"


def get_system_report() -> str:
    cpu = get_cpu_usage()
    memory = get_memory_usage()
    battery = get_battery_status()
    temperature = get_temperature_report()
    network = get_network_stats()

    return (
        f"CPU usage: {cpu:.1f}%\n"
        f"Memory usage: {memory:.1f}%\n"
        f"{battery}\n"
        f"{network}\n"
        f"{temperature}"
    )
