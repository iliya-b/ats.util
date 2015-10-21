
import argparse
import shlex
import sys


class ConfigError(Exception):
    pass


class Option:
    def __init__(self, name, *, default=None, required=True, typ=None, help=''):
        self.name = name
        self.default = default
        self.required = required
        if not typ and default is not None:
            typ = type(default)
        if not typ:
            typ = str
        self.typ = typ
        self.help = help

    @property
    def key(self):
        return self.name.replace('.', '_').upper()

    _booleans = {
        '1': True, 'yes': True, 'true': True, 'on': True,
        '0': False, 'no': False, 'false': False, 'off': False
    }

    def _as_boolean(self, value):
        if isinstance(value, bool):
            return value
        if value.lower() not in self._booleans:
            raise ConfigError('Not a boolean: %s' % value)
        return self._booleans[value.lower()]

    def as_envvar(self, value):
        if value is None:
            return ''
        return str(value)

    def value(self, value):
        if self.typ == bool:
            # btw bool('False') == True
            return self._as_boolean(value)
        return self.typ(value)


def get_configdict(prefix, options, environ):
    config = {
        key[len(prefix):]: value
        for key, value in environ.items()
        if key.startswith(prefix)
    }

    missing = []
    ret = {}

    for op in options:
        if op.required and not op.default and not config.get(op.key):
            missing.append('%s%s' % (prefix, op.key))
        if not config.get(op.key):
            config[op.key] = op.default

        parts = [part for part in op.name.split('.')]
        cur = ret
        for part in parts[:-1]:
            cur.setdefault(part, {})
            cur = cur[part]
        cur[parts[-1]] = op.value(config[op.key])

    if missing:
        raise ConfigError('Missing required options: %s' % ', '.join(missing))

    return ret


def EnvConfigPrinter(prefix, options):
    class PrinterAction(argparse.Action):
        def __call__(self, *args, **kw):
            for op in options:
                envvalue = op.as_envvar(op.default)
                if op.help:
                    comment = '# {}'.format(op.help)
                else:
                    comment = ''
                line = 'export {}{}={}'.format(prefix, op.key, shlex.quote(envvalue))
                if comment:
                    if len(line) > 45:
                        print(comment)
                        print(line)
                    else:
                        print('{0:<47}{1}'.format(line, comment))
                else:
                    print(line)
            sys.exit()

    def wrapper(*args, **kw):
        return PrinterAction(*args, **kw)
    return wrapper
