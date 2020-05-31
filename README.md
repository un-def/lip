lip
===

irexec and irxevent replacement with INI-style configuration file.

## Requirements

* [LIRC](https://www.lirc.org/) or compatible daemon (e.g., [inputlirc](https://github.com/gsliepen/inputlirc))
* Python 2/3
* xdotool
* x11wininfo ([C](https://github.com/un-def/x11wininfo) or [Go](https://github.com/un-def/x11wininfo-go) version) (optional; required for `WM_CLASS` criteria)

## How to use it

1. Install and configure LIRC–compatible daemon.
2. ```cp lip.example.ini $HOME/.config/lip.ini``` and edit it.
3. ```python lip.py``` (```-v|--verbose``` for verbose mode).
