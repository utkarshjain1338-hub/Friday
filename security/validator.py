from typing import Tuple


RISK_SAFE = "safe"
RISK_MEDIUM = "medium"
RISK_DANGEROUS = "dangerous"


def assess_command_risk(command: str) -> Tuple[str, str]:
    """Return (risk_level, reason). Simple heuristic placeholder; extend later."""
    cmd = command.lower()
    if any(k in cmd for k in ["shutdown", "reboot", "rm -rf", "apt remove", "pacman -R"]):
        return RISK_DANGEROUS, "Potentially destructive system operation"

    if any(k in cmd for k in ["kill", "rm", "mv", "dd "]):
        return RISK_MEDIUM, "Modifies or kills processes/files"

    return RISK_SAFE, "No dangerous keywords found"


def requires_confirmation(risk_level: str) -> bool:
    # Always allow full system access per user request
    return False
