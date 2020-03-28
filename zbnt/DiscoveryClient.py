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

import random
import asyncio
import netifaces
import ipaddress

from .MessageReceiver import *

class DiscoveryClient(MessageReceiver):
	MSG_DISCOVERY_PORT = 5466

	def __init__(self, address_list, on_device_discovered):
		super().__init__(self.send_broadcast, self.message_received, None)

		self.address_list = address_list
		self.on_device_discovered = on_device_discovered

	def datagram_received(self, data, addr):
		self.remote_addr = addr
		super().bytes_received(data)

		self.status = MsgRxStatus.MSG_RX_MAGIC
		self.buffer = b"\x00\x00\x00\x00"

	def send_broadcast(self):
		self.validator = random.randint(0, 2**64 - 1)

		message = MessageReceiver.MSG_MAGIC_IDENTIFIER
		message += Messages.MSG_ID_DISCOVERY.to_bytes(2, byteorder="little")
		message += b"\x08\x00"
		message += self.validator.to_bytes(8, byteorder="little")

		for address in self.address_list:
			self.transport.sendto(message, (address, DiscoveryClient.MSG_DISCOVERY_PORT))

	def message_received(self, msg_id, msg_payload):
		if msg_id != Messages.MSG_ID_DISCOVERY or len(msg_payload) <= 67:
			return

		validator = int.from_bytes(msg_payload[0:8], byteorder='little', signed=False)

		if validator != self.validator:
			return

		device = dict()

		device["version"] = (
			msg_payload[11],
			msg_payload[10],
			int.from_bytes(msg_payload[8:10], byteorder='little', signed=False),
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

		msg_ip, _ = self.remote_addr
		ip4 = str(ipaddress.IPv4Address(msg_payload[48:44:-1]))
		ip6 = str(ipaddress.IPv6Address(msg_payload[49:65]))
		address_list = []

		if ip4 != msg_ip:
			return

		if ip4 != "0.0.0.0":
			address_list.append(ip4)

		if ip6 != "::":
			address_list.append(ip6)

		if len(address_list) == 0:
			return

		device["address"] = address_list
		device["port"] = int.from_bytes(msg_payload[65:67], byteorder='little', signed=False)
		device["name"] = msg_payload[67:].decode("UTF-8")

		self.on_device_discovered(device)

	@staticmethod
	async def create(addr, callback):
		loop = asyncio.get_running_loop()

		_, protocol = await loop.create_datagram_endpoint(
			lambda: DiscoveryClient(addr, callback),
			remote_addr=None,
			family=socket.AF_INET,
			allow_broadcast=True
		)

		return protocol

async def discover_devices(timeout):
	address_list = []
	device_list = []

	# Get broadcast address of every available interface
	for iface in netifaces.interfaces():
		for addr_family, addr_list in netifaces.ifaddresses(iface).items():
			if netifaces.address_families[addr_family] == "AF_INET":
				for addr in addr_list:
					if "broadcast" in addr:
						address_list.append(addr["broadcast"])

	# Broadcast DISCOVERY message on every interface
	await DiscoveryClient.create(
		address_list,
		lambda dev:	device_list.append(dev)
	)

	await asyncio.sleep(timeout)
	return device_list
