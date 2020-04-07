# -*- coding: utf-8 -*-
from unittest import mock

import pytest

from YouPy import YouTubeItem
from YouPy.exceptions import VideoUnavailable


@mock.patch("YouPy.youtube_item.YouTubeItem")
def test_prefetch_deferred(youtube_item):
    instance = youtube_item.return_value
    instance.prefetch_descramble.return_value = None
    YouTubeItem("https://www.youtube.com/watch?v=9bZkp7q19f0", True)
    assert not instance.prefetch_descramble.called


@mock.patch("urllib.request.install_opener")
def test_install_proxy(opener):
    proxies = {"http": "http://www.example.com:3128/"}
    YouTubeItem(
        "https://www.youtube.com/watch?v=9bZkp7q19f0",
        defer_prefetch_init=True,
        proxies=proxies,
    )
    opener.assert_called()


@mock.patch("YouPy.request.get")
def test_video_unavailable(get):
    get.return_value = None
    youtube_item = YouTubeItem(
        "https://www.youtube.com/watch?v=9bZkp7q19f0", defer_prefetch_init=True
    )
    with pytest.raises(VideoUnavailable):
        youtube_item.prefetch()
