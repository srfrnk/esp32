import aioble  # type: ignore
import bluetooth
import uasyncio as asyncio


class BlindsController:
    def __init__(self, mac_addr="C6:0F:80:3B:C7:20"):
        self.mac_addr = mac_addr
        self.target_char_uuid = bluetooth.UUID("00010405-0405-0607-0809-0a0b0c0d1910")
        self.cmd_connect = bytes.fromhex("ff03030303787878787878")
        self.cmd_init = bytes.fromhex("ff78ea41d10301")
        self.connection = None
        self.target_char = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    async def connect(self, max_retries: int = 5):
        for attempt in range(max_retries):
            print(
                f"Connecting (Random Type) to {self.mac_addr}... (Attempt {attempt + 1}/{max_retries})"
            )

            try:
                # Create a new Device instance for each attempt to avoid stale discovery states
                device = aioble.Device(aioble.ADDR_RANDOM, self.mac_addr)
                self.connection = await device.connect(timeout_ms=10000)
                print("Connected! Discovering services...")

                # Resolve service discovery completely first to free up the BLE stack
                services = []
                async for service in self.connection.services():
                    services.append(service)

                print(
                    f"Discovered {len(services)} services. Searching for characteristic..."
                )
                self.target_char = None
                for service in services:
                    async for char in service.characteristics():
                        if char.uuid == self.target_char_uuid:
                            self.target_char = char
                            break
                    if self.target_char:
                        break

                if not self.target_char:
                    print("Target characteristic not found on this device.")
                    await self.disconnect()
                    return

                print("Found characteristic! Transmitting handshakes...")
                await self.target_char.write(self.cmd_connect)
                await asyncio.sleep(0.3)  # wait 300ms

                await self.target_char.write(self.cmd_init)
                await asyncio.sleep(0.3)  # wait 300ms

                print("Initialization complete.")
                return

            except Exception as e:
                print(f"GATT Protocol Error: {type(e).__name__} - {e}")
                await self.disconnect()
                if attempt < max_retries - 1:
                    print("Waiting before retry...")
                    await asyncio.sleep(2.0)  # wait 2s
                else:
                    print("Failed after all retries.")

    async def disconnect(self):
        if self.connection:
            try:
                await self.connection.disconnect()
            except Exception:
                pass
            self.connection = None
        self.target_char = None
        print("Disconnected.")

    def _get_position_payload(self, closed_percent: float) -> bytes:
        blind_percent = 100 - closed_percent
        total_val = int(round(blind_percent * 10))
        position_value = total_val % 256
        group_value = total_val // 256

        payload = bytearray.fromhex("ff78ea41bf03")
        payload.append(position_value)
        payload.append(group_value)
        return bytes(payload)

    async def set_position(self, closed_percent: float):
        payload_bytes = self._get_position_payload(closed_percent)
        print(f"Sending movement command for {closed_percent}%...")

        for attempt in range(2):
            if not self.target_char:
                print("Not connected, attempting to connect...")
                await self.connect()

            if not self.target_char:
                print("Failed to connect.")
                return

            try:
                await self.target_char.write(payload_bytes)
                print("Success!")
                return
            except Exception as e:
                print(f"Error sending command: {e}. Connection may have dropped. Reconnecting...")
                await self.disconnect()

        print("Failed to send movement command after retries.")
