
from concurrent.futures import thread
from xmlrpc.client import Boolean
import pychromecast
import zeroconf
import time
import threading

class ChromecastPlayer(object):
    def __init__(self, on_mc_status_callback) -> None:
        self.cast_lock = threading.Lock()
        self.on_mc_status_callback = on_mc_status_callback
        with(self.cast_lock):
            self.__setup()
    
        self.current_session_id = None  # Track current session ID
        #start a thread that wakes up every hour to check on the connection, re establish if not
        self.is_resetting = False
        self.reset_thread = threading.Thread(target=self.__reset_connection )
        self.reset_thread.start()

    def __setup(self) -> None:
        print(f"Setting up or resetting player")
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["All Speakers"])
        self.cast = chromecasts[0]
        self.cast.wait()
        self.cast.media_controller.register_status_listener(self.on_mc_status_callback)
        

    def play_next(self, url, session_id: str):
        print(f"Requesting to play {url} for {session_id}", flush=True)
        self.current_session_id = session_id
        # If a new session ID comes in, evict the old session
        # If the player is not playing and the index is 0, start playing
        self.cast.wait()
        isPlaying = self.__isPlaying()
        self.cast.media_controller.play_media(url, "audio/wav", enqueue=isPlaying)
        
    def __isPlaying(self) -> Boolean:
        return self.cast.media_controller.player_is_playing
        

    def __reset_connection(self):
        while True:
            try:
                time.sleep(60*60)
                if( not self.__isPlaying()):
                    self.cast_lock.acquire()
                    self.cast.disconnect()
                    self.__setup()
                    self.cast_lock.release()
            except:
                continue
