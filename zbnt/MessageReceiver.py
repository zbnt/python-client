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

import socket
import asyncio
import netifaces

from enum import Enum, auto

from .Enums import *

class MsgRxStatus(Enum):
	MSG_RX_MAGIC = auto()
	MSG_RX_HEADER = auto()
	MSG_RX_EXTENDED_HEADER = auto()
	MSG_RX_DATA = auto()

class MessageReceiver(asyncio.Protocol):
	MSG_MAGIC_IDENTIFIER = b"\xFFZB\x02"

	def __init__(self, on_connection_made, on_message, on_error):
		loop = asyncio.get_running_loop()

		self.on_connection_lost = loop.create_future()
		self.on_connection_made = on_connection_made
		self.on_message = on_message
		self.on_error = on_error

		self.status = MsgRxStatus.MSG_RX_MAGIC
		self.buffer = b"\x00\x00\x00\x00"
		self.count = 0
		self.size = 0
		self.id = 0

	def connection_made(self, transport):
		self.transport = transport

		if self.on_connection_made != None:
			self.on_connection_made()

	def bytes_received(self, data):
		for b in data:
			b = b.to_bytes(1, "little")

			if self.status == MsgRxStatus.MSG_RX_MAGIC:
				# Magic sequence: \xFFZB\x02
				self.buffer = self.buffer[1:] + b

				if self.buffer == MessageReceiver.MSG_MAGIC_IDENTIFIER:
					self.status = MsgRxStatus.MSG_RX_HEADER
					self.buffer = b""
			elif self.status == MsgRxStatus.MSG_RX_HEADER:
				# Header: message_id (2 bytes) + length (2 bytes)
				self.buffer += b

				if len(self.buffer) == 4:
					self.id = int.from_bytes(self.buffer[0:2], byteorder='little', signed=False)
					self.size = int.from_bytes(self.buffer[2:4], byteorder='little', signed=False)
					self.buffer = b""

					if self.id == Messages.MSG_ID_EXTENDED:
						self.status = MsgRxStatus.MSG_RX_EXTENDED_HEADER
						self.id = self.size
					elif self.size == 0:
						if self.on_message != None:
							self.on_message(self.id, self.buffer)

						self.status = MsgRxStatus.MSG_RX_MAGIC
						self.buffer = b"\x00\x00\x00\x00"
					else:
						self.status = MsgRxStatus.MSG_RX_DATA

					try:
						self.id = Messages(self.id)
					except ValueError:
						pass
			elif self.status == MsgRxStatus.MSG_RX_EXTENDED_HEADER:
				# Extended header: special_id (2 bytes) + real_id (2 bytes) + real_length (4 bytes)
				self.buffer += b

				if len(self.buffer) == 4:
					self.size = int.from_bytes(self.buffer, byteorder='little', signed=False)
					self.buffer = b""

					if self.size == 0:
						self.status = MsgRxStatus.MSG_RX_DATA
					else:
						if self.on_message != None:
							self.on_message(self.id, self.buffer)

						self.status = MsgRxStatus.MSG_RX_MAGIC
						self.buffer = b"\x00\x00\x00\x00"
			else:
				self.buffer += b

				if len(self.buffer) == self.size:
					if self.on_message != None:
						self.on_message(self.id, self.buffer)

					self.status = MsgRxStatus.MSG_RX_MAGIC
					self.buffer = b"\x00\x00\x00\x00"

	def error_received(self, exc):
		if self.on_error != None:
			self.on_error(exc)

	def connection_lost(self, exc):
		self.on_connection_lost.set_result(True)
