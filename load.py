#!/usr/bin/env python3
import os
import select
import sys
import termios
import time

DEV = "/dev/ttyUSB0"
BAUD = 38400
XOFF = 0x13
XON = 0x11
PROMPT = b"1:"


def open_port(baud):
    fd = os.open(DEV, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    attrs = termios.tcgetattr(fd)
    attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK | termios.ISTRIP |
                  termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IXON)
    attrs[1] &= ~(termios.OPOST | termios.ONLCR)
    attrs[2] &= ~(termios.CSIZE | termios.PARENB | termios.CSTOPB)
    attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
    b = {"9600": termios.B9600, "19200": termios.B19200, "38400": termios.B38400}[str(baud)]
    attrs[4] = b
    attrs[5] = b
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return fd


def set_baud(fd, baud):
    attrs = termios.tcgetattr(fd)
    b = {"9600": termios.B9600, "19200": termios.B19200, "38400": termios.B38400}[str(baud)]
    attrs[4] = b
    attrs[5] = b
    termios.tcsetattr(fd, termios.TCSANOW, attrs)


PENDING = b""


def read_byte(fd, timeout):
    global PENDING
    if PENDING:
        b = PENDING[0]
        PENDING = PENDING[1:]
        return b
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.02)
        if r:
            try:
                d = os.read(fd, 1)
                if d:
                    return d[0]
            except BlockingIOError:
                pass
    return None


def drain(fd, timeout):
    end = time.time() + timeout
    out = b""
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.02)
        if r:
            try:
                d = os.read(fd, 4096)
                if d:
                    out += d
            except BlockingIOError:
                pass
    return out


def wait_for(fd, needle, timeout):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        b = read_byte(fd, 0.1)
        if b is None:
            continue
        buf += bytes([b])
        if needle in buf:
            return True, buf
    return False, buf


def wait_prompt(fd, timeout):
    ok, buf = wait_for(fd, PROMPT, timeout)
    if not ok:
        print(f"ERROR: no prompt in {timeout}s (got: {buf!r})")
        sys.exit(1)
    return buf


def send_lines(fd, mot_path):
    global PENDING
    with open(mot_path, "rb") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        os.write(fd, line + b"\r")
        end = time.time() + 0.1
        while time.time() < end:
            b = read_byte(fd, 0.02)
            if b == XOFF:
                while True:
                    b2 = read_byte(fd, 5)
                    if b2 is None:
                        print(f"ERROR: XOFF but no XON (line {i})")
                        sys.exit(1)
                    if b2 == XON:
                        break
            elif b is not None:
                PENDING += bytes([b])
        time.sleep(0.02)
    print(f"sent {len(lines)} records")


def listen(fd, seconds):
    end = time.time() + seconds
    while time.time() < end:
        d = drain(fd, 0.2)
        if d:
            sys.stdout.buffer.write(d)
            sys.stdout.buffer.flush()


def main():
    mot = sys.argv[1] if len(sys.argv) > 1 else "sender.mot"
    addr = sys.argv[2] if len(sys.argv) > 2 else "ffbf20"
    listen_secs = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    listen_baud = int(sys.argv[4]) if len(sys.argv) > 4 else BAUD

    fd = open_port(BAUD)
    drain(fd, 0.5)
    os.write(fd, b"\r")
    wait_prompt(fd, 3)

    os.write(fd, b"ld\r")
    time.sleep(0.2)
    send_lines(fd, mot)
    wait_prompt(fd, 10)

    os.write(fd, f"go {addr}\r".encode())
    print(f"go {addr}: running")
    if listen_baud != BAUD:
        set_baud(fd, listen_baud)
    listen(fd, listen_secs)
    os.close(fd)


main()