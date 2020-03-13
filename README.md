lip
===

irexec and irxevent replacement with INI-style configuration file.

## Requirements

* LIRC
* Python 2/3
* xdotool
* [x11wininfo](https://github.com/un-def/x11wininfo) (optional; required for `WM_CLASS` criteria)

## How to use it

1. Install and configure LIRC.
2. ```cp liprc.example $HOME/.liprc``` and edit it.
3. ```python lip.py``` (```-v|--verbose``` for verbose mode).
