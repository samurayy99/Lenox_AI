from bark import generate_audio, SAMPLE_RATE
import numpy as np
from scipy.io.wavfile import write

# Test audio generation
text = "Hello, welcome to the world of speech synthesis!"
audio_array = generate_audio(text)

# Convert audio array to int16 format and save to file
audio_int16 = np.int16(audio_array * 32767)
write('test_output.wav', SAMPLE_RATE, audio_int16)
print("Audio generated and saved as 'test_output.wav'")
