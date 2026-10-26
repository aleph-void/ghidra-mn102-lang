# MN10200 routines for the real-code check (gcc mn10200 calling convention: arguments in d0, d1,
# then the stack; result in d0, pointers in a0; d2, d3, a1, a2 callee-saved).
	.text
	.global _start
_start:
	mov 0x9800,a3
	mov 0x9000,a0
	mov 0x55,d0
	mov 16,d1
	jsr fill
	mov 0x9000,a0
	jsr length
	mov d0,d2
	mov 3,d0
	mov 7,d1
	jsr mul16
	add d2,d0
	mov 2,d1
	jsr dispatch
loop:	bra loop

# void fill(char *a0, int d0 value, int d1 count)
fill:
	add -4,a3
	movx d2,(0,a3)
	mov d0,d2
	sub d0,d0
	bra .Ltest
.Lloop:
	movb d2,(a0)
	add 1,d0
	add 1,a0
.Ltest:
	cmp d1,d0
	bcs .Lloop
	movx (0,a3),d2
	add 4,a3
	rts

# int length(const char *a0)
length:
	sub d0,d0
.Lnext:
	movbu (a0),d1
	cmp 0,d1
	beq .Ldone
	add 1,d0
	add 1,a0
	bra .Lnext
.Ldone:
	rts

# int mul16(int d0, int d1)
mul16:
	mul d1,d0
	rts

# int dispatch(int d0 value, int d1 selector): a jump table of 4-byte pointers, bounded with a
# 24-bit compare (bccx)
dispatch:
	mov table,a0
	cmp 3,d1
	bccx .Ldef
	add d1,d1
	add d1,d1
	add d1,a0
	mov (0,a0),a0
	jmp (a0)
.Lzero:	sub d0,d0
	rts
.Lneg:	not d0
	rts
.Lshift:
	add d0,d0
	rts
.Ldef:	mov -1,d0
	rts
	.data
table:	.long .Lzero
	.long .Lneg
	.long .Lshift
