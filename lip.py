#!/usr/bin/env python
# -*- coding: utf-8 -*-
# lip v0.0.4
import sys
import socket
import re
import subprocess
import os
import signal

py3 = True if sys.version_info.major > 2 else False
if py3:
    import configparser
    customize_configparser = {'inline_comment_prefixes': ';'}
else:
    import ConfigParser as configparser
    customize_configparser = {}
    FileNotFoundError = ConnectionRefusedError = socket.error

if len(sys.argv) > 1 and (sys.argv[1] == '-v' or sys.argv[1] == '--verbose'):
    verbose = True
    print("lip v0.0.4")
    from datetime import datetime
else:
    verbose = False

def sigint_handler(signal, frame):
    print("\n<Ctrl+C>")
    lircd.close()
    sys.exit(0)

def exec_cmd(cmd):   # cmd - str || list
    if verbose: print("Key action: " + cmd)
    if isinstance(cmd, str):
        cmd = cmd.split()
    if cmd[0] == 'run':
        cmd.pop(0)
    else:
        cmd.insert(0, 'xdotool')
    subprocess.Popen(cmd)

def get_cmd_out(cmd):   # cmd - str || list
    if isinstance(cmd, str):
        cmd = cmd.split()
    cmd_out = subprocess.check_output(cmd).rstrip()
    if py3:
        cmd_out = cmd_out.decode('utf-8')
    return cmd_out

comm_re = re.compile('([0-9A-Fa-f]+) ([0-9a-f]+) (.+) (.+)')
xdo_cmd_version = ['xdotool', 'version']
xdo_cmd_windowname = ['xdotool', 'getactivewindow', 'getwindowname']
lircd = socket.socket(socket.AF_UNIX)
signal.signal(signal.SIGINT, sigint_handler)

try:
    xdo_version = get_cmd_out(xdo_cmd_version)
except (OSError, FileNotFoundError, subprocess.CalledProcessError):
    sys.exit("Can\'t execute xdotool")
if verbose: print(xdo_version)

config = configparser.ConfigParser(**customize_configparser)
if not config.read(os.path.join(os.path.expanduser('~'), '.lip.ini')):
    sys.exit("Can\'t open ~/.lip.ini")
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

while True:
    comm = lircd.recv(256).rstrip()
    if py3:
        comm = comm.decode('utf-8')
    if verbose: print("Time: {0:%X.%f %x}\nCommand: {1}".format(datetime.now(), comm))
    comm_parsed = comm_re.match(comm)
    if comm_parsed:
        rc_key, rc_name = comm_parsed.group(3, 4)
        if not config_rc_name or rc_name == config_rc_name:
            active_window_name = get_cmd_out(xdo_cmd_windowname)
            if verbose: print("Active window: " + active_window_name)
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
    if verbose: print("\n")
