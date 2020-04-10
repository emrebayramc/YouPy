# -*- coding: utf-8 -*-
import argparse
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest

from YouPy import cli, StreamQuery, Caption, CaptionQuery
from YouPy.exceptions import PytubeError

parse_args = cli._parse_args


@mock.patch("YouPy.cli._parse_args")
def test_main_invalid_url(_parse_args):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["crikey",],)
    _parse_args.return_value = args
    with pytest.raises(SystemExit):
        cli.main()


@mock.patch("YouPy.cli.display_streams")
@mock.patch("YouPy.cli.YouTubeItem")
def test_download_when_itag_not_found(youtube_item, display_streams):
    # Given
    youtube_item.streams = mock.Mock()
    youtube_item.streams.get_by_itag.return_value = None
    # When
    with pytest.raises(SystemExit):
        cli.download_by_itag(youtube_item, 123)
    # Then
    youtube_item.streams.get_by_itag.assert_called_with(123)
    display_streams.assert_called_with(youtube_item)


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.Stream")
def test_download_when_itag_is_found(youtube_item, stream):
    stream.itag = 123
    stream.exists_at_path.return_value = False
    youtube_item.streams = StreamQuery([stream])
    with patch.object(
        youtube_item.streams, "get_by_itag", wraps=youtube_item.streams.get_by_itag
    ) as wrapped_itag:
        cli.download_by_itag(youtube_item, 123)
        wrapped_itag.assert_called_with(123)
    youtube_item.register_on_progress_callback.assert_called_with(cli.on_progress)
    stream.download.assert_called()


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.Stream")
def test_display_stream(youtube_item, stream):
    # Given
    stream.itag = 123
    stream.__repr__ = MagicMock(return_value="")
    youtube_item.streams = StreamQuery([stream])
    # When
    cli.display_streams(youtube_item)
    # Then
    stream.__repr__.assert_called()


@mock.patch("YouPy.cli._print_available_captions")
@mock.patch("YouPy.cli.YouTubeItem")
def test_download_caption_with_none(youtube_item, print_available):
    # Given
    caption = Caption(
        {"url": "url1", "name": {"simpleText": "name1"}, "languageCode": "en"},
        None
    )
    youtube_item.captions = CaptionQuery([caption])
    # When
    cli.download_caption(youtube_item, None)
    # Then
    print_available.assert_called_with(youtube_item.captions)


@mock.patch("YouPy.cli.YouTubeItem")
def test_download_caption_with_language_found(youtube_item):
    youtube_item.title = "video title"
    caption = Caption(
        {"url": "url1", "name": {"simpleText": "name1"}, "languageCode": "en"},
        None
    )
    caption.download = MagicMock(return_value="file_path")
    youtube_item.captions = CaptionQuery([caption])
    cli.download_caption(youtube_item, "en")
    caption.download.assert_called_with(title="video title", output_path=None)


@mock.patch("YouPy.cli._print_available_captions")
@mock.patch("YouPy.cli.YouTubeItem")
def test_download_caption_with_lang_not_found(youtube_item, print_available):
    # Given
    caption = Caption(
        {"url": "url1", "name": {"simpleText": "name1"}, "languageCode": "en"},
        None
    )
    youtube_item.captions = CaptionQuery([caption])
    # When
    cli.download_caption(youtube_item, "blah")
    # Then
    print_available.assert_called_with(youtube_item.captions)


def test_print_available_captions(capsys):
    # Given
    caption1 = Caption(
        {"url": "url1", "name": {"simpleText": "name1"}, "languageCode": "en"},
        None
    )
    caption2 = Caption(
        {"url": "url2", "name": {"simpleText": "name2"}, "languageCode": "fr"},
        None
    )
    query = CaptionQuery([caption1, caption2])
    # When
    cli._print_available_captions(query)
    # Then
    captured = capsys.readouterr()
    assert captured.out == "Available caption codes are: en, fr\n"


def test_display_progress_bar(capsys):
    cli.display_progress_bar(bytes_received=25, filesize=100, scale=0.55)
    out, _ = capsys.readouterr()
    assert "25.0%" in out


