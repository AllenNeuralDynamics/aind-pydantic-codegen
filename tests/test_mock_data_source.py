import unittest

from . import MOCK_DATA_SOURCE, MOCK_PARSED_SOURCE, mock_data_parser


class MockParsedSourceTest(unittest.TestCase):
    def test_mock_data_parser(self):
        assert mock_data_parser(MOCK_DATA_SOURCE) == MOCK_PARSED_SOURCE
