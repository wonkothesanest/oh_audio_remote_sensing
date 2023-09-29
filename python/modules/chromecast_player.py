
from concurrent.futures import thread
from xmlrpc.client import Boolean
import pychromecast
import zeroconf
import time
import threading

class ChromecastPlayer(object):
    def __init__(self) -> None:

        self.cast_semaphore = threading.Semaphore()
        self.cast_semaphore.acquire()
        self.__setup()
        self.cast_semaphore.release()

        self.cache = {}  # Cache to store URLs
        self.current_session_id = None  # Track current session ID
        self.expected_index = 0  # Expected index for the next URL to play
        #start a thread that wakes up every hour to check on the connection, re establish if not
        self.is_resetting = False
        self.reset_thread = threading.Thread(target=self.__reset_connection )
        self.reset_thread.start()

    def __setup(self) -> None:
        print(f"Setting up or resetting player")
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["All Speakers"])
        self.cast = chromecasts[0]
        self.cast.wait()
        

    def play_next(self, url, index, session_id):
        print(f"Requesting {session_id} Track Number {index} to play {url}")
        # If a new session ID comes in, evict the old session
        if session_id != self.current_session_id:
            print("Clearing the cache")
            self.cache.clear()
            self.current_session_id = session_id
            self.expected_index = 0

        # Store the URL in the cache
        self.cache[index] = url

        # If the player is not playing and the index is 0, start playing
        self._play_from_cache()

    def _play_from_cache(self):
        while self.expected_index in self.cache:
            self.cast_semaphore.acquire()
            url = self.cache.pop(self.expected_index)
            self.cast.wait()
            isPlaying = self.__isPlaying()
            # it toggles for a brief moment between tracks
            r = 5 if (self.expected_index == 0) else 20
            for _ in range(r):
                if(isPlaying):
                    break
                time.sleep(0.1)
                isPlaying = self.__isPlaying()

            print(f"Playing index {self.expected_index} and will be enqueueing with {isPlaying}")
            self.cast.media_controller.play_media(url, "audio/mp3", enqueue=isPlaying)
            self.expected_index += 1
            self.cast_semaphore.release()
        
    def __isPlaying(self) -> Boolean:
        player_state = self.cast.media_controller.status.player_state 
        return player_state == "PLAYING"

    def __reset_connection(self):
        while True:
            try:
                time.sleep(60*60)
                if( not self.__isPlaying()):
                    self.cast_semaphore.acquire()
                    self.cast.disconnect()
                    self.__setup()
                    self.cast_semaphore.release()
            except:
                continue

# Example usage
#player = ChromecastPlayer()
#player.play_next("https://cdn.pixabay.com/download/audio/2022/11/21/audio_1b7f7e3ca3.mp3", 0, "session1")
#player.play_next("https://cdn.pixabay.com/download/audio/2022/11/21/audio_1b7f7e3ca3.mp3", 1, "session1")
#time.sleep(5)
#player.play_next("https://cdn.pixabay.com/download/audio/2022/11/21/audio_1b7f7e3ca3.mp3", 0, "session2")
#player.play_next("https://cdn.pixabay.com/download/audio/2022/11/21/audio_1b7f7e3ca3.mp3", 1, "session2")

