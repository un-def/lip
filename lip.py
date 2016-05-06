#!/usr/bin/env python
# -*- coding: utf-8 -*-
# lip v0.0.4

from __future__ import print_function, unicode_literals

import os
import sys
import signal
import socket
import subprocess
import re
import argparse
from datetime import datetime

VERSION = '0.0.4'

PY3 = True if sys.version_info.major > 2 else False
if PY3:
    import configparser
    customize_configparser = {'inline_comment_prefixes': ';'}
else:
    import ConfigParser as configparser
    customize_configparser = {}
    FileNotFoundError = ConnectionRefusedError = socket.error


def verbose_print(*args, **kwargs):
    if not cli_args.verbose:
        return
    print(*args, **kwargs)


def sigint_handler(signal, frame):
    print("\r<SIGINT>")
    lircd.close()
    sys.exit(0)


def exec_cmd(cmd):   # cmd - str || list
    verbose_print("Key action: " + cmd)
    if isinstance(cmd, str):
        cmd = cmd.split()
    if cmd[0] == 'run':
        cmd.pop(0)
    else:
        cmd.insert(0, 'xdotool')
    subprocess.call(cmd)


def get_cmd_out(cmd):   # cmd - str || list
    if isinstance(cmd, str):
        cmd = cmd.split()
    cmd_out = subprocess.check_output(cmd).rstrip()
    if PY3:
        cmd_out = cmd_out.decode('utf-8')
    return cmd_out


comm_re = re.compile('([0-9A-Fa-f]+) ([0-9a-f]+) (.+) (.+)')
xdo_cmd_version = ['xdotool', 'version']
xdo_cmd_windowname = ['xdotool', 'getactivewindow', 'getwindowname']
lircd = socket.socket(socket.AF_UNIX)
signal.signal(signal.SIGINT, sigint_handler)

parser = argparse.ArgumentParser(description='lip')
parser.add_argument('-c', '--config',
                    required=False,
                    help='config file')
parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='verbose mode')
cli_args = parser.parse_args()


verbose_print("lip v" + VERSION)

try:
    xdo_version = get_cmd_out(xdo_cmd_version)
except (OSError, FileNotFoundError, subprocess.CalledProcessError):
    sys.exit("Can\'t execute xdotool")
verbose_print(xdo_version)

config = configparser.ConfigParser(**customize_configparser)
if cli_args.config:
    config_path = os.path.abspath(cli_args.config)
else:
    config_path = os.path.join(os.path.expanduser('~'), '.liprc')
if not config.read(config_path):
    sys.exit("Can\'t open {}".format(config_path))
verbose_print("config file: {}".format(config_path))
try:
    config_rc_name = config.get('Settings', 'remote')
except configparser.NoOptionError:
    config_rc_name = None
try:
    use_default_keys = config.getboolean('Settings', 'use_default_keys')
except (configparser.NoOptionError, ValueError):
    use_default_keys = True
apps_sections = config.sections()[2:]

try:
    lircd.connect('/dev/lircd')
except (FileNotFoundError, ConnectionRefusedError):
    sys.exit("Can\'t open /dev/lircd")

verbose_print("\n")

while True:
    comm = lircd.recv(256).rstrip()
    if PY3:
        comm = comm.decode('utf-8')
    verbose_print("Time: {0:%X.%f %x}\nCommand: {1}".format(datetime.now(), comm))
    comm_parsed = comm_re.match(comm)
    if comm_parsed:
        rc_key, rc_name = comm_parsed.group(3, 4)
        if not config_rc_name or rc_name == config_rc_name:
            active_window_name = get_cmd_out(xdo_cmd_windowname)
            verbose_print("Active window: " + active_window_name)
            key_found = False
            for section in apps_sections:
                if config.has_option(section, 'window_name') and re.search(config.get(section, 'window_name'), active_window_name):
                    if config.has_option(section, rc_key):
                        key_found = True
                        key_cmd = config.get(section, rc_key)
                        exec_cmd(key_cmd)
                    break
            if not key_found and use_default_keys and config.has_option('Default', rc_key):
                exec_cmd(config.get('Default', rc_key))
    else:
        print("Can\'t parse: " + comm)
    verbose_print("\n")
