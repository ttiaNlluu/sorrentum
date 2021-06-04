import logging
import pprint

import helpers.dbg as dbg
import helpers.printing as hprint
import helpers.unit_test as hut

_LOG = logging.getLogger(__name__)


class Test_printing1(hut.TestCase):
    def test_color_highlight1(self) -> None:
        for c in hprint.COLOR_MAP:
            _LOG.debug(hprint.color_highlight(c, c))


class Test_to_str1(hut.TestCase):
    def test1(self) -> None:
        x = 1
        # To disable linter complaints.
        _ = x
        act = hprint.to_str("x")
        exp = "x=1"
        self.assertEqual(act, exp)

    def test2(self) -> None:
        x = "hello world"
        # To disable linter complaints.
        _ = x
        act = hprint.to_str("x")
        exp = "x='hello world'"
        self.assertEqual(act, exp)

    def test3(self) -> None:
        x = 2
        # To disable linter complaints.
        _ = x
        act = hprint.to_str("x*2")
        exp = "x*2=4"
        self.assertEqual(act, exp)

    def test4(self) -> None:
        """
        Test printing multiple values separated by space.
        """
        x = 1
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        act = hprint.to_str("x y")
        exp = "x=1, y='hello'"
        self.assertEqual(act, exp)

    def test5(self) -> None:
        """
        Test printing multiple strings separated by space.
        """
        x = "1"
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        act = hprint.to_str("x y")
        exp = "x='1', y='hello'"
        self.assertEqual(act, exp)

    def test6(self) -> None:
        """
        Test printing a list.
        """
        x = [1, "hello", "world"]
        # To disable linter complaints.
        _ = x
        act = hprint.to_str("x")
        exp = "x=[1, 'hello', 'world']"
        self.assertEqual(act, exp)


class Test_log(hut.TestCase):
    def test1(self) -> None:
        dbg.test_logger()

    def test2(self) -> None:
        x = 1
        # To disable linter complaints.
        _ = x
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x")

    def test3(self) -> None:
        x = 1
        y = "hello"
        # To disable linter complaints.
        _ = x, y
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x y")

    def test4(self) -> None:
        """
        The command:

        > pytest -k Test_log::test4  -o log_cli=true --dbg_verbosity DEBUG

        should print something like:

        DEBUG    test_printing:printing.py:315 x=1, y='hello', z=['cruel', 'world']
        INFO     test_printing:printing.py:315 x=1, y='hello', z=['cruel', 'world']
        """
        x = 1
        y = "hello"
        z = ["cruel", "world"]
        # To disable linter complaints.
        _ = x, y, z
        for verb in [logging.DEBUG, logging.INFO]:
            hprint.log(_LOG, verb, "x y z")


class Test_sort_dictionary(hut.TestCase):
    def test1(self):
        dict_ = {
            "tool": {
                "poetry": {
                    "name": "lem",
                    "version": "0.1.0",
                    "description": "",
                    "authors": [""],
                    "dependencies": {
                        "awscli": "*",
                        "boto3": "*",
                        "flaky": "*",
                        "fsspec": "*",
                        "gluonts": "*",
                        "invoke": "*",
                        "jupyter": "*",
                        "matplotlib": "*",
                        "mxnet": "*",
                        "networkx": "*",
                        "pandas": "^1.1.0",
                        "psycopg2": "*",
                        "pyarrow": "*",
                        "pytest": "^6.0.0",
                        "pytest-cov": "*",
                        "pytest-instafail": "*",
                        "pytest-xdist": "*",
                        "python": "^3.7",
                        "pywavelets": "*",
                        "s3fs": "*",
                        "seaborn": "*",
                        "sklearn": "*",
                        "statsmodels": "*",
                        "bs4": "*",
                        "jsonpickle": "*",
                        "lxml": "*",
                        "tqdm": "*",
                        "requests": "*",
                    },
                    "dev-dependencies": {},
                }
            },
            "build-system": {
                "requires": ["poetry>=0.12"],
                "build-backend": "poetry.masonry.api",
            },
        }
        act = hprint.sort_dictionary(dict_)
        self.check_string(pprint.pformat(act))