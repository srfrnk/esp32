# SPDX-FileCopyrightText: 2022-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: CC0-1.0

import pytest
from pytest_embedded_idf.dut import IdfDut
from pytest_embedded_idf.utils import idf_parametrize
from pytest_embedded_qemu.app import QemuApp
from pytest_embedded_qemu.dut import QemuDut


@pytest.mark.generic
@idf_parametrize(
    "target", ["supported_targets", "preview_targets"], indirect=["target"]
)
def test_hello_world(dut: IdfDut) -> None:
    dut.expect("Hello world!")


@pytest.mark.host_test
@idf_parametrize("target", ["linux"], indirect=["target"])
def test_hello_world_linux(dut: IdfDut) -> None:
    dut.expect("Hello world!")


@pytest.mark.host_test
@pytest.mark.macos
@idf_parametrize("target", ["linux"], indirect=["target"])
def test_hello_world_macos(dut: IdfDut) -> None:
    dut.expect("Hello world!")


@pytest.mark.host_test
@pytest.mark.qemu
@idf_parametrize("target", ["esp32", "esp32c3", "esp32s3"], indirect=["target"])
def test_hello_world_host(app: QemuApp, dut: QemuDut) -> None:
    dut.expect("Hello world!")
