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

class StatsCollector(AxiDevice):
	device_type = Devices.DEV_STATS_COLLECTOR

	_property_encoding = {
		Properties.PROP_ENABLE: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_LOG: (encode_bool, decode_bool),
		Properties.PROP_SAMPLE_PERIOD: (encode_u32, decode_u32),
		Properties.PROP_OVERFLOW_COUNT: (None, decode_u64)
	}

	class Statistics:
		def __init__(self, time, tx_bytes, tx_good, tx_bad, rx_bytes, rx_good, rx_bad):
			self.time = time
			self.tx_bytes = tx_bytes
			self.tx_good = tx_good
			self.tx_bad = tx_bad
			self.rx_bytes = rx_bytes
			self.rx_good = rx_good
			self.rx_bad = rx_bad

		def __repr__(self):
			return f"StatsCollector.Statistics(time={self.time}, tx=({self.tx_bytes}, {self.tx_good}, {self.tx_bad}), rx=({self.rx_bytes}, {self.rx_good}, {self.rx_bad}))"

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

	def receive_measurement(self, data):
		if len(data) < 56:
			return None

		time = decode_u64(data[0:8])

		tx_bytes = decode_u64(data[8:16])
		tx_good = decode_u64(data[16:24])
		tx_bad = decode_u64(data[24:32])

		rx_bytes = decode_u64(data[32:40])
		rx_good = decode_u64(data[40:48])
		rx_bad = decode_u64(data[48:56])

		return StatsCollector.Statistics(time, tx_bytes, tx_good, tx_bad, rx_bytes, rx_good, rx_bad)
