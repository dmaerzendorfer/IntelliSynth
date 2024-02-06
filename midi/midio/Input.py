import pygame.midi
import midi.midio.DeviceFinder as DeviceFinder
import midi.midio.MidiMetadata as MidiMetadata


class MidiInput:

    __midiInput = None

    @classmethod
    def __init__(cls):
        if not pygame.midi.get_init():
            pygame.midi.init()

        deviceId = cls.__findInputDevice()
        cls.__midiInput = pygame.midi.Input(deviceId)

    @classmethod
    def __findInputDevice(cls):
        return DeviceFinder.findDevice(MidiMetadata.MIDIDeviceDirection.INPUT.value)

    @classmethod
    def getEvent(cls, amount):
        if cls.__midiInput.poll():
            return cls.__midiInput.read(amount)
        return None

    @classmethod
    def flushBuffer(cls):
        while cls.__midiInput.poll():
            cls.__midiInput.read(1)
