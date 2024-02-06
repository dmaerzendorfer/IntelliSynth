import enum

acceptedInputDeviceList = [b'Roland Digital Piano MIDI 1', b'Digital Piano MIDI 1']
acceptedOutputDeviceList = [b'CH345 MIDI 1']


## Defines standard Midievents as their representing byte sequence in the MIDI stream
# since Midi Events consist of 4 Message Bits followed by 4 Channel bits these following
# Messages are all defined for channel 0 and therefore have to be summed together with the channel number#
class MidiEvent(enum.Enum):
    noteOn = 0x90
    noteOff = 0x80
    channelChange = 0xB0


class MIDIDeviceDirection(enum.Enum):
    OUTPUT = 0
    INPUT = 1
