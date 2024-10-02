import numpy as np
from scipy.signal import lfilter
import matplotlib.pyplot as plt
from scipy.io.wavfile import write
from IPython.display import Audio
from process_bigraph import Process, Composite, Step

from biosimulators_processes import CORE


class ToneGenerator(Step):
    config_schema = {
        'frequency': 'integer',
        'duration': 'integer',
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.frequency = self.config['frequency']
        self.duration = self.config['duration']

    def outputs(self):
        return {'tone': 'list[float]'}

    def update(self, state):
        return {'tone': generate_sine_wave(self.frequency, self.duration).tolist()}


class EffectPedal(Step):
    config_schema = {
        'type': 'string',
        'params': 'tree[float]'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

        effect_type = self.config['type']
        self.function_generator = None
        if "phaser" in effect_type:
            self.function_generator = apply_phaser
        elif "flanger" in effect_type:
            self.function_generator = apply_flanger
        elif "ring_modulation" in effect_type:
            self.function_generator = apply_ring_modulation
        elif "tremolo" in effect_type:
            self.function_generator = apply_tremolo

        if self.function_generator is None:
            raise ValueError("Function generator not defined in config!")

        self.params = self.config['params']

    def inputs(self):
        return {'tone': 'list[float]'}

    def outputs(self):
        return {'modulated_tone': 'list[float]'}

    def update(self, state):
        tone = np.array(state['tone'])
        modulated_tone = self.function_generator(tone, **self.params)
        return {'modulated_tone': modulated_tone.tolist()}


def test_synthesizer():
    doc = {
        'tone_generator': {
            '_type': 'step',
            'address': 'local:tone-generator',
            'config': {
                'duration': 5,
                'frequency': 200
            },
            'inputs': {},
            'outputs': {
                'tone': ['tone_store']
            }
        },
        'phaser': {
            '_type': 'step',
            'address': 'local:effect-pedal',
            'config': {
                'type': 'phaser',
            },
            'inputs': {
                'tone': ['tone_store']
            },
            'outputs': {
                'modulated_tone': ['modulated_tone_store']
            }
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    'tone': 'list[float]',
                    'modulated_tone': 'list[float]'
                }
            },
            'inputs': {
                'tone': ['tone_store'],
                'modulated_tone': ['modulated_tone_store']
            }
        }
    }

    c = Composite(config={'state': doc}, core=CORE)
    c.run(1)
    return c.gather_results()


def generate_sine_wave(frequency, duration, sample_rate=44100) -> np.ndarray:
    """
    Generate a sine wave based on the given frequency and duration.

    Args:
    - frequency (float): The frequency of the note (in Hz).
    - duration (float): Duration of the wave (in seconds).
    - sample_rate (int): The sampling rate (default is 44100 Hz).

    Returns:
    - numpy.ndarray: The generated sine wave.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    sine_wave = np.sin(2 * np.pi * frequency * t)
    return sine_wave


def apply_tremolo(wave, rate=10, depth=0.5, sample_rate=44100):
    """
    Apply a tremolo effect to the sine wave.

    Args:
    - wave (numpy.ndarray): The original sine wave.
    - rate (float): The frequency of the tremolo modulation (in Hz).
    - depth (float): The depth of the modulation (between 0 and 1).
    - sample_rate (int): The sampling rate (default is 44100 Hz).

    Returns:
    - numpy.ndarray: The sine wave with the tremolo effect applied.
    """
    t = np.linspace(0, len(wave) / sample_rate, len(wave), endpoint=False)
    modulation = 1 + depth * np.sin(2 * np.pi * rate * t)
    return wave * modulation


def apply_phaser(wave, depth=0.5, rate=1.0, feedback=0.5, sample_rate=44100):
    """
    Apply a phaser effect to the sine wave.

    Args:
    - wave (numpy.ndarray): The original sine wave.
    - depth (float): The depth of the phaser modulation.
    - rate (float): The rate of the phaser sweep (in Hz).
    - feedback (float): The feedback coefficient.
    - sample_rate (int): The sampling rate (default is 44100 Hz).

    Returns:
    - numpy.ndarray: The sine wave with the phaser effect applied.
    """
    # Create LFO for phasing
    t = np.linspace(0, len(wave) / sample_rate, len(wave), endpoint=False)
    lfo = depth * np.sin(2 * np.pi * rate * t)

    # All-pass filter coefficients for phasing
    a1 = feedback
    phaser_wave = lfilter([1], [1, -a1], wave + lfo)

    return phaser_wave


def apply_flanger(wave, delay=0.002, depth=0.5, rate=0.25, sample_rate=44100):
    """
    Apply a flanger effect to the sine wave.

    Args:
    - wave (numpy.ndarray): The original sine wave.
    - delay (float): Base delay time in seconds.
    - depth (float): The depth of the flanger modulation.
    - rate (float): The rate of the flanger sweep (in Hz).
    - sample_rate (int): The sampling rate (default is 44100 Hz).

    Returns:
    - numpy.ndarray: The sine wave with the flanger effect applied.
    """
    t = np.linspace(0, len(wave) / sample_rate, len(wave), endpoint=False)
    lfo = depth * np.sin(2 * np.pi * rate * t)
    max_delay_samples = int(delay * sample_rate)

    flanger_wave = np.zeros_like(wave)

    for i in range(len(wave)):
        delay_samples = int((lfo[i] + delay) * sample_rate)
        if i - delay_samples >= 0:
            flanger_wave[i] = wave[i] + wave[i - delay_samples]

    return flanger_wave / (1 + depth)  # Normalize to avoid clipping


def apply_ring_modulation(wave, mod_freq=30.0, sample_rate=44100):
    """
    Apply a ring modulator effect to the sine wave.

    Args:
    - wave (numpy.ndarray): The original sine wave.
    - mod_freq (float): The modulation frequency (in Hz).
    - sample_rate (int): The sampling rate (default is 44100 Hz).

    Returns:
    - numpy.ndarray: The sine wave with the ring modulation applied.
    """
    t = np.linspace(0, len(wave) / sample_rate, len(wave), endpoint=False)
    mod_wave = np.sin(2 * np.pi * mod_freq * t)
    return wave * mod_wave


def plot_wave(wave, sample_rate=44100, title="Waveform"):
    """
    Plot the waveform using matplotlib.

    Args:
    - wave (numpy.ndarray): The waveform to plot.
    - sample_rate (int): The sample rate (default is 44100 Hz).
    - title (str): Title for the plot.
    """
    duration = len(wave) / sample_rate
    t = np.linspace(0, duration, len(wave), endpoint=False)

    plt.figure(figsize=(10, 4))
    plt.plot(t, wave)
    plt.title(title)
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude")
    plt.show()


def play_wave(wave, sample_rate=44100):
    """
    Play the waveform using IPython display Audio.

    Args:
    - wave (numpy.ndarray): The waveform to play.
    - sample_rate (int): The sample rate (default is 44100 Hz).

    Returns:
    - IPython.display.Audio: The audio object to play in the notebook.
    """
    # Normalize the wave to be in the range -1 to 1
    normalized_wave = np.int16(wave / np.max(np.abs(wave)) * 32767)

    # Save as a temporary file and play it
    return Audio(normalized_wave, rate=sample_rate)