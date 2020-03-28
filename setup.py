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

import setuptools

setuptools.setup(
	name = "zbnt-client",
	version = "1.0.0",
	packages = setuptools.find_packages(),

	install_requires=["netifaces"],

	author = "Oscar R.",
	author_email = "oscar@oscar-rc.dev",

	description = "Python library for controlling ZBNT devices",
	license="GPLv3",
	keywords = "",
	url = "https://github.com/zbnt",
	project_urls = {
		"Source Code": "https://github.com/zbnt/python-client"
	},
	classifiers = [
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Programming Language :: Python :: 3",
		"Topic :: System :: Networking",
		"Topic :: System :: Networking :: Monitoring",
		"Intended Audience :: Developers",
		"Development Status :: 4 - Beta"
	]
)
