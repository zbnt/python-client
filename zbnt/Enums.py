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

from enum import IntEnum, auto

class Messages(IntEnum):
	# Added in 2.0.0

	MSG_ID_DISCOVERY    = 1
	MSG_ID_HELLO        = 2
	MSG_ID_PROGRAM_PL   = 3
	MSG_ID_RUN_START    = 4
	MSG_ID_RUN_STOP     = 5
	MSG_ID_SET_PROPERTY = 6
	MSG_ID_GET_PROPERTY = 7
	MSG_ID_USER_MESSAGE = 8

	MSG_ID_EXTENDED     = 0x7FFF
	MSG_ID_MEASUREMENT  = 0x8000

class Properties(IntEnum):
	# Added in 2.0.0

	PROP_ENABLE = 1
	PROP_ENABLE_LOG = auto()
	PROP_ENABLE_BURST = auto()
	PROP_ENABLE_SCRIPT = auto()
	PROP_ENABLE_PATTERN = auto()
	PROP_ENABLE_BROADCAST = auto()

	PROP_TIMER_MODE = auto()
	PROP_TIMER_TIME = auto()
	PROP_TIMER_LIMIT = auto()

	PROP_FRAME_SIZE = auto()
	PROP_FRAME_GAP = auto()
	PROP_FRAME_PADDING = auto()
	PROP_FRAME_TEMPLATE = auto()
	PROP_FRAME_PATTERN = auto()
	PROP_FRAME_SCRIPT = auto()
	PROP_FRAME_SCRIPT_NAME = auto()

	PROP_BURST_TIME_ON = auto()
	PROP_BURST_TIME_OFF = auto()

	PROP_MAC_ADDR = auto()
	PROP_IP_ADDR = auto()
	PROP_TIMEOUT = auto()

	PROP_OVERFLOW_COUNT = auto()
	PROP_SAMPLE_PERIOD = auto()
	PROP_LFSR_SEED = auto()
	PROP_RESET = auto()

	PROP_PORTS = auto()
	PROP_FEATURE_BITS = auto()
	PROP_NUM_SCRIPTS = auto()
	PROP_MAX_TEMPLATE_SIZE = auto()
	PROP_MAX_SCRIPT_SIZE = auto()
	PROP_FIFO_SIZE = auto()
	PROP_PHY_ADDR = auto()
	PROP_CLOCK_FREQ = auto()

class Devices(IntEnum):
	# Added in 2.0.0

	DEV_AXI_DMA = 1
	DEV_AXI_MDIO = auto()
	DEV_DMA_BUFFER = auto()
	DEV_SIMPLE_TIMER = auto()
	DEV_FRAME_DETECTOR = auto()
	DEV_STATS_COLLECTOR = auto()
	DEV_LATENCY_MEASURER = auto()
	DEV_TRAFFIC_GENERATOR = auto()
