import unittest

from mcxlib.libutil import validate_date_param


class ValidateDateParamTest(unittest.TestCase):
    def test_accepts_valid_range(self):
        self.assertIsNone(validate_date_param('20230101', '20230331'))

    def test_accepts_single_day_range(self):
        self.assertIsNone(validate_date_param('20230101', '20230101'))

    def test_rejects_end_date_before_start_date(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_param('20230201', '20230101')
        self.assertIn('earlier than start_date', str(ctx.exception))

    def test_rejects_range_longer_than_365_days(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_param('20230101', '20250101')
        self.assertIn('365 days', str(ctx.exception))

    def test_rejects_invalid_date_format(self):
        with self.assertRaises(ValueError) as ctx:
            validate_date_param('2023-01-01', '20230331')
        self.assertIn('not valid value', str(ctx.exception))

    def test_rejects_missing_dates(self):
        with self.assertRaises(ValueError):
            validate_date_param('', '20230331')


if __name__ == "__main__":
    unittest.main()
