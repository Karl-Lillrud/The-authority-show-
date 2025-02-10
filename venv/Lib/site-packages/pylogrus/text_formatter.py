# -*- coding: utf-8 -*-

import copy
import re
import sys

import six

from .base import BaseFormatter

# Customize the console colors
CL_TXTBLK = '\x1b[0;30m'  # Black - Regular
CL_TXTRED = '\x1b[0;31m'  # Red
CL_TXTGRN = '\x1b[0;32m'  # Green
CL_TXTYLW = '\x1b[0;33m'  # Yellow
CL_TXTBLU = '\x1b[0;34m'  # Blue
CL_TXTPUR = '\x1b[0;35m'  # Purple
CL_TXTCYN = '\x1b[0;36m'  # Cyan
CL_TXTWHT = '\x1b[0;37m'  # White
CL_BLDBLK = '\x1b[1;30m'  # Black - Bold
CL_BLDRED = '\x1b[1;31m'  # Red
CL_BLDGRN = '\x1b[1;32m'  # Green
CL_BLDYLW = '\x1b[1;33m'  # Yellow
CL_BLDBLU = '\x1b[1;34m'  # Blue
CL_BLDPUR = '\x1b[1;35m'  # Purple
CL_BLDCYN = '\x1b[1;36m'  # Cyan
CL_BLDWHT = '\x1b[1;37m'  # White
CL_DRKBLK = '\x1b[2;30m'  # Black - Dark
CL_DRKRED = '\x1b[2;31m'  # Red
CL_DRKGRN = '\x1b[2;32m'  # Green
CL_DRKYLW = '\x1b[2;33m'  # Yellow
CL_DRKBLU = '\x1b[2;34m'  # Blue
CL_DRKPUR = '\x1b[2;35m'  # Purple
CL_DRKCYN = '\x1b[2;36m'  # Cyan
CL_DRKWHT = '\x1b[2;37m'  # White
CL_UNDBLK = '\x1b[4;30m'  # Black - Underline
CL_UNDRED = '\x1b[4;31m'  # Red
CL_UNDGRN = '\x1b[4;32m'  # Green
CL_UNDYLW = '\x1b[4;33m'  # Yellow
CL_UNDBLU = '\x1b[4;34m'  # Blue
CL_UNDPUR = '\x1b[4;35m'  # Purple
CL_UNDCYN = '\x1b[4;36m'  # Cyan
CL_UNDWHT = '\x1b[4;37m'  # White
CL_BAKBLK = '\x1b[40m'    # Black - Background
CL_BAKRED = '\x1b[41m'    # Red
CL_BAKGRN = '\x1b[42m'    # Green
CL_BAKYLW = '\x1b[43m'    # Yellow
CL_BAKBLU = '\x1b[44m'    # Blue
CL_BAKPUR = '\x1b[45m'    # Purple
CL_BAKCYN = '\x1b[46m'    # Cyan
CL_BAKWHT = '\x1b[47m'    # White
CL_TXTRST = '\x1b[0m'     # Text Reset


class TextFormatter(BaseFormatter):

    __BASE_FORMAT = "{cl_dtm}[{cl_rst}%(asctime)s{cl_dtm}]{cl_rst} %(levelname)8s %(message)s"

    def __init__(self, fmt=None, datefmt=None, style='%', colorize=True):
        """Initialize the formatter with specified format strings.

        :param fmt: Format of string
        :type fmt: str
        :param datefmt: Date format (set as 'Z' to get the Zulu format)
        :type datefmt: str
        :param style: Use a style parameter of '%', '{' or '$' to specify that you want to use one of %-formatting,
                      :meth:`str.format` (``{}``) formatting or
                      :class:`string.Template` formatting in your format string.
        :type style: str
        :param colorize: If ``True``, output will be colorized
        :type colorize: bool
        """
        self._colorize = bool(colorize)
        self._color_reset = CL_TXTRST if self._colorize else ''
        self._color = {
            True: {
                'asctime': CL_DRKWHT,
                'prefix': CL_TXTCYN,
                'field': CL_TXTGRN,
                'value': CL_TXTRST,
                'debug': CL_TXTBLU,
                'info': CL_TXTGRN,
                'warning': CL_TXTYLW,
                'error': CL_TXTRED,
                'critical': CL_DRKRED
            },
            False: {}
        }

        basefmt = fmt or self.__BASE_FORMAT.format(cl_dtm=self._color[self._colorize].get('asctime', ''),
                                                   cl_rst=self._color_reset)
        if self._colorize:
            p = re.compile(r'(?<=%\(levelname\))(-?\d*)(?=(?:\.\d+)?s)')
            res = p.search(basefmt)
            if res is not None:
                ln_color = max([len(i) for i in self._color[True]
                                if i in ['debug', 'info', 'warning', 'error', 'critical']])
                ln_color += len(self._color_reset) - 1
                ln = int(res.group(1) or 0)
                ln = ln + ln_color if ln > 0 else ln - ln_color
                basefmt = p.sub(str(ln), basefmt, re.VERBOSE)

        super(TextFormatter, self).__init__(fmt=basefmt, datefmt=datefmt, style=style)

    @property
    def color(self):
        return self._color[True]

    def override_colors(self, colors):
        """Override default color of elements.

        :param colors: New color value for given elements
        :type colors: dict
        """
        if not isinstance(colors, dict):
            return
        for key in self._color[True]:
            if key in colors:
                self._color[True][key] = colors[key]

    def format(self, original_record):
        record = copy.copy(original_record)
        message = record.getMessage()
        if hasattr(record, 'prefix'):
            message = "{cl_pfx}{prefix}{cl_rst}{message}".format(
                cl_pfx=self._color[self._colorize].get('prefix', ''),
                cl_rst=self._color_reset,
                prefix=(str(record.prefix) + ' ') if record.prefix else '',
                message=message
            )
        if hasattr(record, 'extra_fields') and isinstance(record.extra_fields, dict):
            for k, v in sorted(record.extra_fields.items()):
                message += "; {cl_fld}{field}{cl_rst}={cl_val}{value}{cl_rst}".format(
                    cl_fld=self._color[self._colorize].get('field', ''),
                    cl_val=self._color[self._colorize].get('value', ''),
                    cl_rst=self._color_reset,
                    field=k,
                    value=v
                )
        record.message = message

        if self.usesTime():
            record.asctime = "{cl_dtm}{asctime}{cl_rst}".format(
                cl_dtm=self._color[self._colorize].get('asctime', ''),
                cl_rst=self._color_reset,
                asctime=self.formatTime(record, self.datefmt)
            )

        record.levelname = "{cl_lvl}{level}{cl_rst}".format(
            cl_lvl=self._color[self._colorize].get(record.levelname.lower(), ''),
            cl_rst=self._color_reset,
            level=self._level_names[record.levelname]
        )

        return (self._format_py2, self._format_py3)[six.PY3](record)

    def _format_py2(self, record):
        try:
            s = self._fmt % record.__dict__
        except UnicodeDecodeError as e:
            try:
                record.name = record.name.decode('utf-8')
                s = self._fmt % record.__dict__
            except UnicodeDecodeError:
                raise e
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            try:
                s = s + record.exc_text
            except UnicodeError:
                s = s + record.exc_text.decode(sys.getfilesystemencoding(), 'replace')

        return s

    def _format_py3(self, record):
        s = self.formatMessage(record)

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)

        return s
