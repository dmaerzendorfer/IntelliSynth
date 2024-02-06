import time

import music21.midi.translate

from musicautobot.musicautobot.numpy_encode import *
from musicautobot.musicautobot.utils.file_processing import process_all, process_file
from musicautobot.musicautobot.config import *
from musicautobot.musicautobot.music_transformer import *
from musicautobot.musicautobot.multitask_transformer import *
from musicautobot.musicautobot.numpy_encode import stream2npenc_parts
from musicautobot.musicautobot.utils.setup_musescore import setup_musescore
setup_musescore()

from midi2audio import FluidSynth
from IPython.display import Audio
from IPython.core.display import display
import pygame.midi

# Colab cannot play music directly from music21 - must convert to .wav first
def output_midi(stream, bpm, output_device):

    tick_in_ms = (60000000 / bpm / 1024) / 1000

    #stream.show()

    flat_stream = stream.flatten()
    packets = music21.midi.translate.streamToPackets(flat_stream)
    midi_track = music21.midi.MidiTrack()
    delta_seperated_events = music21.midi.translate.packetsToDeltaSeparatedEvents(packets, midi_track)
    #maybe midi.realtime.stringio.play()
    absolute_time = 0
    delta_timestamp = 0
    for event in delta_seperated_events:

        if event.isDeltaTime():
            delta_timestamp = int(event.time * tick_in_ms)
            absolute_time += delta_timestamp #konn ma sie sparen
        elif event.type == music21.midi.ChannelVoiceMessages.NOTE_ON.value or event.type == music21.midi.ChannelVoiceMessages.NOTE_OFF.value:
            print(absolute_time)
            time.sleep(delta_timestamp/1000)
            output_device.write([[[event.type, event.pitch, event.velocity, 0], absolute_time]]) #absolut time konn ma sich sparen



def runMusicAutoBot(bpm, output_device):
    # Config
    config = multitask_config()

    # Location of your midi files
    midi_path = Path('output.mid')

    # Location of saved datset
    data_path = Path('musicautobot/data/numpy')
    data_save_name = 'musicitem_data_save.pkl'

    # Data
    data = MusicDataBunch.empty(data_path)
    vocab = data.vocab

    # Pretrained Model
    pretrained_path = data_path/'pretrained'/'MultitaskLarge.pth'

    # Learner
    learn = multitask_model_learner(data, pretrained_path=pretrained_path)
    # learn.to_fp16();

    # Encode file
    item = MusicItem.from_file(midi_path, data.vocab) #if directly read into music21 no read is needed

    x = item.to_tensor()
    x_pos = item.get_pos_tensor()

    seed_len = 16 # 4 beats = 1 bar
    seed = item.trim_to_beat(seed_len)

    pred_nw, full = learn.predict_nw(seed, n_words=200)

    full_song = seed.append(pred_nw)

    #full_song.show()
    output_midi(full_song.stream, bpm, output_device)
