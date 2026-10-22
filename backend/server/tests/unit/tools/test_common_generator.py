import sys
sys.path.append('../..')
import os
os.environ.setdefault("MYSQL_IP", 'localhost')
os.environ.setdefault("MYSQL_PORT", "3306")

import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import pytest
import uuid

from main import create_app
from tool.common_generator import CommonGenerator


@pytest.mark.unit
@pytest.mark.utility
class TestCommonGenerator(unittest.TestCase):

    def setUp(self):
        self.app = create_app(False)
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_generate_uuid_single(self):
        result = CommonGenerator.generate_uuid()
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 32)  # UUID4 hex is 32 characters
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_generate_uuid_double(self):
        result = CommonGenerator.generate_uuid(double=True)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 64)  # Double UUID4 hex is 64 characters
        self.assertTrue(all(c in '0123456789abcdef' for c in result))

    def test_generate_uuid_uniqueness(self):
        uuid1 = CommonGenerator.generate_uuid()
        uuid2 = CommonGenerator.generate_uuid()
        
        self.assertNotEqual(uuid1, uuid2)

    def test_camel_to_snake_simple(self):
        result = CommonGenerator.camel_to_snake("camelCase")
        self.assertEqual(result, "camel_case")

    def test_camel_to_snake_multiple_words(self):
        result = CommonGenerator.camel_to_snake("thisIsCamelCase")
        self.assertEqual(result, "this_is_camel_case")

    def test_camel_to_snake_single_word(self):
        result = CommonGenerator.camel_to_snake("word")
        self.assertEqual(result, "word")

    def test_camel_to_snake_already_snake(self):
        result = CommonGenerator.camel_to_snake("snake_case")
        self.assertEqual(result, "snake_case")

    def test_camel_to_snake_starts_with_capital(self):
        result = CommonGenerator.camel_to_snake("CamelCase")
        self.assertEqual(result, "camel_case")

    def test_camel_to_snake_empty_string(self):
        result = CommonGenerator.camel_to_snake("")
        self.assertEqual(result, "")

    def test_camel_to_snake_consecutive_capitals(self):
        result = CommonGenerator.camel_to_snake("XMLHttpRequest")
        self.assertEqual(result, "x_m_l_http_request")

    def test_generate_current_period_exact_match(self):
        last_period_end = datetime(2023, 1, 1, 0, 0, 0)
        current_time = datetime(2023, 1, 8, 0, 0, 0)  # Exactly one week later
        period = timedelta(days=7)
        
        start_time, end_time = CommonGenerator.generate_current_period(
            last_period_end, current_time, period
        )
        
        self.assertEqual(start_time, datetime(2023, 1, 8, 0, 0, 0))
        self.assertEqual(end_time, datetime(2023, 1, 15, 0, 0, 0))

    def test_generate_current_period_partial_period(self):
        last_period_end = datetime(2023, 1, 1, 0, 0, 0)
        current_time = datetime(2023, 1, 5, 0, 0, 0)  # 5 days later
        period = timedelta(days=7)
        
        start_time, end_time = CommonGenerator.generate_current_period(
            last_period_end, current_time, period
        )
        
        self.assertEqual(start_time, datetime(2023, 1, 1, 0, 0, 0))
        self.assertEqual(end_time, datetime(2023, 1, 8, 0, 0, 0))

    def test_generate_current_period_multiple_periods(self):
        last_period_end = datetime(2023, 1, 1, 0, 0, 0)
        current_time = datetime(2023, 1, 22, 0, 0, 0)  # 3 weeks later
        period = timedelta(days=7)
        
        start_time, end_time = CommonGenerator.generate_current_period(
            last_period_end, current_time, period
        )
        
        self.assertEqual(start_time, datetime(2023, 1, 22, 0, 0, 0))
        self.assertEqual(end_time, datetime(2023, 1, 29, 0, 0, 0))

    def test_generate_current_period_with_default_period(self):
        last_period_end = datetime(2023, 1, 1, 0, 0, 0)
        current_time = datetime(2023, 1, 8, 0, 0, 0)
        
        start_time, end_time = CommonGenerator.generate_current_period(
            last_period_end, current_time
        )
        
        self.assertIsNotNone(start_time)
        self.assertIsNotNone(end_time)
        self.assertLess(start_time, end_time)



    @patch('uuid.uuid4')
    def test_generate_uuid_mocked(self, mock_uuid4):
        mock_uuid4.return_value.hex = 'abcd1234'
        
        result = CommonGenerator.generate_uuid()
        
        self.assertEqual(result, 'abcd1234')
        mock_uuid4.assert_called_once()

    @patch('uuid.uuid4')
    def test_generate_uuid_double_mocked(self, mock_uuid4):
        mock_uuid4.return_value.hex = 'abcd1234'
        
        result = CommonGenerator.generate_uuid(double=True)
        
        self.assertEqual(result, 'abcd1234abcd1234')
        self.assertEqual(mock_uuid4.call_count, 2)

    def test_camel_to_snake_edge_cases(self):
        test_cases = [
            ("", ""),
            ("a", "a"),
            ("A", "a"),
            ("aB", "a_b"),
            ("AB", "a_b"),
            ("ABC", "a_b_c"),
            ("ABc", "a_bc"),
            ("AbC", "ab_c"),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = CommonGenerator.camel_to_snake(input_str)
                self.assertEqual(result, expected)

    def test_generate_current_period_edge_cases(self):
        # Test when current time is exactly at the last period end
        last_period_end = datetime(2023, 1, 1, 0, 0, 0)
        current_time = datetime(2023, 1, 1, 0, 0, 0)
        period = timedelta(days=7)
        
        start_time, end_time = CommonGenerator.generate_current_period(
            last_period_end, current_time, period
        )
        
        self.assertEqual(start_time, last_period_end)
        self.assertEqual(end_time, last_period_end + period)