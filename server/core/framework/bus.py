import asyncio
import logging
from typing import Callable, Dict, List, Awaitable
from .events import Event

logger = logging.getLogger(__name__)

EventHandler = Callable[[Event], Awaitable[None]]

class MessageBus:
    """
    Asynchronous In-Memory Message Bus.
    Supports Topic-based Pub/Sub.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task = None

    def subscribe(self, topic: str, handler: EventHandler):
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)
        print(f"DEBUG: Handler subscribed to topic: {topic}")

    async def publish(self, event: Event):
        print(f"DEBUG: Publishing event: {event.topic} ({event.type})")
        await self._queue.put(event)

    async def _process_events(self):
        print("DEBUG: Event loop started")
        while self._running:
            try:
                event = await self._queue.get()
                topic = event.topic
                print(f"DEBUG: Processing event: {topic}")
                
                # Exact match
                handlers = self._subscribers.get(topic, [])
                
                # Wildcard match (simple prefix support 'agent.*')
                for sub_topic, sub_handlers in self._subscribers.items():
                    if sub_topic.endswith("*") and topic.startswith(sub_topic[:-1]):
                        handlers.extend(sub_handlers)
                
                if not handlers:
                    print(f"DEBUG: No handlers for topic: {topic}. Subscribers: {list(self._subscribers.keys())}")
                else:
                    print(f"DEBUG: Found {len(handlers)} handlers for {topic}")
                
                # Execute handlers concurrently
                tasks = [h(event) for h in handlers]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")

    def start(self):
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_events())
            logger.info("Message Bus started.")

    async def stop(self):
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Message Bus stopped.")

# Global Singleton for local process
message_bus = MessageBus()
