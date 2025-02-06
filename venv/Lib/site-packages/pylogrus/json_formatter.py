# -*- coding: utf-8 -*-

from functools import partial
import json

from .base import BaseFormatter


class JsonFormatter(BaseFormatter):

    __BASIC_FIELDS = ['name', 'asctime', 'levelname', 'message', 'exception', 'stacktrace']

    def __init__(self, datefmt=None, enabled_fields=None, indent=None, sort_keys=False):
        """Initialize the formatter with specified fields and date format.

        :param datefmt: Date format (set as 'Z' to get the Zulu format)
        :type datefmt: str
        :param enabled_fields: List of enabled fields. Field should be represented
                               by string (field name) or tuple ((field name, new name))
        :type enabled_fields: list
        :param indent: Format JSON string with the given indent
        :type indent: int
        :param sort_keys: Sort keys in log record
        :type sort_keys: bool
        :return: Log record as JSON string
        :rtype: str
        """
        super(JsonFormatter, self).__init__(datefmt=datefmt)
        self._indent = indent
        self._sort_keys = sort_keys
        self.__compose_record = partial(self.__prepare_record, enabled_fields=enabled_fields or self.__BASIC_FIELDS)

    def __prepare_record(self, record, enabled_fields):
        """Prepare log record with given fields."""
        message = record.getMessage()
        if hasattr(record, 'prefix'):
            message = "{}{}".format((str(record.prefix) + ' ') if record.prefix else '', message)

        obj = {
            'name': record.name,
            'asctime': self.formatTime(record, self.datefmt),
            'created': record.created,
            'msecs': record.msecs,
            'relativeCreated': record.relativeCreated,
            'levelno': record.levelno,
            'levelname': self._level_names[record.levelname],
            'thread': record.thread,
            'threadName': record.threadName,
            'process': record.process,
            'pathname': record.pathname,
            'filename': record.filename,
            'module': record.module,
            'lineno': record.lineno,
            'funcName': record.funcName,
            'message': message,
            'exception': record.exc_info[0].__name__ if record.exc_info else None,
            'stacktrace': record.exc_text,
        }

        if not isinstance(enabled_fields, list):
            enabled_fields = [str(enabled_fields)]

        ef = {}
        for item in enabled_fields:
            if not isinstance(item, (str, tuple)):
                continue
            if not isinstance(item, tuple):
                ef[item] = item
            else:
                ef[item[0]] = item[1]

        result = {}
        for key, val in obj.items():
            if key in ef:
                result[ef[key]] = val

        return result

    def __obj2json(self, obj):
        """Serialize obj to a JSON formatted string.

        This is useful for pretty printing log records in the console.
        """
        return json.dumps(obj, indent=self._indent, sort_keys=self._sort_keys)

    def format(self, record):
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        obj = self.__compose_record(record)
        if hasattr(record, 'extra_fields') and isinstance(record.extra_fields, dict):
            obj.update(record.extra_fields)

        return self.__obj2json(obj)
