import uasyncio as asyncio
from blinds_control import send_blind_command, get_position_payload

async def main():
    print("Sending movement command (Close)...")
    await send_blind_command(get_position_payload(100))

if __name__ == "__main__":
    asyncio.run(main())
