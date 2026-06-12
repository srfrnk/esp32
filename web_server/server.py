import json
import uasyncio as asyncio

async def http_server_handler(reader, writer, diagnostics_data):
    try:
        request_line = await reader.readline()
        if not request_line:
            return
        
        req = request_line.decode().split()
        if len(req) < 2:
            return
            
        path = req[1]
        
        # Read the rest of the headers
        while True:
            line = await reader.readline()
            if not line or line == b'\r\n':
                break
                
        if path == "/api/diagnostics":
            response = json.dumps(diagnostics_data)
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
            writer.write(response.encode())
            await writer.drain()
            return

        if path == "/":
            path = "/index.html"
            
        # Prevent directory traversal
        if ".." in path:
            path = "/index.html"
            
        try:
            with open("web_server/www" + path, "rb") as f:
                writer.write(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n")
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()
        except OSError:
            writer.write(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n404 File Not Found")
            await writer.drain()
            
    except Exception as e:
        print(f"HTTP Server error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass

async def start_server(diagnostics_data, host="0.0.0.0", port=80):
    async def handler(reader, writer):
        await http_server_handler(reader, writer, diagnostics_data)
        
    try:
        server = await asyncio.start_server(handler, host, port)
        return server
    except Exception as e:
        print(f"Failed to start HTTP server: {e}")
        return None
