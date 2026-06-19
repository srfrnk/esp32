.PHONY: info download-firmware clean-flash repl flash run open close stubs monitor


info:
	uvx esptool --port /dev/ttyUSB0 flash-id

download-firmware:
	curl -L -o firmware.bin https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20260406-v1.28.0.bin

stubs:
	uv run stubber clone --add-stubs
	uv run stubber firmware-stubs --serial /dev/ttyUSB0

clean-flash:
	uvx esptool --chip esp32s3 --port /dev/ttyUSB0 erase-flash
	uvx esptool --chip esp32s3 --port /dev/ttyUSB0 write-flash -z 0 firmware.bin
	sleep 5
	uv tool run mpremote mip install package.json

IP ?= 192.168.1.56
DNS ?= esp32.local

certs:
	@echo "Generating SSL Certificates..."
	@echo "[req]" > san.cnf
	@echo "default_bits = 2048" >> san.cnf
	@echo "distinguished_name = req_distinguished_name" >> san.cnf
	@echo "req_extensions = req_ext" >> san.cnf
	@echo "x509_extensions = v3_req" >> san.cnf
	@echo "prompt = no" >> san.cnf
	@echo "[req_distinguished_name]" >> san.cnf
	@echo "CN = $(DNS)" >> san.cnf
	@echo "[req_ext]" >> san.cnf
	@echo "subjectAltName = @alt_names" >> san.cnf
	@echo "[v3_req]" >> san.cnf
	@echo "basicConstraints = critical, CA:true" >> san.cnf
	@echo "subjectAltName = @alt_names" >> san.cnf
	@echo "[alt_names]" >> san.cnf
	@echo "DNS.1 = $(DNS)" >> san.cnf
	@echo "IP.1 = $(IP)" >> san.cnf
	openssl req -x509 -nodes -days 3650 -newkey rsa:2048 -keyout key.pem -out cert.pem -config san.cnf -extensions v3_req
	openssl rsa -in key.pem -out key.der -outform DER
	openssl x509 -in cert.pem -out cert.der -outform DER
	@echo "Certificates generated. Run 'make flash' to upload."
flash:
	uv tool run mpremote cp *.py :
	uv tool run mpremote cp *.json :
	uv tool run mpremote cp *.der :
	uv tool run mpremote cp *.pem :
	uv tool run mpremote cp -r web_server :
	uv tool run mpremote reset

run:
	uv tool run mpremote mount . run main.py


repl:
	uv tool run mpremote repl

resume:
	uv tool run mpremote resume
