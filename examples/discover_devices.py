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
from zbnt import discover_devices

async def main():
	devices = await discover_devices(3)

	for d in devices:
		print(d["name"])
		print("    - Version:", d["versionstr"])
		print("    - Local:", d["local"])

		if not d["local"]:
			print("    - Address:", d["address"])
			print("    - Port:", str(d["port"]))
		else:
			print("    - PID:", str(d["pid"]))

		print("")

asyncio.run(main())
