SECTIONS {
	. = 0xffbf20;
	.text : {
		*(.text)
		*(.rodata*)
	}
}