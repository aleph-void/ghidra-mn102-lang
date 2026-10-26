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

/** MN10200 ELF relocation types (binutils include/elf/mn10200.h). */
public enum MN10200_ElfRelocationType implements ElfRelocationType {

	R_MN10200_NONE(0),
	R_MN10200_32(1),
	R_MN10200_16(2),
	R_MN10200_8(3),
	R_MN10200_24(4),
	R_MN10200_PCREL8(5),
	R_MN10200_PCREL16(6),
	R_MN10200_PCREL24(7);

	public final int typeId;

	private MN10200_ElfRelocationType(int typeId) {
		this.typeId = typeId;
	}

	@Override
	public int typeId() {
		return typeId;
	}
}
