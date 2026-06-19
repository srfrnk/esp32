import json
import uasyncio as asyncio

async def http_server_handler(reader, writer, diagnostics_data):
    try:
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        except asyncio.TimeoutError:
            return
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
            
        if path.startswith("/api/target_light"):
            if "?" in path:
                query = path.split("?")[1]
                if "val=" in query:
                    try:
                        val_str = query.split("val=")[1].split("&")[0]
                        new_target = float(val_str)
                        
                        from config import APP_CONFIG
                        APP_CONFIG.light_control.target = new_target
                        diagnostics_data["target_light"] = new_target
                        
                        try:
                            with open("config.json", "r") as f:
                                config_data = json.load(f)
                            config_data["light_control"]["target"] = new_target
                            with open("config.json", "w") as f:
                                json.dump(config_data, f)
                        except Exception as e:
                            print(f"Failed to save config: {e}")
                            
                        writer.write(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n{\"status\":\"ok\"}")
                        await writer.drain()
                        return
                    except Exception as e:
                        print(f"Error parsing target light: {e}")
            
            writer.write(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n{\"error\":\"Invalid request\"}")
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
    import ssl
    async def handler(reader, writer):
        await http_server_handler(reader, writer, diagnostics_data)
        
    ssl_ctx = None
    try:
        import os
        files = os.listdir()
        if 'cert.der' in files and 'key.der' in files:
            print("Loading DER certificates...")
            with open('cert.der', 'rb') as f:
                cert = f.read()
            with open('key.der', 'rb') as f:
                key = f.read()
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            # In MicroPython, load_cert_chain can take binary buffers
            ssl_ctx.load_cert_chain(cert, key)
            port = 443  # default to HTTPS port
        elif 'cert.pem' in files and 'key.pem' in files:
            print("Loading PEM certificates...")
            ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_ctx.load_cert_chain('cert.pem', 'key.pem')
            port = 443
    except Exception as e:
        print(f"Failed to configure SSL: {e}")
        ssl_ctx = None

    try:
        if ssl_ctx:
            server = await asyncio.start_server(handler, host, port, ssl=ssl_ctx)
            print(f"HTTPS server started on {host}:{port}")
        else:
            server = await asyncio.start_server(handler, host, port)
            print(f"HTTP server started on {host}:{port}")
        return server
    except Exception as e:
        print(f"Failed to start server: {e}")
        return None
