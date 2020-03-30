#!/usr/bin/env python3
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
from zbnt import ZbntClient, discover_devices

async def main():
	devices = await discover_devices(2)

	if len(devices) == 0:
		print("Error: No devices found")
		exit(1)

	if len(devices) > 1:
		print("Available devices:\n")

		for i in range(len(devices)):
			print("{0}) {1} ({2})".format(i + 1, devices[i]["name"], devices[i]["address"]))

		req_dev = int(input("\nSelect a device [1-{0}]: ".format(len(devices)))) - 1

		if req_dev < 0 or req_dev >= len(devices):
			print("Error: Invalid device selected")
			exit(1)
	else:
		req_dev = 0

	req_dev = devices[req_dev]

	print("\n- Connecting to {0} ({1})".format(req_dev["name"], req_dev["address"]))

	client = await ZbntClient.connect(req_dev["address"], req_dev["port"])

	if client == None:
		print("Error: Failed to connect to device")
		exit(1)

	print("- Connected!")

	while True:
		print("\nAvailable bitstreams:\n")

		for i in range(len(client.bitstreams)):
			print("{0}) {1} {2}".format(i + 1, client.bitstreams[i], "*" if client.bitstreams[i] == client.active_bitstream else ""))

		req_bit = int(input("\nSelect a bitstream [1-{0}]: ".format(len(client.bitstreams)))) - 1

		if req_bit < 0 or req_bit >= len(client.bitstreams):
			print("Error: Invalid bitstream selected")
			continue

		await client.load_bitstream(client.bitstreams[req_bit])

asyncio.run(main())
