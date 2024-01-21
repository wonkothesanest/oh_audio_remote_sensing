
from concurrent.futures import thread
from xmlrpc.client import Boolean
import pychromecast
import zeroconf
import time





chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["All Speakers"])
print(chromecasts)
print(browser)

cast = chromecasts[0]
cast.wait()
print(cast)
url = 'http://192.168.0.42:5099/api/stream?session_id=720b2317-34e5-413c-8034-4ead6bc8463a&voice_id=gregorovich'
cast.media_controller.play_media(url, "audio/wav" )
cast.media_controller.block_until_active()
cast.media_controller.play()
print(cast.media_controller.status)
