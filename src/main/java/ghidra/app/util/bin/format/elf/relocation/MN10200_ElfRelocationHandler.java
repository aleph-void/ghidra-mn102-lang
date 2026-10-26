/* ###
 * IP: Apache License 2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package ghidra.app.util.bin.format.elf.relocation;

import ghidra.app.util.bin.format.elf.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Program;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.reloc.Relocation.Status;
import ghidra.program.model.reloc.RelocationResult;

/**
 * MN10200 ELF relocations (binutils bfd/elf-m10200.c, RELA, little-endian). PC-relative fields
 * are relative to the end of the field: S + A - (P + size).
 */
public class MN10200_ElfRelocationHandler
		extends AbstractElfRelocationHandler<MN10200_ElfRelocationType, ElfRelocationContext<?>> {

	public static final int EM_MN10200 = 90;
	/** pre-standard e_machine used by early Cygnus toolchains */
	public static final int EM_CYGNUS_MN10200 = 0xdead;

	public MN10200_ElfRelocationHandler() {
		super(MN10200_ElfRelocationType.class);
	}

	@Override
	public boolean canRelocate(ElfHeader elf) {
		return elf.e_machine() == EM_MN10200 || elf.e_machine() == EM_CYGNUS_MN10200;
	}

	private static void put24(Memory memory, Address a, long v) throws MemoryAccessException {
		memory.setByte(a, (byte) v);
		memory.setByte(a.add(1), (byte) (v >> 8));
		memory.setByte(a.add(2), (byte) (v >> 16));
	}

	@Override
	protected RelocationResult relocate(ElfRelocationContext<?> ctx, ElfRelocation relocation,
			MN10200_ElfRelocationType type, Address relocationAddress, ElfSymbol sym,
			Address symbolAddr, long symbolValue, String symbolName)
			throws MemoryAccessException {

		Program program = ctx.getProgram();
		Memory memory = program.getMemory();
		long addend = relocation.getAddend();
		long offset = relocationAddress.getOffset();

		if (type == MN10200_ElfRelocationType.R_MN10200_NONE) {
			return RelocationResult.SKIPPED;
		}
		if (handleUnresolvedSymbol(ctx, relocation, relocationAddress)) {
			return RelocationResult.FAILURE;
		}
		long s = symbolValue + addend;
		switch (type) {
			case R_MN10200_32:
				memory.setInt(relocationAddress, (int) s);
				return new RelocationResult(Status.APPLIED, 4);
			case R_MN10200_24:
				put24(memory, relocationAddress, s);
				return new RelocationResult(Status.APPLIED, 3);
			case R_MN10200_16:
				memory.setShort(relocationAddress, (short) s);
				return new RelocationResult(Status.APPLIED, 2);
			case R_MN10200_8:
				memory.setByte(relocationAddress, (byte) s);
				return new RelocationResult(Status.APPLIED, 1);
			case R_MN10200_PCREL8:
				memory.setByte(relocationAddress, (byte) (s - (offset + 1)));
				return new RelocationResult(Status.APPLIED, 1);
			case R_MN10200_PCREL16:
				memory.setShort(relocationAddress, (short) (s - (offset + 2)));
				return new RelocationResult(Status.APPLIED, 2);
			case R_MN10200_PCREL24:
				put24(memory, relocationAddress, s - (offset + 3));
				return new RelocationResult(Status.APPLIED, 3);
			default:
				markAsUnhandled(program, relocationAddress, type, relocation.getSymbolIndex(),
					symbolName, ctx.getLog());
				return RelocationResult.UNSUPPORTED;
		}
	}
}
