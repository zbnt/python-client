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

from .Enums import *
from .Encoding import *
from .AxiDevice import *

class TrafficGenerator(AxiDevice):
	device_type = Devices.DEV_TRAFFIC_GENERATOR

	_property_encoding = {
		Properties.PROP_ENABLE: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_BURST: (encode_bool, decode_bool),
		Properties.PROP_FRAME_SIZE: (encode_u16, decode_u16),
		Properties.PROP_FRAME_GAP: (encode_u32, decode_u32),
		Properties.PROP_BURST_TIME_ON: (encode_u16, decode_u16),
		Properties.PROP_BURST_TIME_OFF: (encode_u16, decode_u16),
		Properties.PROP_LFSR_SEED: (encode_u8, decode_u8),
		Properties.PROP_FRAME_TEMPLATE: (lambda x: x, lambda x: x),
		Properties.PROP_FRAME_SOURCE: (lambda x: x, lambda x: x)
	}

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

		self.max_template_size = 0

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_MAX_TEMPLATE_SIZE:
				if len(prop_bytes) >= 4:
					self.max_template_size = decode_u32(prop_bytes)

	@staticmethod
	def load_frame_template(path):
		frame_template = b""
		frame_source = b""

		with open(path) as file_handle:
			i = 1
			seq = ""

			for line in file_handle:
				line = line.strip().lower()

				for j in range(len(line)):
					if line[j] == "#":
						break

					if line[j] in "abcdef0123456789":
						if seq in ["x", "n", "b"]:
							raise ValueError("line {0}, column {1}: Invalid hexadecimal sequence".format(i, j+1))

						seq += line[j]

						if len(seq) == 2:
							frame_template += bytes.fromhex(seq)
							frame_source += encode_u8(0x00)
							seq = ""
					elif line[j] == "x":
						seq += line[j]

						if len(seq) == 2:
							if seq != "xx":
								raise ValueError("line {0}, column {1}: Invalid random byte sequence".format(i, j+1))

							frame_template += b"\x00"
							frame_source += encode_u8(0x01)
							seq = ""
					elif line[j] in "nb":
						seq += line[j]

						if len(seq) == 2:
							if seq not in ["nn", "nb"]:
								raise ValueError("line {0}, column {1}: Invalid frame number sequence".format(i, j+1))

							frame_template += b"\x00"
							frame_source += encode_u8(0x02 if seq == "nn" else 0x03)
							seq = ""
					elif not line[j].isspace():
						raise ValueError("line {0}, column {1}: Invalid character".format(i, j+1))

				if seq != "":
					raise ValueError("line {0}, column {1}: Incomplete byte sequence".format(i, j+1))

				i += 1

		return (frame_template, frame_source)
