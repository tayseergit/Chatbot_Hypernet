import threading
from collections import defaultdict
import logging

logger = logging.getLogger("lock_manager")

class UserLockManager:
    """
    A utility class to manage per-user threading locks to prevent race conditions.
    When multiple threads try to execute a critical section for the same user concurrently,
    only one will be allowed to proceed at a time.
    """
    def __init__(self):
        self._locks = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()

    def get_lock(self, user_id: str) -> threading.Lock:
        """
        Retrieve or create a threading.Lock specific to the given user ID.
        """
        with self._global_lock:
            return self._locks[str(user_id)]

# Global instance to be used across the application
user_lock_manager = UserLockManager()
