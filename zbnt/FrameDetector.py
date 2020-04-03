"""
	zbnt/python-client
	Copyright (C) 2020 Oscar R.

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import re
import math
from enum import IntFlag

from .Enums import *
from .Encoding import *
from .AxiDevice import *

class FrameDetector(AxiDevice):
	device_type = Devices.DEV_FRAME_DETECTOR

	_property_encoding = {
		Properties.PROP_ENABLE: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_LOG: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_SCRIPT: (encode_u32, decode_u32),
		Properties.PROP_OVERFLOW_COUNT: (None, lambda x: (decode_u64(x[:8]), decode_u64(x[8:16]))),
		Properties.PROP_FRAME_SCRIPT: (lambda x: x, lambda x: x),
		Properties.PROP_FRAME_SCRIPT_NAME: (encode_str, decode_str)
	}

	_property_params = {
		Properties.PROP_FRAME_SCRIPT: (4, [
			("index", encode_u32)
		]),

		Properties.PROP_FRAME_SCRIPT_NAME: (4, [
			("index", encode_u32)
		])
	}

	_regex_comp_instr = re.compile("^(?:nop|(s?[lg]tq?|eq|or|and)(8|16|24|32|40|48|56|64|[fd])(l?)|eof)$")
	_regex_edit_instr = re.compile("^(?:nop|setr|(set|(?:xn|x)?or|and|add|s?mul)(8|16|32|64|[fd])(l?)|drop|corrupt)$")

	_edit_opcode_dict = {
		"nop":     0b00_00_000_0,
		"set":     0b00_00_001_0,
		"setr":    0b00_01_001_0,
		"and":     0b00_00_010_0,
		"or":      0b00_01_010_0,
		"xor":     0b00_10_010_0,
		"xnor":    0b00_11_010_0,
		"add":     0b00_00_011_0,
		"mul":     0b00_00_100_0,
		"smul":    0b00_10_100_0,
		"drop":    0b00_10_000_0,
		"corrupt": 0b00_01_000_0
	}

	class FeatureBits(IntFlag):
		HAS_CMP_UNIT  = 1
		HAS_EDIT_UNIT = 2
		HAS_CSUM_UNIT = 4
		HAS_FPU       = 8

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

		self.features = FrameDetector.FeatureBits(0)

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_FEATURE_BITS:
				if len(prop_bytes) >= 4:
					self.features = FrameDetector.FeatureBits(decode_u32(prop_bytes))
			elif prop_id == Properties.PROP_NUM_SCRIPTS:
				if len(prop_bytes) >= 4:
					self.num_scripts = decode_u32(prop_bytes)
			elif prop_id == Properties.PROP_MAX_SCRIPT_SIZE:
				if len(prop_bytes) >= 4:
					self.max_script_size = decode_u32(prop_bytes)
			elif prop_id == Properties.PROP_FIFO_SIZE:
				if len(prop_bytes) >= 8:
					self.tx_fifo_size = decode_u32(prop_bytes[:4])
					self.extr_fifo_size = decode_u32(prop_bytes[4:8])

	def receive_measurement(self, data):
		if len(data) < 14:
			return

		if self.measurement_handler == None:
			return

		time = decode_u64(data[0:8])
		match_dir = data[8] - 65
		log_width = data[9]
		ext_count = decode_u16(data[10:12])
		match_mask = decode_u16(data[12:14])
		ext_offset = ((log_width + 13) // log_width) * log_width

		if match_dir < 0 or match_dir > 1:
			return

		if ext_count > len(data) - ext_offset:
			return

		ext_data = data[ext_offset:]

		if ext_count % log_width != 0:
			ext_data = ext_data[:-log_width] + ext_data[-log_width + ext_count % log_width:]

		self.measurement_handler(self.id, (time, match_dir, match_mask, ext_data))

	def load_script(self, path):
		comparator_instr = [(0, 0)] * self.max_script_size
		editor_instr = [(0, 0)] * self.max_script_size
		extr_instr = [0] * self.max_script_size

		i = 0
		offset = 0
		in_section = 0

		with open(path) as file_handle:
			for line in file_handle:
				try:
					line = line[:line.index("#")]
				except ValueError:
					pass

				line = line.strip().lower().split()
				i += 1

				if len(line) > 2:
					raise ValueError("line {0}: Invalid syntax".format(i))

				if len(line) == 0:
					continue

				instr = line[0]
				param = line[1] if len(line) == 2 else ""

				if instr[0] == ".":
					try:
						in_section = ["", ".comp", ".extr", ".edit"].index(instr)
					except ValueError:
						raise ValueError("line {0}: Invalid section type: '{1}'".format(i, instr))

					if len(line) == 2:
						try:
							offset = int(param)
						except ValueError:
							raise ValueError("line {0}: Invalid section offset: '{1}'".format(i, param))
					else:
						offset = 0

					continue

				if in_section == 0:
					raise ValueError("line {0}: Invalid instruction, not inside a section".format(i))

				if in_section == 1:
					for index, opcode, param in self.__parse_comparator_instr(i, instr, param, offset):
						if isinstance(index, tuple):
							for j in range(index[0], index[1]):
								offset = j + 1
								comparator_instr[j] = (opcode, param)
						else:
							offset = index + 1
							comparator_instr[index] = (opcode, param)
				elif in_section == 2:
					begin, end, value = self.__parse_extractor_instr(i, instr, param, offset)

					offset = end

					for j in range(begin, end):
						extr_instr[j] = value
				else:
					for index, opcode, param in self.__parse_editor_instr(i, instr, param, offset):
						if isinstance(index, tuple):
							for j in range(index[0], index[1]):
								offset = j + 1
								editor_instr[j] = (opcode, param)
						else:
							offset = index + 1
							editor_instr[index] = (opcode, param)

		res = b""

		for i in range(self.max_script_size):
			res += encode_u8(comparator_instr[i][0])
			res += encode_u8(((editor_instr[i][0] >> 1) << 1) | (extr_instr[i] & 0b1))
			res += encode_u8(comparator_instr[i][1])
			res += encode_u8(editor_instr[i][1])

		return res

	def __parse_comparator_instr(self, i, instr, param, offset):
		match = FrameDetector._regex_comp_instr.match(instr)

		if match == None:
			raise ValueError("line {0}: Unknown comparator instruction: '{1}'".format(i, instr))

		if instr == "nop":
			return [ ((offset, offset + self.__parse_instr_len(i, offset, param)), 0, 0) ]
		elif instr == "eof":
			return [ (offset, 0b11110010, 0) ]
		else:
			if len(param) == 0:
				raise ValueError("line {0}: Instruction requires a parameter: '{1}'".format(i, instr))

			base = match[1]
			op_size = match[2]
			endianness = match[3]

			instr_param = b""
			instr_size = 0
			opcode = 0

			if len(endianness) == 0:
				# Big-endian
				opcode |= 0b100

			if base[0] == "s":
				# Signed
				opcode |= 0b1000
				base = base[1:]

			try:
				if op_size == "f":
					instr_size = 4
					instr_param = encode_float(float(param))
				elif op_size == "d":
					instr_size = 8
					instr_param = encode_double(float(param))
				else:
					instr_size = int(op_size) // 8
					instr_param = int(param, 0).to_bytes(instr_size, byteorder="little", signed=bool(opcode & 0b1000))
			except:
				raise ValueError("line {0}: Invalid parameter for instruction: '{1}'".format(i, param))

			opcode |= ["eq", "gt", "lt", "gtq", "ltq", "or", "and"].index(base) << 4

			if offset + instr_size > self.max_script_size:
				raise ValueError("line {0}: Instruction ends beyond the script size limit: {1} + {2} > {3}".format(i, offset, instr_size, self.max_script_size))

			if opcode & 0b100:
				instr_param = instr_param[::-1]

			res = []

			for b in instr_param[:-1]:
				res.append( (offset, opcode | 0b01, b) )
				offset += 1

			res.append( (offset, opcode | 0b11, instr_param[-1]) )
			return res

	def __parse_extractor_instr(self, i, instr, param, offset):
		if instr not in ["nop", "ext"]:
			raise ValueError("line {0}: Unknown extractor instruction: '{1}'".format(i, instr))

		return (offset, offset + self.__parse_instr_len(i, offset, param), int(instr == "ext"))

	def __parse_editor_instr(self, i, instr, param, offset):
		match = FrameDetector._regex_edit_instr.match(instr)

		if match == None:
			raise ValueError("line {0}: Unknown editor instruction: '{1}'".format(i, instr))

		if instr == "nop" or instr == "setr":
			return [ ((offset, offset + self.__parse_instr_len(i, offset, param)), FrameDetector._edit_opcode_dict[instr], 0) ]
		elif instr == "drop" or instr == "corrupt":
			return [ (offset, FrameDetector._edit_opcode_dict[instr], 0) ]
		else:
			if len(param) == 0:
				raise ValueError("line {0}: Instruction requires a parameter: '{1}'".format(i, instr))

			base = match[1]
			op_size = match[2]
			endianness = match[3]

			instr_param = b""
			instr_size = 0
			opcode = FrameDetector._edit_opcode_dict[base]
			big_endian = False
			signed = False

			if len(endianness) == 0:
				big_endian = True

				if base in ["add", "mul", "smul"]:
					# Big-endian
					opcode |= 0b10000

			if (opcode & 0b0100) != 0b0100:
				# Bitwise operations are always unsigned, for everything else check the signed bit
				signed = bool(opcode & 0b100000)

			if base == "add" and param[0] == "-":
				# Set as signed, allows using negative parameters
				signed = True

			try:
				if op_size == "f":
					instr_size = 4
					instr_param = encode_float(float(param))
				elif op_size == "d":
					instr_size = 8
					instr_param = encode_double(float(param))
				else:
					instr_size = int(op_size) // 8
					instr_param = int(param, 0).to_bytes(instr_size, byteorder="little", signed=signed)
			except:
				raise ValueError("line {0}: Invalid parameter for instruction: '{1}'".format(i, param))

			if offset + instr_size > self.max_script_size:
				raise ValueError("line {0}: Instruction ends beyond the script size limit: {1} + {2} > {3}".format(i, offset, instr_size, self.max_script_size))

			opcode |= int(math.log2(instr_size)) << 6

			if big_endian:
				instr_param = instr_param[::-1]

			res = [ (offset, opcode, instr_param[0]) ]

			for b in instr_param[1:]:
				offset += 1
				res.append( (offset, 0, b) )

			return res

	def __parse_instr_len(self, i, offset, param):
		if len(param):
			try:
				param = int(param, 0)
			except ValueError:
				raise ValueError("line {0}: Invalid parameter, must be an integer: '{1}'".format(i, param))
		else:
			param = 1

		if param < 0:
			raise ValueError("line {0}: Invalid parameter, must be a positive integer: {1}".format(i, param))

		if offset + param > self.max_script_size:
			raise ValueError("line {0}: Instruction ends beyond the script size limit: {1} + {2} > {3}".format(i, offset, param, self.max_script_size))

		return param
