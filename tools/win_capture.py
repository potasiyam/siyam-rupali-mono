"""Capture a window via PrintWindow (works when occluded)."""
import ctypes
from ctypes import wintypes
from PIL import Image
import sys

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDPIAware()


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD),
                ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD),
                ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD),
                ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG),
                ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER),
                ("bmiColors", wintypes.DWORD * 3)]


def capture(hwnd, w, h, out):
    hdcWindow = user32.GetWindowDC(hwnd)
    hdcMem = gdi32.CreateCompatibleDC(hdcWindow)
    hbmp = gdi32.CreateCompatibleBitmap(hdcWindow, w, h)
    gdi32.SelectObject(hdcMem, hbmp)
    res = user32.PrintWindow(hwnd, hdcMem, 2)  # PW_RENDERFULLCONTENT
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdcMem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)
    img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
    img.save(out)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdcMem)
    user32.ReleaseDC(hwnd, hdcWindow)
    print(f"PrintWindow={res} -> {out}")


if __name__ == "__main__":
    capture(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]),
            sys.argv[4])
