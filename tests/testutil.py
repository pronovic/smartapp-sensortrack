# -*- coding: utf-8 -*-
# vim: set ft=python ts=4 sw=4 expandtab:

"""
Unit test utilities.
"""
import os
from typing import Dict


def load_data(path: str) -> Dict[str, str]:
    """Load text of all files in a directory into a dict."""
    data = {}
    for f in os.listdir(path):
        p = os.path.join(path, f)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as r:
                data[f] = r.read()
    return data
