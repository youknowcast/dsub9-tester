SECTIONS {
	. = 0xffbf20;
	.text : {
		*(.text)
		*(.rodata*)
	}
	. = 0xffc000;
	.param : {
		*(.param)
	}
}