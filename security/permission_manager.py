from typing import Dict


class PermissionManager:
    def __init__(self):
        # map of action -> approved boolean
        self._permissions: Dict[str, bool] = {}

    def grant(self, action: str):
        self._permissions[action] = True

    def revoke(self, action: str):
        self._permissions.pop(action, None)

    def is_granted(self, action: str) -> bool:
        return self._permissions.get(action, False)
