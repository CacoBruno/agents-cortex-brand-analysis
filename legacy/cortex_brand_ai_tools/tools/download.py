import io
import sys
import zlib

import pandas as pd
import requests


def _make_headers_repr(cols):
    """Creates the string representation of the columns filter"""
    return ",".join(['{"name":"' + col + '"}' for col in cols])


def _make_range_filter(filter_dict):
    """Creates the string representation a range filter"""
    col_name, rng = filter_dict["name"], filter_dict["values"]
    if isinstance(rng[0], str):
        rng = tuple(i.replace("-", "") for i in rng)

    return f'"name":"{col_name}", "rangeStart":{rng[0]},"rangeEnd":{rng[1]}'


def _make_categorical_filter(filter_dict):
    """Creates the string representation a categorical filter"""
    col_name, list_of_values = filter_dict["name"], filter_dict["values"]
    list_of_values_str = str([str(x) for x in list_of_values]).replace("'", '"')
    return f'"name":"{col_name}", "value":{list_of_values_str}'


def _fill_filter_defaults(d):
    if "exclude" not in d:
        d["exclude"] = False
    if "exact_match" not in d:
        d["exact_match"] = True
    return d


def _additional_args(filter):
    s = ""
    if filter["exclude"]:
        s += ',"exclude": true'
    else:
        s += ',"exclude": false'

    if filter["exact_match"]:
        s += ',"exactMatch": true'
    else:
        s += ',"exactMatch": false'
    return s


def make_filter_repr(cube_filters):

    if len(cube_filters) > 0:
        fltr = _fill_filter_defaults(cube_filters[0])
        if isinstance(fltr["values"], tuple):
            s = "{" + _make_range_filter(fltr) + _additional_args(fltr) + "}"
        elif isinstance(fltr["values"], list):
            s = "{" + _make_categorical_filter(fltr) + _additional_args(fltr) + "}"
        else:
            raise ("Filter values must be a list or a tuple")

        if len(cube_filters) > 1:
            s += ","

        return s + make_filter_repr(cube_filters[1:])
    else:
        return ""


def _make_params_payload(cube_name, cube_fields, cube_filters):    
    return {
        "cube": '{"name":"' + cube_name + '"}',
        "charset": "UTF-16",
        "delimiter": "\t",
        "quote": '"',
        "escape": '"',
        "headers": "[" + _make_headers_repr(cube_fields) + "]",
        "filters": "[" + make_filter_repr(cube_filters) + "]",
    }


def get_ctx_cube(
    cube_name,
    cube_fields,
    cube_filters,
    auth_headers,
    cubos_endpoint,
):

    """Returns Cortex Dataset as a Pandas DataFrame

    Parameters
    ----------
    cube_name: str
    cube_fields: list, columns to be retrieved from dataset
    cube_filters: list of dicts
        [
            {"name": "column1", "values": ["apple", "banana"], "exclude": bool, "exact_match": bool},
            {"name": "column2", "values": (5,10), "exclude": bool, "exact_match": bool},
            {"name": "column2", "values": ("2021-01-01", "2021-02-01"), "exclude": bool, "exact_match": bool},
        ]
    auth_headers: dict,
        Authentication response for the Client's plataform
    cubos_endpoint: str,
        Client's endpoint for all Datasets

    * Accepted date formats: YYYY-mm-dd, YYYYmmdd
    Returns
    -------
    Dict
        {"status_code": status_code, "df":Dataset from Cortex Plataform}
    """

    if not isinstance(cube_filters, list):
        raise Exception("cube filters must be a list")
    if not isinstance(cube_fields, list):
        raise Exception("cube fields must be a list")

    params = _make_params_payload(cube_name, cube_fields, cube_filters)
    response = requests.post(cubos_endpoint, headers=auth_headers, data=params)
    response.raise_for_status()

    if response.headers["Content-Type"] == "application/gzip":
        decompressed_data = zlib.decompress(response.content, 16 + zlib.MAX_WBITS)
        data_str = decompressed_data.decode("utf-16", "surrogateescape")
    else:
        data_str = response.content.decode("utf-16", "surrogateescape")

    return pd.read_csv(io.StringIO(data_str), delimiter="\t")
