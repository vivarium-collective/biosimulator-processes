from typing import Callable
import numpy as np 
from process_bigraph.composite import Composite, Process
from biosimulator_processes.steps.viz import ResultsAnimation


class Synthesizer:
   current_note: list

   def __init__(self, sample_rate: int = 44100) -> None:
      self.sample_rate = sample_rate
      self.all_notes = {}
   
   def apply_effect(self, application_func: Callable, **kwargs):
      """This should be called by the processes"""
      return application_func(**kwargs)

   def generate_sine_wave(self, frequency: int, duration: int):
      t = np.arange(0, duration, 1 /self.sample_rate)
      return np.sin(2 * np.pi * frequency * t).tolist()

   def apply_tremolo(self, wave, rate: float, depth: float):
      if isinstance(wave, list):
         wave = np.array(wave)
      t = np.arange(len(wave)) / self.sample_rate
      modulator = 1 + depth * np.sin(2 * np.pi * rate * t)
      return (wave * modulator).tolist()
   
   def apply_flanger(self, wave, delay: int, depth: int, rate: float):
      if isinstance(wave, list):
         wave = np.array(wave)

      length = len(wave)
      flanged = np.copy(wave)
      t = np.arange(length)
      delay_signal = delay + depth * np.sin(2 * np.pi * rate * t / self.sample_rate)

      for i in range(length):
         index = int(i - delay_signal[i])
         if index >= 0 and index < length:
               flanged[i] += wave[index]

      return flanged.tolist()


class SynthesizerProcess(Process):
   config_schema = {
      'frequency': 'int',
      'duration': 'int'
   }

   def __init__(self, config=None, core=None):
      super().__init__(config, core)

   def inputs(self):
      pass
   
      

def play(pitch: int, phrase_duration: int, atomic_duration: int):
   output = []
   synth = Synthesizer()
   '''output[0] = synth.generate_sine_wave(pitch, atomic_duration)
   
   for beat in range(phrase_duration):
      output[beat + 1] = synth.apply_flanger(output[beat], 3, 8, 3.2)'''
   
   output.append(synth.generate_sine_wave(pitch, atomic_duration))
   output.append(synth.apply_tremolo(output[0], 23.23, 8.2))
   output.append(synth.apply_flanger(output[1], 3, 10, 23.4))
   output.append(synth.apply_flanger(output[2], 3, 10, 23.4))
   output.append(synth.apply_flanger(output[3], 3, 10, 23.4))
   return np.array(output)



output = play(440, 10, 2)
print(output)
      
      
   
   


   