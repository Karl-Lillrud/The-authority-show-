from unittest import TestCase

from . import Php


class TestPhp(TestCase):

    maxDiff = None

    def test_http_build_query(self):
        self.assertEqual(
            Php.http_build_query({"alpha": "bravo"}), "alpha=bravo&")

        test = Php.http_build_query({"charlie": ["delta", "echo", "foxtrot"]})
        self.assertTrue("charlie[0]=delta" in test)
        self.assertTrue("charlie[1]=echo" in test)
        self.assertTrue("charlie[2]=foxtrot" in test)

        test = Php.http_build_query({
            "golf": [
                "hotel",
                {"india": "juliet", "kilo": ["lima", "mike"]},
                "november", "oscar"
            ]
        })
        self.assertTrue("golf[0]=hotel" in test)
        self.assertTrue("golf[1][india]=juliet" in test)
        self.assertTrue("golf[1][kilo][0]=lima" in test)
        self.assertTrue("golf[1][kilo][1]=mike" in test)
        self.assertTrue("golf[2]=november" in test)
        self.assertTrue("golf[3]=oscar" in test)

        self.assertEqual(
            Php.http_build_query({"!alpha": "bravo"}), "%21alpha=bravo&")

    def test_parse_ini_file(self):

        ini_file = "/tmp/python-php-test.ini"
        ini = """
            [section alpha]
            bravo = 7
            charlie = "delta"
            echo[] = 1
            echo[] = 2
            echo[] = 3

            [section foxtrot]
            golf[hotel] = 1
            golf[juliet] = 2
            golf[kilo] = "3"
        """.replace("    ", "")

        with open(ini_file, "w") as f:
            f.write(ini)

        self.assertEqual(Php.parse_ini_file(ini_file), {
            'section foxtrot': {
                'golf': {'kilo': 3, 'hotel': 1, 'juliet': 2}
            },
            'section alpha': {
                'bravo': 7,
                'echo': [1, 2, 3],
                'charlie': 'delta'
            }
        })
        self.assertEqual(Php.parse_ini_file(ini_file, strip_quotes=False), {
            'section foxtrot': {
                'golf': {'kilo': '"3"', 'hotel': 1, 'juliet': 2}
            },
            'section alpha': {
                'bravo': 7,
                'echo': [1, 2, 3],
                'charlie': '"delta"'
            }
        })

    def test__parse_ini_loop(self):
        self.assertEqual(
            Php._parse_ini_loop("a = b", None, {}, True), ({"a": "b"}, None))
        self.assertEqual(
            Php._parse_ini_loop("a=b", None, {}, True), ({"a": "b"}, None))
        self.assertEqual(
            Php._parse_ini_loop("a =b", None, {}, True), ({"a": "b"}, None))
        self.assertEqual(
            Php._parse_ini_loop("a= b", None, {}, True), ({"a": "b"}, None))
        self.assertEqual(
            Php._parse_ini_loop('a = "b"', None, {}, True),
            ({"a": "b"}, None)
        )
        self.assertEqual(
            Php._parse_ini_loop('a = "b"', None, {}, False),
            ({"a": '"b"'}, None)
        )
        self.assertEqual(
            Php._parse_ini_loop("a = 1", None, {}, True), ({"a": 1}, None))

    def test_parse_ini_file_special_case(self):

        ini_file = "/tmp/python-php-test.ini"
        ini = """
            alpha = 7
            bravo = "charlie"
            delta[] = 1
            delta[] = 2
        """.replace("    ", "")

        with open(ini_file, "w") as f:
            f.write(ini)

        self.assertEqual(
            Php.parse_ini_file(ini_file),
            {"alpha": 7, "bravo": "charlie", "delta": [1, 2]}
        )
        self.assertEqual(
            Php.parse_ini_file(ini_file, strip_quotes=False),
            {"alpha": 7, "bravo": '"charlie"', "delta": [1, 2]}
        )
