# -*- coding: utf-8 -*-

import abc
import copy
import logging
import sys
import time

import six


@six.add_metaclass(abc.ABCMeta)
class PyLogrusBase(object):

    @abc.abstractmethod
    def withFields(self, fields=None):
        """Add custom fields in log.

        :param fields: List of custom fields
        :type fields: dict
        :return: New instance of logger adapter
        :rtype: CustomAdapter
        """

    @abc.abstractmethod
    def withPrefix(self, prefix=None):
        """Add prefix to log message.

        :param prefix: Prefix of log message
        :type prefix: str
        :return: New instance of logger adapter
        :rtype: CustomAdapter
        """


class PyLogrus(logging.Logger, PyLogrusBase):

    def __init__(self, *args, **kwargs):
        extra = kwargs.pop('extra', None)
        self._extra_fields = extra or {}
        super(PyLogrus, self).__init__(*args, **kwargs)

    def withFields(self, fields=None):
        return CustomAdapter(self, fields)

    def withPrefix(self, prefix=None):
        return CustomAdapter(self, None, prefix)


class CustomAdapter(logging.LoggerAdapter, PyLogrusBase):

    def __init__(self, logger, extra=None, prefix=None):
        """Logger modifier.

        :param logger: Logger instance
        :type logger: PyLogrus
        :param extra: Custom fields
        :type extra: dict | None
        :param prefix: Prefix of log message
        :type prefix: str | None
        """
        self._logger = logger
        self._extra = self._normalize(extra)
        self._prefix = prefix
        super(CustomAdapter, self).__init__(self._logger, {'extra_fields': self._extra, 'prefix': self._prefix})

    @staticmethod
    def _normalize(fields):
        return {k.lower(): v for k, v in fields.items()} if isinstance(fields, dict) else {}

    def withFields(self, fields=None):
        extra = copy.deepcopy(self._extra)
        extra.update(self._normalize(fields))
        return CustomAdapter(self._logger, extra, self._prefix)

    def withPrefix(self, prefix=None):
        return self if prefix is None else CustomAdapter(self._logger, self._extra, prefix)

    def process(self, msg, kwargs):
        kwargs["extra"] = self.extra
        return msg, kwargs


class BaseFormatter(logging.Formatter):

    default_time_format = '%Y-%m-%d %H:%M:%S'
    default_msec_format = '%s,%03d'

    def __init__(self, fmt=None, datefmt=None, style='%'):
        if hasattr(logging, '_levelToName'):  # PY3
            self._level_names = {name: name for name in logging._levelToName.values()}
        else:
            self._level_names = {name: name for name in logging._levelNames.values() if isinstance(name, str)}

        if sys.version_info >= (3, 2):  # Python version >= 3.2
            super(BaseFormatter, self).__init__(fmt=fmt, datefmt=datefmt, style=style)
        else:
            super(BaseFormatter, self).__init__(fmt=fmt, datefmt=datefmt)

    def formatTime(self, record, datefmt=None):
        """Return the creation time of the specified LogRecord as formatted text.

        If ``datefmt`` (a string) is specified, it is used to format the creation time of the record.
        If ``datefmt`` is 'Z' then creation time of the record will be in Zulu Time Zone.
        Otherwise, the ISO8601 format is used.
        """
        ct = self.converter(record.created)
        if datefmt:
            if datefmt == 'Z':
                t = time.strftime("%Y-%m-%dT%H:%M:%S", ct)
                s = "{}.{:03.0f}Z".format(t, record.msecs)
            else:
                s = time.strftime(datefmt, ct)
        else:
            t = time.strftime(self.default_time_format, ct)
            s = self.default_msec_format % (t, record.msecs)

        return s

    def override_level_names(self, mapping):
        """Rename level names.

        :param mapping: Mapping level names to new ones
        :type mapping: dict
        """
        if not isinstance(mapping, dict):
            return
        for key, val in mapping.items():
            if key in self._level_names:
                self._level_names[key] = val
