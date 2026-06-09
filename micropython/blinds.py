import uasyncio as asyncio
import aioble # type: ignore
import bluetooth

MAC_ADDR = "C6:0F:80:3B:C7:20"
TARGET_CHAR_UUID = bluetooth.UUID("00010405-0405-0607-0809-0a0b0c0d1910")

CMD_CONNECT = bytes.fromhex("ff03030303787878787878")
CMD_INIT = bytes.fromhex("ff78ea41d10301")

def get_position_payload(user_percent: float) -> bytes:
    tuiss_percent = 100 - user_percent
    total_val = int(round(tuiss_percent * 10))
    position_value = total_val % 256
    group_value = total_val // 256

    payload = bytearray.fromhex("ff78ea41bf03")
    payload.append(position_value)
    payload.append(group_value)
    return bytes(payload)

async def send_blind_command(payload_bytes: bytes):
    print(f"Connecting (Random Type) to {MAC_ADDR}...")
    device = aioble.Device(aioble.ADDR_RANDOM, MAC_ADDR)

    try:
        connection = await device.connect(timeout_ms=10000)
        async with connection:
            print("Connected! Discovering services...")

            # Resolve service discovery completely first to free up the BLE stack
            services = []
            async for service in connection.services():
                services.append(service)

            print(f"Discovered {len(services)} services. Searching for characteristic...")
            target_char = None
            for service in services:
                async for char in service.characteristics():
                    if char.uuid == TARGET_CHAR_UUID:
                        target_char = char
                        break
                if target_char:
                    break

            if not target_char:
                print("Target characteristic not found on this device.")
                return

            print("Found characteristic! Transmitting handshakes...")
            await target_char.write(CMD_CONNECT)
            await asyncio.sleep_ms(300) # type: ignore

            await target_char.write(CMD_INIT)
            await asyncio.sleep_ms(300) # type: ignore

            print("Sending movement command...")
            await target_char.write(payload_bytes)
            print("Success!")

    except Exception as e:
        print(f"GATT Protocol Error: {type(e).__name__} - {e}")

async def main():
    await send_blind_command(get_position_payload(0))

if __name__ == "__main__":
    asyncio.run(main())