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

class AxiMdio(AxiDevice):
	device_type = Devices.DEV_AXI_MDIO

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_PHY_ADDR:
				self.phys = list(prop_bytes)
