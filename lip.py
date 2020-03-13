#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

import os
import sys
import signal
import socket
import subprocess
import re
import argparse
import shlex
from datetime import datetime

if sys.version_info.major > 2:
    import configparser
    customize_configparser = {'inline_comment_prefixes': ';'}
else:
    import ConfigParser as configparser
    customize_configparser = {}
    FileNotFoundError = ConnectionRefusedError = socket.error


__author__ = 'un.def <un.def@ya.ru>'
__version__ = '0.1.0'


DEFAULT_LIRCD_SOCKET = '/var/run/lirc/lircd'
COMMAND_REGEX = re.compile('(?:[0-9A-Fa-f]+) (?:[0-9a-f]+) (.+) (.+)')


def _noop(*args, **kwargs):
    pass


class LIPError(Exception):

    pass


class LIP:

    print = print
    verbose_print = _noop
    args = None
    config = None
    socket = None
    rc_name = None
    use_default_keys = False
    apps_sections = ()

    def __init__(self):
        self.args = args = self.parse_args()
        if args.verbose:
            self.verbose_print = print

        self.verbose_print("lip v{}".format(__version__))

        try:
            xdo_version = self.get_cmd_out(['xdotool', 'version'])
        except (OSError, FileNotFoundError, subprocess.CalledProcessError):
            raise LIPError("Can't execute xdotool")
        self.verbose_print(xdo_version)

        self.config = config = configparser.ConfigParser(
            **customize_configparser)
        if args.config:
            config_path = os.path.abspath(args.config)
        else:
            config_path = os.path.join(os.path.expanduser('~'), '.liprc')
        if not config.read(config_path):
            raise LIPError("Can't open {}".format(config_path))
        self.verbose_print("config file: {}".format(config_path))

        self.socket = sock = socket.socket(socket.AF_UNIX)
        socket_path = args.socket
        if not socket_path:
            try:
                socket_path = config.get('Settings', 'socket')
            except configparser.NoOptionError:
                socket_path = DEFAULT_LIRCD_SOCKET
        try:
            sock.connect(socket_path)
        except (FileNotFoundError, ConnectionRefusedError):
            raise LIPError("Can't open {}".format(socket_path))
        self.verbose_print("lircd socket: {}".format(socket_path))

        try:
            rc_name = config.get('Settings', 'remote')
        except configparser.NoOptionError:
            rc_name = None
        self.rc_name = rc_name

        if config.has_section('Default'):
            try:
                use_default_keys = config.getboolean(
                    'Settings', 'use_default_keys')
            except (configparser.NoOptionError, ValueError):
                use_default_keys = True
        else:
            use_default_keys = False
        self.use_default_keys = use_default_keys

        self.apps_sections = tuple(
            s for s in config.sections()
            if s.title() not in ('Settings', 'Default')
        )

        self.verbose_print()

    def run(self):
        signal.signal(signal.SIGINT, self.sigint_handler)
        try:
            while True:
                self._run()
        except Exception as exc:
            raise LIPError(str(exc))
        finally:
            self.socket.close()

    def _run(self):
        comm = self.socket.recv(256).decode('utf-8').rstrip()
        self.verbose_print(
            "Time: {0:%X.%f %x}\nCommand: {1}".format(datetime.now(), comm))
        match = COMMAND_REGEX.match(comm)
        if not match:
            self.print("Can't parse: {}\n".format(comm))
            return
        rc_key, rc_name = match.groups()
        if self.rc_name and rc_name != self.rc_name:
            return
        try:
            active_window_name = self.get_cmd_out(
                ['xdotool', 'getactivewindow', 'getwindowname'])
        except subprocess.CalledProcessError:
            self.print("Can't get window name\n")
            return
        self.verbose_print("Active window: {}".format(active_window_name))
        key_found = False
        config = self.config
        for section in self.apps_sections:
            if config.has_option(section, 'window_name') and re.search(
                    config.get(section, 'window_name'), active_window_name):
                if config.has_option(section, rc_key):
                    key_found = True
                    key_cmd = config.get(section, rc_key)
                    self.exec_cmd(key_cmd)
                break
        if (not key_found and self.use_default_keys and
                config.has_option('Default', rc_key)):
            self.exec_cmd(config.get('Default', rc_key))
        self.verbose_print()

    def parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-c', '--config',
            required=False,
            help="config file",
        )
        parser.add_argument(
            '-s', '--socket',
            required=False,
            help="lircd socket (default: {})".format(DEFAULT_LIRCD_SOCKET),
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help="verbose mode",
        )
        return parser.parse_args()

    def exec_cmd(self, cmd):
        self.verbose_print("Key action: " + cmd)
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        if cmd[0] == 'run':
            cmd.pop(0)
        else:
            cmd.insert(0, 'xdotool')
        subprocess.Popen(cmd)

    def get_cmd_out(self, cmd):
        if isinstance(cmd, str):
            cmd = cmd.split()
        return subprocess.check_output(cmd).decode('utf-8').rstrip()

    def sigint_handler(self, signal_, frame):
        self.socket.close()
        raise LIPError("\r<SIGINT>")


if __name__ == '__main__':
    try:
        LIP().run()
    except LIPError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
