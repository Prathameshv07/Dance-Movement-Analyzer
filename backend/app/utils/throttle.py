"""
Progress throttling utility
"""

import time
from typing import Callable, Optional


class ProgressThrottler:
    """Throttles progress updates to reduce message frequency"""
    
    def __init__(
        self,
        callback: Callable,
        min_interval: float = 0.5,  # Minimum 0.5s between updates
        key_milestones: list = [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
    ):
        """
        Args:
            callback: Function to call with (progress, message)
            min_interval: Minimum seconds between updates
            key_milestones: Always send these progress values
        """
        self.callback = callback
        self.min_interval = min_interval
        self.key_milestones = set(key_milestones)
        self.last_update_time = 0
        self.last_progress = -1
    
    async def update(self, progress: float, message: str):
        """
        Send progress update only if:
        1. It's a key milestone (0%, 30%, 50%, 70%, 90%, 100%), OR
        2. Enough time has passed since last update
        """
        current_time = time.time()
        
        # Round progress to 2 decimals for milestone comparison
        progress_rounded = round(progress, 2)
        
        # Always send key milestones
        if progress_rounded in self.key_milestones:
            await self.callback(progress, message)
            self.last_update_time = current_time
            self.last_progress = progress
            return
        
        # Send if enough time passed
        if current_time - self.last_update_time >= self.min_interval:
            await self.callback(progress, message)
            self.last_update_time = current_time
            self.last_progress = progress