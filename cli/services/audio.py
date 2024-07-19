import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

class AudioRecorder:
    def __init__(self, filename='output.wav', channels=1, rate=44100, dtype='int16'):
        self.filename = filename
        self.channels = channels
        self.rate = rate
        self.dtype = dtype
        self.frames = []
        self.is_recording = False

    def start_recording(self, send_message: callable):

        try:
            self.is_recording = True
            self.frames = []

            def callback(indata, frames, time, status):
                self.frames.append(indata.copy())

            with sd.InputStream(samplerate=self.rate, channels=self.channels, dtype=self.dtype, callback=callback):
                while self.is_recording:
                    sd.sleep(100)
        except Exception as e:
            send_message(f"An error occurred while recording: {e}")
            self.is_recording = False

    def stop_recording(self, send_message:callable):
        try:
            if not self.is_recording:
                return

            self.is_recording = False
            audio_data = np.concatenate(self.frames, axis=0)
            write(self.filename, self.rate, audio_data)
        except Exception as e:
            send_message(f"An error occured while stopping recording: {e}")

    def list_devices(self):
        devices = sd.query_devices()
        input_devices = [(i, d['name']) for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        return input_devices