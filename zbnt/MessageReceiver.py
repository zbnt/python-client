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

from enum import Enum, auto

from .Enums import *
from .Encoding import *

class MsgRxStatus(Enum):
	MSG_RX_MAGIC = auto()
	MSG_RX_HEADER = auto()
	MSG_RX_EXTENDED_HEADER = auto()
	MSG_RX_DATA = auto()

class MessageReceiver(asyncio.Protocol):
	MSG_MAGIC_IDENTIFIER = b"\xFFZB\x02"

	def __init__(self):
		self.status = MsgRxStatus.MSG_RX_MAGIC
		self.buffer = b""
		self.count = 0
		self.size = 0
		self.id = 0

	def connection_made(self, transport):
		self.transport = transport

	def bytes_received(self, data):
		for b in data:
			b = b.to_bytes(1, "little")

			if self.status == MsgRxStatus.MSG_RX_MAGIC:
				# Magic sequence: \xFFZB\x02
				self.buffer += b

				if len(self.buffer) == len(MessageReceiver.MSG_MAGIC_IDENTIFIER):
					if self.buffer == MessageReceiver.MSG_MAGIC_IDENTIFIER:
						self.status = MsgRxStatus.MSG_RX_HEADER
						self.buffer = b""
					else:
						print(f"W: Received incorrect magic bytes: {self.buffer.hex()}")
						self.buffer = self.buffer[1:]
			elif self.status == MsgRxStatus.MSG_RX_HEADER:
				# Header: message_id (2 bytes) + length (2 bytes)
				self.buffer += b

				if len(self.buffer) == 4:
					self.id = decode_u16(self.buffer[0:2])
					self.size = decode_u16(self.buffer[2:4])
					self.buffer = b""

					if self.id == Messages.MSG_ID_EXTENDED:
						self.status = MsgRxStatus.MSG_RX_EXTENDED_HEADER
						self.id = self.size
					elif self.size == 0:
						self.message_received(self.id, self.buffer)
						self.status = MsgRxStatus.MSG_RX_MAGIC
						self.buffer = b""
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
					self.size = decode_u32(self.buffer)
					self.buffer = b""

					if self.size == 0:
						self.status = MsgRxStatus.MSG_RX_DATA
					else:
						self.message_received(self.id, self.buffer)
						self.status = MsgRxStatus.MSG_RX_MAGIC
						self.buffer = b""
			else:
				self.buffer += b

				if len(self.buffer) == self.size:
					self.message_received(self.id, self.buffer)
					self.status = MsgRxStatus.MSG_RX_MAGIC
					self.buffer = b""

	def message_received(self, msg_id, msg_payload):
		pass

	def error_received(self, err):
		raise ConnectionError(err)

	def connection_lost(self, exc):
		if exc != None:
			raise ConnectionError(exc)
