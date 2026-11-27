import asyncio
from ai_search_visualizer import App


async def main():
    await App().run_async()


asyncio.run(main())
