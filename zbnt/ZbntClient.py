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

from .Encoding import *
from .MessageReceiver import *

class ZbntClient(MessageReceiver):
	def __init__(self):
		super().__init__()

		self.on_connected = asyncio.get_running_loop().create_future()
		self.received_hello = False
		self.connected = False
		self.disconnecting = False
		self.devices = dict()

	@staticmethod
	async def connect(addr, port, timeout=5):
		loop = asyncio.get_running_loop()

		_, client = await loop.create_connection(
			lambda: ZbntClient(),
			addr,
			port
		)

		try:
			if not await asyncio.wait_for(client.on_connected, timeout=timeout):
				return None
		except asyncio.TimeoutError:
			return None

		return client

	def disconnect(self):
		self.disconnecting = True
		self.transport.close()

	def send_message(self, msg_id, payload):
		self.transport.write(MessageReceiver.MSG_MAGIC_IDENTIFIER)
		self.transport.write(encode_u16(msg_id))
		self.transport.write(encode_u16(len(payload)))
		self.transport.write(payload)

	async def set_raw_property(self, dev_id, prop_id, value):
		if not self.connected:
			raise Exception("Not connected to server")

		self.pending_prop = (dev_id, prop_id)
		self.pending_prop_future = asyncio.get_running_loop().create_future()

		payload = encode_u8(dev_id)
		payload += encode_u16(prop_id)
		payload += value
		self.send_message(Messages.MSG_ID_SET_PROPERTY, payload)

		return await self.pending_prop_future

	async def get_raw_property(self, dev_id, prop_id):
		if not self.connected:
			raise Exception("Not connected to server")

		self.pending_prop = (dev_id, prop_id)
		self.pending_prop_future = asyncio.get_running_loop().create_future()

		payload = encode_u8(dev_id)
		payload += encode_u16(prop_id)
		self.send_message(Messages.MSG_ID_GET_PROPERTY, payload)

		return await self.pending_prop_future

	def connection_made(self, transport):
		super().connection_made(transport)
		self.connected = True

		# Connection must start with a HELLO message to the server, or connection will be dropped
		self.send_message(Messages.MSG_ID_HELLO, b"")

	def connection_lost(self, exc):
		self.connected = False

		if not self.received_hello:
			self.on_connected.set_result(False)

		if not self.disconnecting:
			raise ConnectionError(exc)

	def data_received(self, data):
		super().bytes_received(data)

	def create_device(self, dev_id, dev_type, initial_props):
		if dev_type == Devices.DEV_AXI_MDIO:
			return AxiMdio(self, dev_id, initial_props)

		if dev_type == Devices.DEV_SIMPLE_TIMER:
			return SimpleTimer(self, dev_id, initial_props)

		if dev_type == Devices.DEV_FRAME_DETECTOR:
			return FrameDetector(self, dev_id, initial_props)

		if dev_type == Devices.DEV_STATS_COLLECTOR:
			return StatsCollector(self, dev_id, initial_props)

		if dev_type == Devices.DEV_LATENCY_MEASURER:
			return LatencyMeasurer(self, dev_id, initial_props)

		if dev_type == Devices.DEV_TRAFFIC_GENERATOR:
			return TrafficGenerator(self, dev_id, initial_props)

		return AxiDevice(self, dev_id, initial_props)

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
			self.on_connected.set_result(True)

			while i < len(msg_payload) - 2:
				name_size = decode_u16(msg_payload[i:i+2])
				name = msg_payload[i+2:i+2+name_size].decode("UTF-8")

				if len(name):
					self.bitstreams.append(name)

				i += name_size + 2
		elif msg_id == Messages.MSG_ID_PROGRAM_PL:
			if len(msg_payload) < 3:
				return

			success = msg_payload[0]
			name_len = decode_u16(msg_payload[1:3])

			self.active_bitstream = msg_payload[3:3+name_len].decode("UTF-8")
			self.devices = dict()

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
				props_size = decode_u16(msg_payload[i+2:i+4])
				props_bytes = msg_payload[i+4:i+4+props_size]

				while j + 3 < len(props_bytes):
					prop_id = decode_u16(props_bytes[j:j+2])
					prop_size = decode_u16(props_bytes[j+2:j+4])
					prop_value = props_bytes[j+4:j+4+prop_size]

					try:
						prop_id = Properties(prop_id)
					except ValueError:
						pass

					props_list.append( (prop_id, prop_value) )
					j += 4 + prop_size

				self.devices[dev_id] = self.create_device(dev_id, dev_type, props_list)
				i += 4 + props_size
		elif msg_id == Messages.MSG_ID_SET_PROPERTY or msg_id == Messages.MSG_ID_GET_PROPERTY:
			if len(msg_payload) < 4:
				return

			dev_id = msg_payload[0]
			prop_id = decode_u16(msg_payload[1:3])
			success = bool(msg_payload[3])
			value = msg_payload[4:]

			if self.pending_prop != None and self.pending_prop == (dev_id, prop_id):
				if msg_id == Messages.MSG_ID_GET_PROPERTY:
					self.pending_prop_future.set_result( (success, value) )
				else:
					self.pending_prop_future.set_result(success)

				self.pending_prop = None
				self.pending_prop_future = None
		elif msg_id & Messages.MSG_ID_MEASUREMENT:
			dev_id = msg_id & ~Messages.MSG_ID_MEASUREMENT
			dev_obj = self.devices.get(dev_id, None)

			if dev_id != None and len(msg_payload) >= 8:
				dev_id.receive_measurement(msg_payload)
