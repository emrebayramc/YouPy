# -*- coding: utf-8 -*-
# flake8: noqa: F401
# noreorder
"""
YouPy: a simple Python library to automate youtube downloads
"""
__title__ = "YouPy"
__author__ = "Emre Bayram"
__license__ = "MIT License"
__copyright__ = "Copyright 2020 Emre Bayram"

from YouPy.streams import Stream
from YouPy.captions import Caption
from YouPy.query import CaptionQuery
from YouPy.query import StreamQuery
from YouPy.youtube_item import YouTubeItem
from YouPy.contrib.playlist import Playlist
