#!/usr/bin/env python
import serial
import sys
import argparse
import socket
from time import time
import re
import signal
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

parser = argparse.ArgumentParser(description='P1 port logger')
parser.add_argument('-P', '--port', help='Path the the serial port', dest='port', action='store', required=True)
args = parser.parse_args()

def handle_signal(signal, frame):
    logger.info('Catched SIGINT, closing serial port')
    try:
        ser.close()
    except Exception as e:
        logger.error('Failed closing serial port: {}'.format(e))
        raise Exception(e)
    raise SystemExit(1)
    
signal.signal(signal.SIGINT, handle_signal)

logger.debug('Opening connection to tsdb')
tsdb_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    tsdb_socket.connect(('localhost',4242))
except Exception as e:
    logger.error('Failed opening connection to tsdb with: {}'.format(e))
    raise Exception(e)
if not tsdb_socket:
    logger.error('Failed opening connection to tsdb')
    raise SystemExit()
else:
    logger.info('Connected to tsdb')

def parse_p1_output(line, metric):
    value = re.match(r'.*\(([0-9.]+)[*)].*', line).group(1)
    logger.info('Storing {metric} with value {value}'.format(metric=metric, value=value))
    return 'put {metric} {time} {value} a=b \n'.format(
            metric=metric,
            time=int(time()),
            value=value
    )

logger.debug('Connecting to serial')
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port=args.port

try:
    ser.open()
except Exception as e:
    logger.error('Failed to open serial port: {}'.format(e))
    raise Exception(e)
logger.info('Connected to serial')

logger.info('Starting main loop')
while True:
    line = ser.readline()
    logger.debug(line)
    if line.startswith('1-0:1.8.1'):
        tsdb_socket.send(parse_p1_output(line,'total.1'))
    if line.startswith('1-0:1.8.2'):
        tsdb_socket.send(parse_p1_output(line,'total.2'))
    if line.startswith('0-0:96.14.0'):
        tsdb_socket.send(parse_p1_output(line,'tariff'))
    if line.startswith('1-0:1.7.0'):
        tsdb_socket.send(parse_p1_output(line,'actual'))
    if line.startswith('1-0:31.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L1.current'))
    if line.startswith('1-0:21.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L1.kW1'))
    if line.startswith('1-0:22.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L1.kW2'))
    if line.startswith('1-0:51.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L2.current'))
    if line.startswith('1-0:41.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L2.kW1'))
    if line.startswith('1-0:42.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L2.kW2'))
    if line.startswith('1-0:71.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L3.current'))
    if line.startswith('1-0:61.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L3.kW1'))
    if line.startswith('1-0:62.7.0'):
        tsdb_socket.send(parse_p1_output(line,'L3.kW2'))

try:
    ser.close()
except Exception as e:
    logger.error('Failed closing serial port: {}'.format(e))
    raise Exception(e)

