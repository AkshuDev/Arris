import struct
from Assembler import *
from instructionSet import *
from typing import *
import string

from phardwareitk.Extensions.HyperOut import printH
from phardwareitk.Extensions import TextFont, Color

archTable = {
    0xA0A0: "PVCpu-Avef (Pheonix-Virtual-CPU-Avef)",
    0xA0A1: "PVCpu (Pheonix-Virtual-CPU)",
}

_printable = set(string.printable) - set('\r\n\t\x0b\x0c')

def _to_ascii(bs: bytes) -> str:
    return ''.join(chr(b) if 32 <= b < 127 else '.' for b in bs)

def _read_header(av: bytes):
    if len(av) < HEADER_SIZE:
        raise ValueError("Not a valid AVEF file (too small)")
    magic, version, arch, entry, sec_tab_off, sec_count, flags, mem_size, _ = struct.unpack(
        HEADER_FMT, av[:HEADER_SIZE]
    )
    return {
        "magic": magic,
        "version": version,
        "arch": arch,
        "entry": entry,
        "sec_table_offset": sec_tab_off,
        "sec_count": sec_count,
        "flags": flags,
        "mem_size": mem_size,
    }

def _read_sections(av: bytes, header: dict):
    sections = []
    sec_off = header["sec_table_offset"]
    sec_cnt = header["sec_count"]

    # choose entry size
    entry_sz = SECTION_SIZE 
    for i in range(sec_cnt):
        off = sec_off + i * entry_sz
        if off + entry_sz > len(av):
            raise ValueError("Section table truncated")
        else:
            fields = av[off:off+SECTION_SIZE]
            name, vaddr, file_off, size, flags, align = struct.unpack(SECTION_FMT, fields)
            name = name.decode("utf-8").strip("\x00")
            
            sections.append({
                "name": name,
                "vaddr": vaddr,
                "file_offset": file_off,
                "size": size,
                "flags": flags,
                "align": align,
            })

    return sections

def dump_avef(av: bytes,
              better: bool = False,
              bytes_per_line: int = 20,
              show_sections: Optional[list] = [".text", ".data", ".bss", ".rodata", ".symbols"],
              symbols: Optional[Dict[int, str]] = None,
              decoder: Optional[Callable[[int, bytes, dict], Tuple[str, str, int]]] = None):
    """
    av: raw AVEF bytes
    better: if True, collapse runs of zero-lines, print labels from symbols dict, attempt decode using decoder.
    bytes_per_line: how many bytes per hexdump line
    show_sections: optional list of section names to dump (None = all)
    symbols: optional mapping {vaddr: "symbol_name"} used to annotate output
    decoder: optional function decoder(vaddr, full_bytes_from_vaddr, labels) -> (mnemonic_str_or_None, size_used)
             If mnemonic_str_or_None is not None, the dumper will print that mnemonic on its own line and skip those bytes.
    """
    hdr = _read_header(av)

    keyword_font = TextFont(font_color=Color("neon-red"), Bold=True)
    inst_font = TextFont(font_color=Color("light-cyan-special"))
    symbol_font = TextFont(font_color=Color("light-gray"), Bold=True)

    print("AVEF Header:")
    print(f"  Magic: {hdr['magic']!r}")
    print(f"  Version: 0x{hdr['version']:04x}")
    print(f"  ArchId: {archTable.get(hdr['arch'], "<Unknown>")}")
    print(f"  Entry: 0x{hdr['entry']:x}")
    print(f"  Section table offset: {hdr['sec_table_offset']}")
    print(f"  Section count: {hdr['sec_count']}")
    print(f"  Flags: 0x{hdr['flags']:x}")
    print(f"  Mem size required: 0x{hdr['mem_size']:x}")
    print()

    sections = _read_sections(av, hdr)

    labels = None
    # filter
    if show_sections:
        sections = [s for s in sections if s['name'] in show_sections]

    # Print section summary
    print("Sections:")
    for s in sections:
        print(f"  {s['name']:<12} vaddr=0x{s['vaddr']:08x} size=0x{s['size']:x} file_off=0x{s['file_offset']:x} flags=0x{s['flags']:x} align=0x{s['align']:x}")
    print()

    # Dump each section in a clean objdump-like format
    for s in sections:
        name = s['name']
        vaddr = s['vaddr']
        size = s['size']
        foff = s['file_offset']

        print(f"{name} (0x{vaddr:08x} - 0x{vaddr + size:08x}) size=0x{size:x}")
        if size == 0:
            print("  <empty>")
            print()
            continue

        # extract section bytes from file, if file_off is 0 treat as zero-filled BSS
        if foff == 0 or foff + size > len(av):
            data = bytes([0]) * size
        else:
            data = av[foff:foff + size]

        # collapse runs of zero lines like objdump does
        collapse = better
        repeated_zero = False
        zero_line = b'\x00' * bytes_per_line

        # iterate through data by bytes_per_line
        addr = vaddr
        idx = 0
        last_was_zeros = False
        while idx < len(data):
            if name == ".symbols":
                name = b""
                remaining = data[idx:]
                for i in range(len(remaining)):
                    b = remaining[i:i+1]
                    name += b
                    if b == b"\x00":
                        break
                idx += len(name); addr += len(name)
                name_str = name.decode("utf-8")
                section = int.from_bytes(data[idx:idx + 4]); idx += 4; addr += 4
                location = int.from_bytes(data[idx: idx + 8]); idx += 8; addr += 8
                size = int.from_bytes(data[idx:idx + 4]); idx += 4; addr += 4
                binding = int.from_bytes(data[idx: idx + 1]); idx += 1; addr += 1
                labels = {location: name_str}
            # if decoder provided and better mode: try to decode an instruction at this vaddr
            if decoder is not None and name not in [".rodata", ".data", ".symbols"]:
                # pass the remaining bytes starting at this vaddr (virtual map)
                remaining = data[idx:]
                decoded = decoder(addr, remaining, labels)
                if decoded:
                    keyword, mnemonic, used = decoded
                    if keyword is not None and (mnemonic is not None and used > 0):
                        # print label if exists
                        if symbols and addr in symbols:
                            if better:
                                printH(f"{symbols[addr]}:", FontEnabled=True, Font=symbol_font)
                            else:
                                print(f"{symbols[addr]}:")
                        # print address + keyword + mnemonic
                        if better:
                            printH(f"  0x{addr:08x}:\t", FontEnabled=True, Font=symbol_font, endl="")
                            printH(f"{keyword} ", FontEnabled=True, Font=keyword_font, endl="")
                            printH(f"{mnemonic}", FontEnabled=True, Font=inst_font)
                        else:
                            print(f"  0x{addr:08x}:\t{keyword} {mnemonic}")
                        idx += used
                        addr += used
                        last_was_zeros = False
                        continue

            # normal hexdump line
            line = data[idx:idx + bytes_per_line]
            if collapse and line == zero_line:
                # find how many consecutive zero lines
                run = 1
                j = idx + bytes_per_line
                while j < len(data) and data[j:j+bytes_per_line] == zero_line:
                    run += 1
                    j += bytes_per_line
                if run > 2:
                    # collapse
                    # print previous lines if not already printed a star
                    print(f"  *\t<skipped {run * bytes_per_line} bytes of zeros>")
                    idx = j
                    addr += run * bytes_per_line
                    last_was_zeros = True
                    continue
                # otherwise, fallthrough to normal printing

            # print label if present at address
            if symbols and addr in symbols:
                if better:
                    printH(f"{symbols[addr]}:", FontEnabled=True, Font=symbol_font)
                else:
                    print(f"{symbols[addr]}:")

            # hex bytes grouped in 4s for readability
            hex_groups = []
            for i in range(0, len(line), 4):
                chunk = line[i:i+4]
                hex_groups.append(' '.join(f"{b:02x}" for b in chunk))
            hex_part = '   '.join(hex_groups)
            ascii_part = _to_ascii(line)
            print(f"  0x{addr:08x}:  {hex_part:<{bytes_per_line * 2 + (bytes_per_line//4 - 1) * 3}}  |{ascii_part}|")

            idx += bytes_per_line
            addr += bytes_per_line
            last_was_zeros = (line == zero_line)

        print()

