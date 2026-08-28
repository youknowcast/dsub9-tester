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

BRR_38400	= 15
SCR_TE		= 0x20
SSR_TDRE	= 0x80

_start:
	mov.b	#0x00, r0l
	mov.b	r0l, @SCR1:24
	mov.b	#0x00, r0l
	mov.b	r0l, @SMR1:24
	mov.b	#BRR_38400, r0l
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

	mov.l	#msg, er1
	mov.b	#msg_len, r2l
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

	mov.l	#2000000, er0
1:
	dec.l	#1, er0
	bne	1b

	bra	loop

msg:
	.ascii	"DSUB9 TEST OK"
	.byte	0x0d, 0x0a
.set msg_len, . - msg