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

class SimpleTimer(AxiDevice):
	device_type = Devices.DEV_SIMPLE_TIMER

	_property_encoding = {
		Properties.PROP_ENABLE: (encode_bool, decode_bool),
		Properties.PROP_TIMER_TIME: (None, decode_u64),
		Properties.PROP_TIMER_LIMIT: (encode_u64, decode_u64)
	}

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

		self.freq = 125000000

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_CLOCK_FREQ:
				if len(prop_bytes) >= 4:
					self.freq = int.from_bytes(prop_bytes[:4], byteorder="little", signed=False)

	def __repr__(self):
		return "zbnt.{0}(dev_id={1}, freq={2})".format(self.__class__.__name__, self.id, self.freq)
