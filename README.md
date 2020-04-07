# YouPy
a simple clone of pytube library; and modified for my personal needs

I hit "http error 429 too many requests" while using the pytube library.
Although I have updated my code while using pytube to put sleep between downloads; I am still banned from downloading videos.

To workaround this; I have cloned pytube library and created a new class "YouTubeItem" which can take request header.
By passing cookie and user agent to the request header; i was able to download again.

- Simple Usage:

```from YouPy import YouTubeItem

youtube_item = YouTubeItem(video_url, request_headers = {<optional request headers>})
v_1080p = youtube_item.streams.filter(res='1080p').first()
if v_1080p is not None:
  v_1080p.download('<download_path>', filename=<file_name>)

```
Details:
https://medium.com/@emrebayram_71713/how-to-avoid-http-error-429-too-many-requests-in-python-while-using-pytube-library-39c5eced838e
