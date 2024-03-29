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

class LatencyMeasurer(AxiDevice):
	device_type = Devices.DEV_LATENCY_MEASURER

	_property_encoding = {
		Properties.PROP_ENABLE: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_LOG: (encode_bool, decode_bool),
		Properties.PROP_ENABLE_BROADCAST: (encode_bool, decode_bool),
		Properties.PROP_MAC_ADDR: (encode_mac, decode_mac),
		Properties.PROP_IP_ADDR: (encode_ip4, decode_ip4),
		Properties.PROP_FRAME_PADDING: (encode_u16, decode_u16),
		Properties.PROP_FRAME_GAP: (encode_u32, decode_u32),
		Properties.PROP_TIMEOUT: (encode_u32, decode_u32),
		Properties.PROP_OVERFLOW_COUNT: (None, decode_u64)
	}

	_property_params = {
		Properties.PROP_MAC_ADDR: (1, [
			("index", encode_u8)
		]),

		Properties.PROP_IP_ADDR: (1, [
			("index", encode_u8)
		])
	}

	class Measurement:
		def __init__(self, time, number, ping, pong, lost_pings, lost_pongs):
			self.time = time
			self.number = number
			self.ping = ping
			self.pong = pong
			self.lost_pings = lost_pings
			self.lost_pongs = lost_pongs

		def __repr__(self):
			return f"LatencyMeasurer.Measurement(time={self.time}, number={self.number}, latency=({self.ping}, {self.pong}), lost=({self.lost_pings}, {self.lost_pongs}))"

	def __init__(self, parent, dev_id, initial_props):
		super().__init__(parent, dev_id, initial_props)

	def receive_measurement(self, data):
		if len(data) < 40:
			return None

		time = decode_u64(data[0:8])

		num_pings = decode_u64(data[8:16])
		ping_time = decode_u32(data[16:20])
		pong_time = decode_u32(data[20:24])

		num_lost_pings = decode_u64(data[24:32])
		num_lost_pongs = decode_u64(data[32:40])

		return LatencyMeasurer.Measurement(time, num_pings, ping_time, pong_time, num_lost_pings, num_lost_pongs)