def pvcpu_avef_decoder(vaddr: int, data: bytes, labels: dict={}) -> tuple[str, str, int]:
    """
    PrePacked PVCpu-AVEF decoder
    """
    labels = labels if labels else {}
    if len(data) < 1: return ("", "<cannot decode>", 20)
    op = int.from_bytes(data[:2], "little")
    src = int.from_bytes(data[2:6], "little")
    dest = int.from_bytes(data[6:10], "little")
    imm = int.from_bytes(data[10:18], "little")
    mode = int.from_bytes(data[18:20], "little")
    inst = f"{labels[vaddr]}: " if vaddr in labels else ""
    keyword = ""

    keyword = debug_inst.get(op, "<unknown>").lower() + " "

    if op == POPG:
        inst += debug_regs.get(dest, "<unknown>").lower()
        return (keyword, inst, 20)
    elif op == PUSHI:
        inst += debug_regs.get(src, "<unknown>").lower()
        return (keyword, inst, 20)
    elif op == CALL or op == INT:
        inst += str(hex(imm))
        return (keyword, inst, 20)

    if mode == REGREG:
        inst += debug_regs.get(dest, "<unknown>").lower() + ", "
        inst += debug_regs.get(src, "<unknown>").lower()
    elif mode == MEMREG:
        inst += "[" + debug_regs.get(dest, "<unknown>").lower() + " + " + str(hex(imm)) + "], "
        inst += debug_regs.get(src, "<unknown>").lower()
    elif mode == MEMDIR:
        inst += debug_regs.get(dest, "<unknown>").lower() + ", [" + str(hex(imm)) + "]"
        if imm in labels: inst += f"\t{labels[imm]}"
    elif mode == REGDIR:
        inst += debug_regs.get(dest, "<unknown>").lower() + ", " + str(imm)
    elif mode == MEMONLY:
        inst += "[" + str(hex(imm)) + "]"
        if imm in labels: inst += f"\t{labels[imm]}"
    elif mode == IMMONLY:
        inst += str(imm)
    elif mode == REGMEM:
        inst += "[" + str(hex(imm)) + "], " + debug_regs.get(src, "<unknown>").lower()
    elif mode == REGMEMREG:
        inst += "[" + debug_regs.get(dest, "unknown").lower() + " + " + str(hex(imm)) + "], " + debug_regs.get(src, "<unknown>").lower()
    elif mode == NULL:
        pass
    else:
        inst += "<cannot decode>"

    return (keyword, inst, 20)

