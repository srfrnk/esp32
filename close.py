import uasyncio as asyncio
from blinds_control import BlindsController

async def main():
    print("Sending movement command (Close)...")
    async with BlindsController() as blinds:
        await blinds.set_position(100)

if __name__ == "__main__":
    asyncio.run(main())
