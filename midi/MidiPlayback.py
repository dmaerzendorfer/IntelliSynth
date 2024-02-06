import midi.midio.Output as Output
import midi.EventTimeTranslator as Translator
import music21.midi
from time import sleep


class MidiPlayback:
    __instance = None
    __outputDevice = None
    __bpm = 0

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls, bpm):
        if cls.__instance is None:
            print('Creating new Playback Device')
            cls.__instance = cls.__new__(cls)
            cls.__outputDevice = Output.MidiOutput()
            cls.__bpm = bpm
        return cls.__instance

    @classmethod
    def playEvent(cls, pygEvent, channel=1):
        eventWithChannel = cls.addChannelBitsToEvent(pygEvent[0][0][0], channel)
        cls.__outputDevice.writeEvent([[[eventWithChannel, pygEvent[0][0][1], pygEvent[0][0][2], pygEvent[0][0][3]], pygEvent[0][1]]])

    @classmethod
    def playEvents(cls, m21Stream, channel=1):
        flatStream = m21Stream.flatten()
        packets = music21.midi.translate.streamToPackets(flatStream)
        midiTrack = music21.midi.MidiTrack()
        m21Events = music21.midi.translate.packetsToDeltaSeparatedEvents(packets, midiTrack)

        deltaMs = 0
        for event in m21Events:
            if event.isDeltaTime():
                deltaMs = Translator.EventTimeTranslator.dtToMs(event.time, cls.__bpm)
            elif event.type == music21.midi.ChannelVoiceMessages.NOTE_ON.value or event.type == music21.midi.ChannelVoiceMessages.NOTE_OFF.value:
                sleep(deltaMs / 1000)
                cls.playEvent([[[event.type, event.pitch, event.velocity, 0], 0]], channel)

    @staticmethod
    def addChannelBitsToEvent(eventByte, channelOneIndexed):
        return eventByte + channelOneIndexed - 1