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
