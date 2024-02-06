import enum
import time
import testMultitask

import pygame.midi
from midiutil.MidiFile import MIDIFile


def print_devices():
    for n in range(pygame.midi.get_count()):
        print(n, pygame.midi.get_device_info(n))


def number_to_note(number):
    notes = ['C', 'C#', 'D', 'D#', 'E', ' F', 'F#', 'G', 'G#', 'A', 'A#', 'H']
    return notes[number % 12]


def output_midi(output_device, events):
    output_device.write(events)


def read_input(input_device, output_device, secs):
    events = []
    startTime = time.time()
    print("I am Listening")
    while time.time() <= startTime + secs:
        if input_device.poll():
            event = input_device.read(1)
            output_midi(output_device, event)
            events.append(event[0])
            print(event[0])
    return events


"""

60 bpm

1 beat = 1000 us
|-------|-------|-------|
0       1000    2000    3000
    x
note on 500 us
            x
note off 1500 us

time = timestampNoteOn / beatInUs
duration = timestampNoteOff - timestampNoteOn / beatInUs

time = 0,5 duration = 1
mf.addNote(track, channel, pitch, time, duration, volume)

Calculating Delta Times: 
Now here’s an example of how cumulative delta time gets converted into milliseconds.
In the simplest case, there are 2 pieces of information needed: 1) 
The SMF Header Chunk defines a "division" which is delta ticks per quarter note.  (eg., 96 = 96 ppq)
(Ref: pg. 4, SMF 1.0) 2)  The Tempo setting, which is a non-MIDI data Meta Event typically found at time delta time 0 in the first track of an SMF.
If it isn't specified, tempo is assumed to be 120 bpm.  Tempo  is  expressed  as  microseconds  per  quarter  note.
(eg.,  500000  =  120  bpm).    (Ref:  pgs. 5,9, SMF 1.0) To  convert  delta-time  ticks  into  milliseconds,
you  simply  do  a  straightforward  algebraic  calculation:
    Time (in ms.) = (Number of Ticks) * (Tempo (uS/qn) / Div (ticks/qn)) / 1000
 As an example, if the Set Tempo value were 500000 uS per qn, and the Division were 96 ticks per qn,
then the amount of time at 6144 Ticks into the SMF would be:
    Time = 6144 * (500000/96) / 1000 = 32000 milliseconds
The  above  example  is  a  very  simple  case.
In  practice,  SMFs  can  contain  multiple  Set  Tempo  Meta Events spaced throughout the file, and in order to calculate a correct elapsed time for any Tick,
a running calculation needs to be performed. Note  that  while  the  Time  Signature  is  not  needed  to  perform  the  above  calculation,  Time  Signature is needed,
however, if the elapsed time is desired for a particular Bar/Beat value.  As with Set Tempo  changes, the Time Signature can change throughout an SMF, and a running calculation
is usually necessary to determine a correct elapsed time for any Bar/Beat. 
"""


def quantize_midi_ticks(ticks, quarter_note_divider):
    step_size_2 = int(
        960 / quarter_note_divider)
    # step_size_3 = int(960 / 6)
    error_2 = ticks % step_size_2
    # error_3 = ticks % step_size_3
    return ticks - error_2
    # if error_2 < error_3:
    # if error_2 > step_size_2 / 2:
    # return ticks + (step_size_2 - error_2)
    # else:
    #    return ticks - error_2
    # else:
    #    if error_3 > step_size_3 / 2:
    #        return ticks + (step_size_3 - error_3)
    #    else:
    #        return ticks - error_3


class MIDI_events(enum.Enum):
    note_off = 0x80  # chan 1 note off
    note_on = 0x90  # chan 1 note on
    channel_change = 0xB0  # chan 1 control change


def create_midi(events, bpm):
    # interleaved off maybe?
    # adjust_origin maybe?
    # mess with ticks_per_quarter_note maybe?

    # do it with the music21 midi.realtime / midi.translate modules instead compare runtimes of both

    # create your MIDI object
    # mf = MIDIFile(1)  # only 1 track quarter note as unit
    mf = MIDIFile(1, eventtime_is_ticks=True)
    track = 0  # the only track
    channel = 0  # only channel 0
    time = 0  # start track at beginning

    # tick_to_quarter maybe
    ticks_per_quarter_note = 8  # smallest division of a quarter note
    # Time (in ms.) = (Number of Ticks) * (Tempo (uS/qn) / Div (ticks/qn)) / 1000
    ticks_per_ms = 1 / ((60000000 / bpm / 960) / 1000)
    # ms_per_quarter_note = (60000000 / bpm) / ticks_per_quarter_note / 1000  #60 000 000 us in a minute, 1 000 us in a millisecond

    mf.addTrackName(track, time, "Sample Track")
    mf.addTimeSignature(track, time, 4, 2, 24, ticks_per_quarter_note)
    mf.addTempo(track, time, bpm)

    eventStartTick = 0
    playingNotes = []

    """HOW TICKS WORK
        a quarter note consists of 960 ticks no matter the bpm of the song
        so a eight note would mean 480 ticks and so on...
    """

    for event in events:
        # get all note and timing info
        name = event[0][0]
        note = event[0][1]
        velocity = event[0][2]
        current_tick = int(event[1] * ticks_per_ms)

        # if current_tick == 0:
        #    current_tick += 1

        # move all events back to the beginning
        if eventStartTick == 0:
            eventStartTick = current_tick

        # offset the event
        current_tick = quantize_midi_ticks(current_tick - eventStartTick, ticks_per_quarter_note)

        if name == MIDI_events.note_on.value:
            playingNotes.append((note, velocity, current_tick))

        elif name == MIDI_events.note_off.value:
            for key in reversed(playingNotes):
                if key[0] == note:

                    start_tick = key[2]

                    duration = current_tick - start_tick
                    if duration == 0:
                        print('is vorkommen duration = %i' % (duration))
                        duration = int(960 / ticks_per_quarter_note)

                    print(start_tick, duration)
                    mf.addNote(track, channel, note, start_tick, duration, key[1])

                    playingNotes.remove(key)
                    break

    for openEvent in playingNotes:
        ticks_left = 960 - int(openEvent[2] % 960)
        mf.addNote(track, channel, openEvent[0], openEvent[2], ticks_left, openEvent[1])

    # write it to disk
    with open("output.mid", 'wb') as outf:
        mf.writeFile(outf)


