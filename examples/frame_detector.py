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
from zbnt import ZbntClient, TrafficGenerator, Devices, Properties, discover_devices

output_file = open("results.csv", "w")

def write_fd_measurement(dev_id, measurement_data):
	measurement_data = list(measurement_data)
	measurement_data[-1] = measurement_data[-1].hex()

	output_file.write(",".join(map(str, measurement_data)))
	output_file.write("\n")

async def main():
	# Scan for devices, ask the user to select one if multiple devices are found

	devices = await discover_devices(4)

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

		print("")
	else:
		req_dev = 0

	req_dev = devices[req_dev]

	# Connect to selected device, load a bitstream

	print("- Connecting to {0} ({1})".format(req_dev["name"], req_dev["address"]))

	client = await ZbntClient.connect(req_dev["address"], req_dev["port"])

	if client == None:
		print("Error: Failed to connect to device")
		exit(1)

	print("- Connected!")

	if not await client.load_bitstream("dual_tgen_detector"):
		print("Error: Failed to load bitstream")
		exit(1)

	print("- Bitstream loaded")

	# Get handle to the timer, eth0 traffic generator and eth0 stats collector

	timer = client.get_device(Devices.DEV_SIMPLE_TIMER)
	tgen0 = client.get_device(Devices.DEV_TRAFFIC_GENERATOR, {0})
	fd0 = client.get_device(Devices.DEV_FRAME_DETECTOR, {2, 3})

	# Set function to be called every time the server sends measurement data

	fd0.measurement_handler = write_fd_measurement

	# Tell the server to start the run, this will initialize the DMA core

	await client.start_run()

	# Configure tgen0, sc0 and the timer

	template_bytes, template_mask = TrafficGenerator.load_frame_template("arp_response.hex")
	script_bytes = fd0.load_script("arp_spoof_response.zbscr")

	await fd0.set_property(Properties.PROP_FRAME_SCRIPT, script_bytes, {"index": 0})
	await fd0.set_property(Properties.PROP_ENABLE_SCRIPT, 1)
	await fd0.set_property(Properties.PROP_ENABLE_LOG, True)
	await fd0.set_property(Properties.PROP_ENABLE, True)

	await tgen0.set_property(Properties.PROP_FRAME_TEMPLATE, template_bytes)
	await tgen0.set_property(Properties.PROP_FRAME_TEMPLATE_MASK, template_mask)
	await tgen0.set_property(Properties.PROP_FRAME_SIZE, 64)
	await tgen0.set_property(Properties.PROP_FRAME_GAP, 12500000)
	await tgen0.set_property(Properties.PROP_ENABLE, True)

	await timer.set_property(Properties.PROP_TIMER_LIMIT, 10 * timer.freq)
	await timer.set_property(Properties.PROP_ENABLE, True)

	# Wait until all data has been sent and the server stops the run

	await client.wait_for_run_end()

	# Get overflow counters

	res, (overflow_a2b, overflow_b2a) = await fd0.get_property(Properties.PROP_OVERFLOW_COUNT)

	if res:
		print("- Overflow counters: {0}, {1}".format(overflow_a2b, overflow_b2a))

asyncio.run(main())

output_file.close()
