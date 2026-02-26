import asyncio
from modules.agent import JarvisAgent
from modules.voice_engine import VoiceEngine

class Orchestrator:

    def __init__(self):
        self.agent = JarvisAgent(backend="nvidia")
        self.voice = VoiceEngine()

        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue()

        self.running = False

    async def start(self):
        if not self.running:
            self.running = True
            asyncio.create_task(self._process_queue())

    async def submit(self, source: str, content: str):
    # Reject if agent busy
        if self.agent.state_manager.is_busy():
            print("[Orchestrator] Busy. Rejecting input.")
            return

        await self.queue.put({
            "source": source,
            "content": content})

    async def _process_queue(self):
        while True:
            task = await self.queue.get()

            async with self.lock:
                await self._handle(task)

    async def _handle(self, task):
        user_input = task["content"]
        print(f"[Orchestrator] Processing: {user_input}")
        response = self.agent.handle_input(user_input)
        print(f"[Orchestrator] Responding: {response}")

        # Only speak if source was voice
        if task["source"] == "voice":
            self.voice.speak(response)