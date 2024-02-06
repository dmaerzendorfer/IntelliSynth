import pygame.midi
import midi.midio.DeviceFinder as DeviceFinder
import midi.midio.MidiMetadata as MidiMetadata
from threading import Lock


class MidiOutput:

    __midiOutput = None
    __lock = None

    @classmethod
    def __init__(cls):
        if not pygame.midi.get_init():
            pygame.midi.init()
        cls.__lock = Lock()

        deviceId = cls.__findOutputDevice()
        cls.__midiOutput = pygame.midi.Output(deviceId)

    @classmethod
    def __findOutputDevice(cls):
        return DeviceFinder.findDevice(MidiMetadata.MIDIDeviceDirection.OUTPUT.value)

    @classmethod
    def writeEvent(cls, event):
        cls.__lock.acquire()
        try:
            cls.__midiOutput.write(event)
        finally:
            cls.__lock.release()

