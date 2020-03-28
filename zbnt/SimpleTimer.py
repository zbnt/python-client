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
from .AxiDevice import *

class SimpleTimer(AxiDevice):
	def __init__(self, dev_id, initial_props):
		super().__init__(dev_id, initial_props)

		self.freq = 125000000

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_CLOCK_FREQ:
				if len(prop_bytes) >= 4:
					self.freq = int.from_bytes(prop_bytes[:4], byteorder="little", signed=False)

	def receive_measurement(self, data):
		pass
