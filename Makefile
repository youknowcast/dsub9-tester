PREFIX = $(HOME)/tools/h8300-elf/bin/h8300-elf
AS = $(PREFIX)-as
LD = $(PREFIX)-ld
OBJCOPY = $(PREFIX)-objcopy
OBJDUMP = $(PREFIX)-objdump

RAM_BASE = 0xffbf20

all: test_serial.mot test_serial.lst

%.o: %.S
	$(AS) -o $@ $<

test_serial.elf: test_serial.o linker.ld
	$(LD) -T linker.ld -o $@ test_serial.o

test_serial.mot: test_serial.elf
	$(OBJCOPY) -O srec $< $@

test_serial.lst: test_serial.elf
	$(OBJDUMP) -d $< > $@

clean:
	rm -f *.o *.elf *.mot *.lst

.PHONY: all clean