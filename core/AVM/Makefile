build := avm_build
bin := avm_bin
include := avm

SRCS := $(wildcard avm/*.c)
OBJS := $(SRCS:.c=.o)

CC := gcc
CFLAGS := -g -I $(include) -w

TARGET := $(bin)/avm

all: $(TARGET)

$(TARGET): $(SRCS)
	@echo "Making directories..."
	@mkdir -p $(build)
	@mkdir -p $(bin)
	@echo "Compiling..."
	$(CC) $(CFLAGS) $(SRCS) -o $(TARGET)
	@echo "Done!"
	@echo $(TARGET)

clean:
	@echo "Cleaning..."
	@rm -rf $(build)
	@rm -rf $(bin)
	@echo "Done!"

.PHONY: all clean
