
import pychromecast
import zeroconf
import time

class PulsePlayer(object):
    def __init__(self) -> None:
        chromecasts, browser = pychromecast.get_listed_chromecasts(friendly_names=["All Speakers"])
        self.cast = chromecasts[0]
        self.cast.wait()
        
        self.cache = {}  # Cache to store URLs
        self.current_session_id = None  # Track current session ID
        self.expected_index = 0  # Expected index for the next URL to play

    def play_next(self, url, index, session_id):
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
            url = self.cache.pop(self.expected_index)
            self.cast.wait()
            isPlaying = self.cast.media_controller.status.player_state == "PLAYING"
            # it toggles for a brief moment between tracks
            r = 5 if (self.expected_index == 0) else 20
            for _ in range(r):
                if(isPlaying):
                    break
                time.sleep(0.1)
                isPlaying = self.cast.media_controller.status.player_state == "PLAYING"

            print(f"Playing index {self.expected_index} and will be enqueueing with {isPlaying}")
            self.cast.media_controller.play_media(url, "audio/mp3", enqueue=isPlaying)
            self.expected_index += 1
            # Wait for a short duration before checking the next URL
            time.sleep(2)  # Adjust this duration as needed


# Example usage
#player = PulsePlayer()
#player.play_next("http://example.com/track1.mp3", 1, "session1")
#player.play_next("http://example.com/track0.mp3", 0, "session1")

