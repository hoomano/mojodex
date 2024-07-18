import pyaudio
import wave


class AudioRecorder:
    def __init__(self, filename='output.wav', channels=1, rate=44100, chunk=1024):
        # self.device = self.list_devices()[0] # Default device
        self.filename = filename
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.frames = []
        self.is_recording = False
        self.p = pyaudio.PyAudio()
        self.stream = None

    def start_recording(self, send_message:callable):
        try:
            send_message("Start_recording")
            self.stream = self.p.open(format=pyaudio.paInt16,
                                    channels=self.channels,
                                    rate=self.rate,
                                    input=True,
                                    input_device_index=1,
                                    frames_per_buffer=self.chunk)
            self.is_recording = True
            self.frames = []
            send_message("Recording started...")
            while self.is_recording:
                data = self.stream.read(self.chunk)
                self.frames.append(data)
        except Exception as e:
            send_message(f"Error: {e}")

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        with wave.open(self.filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        print(f"Recording saved to {self.filename}.")
    
    def list_devices(self):
        info = self.p.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        devices = []
        for i in range(num_devices):
            device_info = self.p.get_device_info_by_index(i)
            if device_info.get('maxInputChannels') > 0:
                devices.append((i, device_info.get('name')))
        return devices