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

import asyncio

from .AxiDevice import *
from .AxiMdio import *
from .SimpleTimer import *
from .FrameDetector import *
from .StatsCollector import *
from .LatencyMeasurer import *
from .TrafficGenerator import *

from .MessageReceiver import *

class ZbntClient(MessageReceiver):
	def __init__(self, on_connection_established):
		super().__init__(self.send_hello, self.message_received, None)

		self.on_connection_established = on_connection_established
		self.received_hello = False

	def data_received(self, data):
		super().bytes_received(data)

	def send_hello(self):
		# Connection must start with a HELLO message to the server, or connection will be dropped
		self.transport.write(MessageReceiver.MSG_MAGIC_IDENTIFIER)
		self.transport.write(Messages.MSG_ID_HELLO.to_bytes(2, byteorder="little"))
		self.transport.write(b"\x00\x00")

	@staticmethod
	def create_device(dev_id, dev_type, initial_props):
		if dev_type == Devices.DEV_AXI_MDIO:
			return AxiMdio(dev_id, initial_props)

		if dev_type == Devices.DEV_SIMPLE_TIMER:
			return SimpleTimer(dev_id, initial_props)

		if dev_type == Devices.DEV_FRAME_DETECTOR:
			return FrameDetector(dev_id, initial_props)

		if dev_type == Devices.DEV_STATS_COLLECTOR:
			return StatsCollector(dev_id, initial_props)

		if dev_type == Devices.DEV_LATENCY_MEASURER:
			return LatencyMeasurer(dev_id, initial_props)

		if dev_type == Devices.DEV_TRAFFIC_GENERATOR:
			return TrafficGenerator(dev_id, initial_props)

		return AxiDevice(dev_id, initial_props)

	def message_received(self, msg_id, msg_payload):
		# Server should not send other kind of messages without responding to HELLO first
		if not (self.received_hello ^ (msg_id == Messages.MSG_ID_HELLO)):
			return

		if msg_id == Messages.MSG_ID_HELLO:
			# HELLO response includes list of available bitstreams
			i = 0

			if len(msg_payload) < 2:
				return

			self.bitstreams = []
			self.received_hello = True
			self.active_bitstream = ""

			while i < len(msg_payload) - 2:
				name_size = int.from_bytes(msg_payload[i:i+2], byteorder="little", signed=False)
				name = msg_payload[i+2:i+2+name_size].decode("UTF-8")

				if len(name):
					self.bitstreams.append(name)

				i += name_size + 2
		elif msg_id == Messages.MSG_ID_PROGRAM_PL:
			if len(msg_payload) < 3:
				return

			success = msg_payload[0]
			name_len = int.from_bytes(msg_payload[1:3], byteorder="little", signed=False)

			self.active_bitstream = msg_payload[3:3+name_len].decode("UTF-8")
			self.device_list = dict()

			i = 3 + name_len
			while i + 3 < len(msg_payload):
				dev_id = msg_payload[i]
				dev_type = msg_payload[i+1]

				try:
					dev_type = Devices(dev_type)
				except ValueError:
					pass

				j = 0
				props_list = []
				props_size = int.from_bytes(msg_payload[i+2:i+4], byteorder="little", signed=False)
				props_bytes = msg_payload[i+4:i+4+props_size]

				while j + 3 < len(props_bytes):
					prop_id = int.from_bytes(props_bytes[j:j+2], byteorder="little", signed=False)
					prop_size = int.from_bytes(props_bytes[j+2:j+4], byteorder="little", signed=False)
					prop_value = props_bytes[j+4:j+4+prop_size]

					try:
						prop_id = Properties(prop_id)
					except ValueError:
						pass

					props_list.append( (prop_id, prop_value) )
					j += 4 + prop_size

				self.device_list[dev_id] = ZbntClient.create_device(dev_id, dev_type, props_list)
				i += 4 + props_size

			print(self.active_bitstream, self.device_list)
		elif msg_id == Messages.MSG_ID_SET_PROPERTY or msg_id == Messages.MSG_ID_GET_PROPERTY:
			pass
		elif msg_id & Messages.MSG_ID_MEASUREMENT:
			dev_id = msg_id & ~Messages.MSG_ID_MEASUREMENT
			dev_obj = self.device_list.get(dev_id, None)

			if dev_id != None and len(msg_payload) >= 8:
				dev_id.receive_measurement(msg_payload)

	@staticmethod
	async def connect(addr, port, callback):
		loop = asyncio.get_running_loop()

		_, protocol = await loop.create_connection(
			lambda: ZbntClient(callback),
			addr,
			port
		)

		return protocol
