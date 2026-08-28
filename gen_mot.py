#!/usr/bin/env python3
import argparse
import sys

PARAM_ADDR = 0xffc000
BLOCK_SIZE = 64
OFF_BRR = 0
OFF_INTERVAL = 2
OFF_LEN = 6
OFF_PATTERN = 8
MAX_PATTERN = 56
CLOCK = 20_000_000

ADDRLEN = {"1": 2, "2": 3, "3": 4, "7": 4, "8": 3, "9": 2}


def parse_mot(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line[0] != "S":
                continue
            typ = line[1]
            if typ == "0":
                continue
            count = int(line[2:4], 16)
            addrlen = ADDRLEN[typ]
            addr = int(line[4:4 + addrlen * 2], 16)
            data = bytes.fromhex(line[4 + addrlen * 2: 2 + count * 2])
            records.append((typ, addr, data))
    return records


def write_mot(path, records, name):
    lines = []
    hdr = name.encode()
    payload = bytes([len(hdr) + 3]) + b"\x00\x00" + hdr
    cks = (~sum(payload)) & 0xff
    lines.append(f"S0{payload.hex().upper()}{cks:02X}")
    for typ, addr, data in records:
        addrlen = ADDRLEN[typ]
        payload = bytes([addrlen + len(data) + 1]) + addr.to_bytes(addrlen, "big") + data
        cks = (~sum(payload)) & 0xff
        lines.append(f"S{typ}{payload.hex().upper()}{cks:02X}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def build_block(records):
    image = bytearray(PARAM_ADDR + BLOCK_SIZE + 0x100)
    for typ, addr, data in records:
        image[addr:addr + len(data)] = data
    block = bytearray(image[PARAM_ADDR:PARAM_ADDR + BLOCK_SIZE])
    return block


def patch_records(records, block):
    start = PARAM_ADDR
    end = PARAM_ADDR + BLOCK_SIZE
    out = []
    for typ, addr, data in records:
        lo = max(addr, start)
        hi = min(addr + len(data), end)
        if lo < hi:
            data = bytearray(data)
            for i in range(lo, hi):
                data[i - addr] = block[i - start]
            data = bytes(data)
        out.append((typ, addr, data))
    return out


def main():
    ap = argparse.ArgumentParser(description="patch sender.mot parameter block")
    ap.add_argument("--mot", default="sender.mot")
    ap.add_argument("--pattern")
    ap.add_argument("--baud", type=int)
    ap.add_argument("--interval", type=int)
    ap.add_argument("-o", "--output", default="sender.mot")
    args = ap.parse_args()

    records = parse_mot(args.mot)
    block = build_block(records)

    if args.pattern:
        with open(args.pattern, "rb") as f:
            pat = f.read().replace(b"\n", b"\r\n")
        if len(pat) > MAX_PATTERN:
            print(f"ERROR: pattern {len(pat)} bytes exceeds {MAX_PATTERN}")
            sys.exit(1)
        block[OFF_LEN] = len(pat)
        block[OFF_PATTERN:OFF_PATTERN + len(pat)] = pat
        print(f"pattern: {len(pat)} bytes")

    if args.baud:
        brr = CLOCK // 32 // args.baud - 1
        if not 0 <= brr <= 255:
            print(f"ERROR: baud {args.baud} out of range (BRR={brr})")
            sys.exit(1)
        block[OFF_BRR] = brr
        print(f"baud: {args.baud} (BRR={brr})")

    if args.interval is not None:
        if not 0 <= args.interval <= 0xffffffff:
            print(f"ERROR: interval out of range")
            sys.exit(1)
        block[OFF_INTERVAL:OFF_INTERVAL + 4] = args.interval.to_bytes(4, "big")
        print(f"interval: {args.interval}")

    records = patch_records(records, block)
    write_mot(args.output, records, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()