from typing import List

import pydantic
from aind_pydantic_codegen.generators import ParsedSource


class MyMockType(pydantic.BaseModel):
    name: str
    field: str


MOCK_DATA_SOURCE = "name,field\nfoo,foo_field\nbar,bar_field\nbaz,baz_field"
MOCK_PARSED_SOURCE = [
    {"name": "foo", "field": "foo_field"},
    {"name": "bar", "field": "bar_field"},
    {"name": "baz", "field": "baz_field"},
]


def mock_data_parser(data: str) -> list[ParsedSource]:
    _header, *rows = data.split("\n")
    header = _header.split(",")
    _list: List[ParsedSource] = []
    for _row in rows:
        row = _row.split(",")
        _list.append({key: value for key, value in zip(header, row)})
    return _list
