"""
Task Processor for bl1nk-agent-builder
Processes tasks from the queue
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Task processor for executing tasks"""
    
    def __init__(self, provider_manager, vector_store):
        self.provider_manager = provider_manager
        self.vector_store = vector_store
        self.running = False
        self.worker_task = None
    
    async def start(self):
        """Start the task processor"""
        
        if self.running:
            logger.warning("Task processor is already running")
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._process_tasks())
        
        logger.info("Task processor started")
    
    async def stop(self):
        """Stop the task processor"""
        
        if not self.running:
            return
        
        self.running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Task processor stopped")
    
    async def _process_tasks(self):
        """Main processing loop"""
        
        while self.running:
            try:
                # Process next task (this would come from queue)
                await asyncio.sleep(1)  # Placeholder
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                await asyncio.sleep(5)  # Wait before retrying