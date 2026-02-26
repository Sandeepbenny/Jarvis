import asyncio
from backend.orchestrator import Orchestrator

async def voice_loop(orchestrator):
    loop = asyncio.get_running_loop()

    while True:
        transcript = await loop.run_in_executor(
            None,
            orchestrator.voice.listen
        )

        if transcript:
            await orchestrator.submit("voice", transcript)


async def text_loop(orchestrator):
    loop = asyncio.get_running_loop()

    while True:
        text = await loop.run_in_executor(None, input, "You (Type): ")

        if text.lower() == "exit":
            print("Shutting down...")
            break

        if text.strip():
            await orchestrator.submit("text", text)


async def main():
    orchestrator = Orchestrator()
    await orchestrator.start()

    await asyncio.gather(
        voice_loop(orchestrator),
        text_loop(orchestrator)
    )


if __name__ == "__main__":
    asyncio.run(main())