@mock.patch("YouPy.Stream")
def test_on_progress(stream):
    stream.filesize = 10
    cli.display_progress_bar = MagicMock()
    cli.on_progress(stream, "", 7)
    cli.display_progress_bar.assert_called_once_with(3, 10)


def test_parse_args_falsey():
    parser = argparse.ArgumentParser()
    args = cli._parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0"])
    assert args.url == "http://youtube_item.com/watch?v=9bZkp7q19f0"
    assert args.build_playback_report is False
    assert args.itag is None
    assert args.list is False
    assert args.verbosity == 0


def test_parse_args_truthy():
    parser = argparse.ArgumentParser()
    args = cli._parse_args(
        parser,
        [
            "http://youtube_item.com/watch?v=9bZkp7q19f0",
            "--build-playback-report",
            "-c",
            "en",
            "-l",
            "--itag=10",
            "-vvv",
        ],
    )
    assert args.url == "http://youtube_item.com/watch?v=9bZkp7q19f0"
    assert args.build_playback_report is True
    assert args.itag == 10
    assert args.list is True
    assert args.verbosity == 3


@mock.patch("YouPy.cli.setup_logger", return_value=None)
def test_main_logging_setup(setup_logger):
    # Given
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://fakeurl", "-v"])
    cli._parse_args = MagicMock(return_value=args)
    # When
    with pytest.raises(SystemExit):
        cli.main()
    # Then
    setup_logger.assert_called_with(40)


@mock.patch("YouPy.cli.YouTubeItem", return_value=None)
def test_main_download_by_itag(youtube_item):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "--itag=10"])
    cli._parse_args = MagicMock(return_value=args)
    cli.download_by_itag = MagicMock()
    cli.main()
    youtube_item.assert_called()
    cli.download_by_itag.assert_called()


@mock.patch("YouPy.cli.YouTubeItem", return_value=None)
def test_main_build_playback_report(youtube_item):
    parser = argparse.ArgumentParser()
    args = parse_args(
        parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "--build-playback-report"]
    )
    cli._parse_args = MagicMock(return_value=args)
    cli.build_playback_report = MagicMock()
    cli.main()
    youtube_item.assert_called()
    cli.build_playback_report.assert_called()


@mock.patch("YouPy.cli.YouTubeItem", return_value=None)
def test_main_display_streams(youtube_item):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "-l"])
    cli._parse_args = MagicMock(return_value=args)
    cli.display_streams = MagicMock()
    cli.main()
    youtube_item.assert_called()
    cli.display_streams.assert_called()


@mock.patch("YouPy.cli.YouTubeItem", return_value=None)
def test_main_download_caption(youtube_item):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "-c"])
    cli._parse_args = MagicMock(return_value=args)
    cli.download_caption = MagicMock()
    cli.main()
    youtube_item.assert_called()
    cli.download_caption.assert_called()


@mock.patch("YouPy.cli.YouTubeItem", return_value=None)
@mock.patch("YouPy.cli.download_by_resolution")
def test_download_by_resolution_flag(youtube_item, download_by_resolution):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "-r", "320p"])
    cli._parse_args = MagicMock(return_value=args)
    cli.main()
    youtube_item.assert_called()
    download_by_resolution.assert_called()


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli.Playlist")
@mock.patch("YouPy.cli._perform_args_on_youtube")
def test_download_with_playlist(perform_args_on_youtube, playlist, youtube_item):
    # Given
    cli.safe_filename = MagicMock(return_value="safe_title")
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["https://www.youtube_item.com/playlist?list=PLyn"])
    cli._parse_args = MagicMock(return_value=args)
    videos = [youtube_item]
    playlist_instance = playlist.return_value
    playlist_instance.videos = videos
    # When
    cli.main()
    # Then
    playlist.assert_called()
    perform_args_on_youtube.assert_called_with(youtube_item, args)


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli.Playlist")
@mock.patch("YouPy.cli._perform_args_on_youtube")
def test_download_with_playlist_video_error(
    perform_args_on_youtube, playlist, youtube_item, capsys
):
    # Given
    cli.safe_filename = MagicMock(return_value="safe_title")
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["https://www.youtube_item.com/playlist?list=PLyn"])
    cli._parse_args = MagicMock(return_value=args)
    videos = [youtube_item]
    playlist_instance = playlist.return_value
    playlist_instance.videos = videos
    perform_args_on_youtube.side_effect = PytubeError()
    # When
    cli.main()
    # Then
    playlist.assert_called()
    captured = capsys.readouterr()
    assert "There was an error with video" in captured.out


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.StreamQuery")
@mock.patch("YouPy.Stream")
@mock.patch("YouPy.cli._download")
def test_download_by_resolution(download, stream, stream_query, youtube_item):
    # Given
    stream_query.get_by_resolution.return_value = stream
    youtube_item.streams = stream_query
    # When
    cli.download_by_resolution(youtube_item=youtube_item, resolution="320p", target="test_target")
    # Then
    download.assert_called_with(stream, target="test_target")


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.StreamQuery")
@mock.patch("YouPy.cli._download")
def test_download_by_resolution_not_exists(download, stream_query, youtube_item):
    stream_query.get_by_resolution.return_value = None
    youtube_item.streams = stream_query
    with pytest.raises(SystemExit):
        cli.download_by_resolution(
            youtube_item=youtube_item, resolution="DOESNT EXIST", target="test_target"
        )
    download.assert_not_called()


