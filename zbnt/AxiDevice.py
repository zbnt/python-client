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

from .Enums import *

class AxiDevice:
	device_type = 0
	_property_encoding = dict()
	_property_params = dict()

	def __init__(self, parent, dev_id, initial_props):
		self.id = dev_id
		self.ports = []
		self.client = parent
		self.measurement_handler = None
		self.valid_properties = list(self._property_encoding)

		for prop_id, prop_bytes in initial_props:
			if prop_id == Properties.PROP_PORTS:
				self.ports = list(prop_bytes)

	def __repr__(self):
		return "zbnt.{0}(dev_id={1}, ports={2})".format(self.__class__.__name__, self.id, str(self.ports))

	def receive_measurement(self, data):
		if self.measurement_handler != None:
			self.measurement_handler(self.id, data)

	async def set_property(self, prop_id, value, params=dict()):
		prop_encoding = self._property_encoding.get(prop_id, None)
		_, prop_params = self._property_params.get(prop_id, (0, []))
		value_bytes = b""

		if prop_encoding == None:
			raise ValueError("Property {0} is invalid for {1}".format(prop_id, self.__class__.__name__))

		encoder, _ = prop_encoding

		if encoder == None:
			raise ValueError("Property {0} is read-only".format(prop_id))

		for param_name, param_encoder in prop_params:
			param_value = params.get(param_name, None)

			if param_value == None:
				raise ValueError("Missing parameter: {0}".format(param_name))

			value_bytes += param_encoder(param_value)

		value_bytes += encoder(value)

		return await self.client.set_raw_property(self.id, prop_id, value_bytes)

	async def get_property(self, prop_id, params=dict()):
		prop_encoding = self._property_encoding.get(prop_id, None)
		params_size, prop_params = self._property_params.get(prop_id, (0, []))
		param_bytes = b""

		if prop_encoding == None:
			raise ValueError("Property {0} is invalid for {1}".format(prop_id, self.__class__.__name__))

		_, decoder = prop_encoding

		if decoder == None:
			raise ValueError("Property {0} is write-only".format(prop_id))

		for param_name, param_encoder in prop_params:
			param_value = params.get(param_name, None)

			if param_value == None:
				raise ValueError("Missing parameter: {0}".format(param_name))

			param_bytes += param_encoder(param_value)

		success, value = await self.client.get_raw_property(self.id, prop_id, param_bytes)

		if not success:
			return (False, None)

		return (success, decoder(value[params_size:]))
