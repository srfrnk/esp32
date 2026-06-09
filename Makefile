info:
	uvx esptool --port /dev/ttyUSB0 flash-id

download-firmware:
	curl -L -o firmware.bin https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20260406-v1.28.0.bin

clean-flash:
	uvx esptool --chip esp32s3 --port /dev/ttyUSB0 erase-flash
	uvx esptool --chip esp32s3 --port /dev/ttyUSB0 write-flash -z 0 firmware.bin
	sleep 5
	uv tool run mpremote mip install package.json

repl:
	uv tool run mpremote repl

flash:
	uv tool run mpremote cp *.py :
	uv tool run mpremote reset

run:
	uv tool run mpremote mount . run main.py

open:
	uv tool run mpremote mount . run open.py

close:
	uv tool run mpremote mount . run close.py

stubs:
	uv run stubber clone --add-stubs
	uv run stubber firmware-stubs --serial /dev/ttyUSB0
