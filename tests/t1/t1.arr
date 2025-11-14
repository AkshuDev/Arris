@inc "<stdio.alib>"

@entry kmain
func void kmain(int argc, char** argv) {
    let char* program_name = *argv;
    print("Program Name: ");
    print(program_name);
    print("\nStarting Loop:\n");
    for (let int i = 0; i < 5; i++) {
        print("Looped!\n");
    }
}