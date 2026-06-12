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

flash:
	uv tool run mpremote cp *.py :
	uv tool run mpremote cp *.json :
	uv tool run mpremote cp -r web_server :
	uv tool run mpremote reset

run:
	uv tool run mpremote mount . run main.py


repl:
	uv tool run mpremote repl

resume:
	uv tool run mpremote resume
