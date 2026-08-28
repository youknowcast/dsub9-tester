.h8300h
	.text
	.global _start

SMR1	= 0xffffb8
BRR1	= 0xffffb9
SCR1	= 0xffffba
TDR1	= 0xffffbb
SSR1	= 0xffffbc

PADDR	= 0xfee009
PADR	= 0xffffd9

LED_BIT	= 0x01

SCR_TE	= 0x20
SSR_TDRE	= 0x80

PARAM	= 0xffc000
OFF_BRR	= 0
OFF_INTERVAL	= 2
OFF_LEN	= 6
OFF_PATTERN	= 8

_start:
	mov.b	#0x00, r0l
	mov.b	r0l, @SCR1:24
	mov.b	#0x00, r0l
	mov.b	r0l, @SMR1:24
	mov.b	@PARAM+OFF_BRR:24, r0l
	mov.b	r0l, @BRR1:24

	mov.w	#520, r0
1:
	dec.w	#1, r0
	bne	1b

	mov.b	#SCR_TE, r0l
	mov.b	r0l, @SCR1:24
	mov.b	@SSR1:24, r0l
	mov.b	#SSR_TDRE, r0l
	mov.b	r0l, @SSR1:24

	mov.b	#LED_BIT, r0l
	mov.b	r0l, @PADDR:24

loop:
	mov.b	@PADR:24, r0l
	xor.b	#LED_BIT, r0l
	mov.b	r0l, @PADR:24

	mov.l	#PARAM+OFF_PATTERN, er1
	mov.b	@PARAM+OFF_LEN:24, r2l
send:
	mov.b	@er1+, r0l
1:
	mov.b	@SSR1:24, r0h
	bld	#7, r0h
	bcc	1b
	mov.b	r0l, @TDR1:24
	mov.b	@SSR1:24, r0l
	and.b	#0x7f, r0l
	mov.b	r0l, @SSR1:24
	dec.b	r2l
	bne	send

	mov.l	@PARAM+OFF_INTERVAL:24, er0
1:
	dec.l	#1, er0
	bne	1b

	bra	loop

	.section .param, "a"
	.align 2
param_block:
	.byte	15
	.byte	0
	.long	2000000
	.byte	15
	.byte	0
	.ascii	"DSUB9 TEST OK"
	.byte	0x0d, 0x0a
	.space	56 - 15
