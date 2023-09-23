
import pychromecast
import zeroconf


class PulsePlayer(object):
    def __init__(self) -> None:
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["All Speakers"])
        self.cast = chromecasts[0]
        self.cast.wait()


    def play_next(self, url):
        
        if(self.cast.media_controller.status.player_state != "PLAYING"):
            isPlaying=False
        else:
            isPlaying = True

        self.cast.media_controller.play_media(url, "audio/mp3", enqueue=isPlaying)
