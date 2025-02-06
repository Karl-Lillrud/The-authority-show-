# -*- coding: utf-8 -*-

import unittest

import json
import logging
import sys
import tempfile

from pylogrus import PyLogrus, JsonFormatter


class TestJsonFormatter(unittest.TestCase):

    def get_logger(self, formatter):
        logging.setLoggerClass(PyLogrus)

        logger = logging.getLogger(__name__)  # type: PyLogrus
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(self.filename)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        return logger

    def setUp(self):
        self.temp = tempfile.NamedTemporaryFile()
        self.filename = self.temp.name

    def tearDown(self):
        self.temp.close()

    def test_levels(self):
        formatter = JsonFormatter()
        log = self.get_logger(formatter)

        log.debug("test_debug_output")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            # print(content)
            self.assertIn('levelname', content)
            self.assertEqual(content['levelname'], 'DEBUG')
            self.assertIn('message', content)
            self.assertEqual(content['message'], 'test_debug_output')

        log.info("test_info_output")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('levelname', content)
            self.assertEqual(content['levelname'], 'INFO')
            self.assertIn('message', content)
            self.assertEqual(content['message'], 'test_info_output')

        log.warning("test_warning_output")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('levelname', content)
            self.assertEqual(content['levelname'], 'WARNING')
            self.assertIn('message', content)
            self.assertEqual(content['message'], 'test_warning_output')

        log.error("test_error_output")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('levelname', content)
            self.assertEqual(content['levelname'], 'ERROR')
            self.assertIn('message', content)
            self.assertEqual(content['message'], 'test_error_output')

        log.critical("test_critical_output")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('levelname', content)
            self.assertEqual(content['levelname'], 'CRITICAL')
            self.assertIn('message', content)
            self.assertEqual(content['message'], 'test_critical_output')

    def test_level_names_overriding(self):
        formatter = JsonFormatter()
        formatter.override_level_names({'CRITICAL': 'FATAL'})
        log = self.get_logger(formatter)

        log.critical("test message")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertEqual(content['levelname'], 'FATAL')

    def test_date_format(self):
        formatter = JsonFormatter(datefmt='%m/%d/%Y %I:%M:%S %p')
        log = self.get_logger(formatter)
        log.info("test a date in custom format")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            pattern = "^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} [AP]M$"
            if sys.version_info >= (3, 1):  # Python version >= 3.1
                self.assertRegex(content['asctime'], pattern)
            else:
                self.assertRegexpMatches(content['asctime'], pattern)

    def test_date_format_zulu(self):
        formatter = JsonFormatter(datefmt='Z')
        log = self.get_logger(formatter)
        log.info("test a date in Zulu format")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            pattern = "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
            if sys.version_info >= (3, 1):  # Python version >= 3.1
                self.assertRegex(content['asctime'], pattern)
            else:
                self.assertRegexpMatches(content['asctime'], pattern)

    def test_extra_fields(self):
        formatter = JsonFormatter()
        log = self.get_logger(formatter)
        log.withFields({'user': 'John Doe'}).info("test message")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('user', content)
            self.assertEqual(content['user'], 'John Doe')

    def test_contextual_logging(self):
        formatter = JsonFormatter()
        log = self.get_logger(formatter)

        log_ctx = log.withFields({'context': 1})
        log_ctx.withFields({'user': 'John Doe'}).info("contextual logger")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn('context', content)
            self.assertEqual(content['context'], 1)
            self.assertIn('user', content)
            self.assertEqual(content['user'], 'John Doe')

        log.withFields({'company': 'Awesome Company'}).info("default logger")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertNotIn('context', content)
            self.assertIn('company', content)
            self.assertEqual(content['company'], 'Awesome Company')

    def test_message_with_prefix(self):
        formatter = JsonFormatter()
        log = self.get_logger(formatter)
        log_pfx = log.withPrefix("[API]")

        log_pfx.info("Log message with the prefix")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertEqual(content['message'], "[API] Log message with the prefix")

        log_pfx.critical("Another one log message with the prefix")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertEqual(content['message'], "[API] Another one log message with the prefix")

    def test_enabled_fields(self):
        enabled_fields = [
            ('asctime', 'service_timestamp'),
            ('levelname', 'level'),
            ('threadName', 'thread_name'),
            'message',
            ('exception', 'exception_class'),
            ('stacktrace', 'stack_trace'),
            ('funcName', 'function')
        ]
        formatter = JsonFormatter(enabled_fields=enabled_fields)
        log = self.get_logger(formatter)
        log.info("test message")
        with open(self.filename) as f:
            content = json.loads(f.readlines()[-1])
            self.assertEqual(len(content), 7)
            self.assertIn('service_timestamp', content)
            self.assertIn('level', content)
            self.assertIn('thread_name', content)
            self.assertIn('message', content)
            self.assertIn('exception_class', content)
            self.assertIn('stack_trace', content)
            self.assertIn('function', content)

    def test_unicode(self):
        formatter = JsonFormatter()
        log = self.get_logger(formatter)
        log.debug("😄 😁 😆 😅 😂")
        with open(self.filename, 'rb') as f:
            content = json.loads(f.readlines()[-1])
            self.assertIn("\U0001f604 \U0001f601 \U0001f606 \U0001f605 \U0001f602", repr(content['message']))


if __name__ == '__main__':
    unittest.main()
