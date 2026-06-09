# Type stubs for the ESP32 MicroPython camera module

class FrameSize:
    QQVGA: int
    QCIF: int
    HQVGA: int
    QVGA: int
    CIF: int
    HVGA: int
    VGA: int
    SVGA: int
    XGA: int
    HD: int
    SXGA: int
    UXGA: int
    FHD: int
    P_HD: int
    P_3MP: int
    QXGA: int
    QHD: int
    WQXGA: int
    P_FHD: int
    QSXGA: int

class PixelFormat:
    RGB565: int
    YUV422: int
    GRAYSCALE: int
    JPEG: int
    RGB888: int
    RAW: int
    RGB444: int
    RGB555: int

class Camera:
    def __init__(
        self,
        d0: int = -1, d1: int = -1, d2: int = -1, d3: int = -1, 
        d4: int = -1, d5: int = -1, d6: int = -1, d7: int = -1,
        xclk: int = -1, pclk: int = -1, vsync: int = -1, href: int = -1,
        sda: int = -1, scl: int = -1, pwdn: int = -1, reset: int = -1,
        freq: int = 20000000, pixel_format: int = 3, frame_size: int = 8,
        jpeg_quality: int = 12, init: bool = True
    ) -> None: ...
    
    def init(self) -> bool: ...
    def deinit(self) -> bool: ...
    def capture(self) -> bytes: ...
