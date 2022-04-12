"""
	zbnt/python-client
	Copyright (C) 2022 Oscar R.

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

PCAP_SHB_BLOCKTYPE   = 0x0A0D0D0A
PCAP_BYTEORDER_MAGIC = 0x1A2B3C4D
PCAP_IDB_BLOCKTYPE   = 0x00000001
PCAP_EPB_BLOCKTYPE   = 0x00000006

class PcapWriter:
	def __init__(self, output):
		if isinstance(output, str):
			self.output = open(output, "wb")
		else:
			self.output = output

		self.clk_period = 8
		self.if_count = 0
		self.if_map = dict()

		# Section Header Block

		shb_payload = PCAP_BYTEORDER_MAGIC.to_bytes(4, "little")
		shb_payload += b"\x01\x00" # Major Version
		shb_payload += b"\x00\x00" # Minor Version
		shb_payload += b"\xFF" * 8 # Section Length (not specified)

		self.__write_block(PCAP_SHB_BLOCKTYPE, shb_payload)

	def __repr__(self):
		return f"PcapWriter(file={self.output})"

	def register_devices(self, client):
		for d in client.devices.values():
			if d.device_type == Devices.DEV_SIMPLE_TIMER:
				self.clk_period = 1_000_000_000 // d.freq
			elif d.device_type == Devices.DEV_FRAME_DETECTOR:
				port_a, port_b = d.ports

				self.if_map[d.id] = self.if_count
				self.__register_interface(f"eth{port_a}_to_eth{port_b}", d.extr_fifo_size)
				self.__register_interface(f"eth{port_b}_to_eth{port_a}", d.extr_fifo_size)

	def handle_measurement(self, device, measurement):
		iface_id = self.if_map.get(device.id)

		if iface_id != None:
			self.__write_frame(iface_id + measurement.direction, measurement.time, measurement.number, measurement.match, measurement.flags, measurement.payload)

	def __register_interface(self, name, snap_len):
		# Interface Definition Block

		idb_payload = b"\x01\x00"  # LinkType (LINKTYPE_ETHERNET)
		idb_payload += b"\x00\x00" # Reserved
		idb_payload += snap_len.to_bytes(4, "little")

		# Option (if_name)
		idb_payload += PcapWriter.__build_option(2, name.encode())

		# Option (if_tsresol)
		idb_payload += PcapWriter.__build_option(9, b"\x09")

		self.__write_block(PCAP_IDB_BLOCKTYPE, idb_payload)
		self.if_count += 1

	def __write_frame(self, iface_id, time, number, match_flags, frame_flags, frame):
		time = (self.clk_period * time).to_bytes(8, "little")
		flen = len(frame).to_bytes(4, "little")
		padding = b"\x00" * ((4 - len(frame) % 4) % 4)
		flags = ((match_flags << 8) | (frame_flags >> 1)).to_bytes(4, "little")

		# Enhanced Packet Block

		epb_payload = iface_id.to_bytes(4, "little") # Interface ID
		epb_payload += time[4:]                      # Timestamp High
		epb_payload += time[:4]                      # Timestamp Low
		epb_payload += flen                          # Captured Length
		epb_payload += flen                          # Original Length
		epb_payload += frame                         # Payload
		epb_payload += padding                       # Payload padding

		# Option (epb_packetid)
		epb_payload += PcapWriter.__build_option(5, number.to_bytes(8, "little"))

		# Option (opt_custom)
		epb_payload += PcapWriter.__build_option(2989, flags)

		self.__write_block(PCAP_EPB_BLOCKTYPE, epb_payload)

	def __write_block(self, type_id, payload):
		padding = b"\x00" * ((4 - len(payload) % 4) % 4)
		length = 12 + len(payload) + len(padding)

		self.output.write(type_id.to_bytes(4, "little"))
		self.output.write(length.to_bytes(4, "little"))
		self.output.write(payload)
		self.output.write(padding)
		self.output.write(length.to_bytes(4, "little"))

	@staticmethod
	def __build_option(type_id, value):
		padding = b"\x00" * ((4 - len(value) % 4) % 4)
		return type_id.to_bytes(2, "little") + len(value).to_bytes(2, "little") + value + padding
