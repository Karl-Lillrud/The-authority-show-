# -*- coding: utf-8 -*-

import unittest

import logging
import sys
import tempfile

from pylogrus import PyLogrus, TextFormatter, CL_TXTGRN, CL_TXTBLU, CL_BLDYLW, CL_TXTRST


class TestTextFormatter(unittest.TestCase):

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

    def test_write_to_logfile(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)
        log.info("test log output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            # print("\n" + content)
            self.assertTrue(content.endswith("test log output\n"))

    def test_levels(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)

        log.debug("test_debug_output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" DEBUG ", content)
            self.assertTrue(content.endswith("test_debug_output\n"))

        log.info("test_info_output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" INFO ", content)
            self.assertTrue(content.endswith("test_info_output\n"))

        log.warning("test_warning_output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" WARNING ", content)
            self.assertTrue(content.endswith("test_warning_output\n"))

        log.error("test_error_output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" ERROR ", content)
            self.assertTrue(content.endswith("test_error_output\n"))

        log.critical("test_critical_output")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" CRITICAL ", content)
            self.assertTrue(content.endswith("test_critical_output\n"))

    def test_level_names_overriding(self):
        formatter = TextFormatter(colorize=False)
        # formatter.override_level_names({'CRITICAL': 'CRIT', 'ERROR': 'ERRO', 'WARNING': 'WARN', 'DEBUG': 'DEBU'})
        formatter.override_level_names({'ERROR': 'ERRO'})
        log = self.get_logger(formatter)

        log.error("test message")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" ERRO ", content)

    def test_date_format(self):
        formatter = TextFormatter(datefmt='%m/%d/%Y %I:%M:%S %p', colorize=False)
        log = self.get_logger(formatter)
        log.info("test a date in custom format")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            pattern = "^\[\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} [AP]M\]"
            if sys.version_info >= (3, 1):  # Python version >= 3.1
                self.assertRegex(content, pattern)
            else:
                self.assertRegexpMatches(content, pattern)

    def test_date_format_zulu(self):
        formatter = TextFormatter(datefmt='Z', colorize=False)
        log = self.get_logger(formatter)
        log.info("test a date in Zulu format")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            pattern = "^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]"
            if sys.version_info >= (3, 1):  # Python version >= 3.1
                self.assertRegex(content, pattern)
            else:
                self.assertRegexpMatches(content, pattern)

    def test_extra_fields(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)
        log.withFields({'user': 'John Doe'}).info("test message")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn("; user=John Doe", content)

    def test_contextual_logging(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)

        log_ctx = log.withFields({'context': 1})
        log_ctx.withFields({'user': 'John Doe'}).info("contextual logger")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn("; context=1", content)
            self.assertIn("; user=John Doe", content)

        log.withFields({'company': 'Awesome Company'}).info("default logger")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertNotIn("; context=1", content)
            self.assertIn("; company=Awesome Company", content)

    def test_message_with_prefix(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)
        log_pfx = log.withPrefix("[API]")

        log_pfx.info("Log message with the prefix")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertTrue(content.endswith("[API] Log message with the prefix\n"))

        log_pfx.critical("Another one log message with the prefix")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertTrue(content.endswith("[API] Another one log message with the prefix\n"))

    def test_color_output(self):
        formatter = TextFormatter(colorize=True)
        log = self.get_logger(formatter)
        log.info("test message")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" {}INFO{} ".format(CL_TXTGRN, CL_TXTRST), content)

    def test_color_overriding(self):
        formatter = TextFormatter(colorize=True)
        formatter.override_colors({'info': CL_BLDYLW, 'field': CL_TXTBLU})
        log = self.get_logger(formatter)
        log.withFields({'user': 'John Doe'}).info("test message")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertIn(" {}INFO{} ".format(CL_BLDYLW, CL_TXTRST), content)
            self.assertIn("; {}user{}={}John Doe{}".format(CL_TXTBLU, CL_TXTRST, CL_TXTRST, CL_TXTRST), content)

    def test_message_format(self):
        fmt = "%(levelname)-8s %(message)s"
        formatter = TextFormatter(fmt=fmt, colorize=False)
        log = self.get_logger(formatter)
        log.info("test message")
        with open(self.filename) as f:
            content = f.readlines()[-1]
            self.assertEqual("INFO     test message\n", content)

    def test_unicode(self):
        formatter = TextFormatter(colorize=False)
        log = self.get_logger(formatter)
        log.debug("😄 😁 😆 😅 😂")
        with open(self.filename, 'rb') as f:
            content = f.readlines()[-1]
            self.assertIn("\\xf0\\x9f\\x98\\x84 "
                          "\\xf0\\x9f\\x98\\x81 "
                          "\\xf0\\x9f\\x98\\x86 "
                          "\\xf0\\x9f\\x98\\x85 "
                          "\\xf0\\x9f\\x98\\x82"
                          "\\n", repr(content))


if __name__ == '__main__':
    unittest.main()
