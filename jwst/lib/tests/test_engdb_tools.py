"""
Test suite for engdb_tools

Notes
-----
This file has been named specifically so it is not
automatically found by py.test. This is because, to test,
a connection to the internal engineering service is needed,
which is generally not available.
"""

from __future__ import absolute_import

import pytest

from astropy.time import Time

from .. import engdb_tools
from .engdb_mock import EngDB_Mocker

GOOD_MNEMONIC = 'INRSI_GWA_Y_TILT_AVGED'
GOOD_STARTTIME = '2016-01-18'
GOOD_ENDTIME = '2016-01-19'

SHORT_STARTTIME = '2016-01-18 15:30:00'

BAD_SERVER = 'https://www.stsci.edu'
BAD_MNEMONIC = 'No_Such_MNEMONIC'
NODATA_STARTIME = '2014-01-01'
NODATA_ENDTIME = '2014-01-02'


def test_basic(engdb):
    assert engdb.get_records(GOOD_MNEMONIC, GOOD_STARTTIME, GOOD_ENDTIME)


def test_bad_server():
    with pytest.raises(Exception):
        engdb = engdb_tools.ENGDB_Service(BAD_SERVER)


def test_db_time():
    time = 1234567890123
    stime = ''.join([
        '/Date(',
        str(time),
        '+1234',
        ')/'
    ])
    result = engdb_tools.extract_db_time(stime)
    assert result == time


def test_values(engdb):
    records = engdb.get_records(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME
    )
    assert records['Count'] == 3
    values = engdb.get_values(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME
    )
    assert len(values) == 1
    assert values[0] == 0.19687812


def test_values_with_bracket(engdb):
    records = engdb.get_records(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME
    )
    assert records['Count'] == 3
    values = engdb.get_values(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME,
        include_bracket_values=True
    )
    assert len(values) == 3
    assert values[1] == 0.19687812


def test_values_with_time(engdb):
    values = engdb.get_values(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME,
        include_obstime=True
    )
    assert len(values) >= 1
    assert isinstance(values[0], tuple)
    assert isinstance(values[0].obstime, Time)


def test_novalues(engdb):
    values = engdb.get_values(
        GOOD_MNEMONIC, NODATA_STARTIME, NODATA_ENDTIME)
    assert len(values) == 0

def test_meta(engdb):
    response = engdb.get_meta(GOOD_MNEMONIC)
    assert response['Count'] == 1
    assert response['TlmMnemonics'][0]['TlmMnemonic'] == GOOD_MNEMONIC


def test_unzip(engdb):
    """Test forunzipped versions of content"""
    values = engdb.get_values(
        GOOD_MNEMONIC, SHORT_STARTTIME, SHORT_STARTTIME,
        include_obstime=True,
        zip=False
    )
    assert isinstance(values, tuple)
    assert len(values.obstime) == len(values.value)


# #####################
# Utilities for testing
# #####################
@pytest.fixture
def engdb():
    with EngDB_Mocker() as mocker:
        engdb = engdb_tools.ENGDB_Service()
        yield engdb
