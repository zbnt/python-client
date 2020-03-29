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
