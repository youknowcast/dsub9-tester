PREFIX = $(HOME)/tools/h8300-elf/bin/h8300-elf
AS = $(PREFIX)-as
LD = $(PREFIX)-ld
OBJCOPY = $(PREFIX)-objcopy
OBJDUMP = $(PREFIX)-objdump

all: sender.mot sender.lst

%.o: %.S
	$(AS) -o $@ $<

sender.elf: sender.o linker.ld
	$(LD) -T linker.ld -o $@ sender.o

sender.mot: sender.elf
	$(OBJCOPY) -O srec $< $@

sender.lst: sender.elf
	$(OBJDUMP) -d $< > $@

clean:
	rm -f *.o *.elf *.mot *.lst

.PHONY: all clean