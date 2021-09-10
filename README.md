# Elexon-BMRS-API
A Python implementation of the Elexon Balancing Mechanism Reporting Service (BMRS) web API. See https://www.elexon.co.uk/guidance-note/bmrs-api-data-push-user-guide/

**Latest Version: 0.1**

## About this repository

* This Python library provides a convenient interface for the Elexon BMRS web API to facilitate accessing BMRS data in Python code.
* Developed and tested with Python 3.9, should work with Python 3.6+.

## How do I get set up?

* Make sure you have Git installed - [Download Git](https://git-scm.com/downloads)
* Run `pip install git+https://github.com/SheffieldSolar/Elexon-BMRS-API`

## Usage

The datasets available via the BMRS API are denoted by 'report name', a string in the format "Bxxxx" where x is a positive integer. For example, "B1630" denotes "Actual Or Estimated Wind and Solar Power Generation". A complete list of report names can be found in the [BMRS API User Guide](https://www.elexon.co.uk/guidance-note/bmrs-api-data-push-user-guide/).

This module consists of one class, `BMRSDownloader`, with two public methods:

|Method|Description|Docs Link|
|------|-----------|---------|
|`BMRSDownloader.download(report_name, **kwargs)`|Download data from the API to a Pandas DataFrame.|To be added|
|`BMRSDownloader.download_to_file(self, report_name, outfile, **kwargs)`|Download data from the API to a CSV file.|To be added|

The above methods require different `kwargs` depending on which `report_name` is being downloaded:

|Report Type|Example `report_name`|Required `kwargs`|Example Usage|
|-----------|---------------------|-----------------|-------------|
|SettlementDate and Period|B1630|`start` : `datetime.date`<br/>`end` : `datetime.date`|`bmrs.download("B1630", start=date(2021, 1, 1), end=date(2021, 9, 10))`|
|Year and Month|B0640|`start_year` : `int`<br/>`start_month` : `int`<br/>`end_year` : `int`<br/>`end_month` : `int`|`bmrs.download("B0640", start_year=2020, start_month=1, end_year=2021, end_month=9)`|
|Year and Week|B0630|`start_year` : `int`<br/>`start_week` : `int`<br/>`end_year` : `int`<br/>`end_week` : `int`|`bmrs.download("B0630", start_year=2020, start_week=1, end_year=2021, end_week=36)`|
|Year|B0650|`start_year` : `int`<br/>`end_year` : `int`|`bmrs.download("B0650", start_year=2020, end_year=2021)`|
|StartTime, StartDate, EndTime, EndDate|B1030|`start` : `datetime.date`<br/>`end` : `datetime.date`|`bmrs.download("B1030", start=date(2021, 1, 1), end=date(2021, 9, 10))`|

N.B. The above code example use the following setup:

```Python
from datetime import date

from bmrs_api import BMRSDownloader

if __name__ == "__main__":
    bmrs = BMRSDownloader(api_key="my-api-key")
    # Download some data...
```

## Command Line Utilities

### bmrs_api

This utility can be used to download data to a CSV file:

```
>> bmrs_api -h
usage: bmrs_api.py [-h] -r "B1234" -s "<yyyy-mm-dd>" -e "<yyyy-mm-dd>" [-q] [-o </path/to/output/file>]

This is a command line interface (CLI) for the bmrs_api module

optional arguments:
  -h, --help            show this help message and exit
  -r "B1234", --report-name "B1234"
                        Specify a report name e.g. B1630.
  -s "<yyyy-mm-dd>", --start "<yyyy-mm-dd>"
                        Specify `start`.
  -e "<yyyy-mm-dd>", --end "<yyyy-mm-dd>"
                        Specify `end`.
  -q, --quiet           Specify to not print anything to stdout.
  -o </path/to/output/file>, --outfile </path/to/output/file>
                        Specify a CSV file to write results to (existing files will be overwritten).

Jamie Taylor 2021-09-10
```

## Using the Docker Image

There is also a Docker Image hosted on Docker Hub which can be used to download data from the BMRS API with minimal setup:

```
>> docker run -it --rm sheffieldsolar/elexon-bmrs-api:<release> bmrs_api -h
```

## Documentation

* To be added

## How do I upgrade?

Sheffield Solar will endeavour to update this library in sync with [Elexon's BMRS API](https://www.elexon.co.uk/guidance-note/bmrs-api-data-push-user-guide/ "BMRS API User Guide") and ensure the latest version of this library always supports the latest version of the BMRS API, but cannot guarantee this. If you use this library and find it has fallen out of sync with the BMRS API, you should email [solar@sheffield.ac.uk](mailto:solar@sheffield.ac.uk?subject=Elexon-BMRS-API%20Python%20Library "Email Sheffield Solar").

To upgrade the code:
* Run `pip install --upgrade git+https://github.com/SheffieldSolar/Elexon-BMRS-API`

## Who do I talk to?

* Jamie Taylor - [jamie.taylor@sheffield.ac.uk](mailto:jamie.taylor@sheffield.ac.uk "Email Jamie") - [SheffieldSolar](https://github.com/SheffieldSolar)

## Authors

* **Jamie Taylor** - [SheffieldSolar](https://github.com/SheffieldSolar)

## License

No license is defined yet - use at your own risk.

## To Do

* Generate Docs
* Add unit tests
* Add GH Actions for automatic testing etc
* Add support for downloading "Legacy BMRS Data"