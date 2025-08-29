build := avm_build
bin := avm_bin
include := avm

SRCS := $(wildcard *.c)
OBJS := $(SRCS:.c=.o)

CC := gcc
CFLAGS := -I $(include) -w

TARGET := $(bin)/avm

all: $(TARGET)

$(TARGET): $(SRCS)
	@echo "Making directories..."
	@mkdir $(build)
	@mkdir $(bin)
	@echo "Compiling..."
	$(CC) $(CFLAGS) $(SRCS) -o $(TARGET)
	@echo "Done!"
	@echo $(TARGET)

clean:
	@echo "Cleaning..."
	@rmdir $(build)
	@rmdir $(bin)
	@echo "Done!"

.PHONY: all clean