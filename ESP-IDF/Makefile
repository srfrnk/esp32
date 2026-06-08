SHELL := /bin/bash
.PHONY: build test

PROJECT_PATH ?= .
TEST_NAME ?= pytest_hello_world.py

build:
	. ~/.espressif/tools/activate_idf_v6.0.1.sh && \
	unset CPATH C_INCLUDE_PATH CPLUS_INCLUDE_PATH && \
	cd "${PROJECT_PATH}" && \
	rm -rf build && \
	idf.py build && \
	idf.py flash

monitor:
	. ~/.espressif/tools/activate_idf_v6.0.1.sh && \
	cd "${PROJECT_PATH}" && \
	idf.py monitor

test:
	. ~/.espressif/tools/activate_idf_v6.0.1.sh && \
	cd "${PROJECT_PATH}" && \
	pytest "$(patsubst %.py,%,$(strip $(TEST_NAME))).py" -m generic --target esp32s3 --port /dev/ttyUSB0 --embedded-services idf,serial

test-qemu:
	. ~/.espressif/tools/activate_idf_v6.0.1.sh && \
	cd "${PROJECT_PATH}" && \
	pytest "$(patsubst %.py,%,$(strip $(TEST_NAME))).py" -m qemu --target esp32s3 --embedded-services qemu,idf
