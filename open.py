import uasyncio as asyncio
from blinds import send_blind_command, get_position_payload

async def main():
    print("Sending movement command (Open)...")
    await send_blind_command(get_position_payload(0))

if __name__ == "__main__":
    asyncio.run(main())
