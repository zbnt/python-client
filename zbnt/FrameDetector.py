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
from .AxiDevice import *

class FrameDetector(AxiDevice):
	class FeatureBits(IntFlag):
		HAS_CMP_UNIT  = 1
		HAS_EDIT_UNIT = 2
		HAS_CSUM_UNIT = 4
		HAS_FPU       = 8

	def __init__(self, dev_id, initial_props):
		super().__init__(dev_id, initial_props)

		self.features = FrameDetector.FeatureBits(0)

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_FEATURE_BITS:
				if len(prop_bytes) >= 4:
					self.features = FrameDetector.FeatureBits(int.from_bytes(prop_bytes[:4], byteorder="little", signed=False))
			elif prop_id == Properties.PROP_NUM_SCRIPTS:
				if len(prop_bytes) >= 4:
					self.num_scripts = int.from_bytes(prop_bytes[:4], byteorder="little", signed=False)
			elif prop_id == Properties.PROP_MAX_SCRIPT_SIZE:
				if len(prop_bytes) >= 4:
					self.max_script_size = int.from_bytes(prop_bytes[:4], byteorder="little", signed=False)
			elif prop_id == Properties.PROP_FIFO_SIZE:
				if len(prop_bytes) >= 8:
					self.tx_fifo_size = int.from_bytes(prop_bytes[:4], byteorder="little", signed=False)
					self.extr_fifo_size = int.from_bytes(prop_bytes[4:8], byteorder="little", signed=False)

	def receive_measurement(self, data):
		pass
