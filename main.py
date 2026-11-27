print("DEBUG main.py: start", flush=True)
import asyncio
from ai_search_visualizer import App


async def main():
    print("DEBUG main.py: creating App", flush=True)
    app = App()
    print("DEBUG main.py: App created, running loop", flush=True)
    await app.run_async()


asyncio.run(main())
