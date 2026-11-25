"""Query stream metadata on local Windows snapshots without opening named streams."""

import ctypes
from ctypes import wintypes


class StreamData(ctypes.Structure):
    _fields_ = [("size", ctypes.c_longlong), ("name", ctypes.c_wchar * 296)]


kernel = ctypes.WinDLL("kernel32", use_last_error=True)
first = kernel.FindFirstStreamW
first.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.POINTER(StreamData), wintypes.DWORD]
first.restype = wintypes.HANDLE
next_stream = kernel.FindNextStreamW
next_stream.argtypes = [wintypes.HANDLE, ctypes.POINTER(StreamData)]
next_stream.restype = wintypes.BOOL
close = kernel.FindClose
close.argtypes = [wintypes.HANDLE]
close.restype = wintypes.BOOL


def has_named_stream(path):
    data = StreamData()
    handle = first(str(path), 0, ctypes.byref(data), 0)
    if handle != wintypes.HANDLE(-1).value:
        try:
            while True:
                if data.name != "::$DATA":
                    return True
                if not next_stream(handle, ctypes.byref(data)):
                    error = ctypes.get_last_error()
                    break
        finally:
            close(handle)
    else:
        error = ctypes.get_last_error()
    if error == 38:  # ERROR_HANDLE_EOF: stream enumeration exhausted
        return False
    raise ctypes.WinError(error)
