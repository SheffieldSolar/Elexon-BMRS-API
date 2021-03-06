#!/usr/bin/env python3
"""
Download data from the BMRS API.

Jamie Taylor 2021-08-25

Endpoints supported: FUELHH, INDOITSDO, MID, SYSDEM, B1440, B1630, B1770

To-do:
    - Separate upload code into standalone module and facilitate arbitrary upload callback methods.
    - Combine with other BMRS download scripts to enable download of multiple datasets with single
      CLI.
    - Load API key securely from file.
    - Optionally convert extracted data to Pandas DataFrame.
"""

import os
import requests
import argparse
from datetime import date, datetime, timedelta
from urllib.parse import urlencode
from io import StringIO
import time as TIME
import pytz
import pandas as pd

from sp2ts import sp2dt

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

class BMRSDownloader:
    """Class for downloading data from the BMRS API."""
    def __init__(self, api_key=None, quiet=False, progress_bar=False, prefix="", retries=3):
        self.quiet = quiet
        self.progress_bar = progress_bar
        self.prefix = prefix
        self.retries = retries
        api_key_file = os.path.join(SCRIPT_DIR, "api_key.txt")
        self.api_key = api_key if api_key is not None else self._load_api_key(api_key_file)
        self.timer = 0
        self.api_base_url = "https://api.bmreports.com/BMRS"
        self.api_version = "v1"
        self.endpoint_types = self._endpoint_types()

    def _load_api_key(self, filename):
        if not os.path.isfile(filename):
            raise Exception(f"API key file '{filename}' not found and `api_key` not set")
        with open(filename) as fid:
            api_key = fid.read().strip()
        return api_key

    def download(self, report_name, **kwargs):
        """
        Download a given report.

        Parameters
        ----------
        `report_name` : str
            The unique identifier for the report generated by the API e.g. B1440, B1630 etc.
        **kwargs : dict
            Keyword arguments as appropriate for the report.

        Returns
        -------
        Pandas DataFrame
            Data returned by the API. See API docs for columns [1].

        References
        ----------
        [1] https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-and-data-push-user-guide-2/

        Notes
        -----
        There are 5 types of API endpoint in the Transparency Data and REMIT API:
        - Type1 endpoints with SettlementDate and Period parameters: pass `start` and `end` kwargs
          where both start and end are datetime.date objects.
        - Type2 endpoints with Year and Month parameters: pass `start_year`, `start_month`,
          `end_year` and `end_month` kwargs where all are ints.
        - Type3 endpoints with Year and Week parameters: pass `start_year`, `start_week`,
          `end_year` and `end_week` kwargs where all are ints.
        - Type4 endpoints with Year parameter: pass `start_year`, `end_year` kwargs where both are
          ints.
        - Type5 endpoints with StartTime, StartDate, EndTime, EndDate parameters: pass `start_time`,
          `start_date`, `end_time`, `end_date` as datetime.time, datetime.date, datetime.time,
          datetime.date respectively.
        """
        if not isinstance(report_name, str):
            raise TypeError("`report_name` must be string")
        return self._download(report_name.upper(), **kwargs)

    def download_to_file(self, report_name, outfile, **kwargs):
        """
        Download a given report to file.

        Parameters
        ----------
        `report_name` : str
            The unique identifier for the report generated by the API e.g. B1440, B1630 etc.
        `outfile` : str
            File to write data to.
        **kwargs : dict
            Keyword arguments as appropriate for the report. See `BMRSDownloader.download()`.

        Returns
        -------
        Pandas DataFrame
            Data returned by the API. See API docs for columns [1].

        References
        ----------
        [1] https://www.elexon.co.uk/documents/training-guidance/bsc-guidance-notes/bmrs-api-and-data-push-user-guide-2/
        """
        data = self.download(report_name, **kwargs)
        data.to_csv(outfile, index=False)
        return data

    def _endpoint_types(self):
        return {
            # Type1 endpoints use SettlementDate and Period params
            "type1": {
                "report_names": ["B1720", "B1730", "B1740", "B1750", "B1760", "B1770", "B1780",
                                 "B1810", "B01820", "B01830", "B0610", "B0620", "B1430", "B1440",
                                 "B1610", "B1620", "B1630", "B1320"],
                "args": ["start", "end"],
                "downloader": self._download_type1
            },
            # Type2 endpoints use Year and Month params
            "type2": {
                "report_names": ["B1790", "B0640", "B1330"],
                "args": ["start_year", "start_month", "end_year", "end_month"],
                "downloader": self._download_type2
            },
            # Type3 endpoints use Year and Week params
            "type3": {
                "report_names": ["B0630"],
                "args": ["start_year", "start_week", "end_year", "end_week"],
                "downloader": self._download_type3
            },
            # Type4 endpoints use Year param
            "type4": {
                "report_names": ["B0650", "B0810", "B1410", "B1420", "B0910"],
                "args": ["start_year", "end_year"],
                "downloader": self._download_type4
            },
            # Type5 endpoints use StartTime, StartDate, EndTime, EndDate params
            "type5": {
                "report_names": ["B0710", "B0720", "B1010", "B1020", "B1030", "B1510", "B1520",
                                 "B1530", "B1540"],
                "args": ["start", "end"],
                "downloader": self._download_type5
            }
        }

    def _download(self, report_name, **kwargs):
        """Map Report Names to parsing functions and apply arg validation."""
        endpoint_type = [t for label, t in self.endpoint_types.items() \
                         if report_name in t["report_names"]]
        if not endpoint_type:
            raise ValueError(f"`report_name` '{report_name}' is not supported")
        else:
            endpoint_type = endpoint_type[0]
        if any(arg not in kwargs for arg in endpoint_type["args"]):
            raise TypeError(f"'{report_name}' requires the follwing kwargs: "
                            f"{', '.join(endpoint_type['args'])}")
        kwargs_ = {k: kwargs[k] for k in endpoint_type['args']}
        return endpoint_type["downloader"](report_name, **kwargs_)

    @staticmethod
    def _parse_data(raw):
        if "<errorType>No Content</errorType>" not in raw:
            data_ = [l.strip().strip("*").strip("<EOF>") for l in raw.splitlines()[5:]]
            if data_:
                headers = raw.splitlines()[4].strip().strip("*").replace(" ", "").split(",")
                if "SettlementDate" in headers:
                    data_ = pd.read_csv(StringIO("\n".join(data_)), parse_dates=["SettlementDate"],
                                        skipinitialspace=True, names=headers)
                else:
                    data_ = pd.read_csv(StringIO("\n".join(data_)), skipinitialspace=True,
                                        names=headers)
                data_.rename(columns={c: c.replace(" ", "") for c in data_.columns}, inplace=True)
                return data_
        return None

    def _download_type1(self, report_name, start, end):
        """Download data from type1 endpoints with SettlementDate, Period params."""
        data = None
        start_ = start
        sp2dt_ = lambda r: sp2dt(r.SettlementDate.date(), r.SettlementPeriod)
        while start_ <= end:
            params = {"SettlementDate": start_.isoformat(), "Period": "*", "ServiceType": "csv"}
            url = self._construct_url(report_name, params)
            raw = self._fetch(url)
            data_ = self._parse_data(raw)
            if data_ is not None:
                data_["datetime"] = data_.apply(sp2dt_, axis=1)
                if data is None:
                    data = data_
                else:
                    data = pd.concat([data, data_], ignore_index=True)
            start_ += timedelta(days=1)
        return data

    def _download_type2(self, report_name, start_year, start_month, end_year, end_month):
        """Download data from type2 endpoints with Year, Month params."""
        data = None
        year_ = start_year
        month_ = start_month
        while date(year_, month_, 1) <= date(end_year, end_month, 1):
            params = {"Year": year_, "Month": date(year_, month_, 1).strftime("%b"),
                      "ServiceType": "csv"}
            url = self._construct_url(report_name, params)
            raw = self._fetch(url)
            data_ = self._parse_data(raw)
            if data_ is not None:
                if data is None:
                    data = data_
                else:
                    data = pd.concat([data, data_], ignore_index=True)
            month_ += 1
            if month_ > 12:
                year_ += 1
                month_ = 1
        return data

    def _download_type3(self, report_name, start_year, start_week, end_year, end_week):
        """Download data from type3 endpoints with Year, Week params."""
        data = None
        as_date = lambda y, w: datetime.strptime(f"{y}-{w}-1", "%G-%V-%w").date()
        date_ = as_date(start_year, start_week)
        while date_ <= as_date(end_year, end_week):
            params = {"Year": date_.year, "Week": date_.strftime("%V"),
                      "ServiceType": "csv"}
            url = self._construct_url(report_name, params)
            raw = self._fetch(url)
            data_ = self._parse_data(raw)
            if data_ is not None:
                if data is None:
                    data = data_
                else:
                    data = pd.concat([data, data_], ignore_index=True)
            date_ += timedelta(days=7)
        return data

    def _download_type4(self, report_name, start_year, end_year):
        """Download data from type4 endpoints with Year param."""
        data = None
        year_ = start_year
        while year_ <= end_year:
            params = {"Year": year_, "ServiceType": "csv"}
            url = self._construct_url(report_name, params)
            raw = self._fetch(url)
            data_ = self._parse_data(raw)
            if data_ is not None:
                if data is None:
                    data = data_
                else:
                    data = pd.concat([data, data_], ignore_index=True)
            year_ += 1
        return data

    def _download_type5(self, report_name, start, end):
        """Download data from type2 endpoints with StartTime, StartDate, EndTime, EndDate params."""
        params = {"StartDate": start.isoformat(), "StartTime": "00:00:00",
                  "EndDate": end.isoformat(), "EndTime": "23:59:59", "ServiceType": "csv"}
        url = self._construct_url(report_name, params)
        raw = self._fetch(url)
        data_ = self._parse_data(raw)
        return data_

    def _construct_url(self, report_name, params):
        """Combine URL components."""
        url = f"{self.api_base_url}/{report_name.upper()}/{self.api_version}?APIKey={self.api_key}&"
        params_ = urlencode(params)
        return url + params_

    def _fetch(self, url):
        """Fetch the URL with GET request."""
        success = False
        try_counter = 0
        delay = 1
        while not success and try_counter < self.retries + 1:
            try_counter += 1
            try:
                page = requests.get(url)
                page.raise_for_status()
                success = True
            except requests.exceptions.HTTPError:
                TIME.sleep(delay)
                delay *= 2
                continue
        if not success:
            raise Exception(f"Error communicating with the BMRS API after {self.retries} retries.")
        try:
            return page.text
        except Exception as e:
            raise Exception("Error communicating with the BMRS API.") from e