if __name__ == '__main__':
    bpm = 100
    measures = 4
    # time = (60/bpm) * measures

    pygame.midi.init()
    print_devices()
    my_input = pygame.midi.Input(5)  # get default in
    my_output = pygame.midi.Output(2)  # get defult out
    while True:
        events = read_input(my_input, my_output, 12) #länge anhand von bpm
        create_midi(events, bpm)
        testMultitask.runMusicAutoBot(bpm, my_output)
    """events = \
        [[[144, 61, 37, 0], 867],
         [[144, 64, 32, 0], 1011],
         [[144, 69, 31, 0], 1196],
         [[144, 73, 29, 0], 1258],
         [[128, 64, 63, 0], 1327],
         [[128, 69, 106, 0], 1343],
         [[128, 61, 100, 0], 1407],
         [[128, 73, 107, 0], 1457]]"""
    # events = [[[128, 52, 105, 0], 0], [[128, 57, 101, 0], 0], [[144, 61, 32, 0], 0], [[144, 64, 28, 0], 28], [[144, 69, 26, 0], 185], [[128, 64, 94, 0], 251], [[144, 73, 19, 0], 263], [[128, 69, 104, 0], 263], [[128, 61, 107, 0], 301], [[144, 76, 31, 0], 364], [[128, 73, 100, 0], 398], [[144, 78, 43, 0], 502], [[128, 76, 101, 0], 504], [[128, 78, 86, 0], 585], [[144, 80, 38, 0], 623], [[144, 75, 53, 0], 727], [[128, 80, 90, 0], 758], [[128, 75, 110, 0], 848], [[144, 71, 33, 0], 863], [[144, 68, 35, 0], 954], [[128, 71, 106, 0], 963], [[144, 63, 46, 0], 1058], [[128, 68, 112, 0], 1082], [[144, 59, 31, 0], 1186], [[128, 63, 83, 0], 1271], [[144, 57, 53, 0], 1318], [[128, 59, 99, 0], 1324], [[144, 61, 47, 0], 1439], [[144, 66, 39, 0], 1548], [[128, 66, 98, 0], 1624], [[128, 61, 108, 0], 1625], [[144, 69, 22, 0], 1631], [[128, 57, 103, 0], 1699], [[144, 73, 39, 0], 1742], [[128, 69, 94, 0], 1774], [[144, 75, 42, 0], 1875], [[128, 73, 101, 0], 1897], [[128, 75, 75, 0], 1974], [[144, 76, 27, 0], 2006], [[144, 71, 58, 0], 2085], [[128, 76, 89, 0], 2168], [[144, 68, 46, 0], 2249], [[128, 71, 109, 0], 2263], [[144, 64, 45, 0], 2310], [[128, 68, 86, 0], 2334], [[128, 64, 105, 0], 2476], [[144, 59, 33, 0], 2490], [[144, 56, 52, 0], 2534], [[128, 59, 99, 0], 2556], [[128, 56, 104, 0], 2658], [[144, 54, 54, 0], 2701], [[144, 57, 32, 0], 2887], [[144, 61, 55, 0], 2972], [[128, 57, 101, 0], 3044], [[144, 73, 41, 0], 3079], [[128, 61, 97, 0], 3115], [[128, 54, 107, 0], 3120], [[144, 66, 42, 0], 3165], [[128, 73, 92, 0], 3223], [[144, 69, 44, 0], 3279], [[128, 66, 110, 0], 3326], [[144, 78, 64, 0], 3435], [[128, 69, 90, 0], 3465], [[144, 52, 48, 0], 3491], [[128, 78, 106, 0], 3592], [[144, 57, 52, 0], 3594], [[128, 52, 40, 0], 3699], [[144, 61, 42, 0], 3727], [[128, 57, 101, 0], 3805], [[128, 61, 79, 0], 3816], [[144, 73, 48, 0], 3830], [[144, 66, 47, 0], 3945], [[128, 73, 90, 0], 3987]]
    #create_midi(events, bpm)
