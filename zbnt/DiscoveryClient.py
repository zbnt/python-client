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
import random
import asyncio
import netifaces
import ipaddress

from .Encoding import *
from .MessageReceiver import *

class DiscoveryClient(MessageReceiver):
	MSG_DISCOVERY_PORT = 5466

	def __init__(self, address_list, ip6):
		super().__init__()

		self.ip6 = ip6
		self.address_list = address_list
		self.devices_found = []
		self.address_set = set([])

	@staticmethod
	async def create(addr, ip6):
		loop = asyncio.get_running_loop()

		_, protocol = await loop.create_datagram_endpoint(
			lambda: DiscoveryClient(addr, ip6),
			remote_addr=None,
			family=socket.AF_INET6 if ip6 else socket.AF_INET,
			allow_broadcast=True
		)

		return protocol

	def connection_made(self, transport):
		super().connection_made(transport)

		self.validator = random.randint(0, 2**64 - 1)

		message = MessageReceiver.MSG_MAGIC_IDENTIFIER
		message += encode_u16(Messages.MSG_ID_DISCOVERY)
		message += encode_u16(8)
		message += encode_u64(self.validator)

		for address in self.address_list:
			if not self.ip6:
				self.transport.sendto(message, (address, DiscoveryClient.MSG_DISCOVERY_PORT))
			else:
				self.transport.sendto(message, address)

	def datagram_received(self, data, addr):
		self.remote_addr = addr
		super().bytes_received(data)

		self.status = MsgRxStatus.MSG_RX_MAGIC
		self.buffer = b""

	def error_received(self, err):
		pass

	def connection_lost(self, exc):
		pass

	def message_received(self, msg_id, msg_payload):
		if msg_id != Messages.MSG_ID_DISCOVERY or len(msg_payload) <= 54:
			return

		validator = decode_u64(msg_payload[0:8])

		if validator != self.validator:
			return

		device = dict()

		device["version"] = (
			msg_payload[11],
			msg_payload[10],
			decode_u16(msg_payload[8:10]),
			msg_payload[12:28].strip(b"\x00").decode("UTF-8"),
			msg_payload[28:44].strip(b"\x00").decode("UTF-8"),
			"d" if msg_payload[44] else ""
		)

		device["versionstr"] = "{0}.{1}.{2}".format(*device["version"][0:3])

		if len(device["version"][3]) != 0:
			device["versionstr"] += "-" + device["version"][3]

		if len(device["version"][4]) != 0:
			device["versionstr"] += "+" + device["version"][4]

			if len(device["version"][5]) != 0:
				device["versionstr"] += ".d"
		elif len(device["version"][5]) != 0:
			device["versionstr"] += "+d"

		if not self.ip6:
			ip, _ = self.remote_addr
		else:
			ip, _ = socket.getnameinfo(self.remote_addr, socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)

		device["address"] = ip
		device["local"] = bool(msg_payload[45])

		if not device["local"]:
			device["port"] = decode_u16(msg_payload[46:48])
		else:
			device["pid"] = decode_s64(msg_payload[46:54])

		device["name"] = msg_payload[54:].decode("UTF-8")

		if ip not in self.address_set:
			self.address_set.add(ip)
			self.devices_found.append(device)

async def discover_devices(timeout, ip4=False):
	address4_set = set(["127.0.0.1"])
	address6_set = set([])

	# Get broadcast address of every available interface

	for iface in netifaces.interfaces():
		if ip4:
			for addr_family, addr_list in netifaces.ifaddresses(iface).items():
				if netifaces.address_families[addr_family] == "AF_INET":
					for addr in addr_list:
						if "broadcast" in addr:
							address4_set.add(addr["broadcast"])
						elif addr["addr"][:8] == "169.254.":
							address4_set.add("169.254.255.255")

		address6_set.add(
			socket.getaddrinfo(
				"ff12::{0}%{1}".format(DiscoveryClient.MSG_DISCOVERY_PORT, iface),
				5466, socket.AF_INET6, socket.SOCK_DGRAM
			)[0][-1]
		)

	# Broadcast DISCOVERY message on every interface

	ip4_client = await DiscoveryClient.create(address4_set, False)
	ip6_client = await DiscoveryClient.create(address6_set, True)

	await asyncio.sleep(timeout)

	return ip4_client.devices_found + ip6_client.devices_found