def parse_options():
    """Parse command line options."""
    parser = argparse.ArgumentParser(description=("This is a command line interface (CLI) for "
                                                  "the bmrs_api module"),
                                     epilog="Jamie Taylor 2021-09-10")
    parser.add_argument("-k", "--api-key", dest="api_key", action="store", required=True,
                        type=str, metavar="\"<my-api-key>\"",
                        help="Your BMRS API key (a.k.a Scripting Key).")
    parser.add_argument("-r", "--report-name", dest="report_name", action="store", required=True,
                        type=str, metavar="\"B1234\"", help="Specify a report name e.g. B1630.")
    parser.add_argument("-s", "--start", dest="start", action="store", type=str, required=True,
                        metavar="\"<yyyy-mm-dd>\"", help="Specify `start`.")
    parser.add_argument("-e", "--end", dest="end", action="store", type=str, required=True,
                        metavar="\"<yyyy-mm-dd>\"", help="Specify `end`.")
    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        required=False, help="Specify to not print anything to stdout.")
    parser.add_argument("-o", "--outfile", metavar="</path/to/output/file>", dest="outfile",
                        action="store", type=str, required=False,
                        help="Specify a CSV file to write results to (existing files will be "
                             "overwritten).")
    options = parser.parse_args()
    def handle_options(options):
        """Collect options from command line."""
        if options.start:
            try:
                options.start = datetime.strptime(options.start, "%Y-%m-%d")\
                                    .replace(tzinfo=pytz.utc).date()
            except:
                raise ValueError("OptionsError: Failed to parse start date, make sure "
                                 "you use 'yyyy-mm-dd' format.")
        if options.end:
            try:
                options.end = datetime.strptime(options.end, "%Y-%m-%d").replace(tzinfo=pytz.utc)\
                                  .date()
            except:
                raise ValueError("OptionsError: Failed to parse end date, make sure "
                                 "you use 'yyyy-mm-dd' format.")
        options.start_year = options.start.year
        options.start_month = options.start.month
        options.start_week = int(options.start.strftime("%V"))
        options.end_year = options.end.year
        options.end_month = options.end.month
        options.end_week = int(options.end.strftime("%V"))
        return options
    return handle_options(options)

def main():
    options = parse_options()
    bmrs = BMRSDownloader(api_key=options.api_key)
    if options.outfile:
        bmrs.download_to_file(**vars(options))
    else:
        print(bmrs.download(**vars(options)))

if __name__ == "__main__":
    main()