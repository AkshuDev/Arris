import struct
import Assembler

def dump_avef(data: bytes):
    archTable = {
        0xA0A0: "PVCpu",
    }

    # Unpack header
    magic, version, arch, entry, sec_off, nsects, flags, mem_size, reserved = struct.unpack(Assembler.HEADER_FMT, data[:Assembler.HEADER_SIZE])
    print("Magic:", magic.decode())
    print("Version:", hex(version))
    print("Architecture RAW:", hex(arch))
    print("Architecture:", archTable.get(arch, "Unknown"))
    print("Entry Point:", hex(entry))
    print("Section Table Offset:", hex(sec_off))
    print("Number of Sections:", nsects)
    print("Flags:", hex(flags))
    print("Memory Size (bytes):", mem_size)

    # Section table
    offset = sec_off
    for i in range(nsects):
        name, vaddr, file_off, size, flags, align = struct.unpack(Assembler.SECTION_FMT, data[offset:offset + Assembler.SECTION_SIZE])
        print(f"\nSection {i+1}:")
        print("Name:", name.decode("utf-8").strip("\x00"))
        print("Virtual Address:", vaddr)
        print("File Offset:", file_off)
        print("Size:", size)
        print("Flags:", flags)
        print("Align:", align)
        offset += Assembler.SECTION_SIZE