@mock.patch("YouPy.Stream")
def test_download_stream_file_exists(stream, capsys):
    # Given
    stream.exists_at_path.return_value = True
    # When
    cli._download(stream=stream)
    # Then
    captured = capsys.readouterr()
    assert "Already downloaded at" in captured.out
    stream.download.assert_not_called()


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli.ffmpeg_process")
def test_perform_args_should_ffmpeg_process(ffmpeg_process, youtube_item):
    # Given
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "-f", "best"])
    cli._parse_args = MagicMock(return_value=args)
    # When
    cli._perform_args_on_youtube(youtube_item, args)
    # Then
    ffmpeg_process.assert_called_with(youtube_item=youtube_item, resolution="best", target=None)


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli._ffmpeg_downloader")
def test_ffmpeg_process_best_should_download(_ffmpeg_downloader, youtube_item):
    # Given
    target = "/target"
    streams = MagicMock()
    youtube_item.streams = streams
    video_stream = MagicMock()
    streams.filter.return_value.order_by.return_value.last.return_value = video_stream
    audio_stream = MagicMock()
    streams.get_audio_only.return_value = audio_stream
    # When
    cli.ffmpeg_process(youtube_item, "best", target)
    # Then
    _ffmpeg_downloader.assert_called_with(
        audio_stream=audio_stream, video_stream=video_stream, target=target
    )


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli._ffmpeg_downloader")
def test_ffmpeg_process_res_should_download(_ffmpeg_downloader, youtube_item):
    # Given
    target = "/target"
    streams = MagicMock()
    youtube_item.streams = streams
    video_stream = MagicMock()
    streams.filter.return_value.first.return_value = video_stream
    audio_stream = MagicMock()
    streams.get_audio_only.return_value = audio_stream
    # When
    cli.ffmpeg_process(youtube_item, "XYZp", target)
    # Then
    _ffmpeg_downloader.assert_called_with(
        audio_stream=audio_stream, video_stream=video_stream, target=target
    )


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli._ffmpeg_downloader")
def test_ffmpeg_process_res_none_should_not_download(_ffmpeg_downloader, youtube_item):
    # Given
    target = "/target"
    streams = MagicMock()
    youtube_item.streams = streams
    streams.filter.return_value.first.return_value = None
    audio_stream = MagicMock()
    streams.get_audio_only.return_value = audio_stream
    # When
    with pytest.raises(SystemExit):
        cli.ffmpeg_process(youtube_item, "XYZp", target)
    # Then
    _ffmpeg_downloader.assert_not_called()


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli._ffmpeg_downloader")
def test_ffmpeg_process_audio_none_should_fallback_download(
    _ffmpeg_downloader, youtube_item
):
    # Given
    target = "/target"
    streams = MagicMock()
    youtube_item.streams = streams
    stream = MagicMock()
    streams.filter.return_value.order_by.return_value.last.return_value = stream
    streams.get_audio_only.return_value = None
    # When
    cli.ffmpeg_process(youtube_item, "best", target)
    # Then
    _ffmpeg_downloader.assert_called_with(
        audio_stream=stream, video_stream=stream, target=target
    )


