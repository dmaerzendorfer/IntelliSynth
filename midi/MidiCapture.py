from socket import AddressFamily
import music21.midi
from music21.midi import translate as StreamTranslator
from threading import *
import time

import midi.midio.Input as Input
import midi.MidiPlayback as MidiPlayback
import midi.EventTimeTranslator as Translator


class MidiCapture:
    input = None
    playBackDevice = None
    bpm = 0
    captureDuration = 0
    midiChannel = 1
    beats = 0

    @classmethod
    def __init__(cls, bpm: int, beats: int, playbackChannel: int):
        cls.input = Input.MidiInput()
        cls.bpm = bpm
        cls.beats = beats
        cls.captureDuration = beats * (60000000 / bpm) / 1000000
        cls.playBackDevice = MidiPlayback.MidiPlayback.instance(bpm)
        cls.midiChannel = playbackChannel

    @classmethod
    def captureAndPlayback(cls):
        events = []
        startTime = time.time()
        print("Listening Phase Starting")
        cls.capturePygameEvents(events, startTime)
        print("Listening Phase Ended")
        return events

    @classmethod
    def capturePygameEvents(cls, events, startTime):
        firstNoteOnReceived = False 
        cls.input.flushBuffer()
        while time.time() <= startTime + cls.captureDuration:
            event = cls.input.getEvent(1)
            if event is not None and event[0][0][0] == Input.MidiMetadata.MidiEvent.noteOn.value and not firstNoteOnReceived:
                firstNoteOnReceived = True
                #capture time starts now
                startTime = time.time()

            if event is not None and firstNoteOnReceived:
                events.append(event[0])
                cls.playBack(event, cls.midiChannel)

    @classmethod
    def playBack(cls, pygEvent, channel):
        cls.playBackDevice.playEvent(pygEvent, channel)

    @classmethod
    def addMetaEvents(cls, midiTrack):
        instrument = music21.instrument.Instrument('')
        eventList = StreamTranslator.instrumentToMidiEvents(instrument)
        midiTrack.events.append(eventList[0])
        midiTrack.events.append(eventList[1])

        tempo = music21.tempo.MetronomeMark(number=cls.bpm)
        eventList = StreamTranslator.tempoToMidiEvents(tempo)
        midiTrack.events.append(eventList[0])
        midiTrack.events.append(eventList[1])

        timeSignature = music21.meter.TimeSignature('4/4')
        eventList = StreamTranslator.timeSignatureToMidiEvents(timeSignature)
        midiTrack.events.append(eventList[0])
        midiTrack.events.append(eventList[1])

    @classmethod
    def createMidiTrackFromPygameEvents(cls, pygEvents):

        midiTrack = music21.midi.MidiTrack(index=0)
        cls.addMetaEvents(midiTrack)
        cls.addEventsToMidiTrack(midiTrack, pygEvents)
        return midiTrack

    @classmethod
    def addEventsToMidiTrack(cls, midiTrack, pygEvents):
        absoluteTime = 0
        noteOnList = []
        noteOffList = []
        
        for pygEvent in pygEvents:
            name = pygEvent[0][0]
            note = pygEvent[0][1]
            keyVelocity = pygEvent[0][2]
            deltaTime = pygEvent[1] - absoluteTime
            deltaTicks = cls.deltaTimeToTicks(absoluteTime, deltaTime)
            #assigned here so the first deltaTicks will be shifted to the beginning of the midi track
            absoluteTime = pygEvent[1]

            deltaTime = cls.createM21DeltaTime(deltaTicks, midiTrack)
            m21Event = cls.createM21MidiEvent(keyVelocity, midiTrack, name, note)

            if m21Event.type == music21.midi.ChannelVoiceMessages.NOTE_ON.value:
                noteOnList.append(note)
            elif m21Event.type == music21.midi.ChannelVoiceMessages.NOTE_OFF.value:
                noteOffList.append(note)
            else:
                continue

            midiTrack.events.append(deltaTime)
            midiTrack.events.append(m21Event)

        if len(noteOnList) >= len(noteOffList):
            for note in noteOffList:
                try:
                    noteOnList.remove(note)
                except ValueError:
                    pass
        cls.closeOpenNotesInTrack(midiTrack, noteOnList)

    @classmethod
    def deltaTimeToTicks(cls, absoluteTime, deltaTime):
        deltaTicks = 0
        if absoluteTime != 0:
            deltaTicks = Translator.EventTimeTranslator.msToDt(deltaTime, cls.bpm)
        return deltaTicks

    @classmethod
    def createM21MidiEvent(cls, keyVelocity, midiTrack, name, note):
        m21Event = music21.midi.MidiEvent(midiTrack, type=name, channel=cls.midiChannel)
        m21Event.velocity = keyVelocity
        m21Event.pitch = note
        return m21Event

    @classmethod
    def createM21DeltaTime(cls, deltaTicks, midiTrack):
        deltaTime = music21.midi.DeltaTime(midiTrack, time=deltaTicks)
        deltaTime.channel = cls.midiChannel
        return deltaTime

    @classmethod
    def closeOpenNotesInTrack(cls, midiTrack, openNote):
        for note in openNote:
            deltaTime = cls.createM21DeltaTime(1024, midiTrack)
            m21Event = music21.midi.MidiEvent(midiTrack, type=music21.midi.ChannelVoiceMessages.NOTE_OFF.value,
                                              channel=cls.midiChannel)
            m21Event.pitch = note
            midiTrack.events.append(deltaTime)
            midiTrack.events.append(m21Event)

    @classmethod
    def createStreamFromLiveInput(cls):
        pygEvents = cls.captureAndPlayback()
        m21MidiTrack = cls.createMidiTrackFromPygameEvents(pygEvents)
        m21Stream = StreamTranslator.midiTrackToStream(m21MidiTrack, quantizePost=True, quarterLengthDivisors=(4, 3), isFirst=True)
        #m21Stream.show()
        return m21Stream
    
    
    @classmethod
    def dryPlaybackBeats(cls, beats):
        #for the given amount of beats just output what the player plays
        duration = beats * (60000000 / cls.bpm) / 1000000
        cls.dryPlaybackMs(duration)
        
    @classmethod
    def dryPlaybackMs(cls, ms):
        #for the given time just output what the player plays
        startTime = time.time()
        #events=[]
        firstNoteOnReceived = False

        cls.input.flushBuffer()
        while time.time() <= startTime + ms:
            event = cls.input.getEvent(1)
            #we do not want to start playing a note-off event
            if event is not None and event[0][0][0] == Input.MidiMetadata.MidiEvent.noteOn.value:
                firstNoteOnReceived = True

            if event is not None and firstNoteOnReceived:
                #events.append(event[0])
                cls.playBack(event, cls.midiChannel)
        #maybe will have to close any lingering note-on events will see about that, if it works remove the then useless events list
        
    
        

        

        

#Todo Traceback (most recent call last):
#  File "/home/flowko/FH/BAC1/intellisynth/IntelliSynth.py", line 13, in <module>
#    capturedStream = midiCaptureDevice.createStreamFromLiveInput()
#  File "/home/flowko/FH/BAC1/intellisynth/midi/MidiCapture.py", line 147, in createStreamFromLiveInput
#    m21MidiTrack = cls.createMidiTrackFromPygameEvents(pygEvents)
#  File "/home/flowko/FH/BAC1/intellisynth/midi/MidiCapture.py", line 83, in createMidiTrackFromPygameEvents
#    cls.addEventsToMidiTrack(midiTrack, pygEvents)
#  File "/home/flowko/FH/BAC1/intellisynth/midi/MidiCapture.py", line 105, in addEventsToMidiTrack
#    openNote.remove(note)
#   ValueError: list.remove(x): x not in list