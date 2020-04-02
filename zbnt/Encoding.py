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

import struct

# encode_x : number to bytes

def encode_bool(value):
	return bool(value).to_bytes(1, byteorder="little", signed=False)

def encode_u8(value):
	return value.to_bytes(1, byteorder="little", signed=False)

def encode_u16(value):
	return value.to_bytes(2, byteorder="little", signed=False)

def encode_u32(value):
	return value.to_bytes(4, byteorder="little", signed=False)

def encode_u64(value):
	return value.to_bytes(8, byteorder="little", signed=False)

def encode_s8(value):
	return value.to_bytes(1, byteorder="little", signed=True)

def encode_s16(value):
	return value.to_bytes(2, byteorder="little", signed=True)

def encode_s32(value):
	return value.to_bytes(4, byteorder="little", signed=True)

def encode_s64(value):
	return value.to_bytes(8, byteorder="little", signed=True)

def encode_float(value):
	return struct.pack("<f", value)

def encode_double(value):
	return struct.pack("<d", value)

def encode_str(value):
	return value.encode("UTF-8")

def encode_mac(value):
	return bytes.fromhex(value.replace(":", "").replace(" ", ""))

def encode_ip4(value):
	return b"".join(map(lambda x: encode_u8(int(x)), value.split(".")[::-1]))

# decode_x : bytes to number

def decode_bool(value):
	return bool(value[0])

def decode_u8(value):
	return int.from_bytes(value[:1], byteorder="little", signed=False)

def decode_u16(value):
	return int.from_bytes(value[:2], byteorder="little", signed=False)

def decode_u32(value):
	return int.from_bytes(value[:4], byteorder="little", signed=False)

def decode_u64(value):
	return int.from_bytes(value[:8], byteorder="little", signed=False)

def decode_s8(value):
	return int.from_bytes(value[:1], byteorder="little", signed=True)

def decode_s16(value):
	return int.from_bytes(value[:2], byteorder="little", signed=True)

def decode_s32(value):
	return int.from_bytes(value[:4], byteorder="little", signed=True)

def decode_s64(value):
	return int.from_bytes(value[:8], byteorder="little", signed=True)

def decode_float(value):
	return struct.unpack("<f", value)[0]

def decode_double(value):
	return struct.unpack("<d", value)[0]

def decode_str(value):
	return value.encode("UTF-8")

def decode_mac(value):
	hex_mac = value.hex().upper()
	return ":".join([hex_mac[i:i+1] for i in range(0, len(hex_mac), 2)])

def decode_ip4(value):
	return "{0}.{1}.{2}.{3}".format(value[3], value[2], value[1], value[0])
