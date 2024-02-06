from multiprocessing import Event
import midi.midio.MidiMetadata as MidiMetadata
from time import sleep


class MidiMetronome:
    __outputDevice = None
    __channel = 0
    __bpm = 0

    @classmethod
    def __init__(cls, outputDevice, bpm, channel):
        cls.__outputDevice = outputDevice
        cls.__bpm = bpm
        cls.__channel = channel

    @classmethod
    def tickForNBeats(cls, beats):
        #play the metronome for a certain amount of beats
        beatDuration = 60 / cls.__bpm

        for beat in range(beats):
            cls.__sound(beatDuration)
            
    @classmethod
    def __sound(cls, beatDuration):
        #make a single tick sound
        cls.__outputDevice.playEvent([[[MidiMetadata.MidiEvent.noteOn.value, 60, 100, 0], 0]], cls.__channel)
        sleep(0.01)
        cls.__outputDevice.playEvent([[[MidiMetadata.MidiEvent.noteOff.value, 60, 0, 0], 0]], cls.__channel)
        sleep(beatDuration - 0.01)
        
            
    @classmethod
    def tickInfinite(cls, tickEvent: Event):
        #continuously play the metronome
        beatDuration = 60 / cls.__bpm
        
        while True:
            #let others know i will tick now
            tickEvent.set()
            tickEvent.clear()
            cls.__sound(beatDuration)
            
        
        
        

