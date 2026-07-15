from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch

import mcxlib
import mcxlib.market_data as market_data


class MCXDatetimeTest(unittest.TestCase):
    def test_parse_mcx_datetime_returns_ist_datetime(self):
        parsed = market_data._parse_mcx_datetime("/Date(1777441209000)/")

        self.assertEqual(
            parsed,
            datetime(2026, 4, 29, 11, 10, 9, tzinfo=market_data.MCX_TIMEZONE),
        )

    def test_parse_mcx_datetime_accepts_offset_suffix(self):
        parsed = market_data._parse_mcx_datetime("/Date(0+0530)/")

        self.assertEqual(
            parsed,
            datetime.fromtimestamp(0, tz=timezone.utc).astimezone(
                market_data.MCX_TIMEZONE
            ),
        )

    def test_parse_mcx_datetime_accepts_default_negative_value(self):
        parsed = market_data._parse_mcx_datetime("/Date(-19800000)/")

        self.assertEqual(
            parsed,
            datetime.fromtimestamp(-19800, tz=timezone.utc).astimezone(
                market_data.MCX_TIMEZONE
            ),
        )

    def test_get_mcx_datetime_returns_latest_market_watch_ltt(self):
        response = {
            "d": {
                "Data": [
                    {"LTT": "/Date(1000)/"},
                    {"LTT": ""},
                    {},
                    {"LTT": "/Date(3000)/"},
                ]
            }
        }

        with patch.object(market_data, "post_json", return_value=response):
            result = market_data.get_mcx_datetime()

        self.assertEqual(
            result,
            datetime.fromtimestamp(3, tz=timezone.utc).astimezone(
                market_data.MCX_TIMEZONE
            ),
        )

    def test_get_mcx_datetime_is_exported(self):
        self.assertIs(mcxlib.get_mcx_datetime, market_data.get_mcx_datetime)


class AvailableContractsTest(unittest.TestCase):
    def setUp(self):
        self.response = {
            "d": {
                "Data": [
                    {
                        "__type": "MarketWatch",
                        "Symbol": "LEADMINI",
                        "InstrumentName": "FUTCOM",
                        "ContractName": "LEADMINI17DECFUT",
                        "LTP": 180.5,
                        "PercentChange": 1.25,
                        "ExpiryDate": "17DEC2026",
                    },
                    {
                        "__type": "MarketWatch",
                        "Symbol": "LEADMINI",
                        "InstrumentName": "OPTCOM",
                        "ContractName": "LEADMINI17DEC180CE",
                        "LTP": 3.2,
                        "PercentChange": -0.5,
                        "ExpiryDate": "17DEC2026",
                    },
                    {
                        "__type": "MarketWatch",
                        "Symbol": "GOLD",
                        "InstrumentName": "FUTCOM",
                        "ContractName": "GOLD05JUNFUT",
                        "LTP": 72800,
                        "PercentChange": 0.35,
                        "ExpiryDate": "05JUN2026",
                    },
                ]
            }
        }

    def test_get_available_contracts_filters_by_commodity_and_instrument(self):
        with patch.object(market_data, "post_json", return_value=self.response):
            result = market_data.get_available_contracts(
                commodity="LEADMINI",
                instrument="FUTCOM",
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "ContractName"], "LEADMINI17DECFUT")
        self.assertEqual(result.loc[0, "LTP"], 180.5)
        self.assertNotIn("__type", result.columns)

    def test_get_available_contracts_can_filter_by_contract_name(self):
        with patch.object(market_data, "post_json", return_value=self.response):
            result = market_data.get_available_contracts(
                commodity="LEADMINI17DECFUT",
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "Symbol"], "LEADMINI")

    def test_get_available_contracts_rejects_unknown_commodity(self):
        with patch.object(market_data, "post_json", return_value=self.response):
            with self.assertRaises(ValueError):
                market_data.get_available_contracts(commodity="UNKNOWN")

    def test_get_available_contracts_is_exported(self):
        self.assertIs(mcxlib.get_available_contracts, market_data.get_available_contracts)


class RequestPayloadTest(unittest.TestCase):
    def _capture_payload(self, func, response, **kwargs):
        with patch.object(market_data, "post_json", return_value=response) as mock_post:
            func(**kwargs)
        return mock_post.call_args.kwargs["payload"]

    def test_get_bhav_copy_sends_valid_json_payload(self):
        response = {"d": {"Data": [{"__type": "BhavCopy", "Symbol": "GOLD", "Open": 60000.0}]}}

        payload = self._capture_payload(
            market_data.get_bhav_copy,
            response,
            trade_date="20230102",
            instrument="ALL",
        )

        self.assertEqual(json.loads(payload), {"Date": "20230102", "InstrumentName": "ALL"})

    def test_get_option_chain_sends_valid_json_payload(self):
        response = {
            "d": {
                "Data": [
                    {
                        "ExtensionData": None,
                        "PE_LTT": "",
                        "CE_LTT": "",
                        "LTT": "",
                        "Symbol": "CRUDEOIL",
                        "CE_OpenInterest": 10,
                        "PE_OpenInterest": 0,
                        "StrikePrice": 6000,
                    }
                ]
            }
        }

        payload = self._capture_payload(
            market_data.get_option_chain,
            response,
            commodity="CRUDEOIL",
            expiry="15NOV2023",
        )

        self.assertEqual(json.loads(payload), {"Commodity": "CRUDEOIL", "Expiry": "15NOV2023"})

    def test_get_most_active_puts_calls_sends_valid_json_payload(self):
        response = {
            "d": {
                "Data": [
                    {"ExtensionData": None, "LTT": "", "Symbol": "CRUDEOIL", "Volume": 100}
                ]
            }
        }

        payload = self._capture_payload(
            market_data.get_most_active_puts_calls,
            response,
            option_type="PE",
            product="ALL",
            instrument="OPTFUT",
        )

        self.assertEqual(
            json.loads(payload),
            {"OptionType": "PE", "Product": "ALL", "InstrumentType": "OPTFUT"},
        )


if __name__ == "__main__":
    unittest.main()
