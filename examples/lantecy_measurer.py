#!/usr/bin/env python3
"""
	zbnt/python-client
	Copyright (C) 2021 Oscar R.

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
import os
from zbnt import ZbntClient, StatsCollector, LatencyMeasurer, TrafficGenerator, Devices, Properties, discover_devices

if not os.path.exists("results"):
	os.mkdir("results")

files = [
	open(f"results/{f}.csv", "w") for f in [
		"latency",
		"traffic_p0",
		"traffic_p1",
		"traffic_p2",
		"traffic_p3"
	]
]

def handle_measurement(device, measurement):
	measurement_csv = ",".join(map(str, measurement.__dict__.values()))

	if isinstance(device, LatencyMeasurer):
		files[0].write(measurement_csv)
		files[0].write("\n")
	elif isinstance(device, StatsCollector):
		files[device.ports[0] + 1].write(measurement_csv)
		files[device.ports[0] + 1].write("\n")

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

		print("")
	else:
		req_dev = 0

	req_dev = devices[req_dev]

	if not req_dev["local"]:
		print("- Connecting to {0} ({1})".format(req_dev["name"], req_dev["address"]))
	else:
		print("- Connecting to {0} (PID {1})".format(req_dev["name"], req_dev["pid"]))

	client = await ZbntClient.connect(req_dev)

	if client == None:
		print("Error: Failed to connect to device")
		exit(1)

	print("- Loading bitstream")
	await client.load_bitstream("dual_tgen_latency")

	# Get handle to the timer, eth0/1 traffic generators and latency measurer

	timer = client.get_device(Devices.DEV_SIMPLE_TIMER)
	tgen0 = client.get_device(Devices.DEV_TRAFFIC_GENERATOR, {0})
	tgen1 = client.get_device(Devices.DEV_TRAFFIC_GENERATOR, {1})
	lm = client.get_device(Devices.DEV_LATENCY_MEASURER, {2, 3})
	sc0 = client.get_device(Devices.DEV_STATS_COLLECTOR, {0})
	sc1 = client.get_device(Devices.DEV_STATS_COLLECTOR, {1})
	sc2 = client.get_device(Devices.DEV_STATS_COLLECTOR, {2})
	sc3 = client.get_device(Devices.DEV_STATS_COLLECTOR, {3})

	# Tell the server to start the run, this will initialize the DMA core

	await client.start_run()
	await asyncio.sleep(4)

	# Configure devices

	tg0_template, tg0_source = TrafficGenerator.load_frame_template("udp_broadcast.hex")
	tg1_template, tg1_source = TrafficGenerator.load_frame_template("udp_unicast.hex")

	await lm.set_property(Properties.PROP_MAC_ADDR, "9A:B1:2B:CF:93:02", {"index": 0})
	await lm.set_property(Properties.PROP_MAC_ADDR, "9A:B1:2B:CF:93:03", {"index": 1})
	await lm.set_property(Properties.PROP_IP_ADDR, "192.168.111.102", {"index": 0})
	await lm.set_property(Properties.PROP_IP_ADDR, "192.168.111.103", {"index": 1})
	await lm.set_property(Properties.PROP_FRAME_PADDING, 82)
	await lm.set_property(Properties.PROP_FRAME_GAP, 6250000 - 82)
	await lm.set_property(Properties.PROP_ENABLE_LOG, True)
	await lm.set_property(Properties.PROP_ENABLE, True)

	await tgen0.set_property(Properties.PROP_FRAME_TEMPLATE, tg0_template)
	await tgen0.set_property(Properties.PROP_FRAME_SOURCE, tg0_source)
	await tgen0.set_property(Properties.PROP_FRAME_SIZE, 1500)
	await tgen0.set_property(Properties.PROP_FRAME_GAP, 1200000)
	await tgen0.set_property(Properties.PROP_ENABLE, True)

	await tgen1.set_property(Properties.PROP_FRAME_TEMPLATE, tg1_template)
	await tgen1.set_property(Properties.PROP_FRAME_SOURCE, tg1_source)
	await tgen1.set_property(Properties.PROP_FRAME_SIZE, 1500)
	await tgen1.set_property(Properties.PROP_FRAME_GAP, 1200000)
	await tgen1.set_property(Properties.PROP_ENABLE, True)

	for d in [sc0, sc1, sc2, sc3]:
		await d.set_property(Properties.PROP_SAMPLE_PERIOD, timer.freq // 10)
		await d.set_property(Properties.PROP_ENABLE_LOG, True)
		await d.set_property(Properties.PROP_ENABLE, True)

	await timer.set_property(Properties.PROP_TIMER_LIMIT, 10 * timer.freq)

	# Register measurement handler

	client.set_callback(handle_measurement)

	# Start the timer

	await timer.set_property(Properties.PROP_ENABLE, True)

	# Increase data rate every 2 seconds

	frame_gap = 1200000

	for i in range(4):
		await asyncio.sleep(2)

		frame_gap //= 10

		await tgen0.set_property(Properties.PROP_FRAME_GAP, frame_gap)

	# Wait until all data has been sent and the server stops the run

	await client.wait_for_run_end()

	# Close output files

	for f in files:
		f.close()

asyncio.run(main())