@mock.patch("YouPy.cli.YouTubeItem")
@mock.patch("YouPy.cli._ffmpeg_downloader")
def test_ffmpeg_process_audio_fallback_none_should_exit(_ffmpeg_downloader, youtube_item):
    # Given
    target = "/target"
    streams = MagicMock()
    youtube_item.streams = streams
    stream = MagicMock()
    streams.filter.return_value.order_by.return_value.last.side_effect = [
        stream,
        stream,
        None,
    ]
    streams.get_audio_only.return_value = None
    # When
    with pytest.raises(SystemExit):
        cli.ffmpeg_process(youtube_item, "best", target)
    # Then
    _ffmpeg_downloader.assert_not_called()


@mock.patch("YouPy.cli.os.unlink", return_value=None)
@mock.patch("YouPy.cli.subprocess.run", return_value=None)
@mock.patch("YouPy.cli._download", return_value=None)
@mock.patch("YouPy.cli._unique_name", return_value=None)
def test_ffmpeg_downloader(unique_name, download, run, unlink):
    # Given
    target = "target"
    audio_stream = MagicMock()
    video_stream = MagicMock()
    video_stream.id = "video_id"
    audio_stream.subtype = "audio_subtype"
    video_stream.subtype = "video_subtype"
    unique_name.side_effect = ["video_name", "audio_name"]

    # When
    cli._ffmpeg_downloader(
        audio_stream=audio_stream, video_stream=video_stream, target=target
    )
    # Then
    download.assert_called()
    run.assert_called_with(
        [
            "ffmpeg",
            "-i",
            "target/video_name.video_subtype",
            "-i",
            "target/audio_name.audio_subtype",
            "-codec",
            "copy",
            "target/safe_title.video_subtype",
        ]
    )
    unlink.assert_called()


@mock.patch("YouPy.cli.download_audio")
@mock.patch("YouPy.cli.YouTubeItem.__init__", return_value=None)
def test_download_audio_args(youtube_item, download_audio):
    # Given
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0", "-a", "mp4"])
    cli._parse_args = MagicMock(return_value=args)
    # When
    cli.main()
    # Then
    youtube_item.assert_called()
    download_audio.assert_called()


@mock.patch("YouPy.cli._download")
@mock.patch("YouPy.cli.YouTubeItem")
def test_download_audio(youtube_item, download):
    # Given
    youtube_instance = youtube_item.return_value
    audio_stream = MagicMock()
    youtube_instance.streams.filter.return_value.order_by.return_value.last.return_value = (
        audio_stream
    )
    # When
    cli.download_audio(youtube_instance, "filetype", "target")
    # Then
    download.assert_called_with(audio_stream, target="target")


@mock.patch("YouPy.cli._download")
@mock.patch("YouPy.cli.YouTubeItem")
def test_download_audio_none(youtube_item, download):
    # Given
    youtube_instance = youtube_item.return_value
    youtube_instance.streams.filter.return_value.order_by.return_value.last.return_value = (
        None
    )
    # When
    with pytest.raises(SystemExit):
        cli.download_audio(youtube_instance, "filetype", "target")
    # Then
    download.assert_not_called()


@mock.patch("YouPy.cli.YouTubeItem.__init__", return_value=None)
def test_perform_args_on_youtube(youtube_item):
    parser = argparse.ArgumentParser()
    args = parse_args(parser, ["http://youtube_item.com/watch?v=9bZkp7q19f0"])
    cli._parse_args = MagicMock(return_value=args)
    cli._perform_args_on_youtube = MagicMock()
    cli.main()
    youtube_item.assert_called()
    cli._perform_args_on_youtube.assert_called()


@mock.patch("YouPy.cli.os.path.exists", return_value=False)
def test_unique_name(path_exists):
    assert cli._unique_name("base", "subtype", "video", "target") == "base_video_0"


@mock.patch("YouPy.cli.os.path.exists")
def test_unique_name_counter(path_exists):
    path_exists.side_effect = [True, False]
    assert cli._unique_name("base", "subtype", "video", "target") == "base_video_1"
