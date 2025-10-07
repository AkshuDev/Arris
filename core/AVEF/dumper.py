import struct
import Assembler
import instructionSet

def dump_avef(data: bytes, debug_code:bool):
    archTable = {
        0xA0A0: "PVCpu (Pheonix-Virtual-CPU)",
    }

    # Unpack header
    print("RAW Header:", data[:Assembler.HEADER_SIZE].hex(" "))
    magic, version, arch, entry, sec_off, nsects, flags, mem_size, reserved = struct.unpack(Assembler.HEADER_FMT, data[:Assembler.HEADER_SIZE])
    print("Magic:", magic.decode())
    print("Version:", hex(version))
    print("Architecture RAW:", hex(arch))
    print("Architecture:", archTable.get(arch, "Unknown"))
    print("Entry Point:", hex(entry))
    print("Section Table Offset:", hex(sec_off))
    print("Number of Sections:", nsects)
    print("Flags:", hex(flags))
    print("Memory Size (bytes):", hex(mem_size))

    # Section table
    offset = Assembler.HEADER_SIZE
    for i in range(nsects):
        print("RAW Entry:", data[offset:offset + Assembler.SECTION_SIZE].hex(" "))
        name, vaddr, file_off, size, flags, align = struct.unpack(Assembler.SECTION_FMT, data[offset:offset + Assembler.SECTION_SIZE])
        print(f"\nSection {i+1}:")
        print("Name:", name.decode("utf-8").strip("\x00"))
        print("Virtual Address:", hex(vaddr))
        print("File Offset:", hex(file_off))
        print("Size:", hex(size))
        print("Flags:", hex(flags))
        print("Align:", hex(align))
        offset += Assembler.SECTION_SIZE
        
        str_name:str = name.decode("utf-8").strip("\x00")
    
        print("Data in hex:", data[file_off:file_off + size].hex())
        if str_name == ".text" and debug_code:
            print("Trying to decode the data...")
            index = 0
            instructions:list[bytes] = []
            instruction:bytes = b""
            for i in range(len(data[file_off:file_off + size])):
                index += 1
                instruction += data[file_off + i:file_off + i + 1]
                if index == 20: # 20 byte instructions
                    index = 0
                    instructions.append(instruction)
                    instruction = b""
                    
            for inst in instructions:
                print("RAW instruction:", inst.hex(" "))
                instruction = int().from_bytes(inst[0:2], "little") # 2 bytes
                src = int().from_bytes(inst[2:6], "little")
                dest = int().from_bytes(inst[6:10], "little")
                imm = int().from_bytes(inst[10:18], "little")
                mode = int().from_bytes(inst[18:20], "little")
                
                # get instruction
                print("Instruction:", instructionSet.debug_inst.get(instruction, "Unknown"))
                print("Source:", instructionSet.debug_regs.get(src, "Unknown"))
                print("Dest:", instructionSet.debug_regs.get(dest, "Unknown"))
                print("Imm:", imm)
                print("Mode:", instructionSet.debug_modes.get(mode, "Unknown"))
                print("\n")
        elif str_name in [".data", ".bss", ".symbols"]:
            print("Trying to decode data...")
            vars:list[bytes] = []
            var:bytes = b""
            index:int = 0
            
            while True:
                if index >= size: break
                byte = data[file_off + index:file_off + index + 1]
                index += 1
                var += byte
                if byte == b"\x00":
                    vars.append(var[:len(var) - 1])
                    var = b""

            for var in vars:
                print("Data: '" + var.decode("utf-8") + "'")