from musicautobot.musicautobot.config import *
from musicautobot.musicautobot.multitask_transformer import *
from musicautobot.musicautobot.music_transformer import *
from musicautobot.musicautobot.utils.setup_musescore import setup_musescore

setup_musescore()


class OpusPrime:

    __config = None
    # Location of our midi files
    __midi_path = Path('musicautobot/data/midi')
    # Location of saved datset
    __data_path = Path('musicautobot/data/numpy')
    # Path ot the pretrained Model
    __pretrained_path = None
    # The Datas Vocab
    __vocab = None
    # The Learner
    __learnSimple = None
    # The Learner for the multitaskModel
    __learnMulti = None

    @classmethod
    def initMultitaskMusicautobot(cls):
        # Config
        cls.__config = multitask_config()

        # Data
        data = MusicDataBunch.empty(cls.__data_path)
        cls.__vocab = data.vocab

        # Pretrained Model
        cls.__pretrained_path = cls.__data_path/'pretrained'/'MultitaskLarge.pth'

        # Learner
        cls.__learnMulti = multitask_model_learner(
            data, pretrained_path=cls.__pretrained_path)
        # learn.to_fp16();

    @classmethod
    def initSimpleMusicautobot(cls):

        # Data
        data = MusicDataBunch.empty(cls.__data_path)
        cls.__vocab = data.vocab
        # For Saved Data:
        # data = load_data(data_path, 'musicitem_data_save.pkl')

        # Pretrained Model
        cls.__pretrained_path = cls.__data_path/'pretrained'/'MusicTransformer.pth'

        # Learner
        cls.__learnSimple = music_model_learner(
            data, pretrained_path=cls.__pretrained_path)

    @classmethod
    def simple_Predict_from_stream(cls, stream, cutoff_beat=None, n_words=400, temperatures=(1.1, 0.4), min_bars=12, top_k=24, top_p=0.7):
        # prediciton with the simple model-->just the transformer, returns prediction

        # if init has not been run yet-->run it
        if cls.__learnSimple is None:
            cls.initSimpleMusicautobot()

        # make MusicItem from stream
        item = MusicItem.from_stream(stream, cls.__vocab)

        if cutoff_beat is not None:
            # take the first cutoff_beat beats
            seed_item = item.trim_to_beat(cutoff_beat)
        else:
            seed_item = item

        # use the seed to make a prediction
        #temperatures is (note_temp, duration_temp)
        # >note_temp-->determines variation in note pitch
        # >duration_temp-->amount of randomness in rythm
        # n_words = how many words to predict
        # top_k/p-->filters out lower probability tokens. makes sure no outliers with really small probability are taken
        pred, full = cls.__learnSimple.predict(
            seed_item, n_words=n_words, temperatures=temperatures, min_bars=min_bars, top_k=top_k, top_p=top_p)

        # append pred to seed to get full_song
        #full_song = seed_item.append(pred)
        # return full_song

        # just return the prediction
        return pred

    @classmethod
    def nw_predict_from_stream(cls, stream, cutoff_beat=None, n_words=400, temperatures=(1.1, 0.4), top_k=24, top_p=0.7):
        # predict nextWord with the MultitaskModel, returns prediction
        # similiar to musicautobots nw_predict_from_midi, however we predict from a music21 stream

        # if init has not been run yet-->run it
        if cls.__learnMulti is None:
            cls.initMultitaskMusicautobot()

        # make MusicItem from stream
        item = MusicItem.from_stream(stream, cls.__vocab)

        seed_item = item
        # if a cutoff is set: trim the item
        if cutoff_beat is not None:
            seed_item = item.trim_to_beat(cutoff_beat)

        pred, full = cls.__learnMulti.predict_nw(
            seed_item, n_words=n_words, temperatures=temperatures, top_k=top_k, top_p=top_p)
        return pred
    
    @classmethod
    def nw_predict_from_stream_process(cls, stream, pipe:Pipe, n_words=400, cutoff_beat=None, temperatures=(1.1, 0.4), top_k=24, top_p=0.7):
        # predict nextWord with the MultitaskModel, writes the prediction into the given pipe (format is in the vocab, needs to be translated into acutal MusicItem or m21)
        # similiar to musicautobots nw_predict_from_midi, however we predict from a music21 stream
        # ment to be rund as a process

        p_output, p_input = pipe

        # if init has not been run yet-->run it
        if cls.__learnMulti is None:
            cls.initMultitaskMusicautobot()

        # make MusicItem from stream
        item = MusicItem.from_stream(stream, cls.__vocab)

        seed_item = item
        # if a cutoff is set: trim the item
        if cutoff_beat is not None:
            seed_item = item.trim_to_beat(cutoff_beat)
        
        pred, full = cls.__learnMulti.predict_nw_into_pipe(pipe,
            seed_item, n_words=n_words, temperatures=temperatures, top_k=top_k, top_p=top_p)
        
        #once we are done push 'DONE' into the pipe
        p_input.send('DONE')

    @classmethod
    def s2s_predict_from_multitrackstream(cls, multitrackStream, cutoff_beat=None, n_words=400,
                                        temperatures=(1.1, 0.4), top_k=24, top_p=0.7, pred_melody=True):
        # uses seq2seq to either predict a melody from chords, or chords from a melody
        # similiar to musicautobots s2s_predict_from_midi just with a music21 stream

        # if init has not been run yet-->run it
        if cls.__learnMulti is None:
            cls.initMultitaskMusicautobot()

        # make MultitrackItem from stream
        multitrack_item = MultitrackItem.from_stream(
            multitrackStream, cls.__vocab)

        # for this to work we need a multitrack_item-->treble=melody, bass=chords
        melody, chords = multitrack_item.melody, multitrack_item.chords
        # depending on what we predict(melody/chords) the input/target changes
        inp, targ = (chords, melody) if pred_melody else (melody, chords)

        # if a cutoff is set: trim the item
        if cutoff_beat is not None:
            targ = targ.trim_to_beat(cutoff_beat)
        targ = targ.remove_eos()
        # remove the end of sequence of the target so we can add something to it

        pred = cls.__learnMulti.predict_s2s(
            inp, targ, n_words=n_words, temperatures=temperatures, top_k=top_k, top_p=top_p)

        # create a MultitrackItem from input and prediction again
        # also make sure its in the right order-->1. melody, 2. chords(harmony)
        part_order = (pred, inp) if pred_melody else (inp, pred)
        return MultitrackItem(*part_order)

    @classmethod
    def mask_predict_from_stream(cls, stream, temperatures=(1.1, 0.4), top_k=24, top_p=0.7, pred_notes=True, section=None):
        # masks/remixes the given MusicItem in a given section=(mask_start, mask_end)
        # either masks the notes (changes pitch) or the durations (changes rhythm)
        # similiar to musicautobots mask_predict_from_midi just with a music21 stream instead

        # if init has not been run yet-->run it
        if cls.__learnMulti is None:
            cls.initMultitaskMusicautobot()

        # make MusicItem from stream
        item = MusicItem.from_stream(stream, cls.__vocab)
        
        # depending on pred_notes mask notes or durations
        masked_item = item.mask_pitch(
            section) if pred_notes else item.mask_duration(section)

        pred = cls.__learnMulti.predict_mask(
            masked_item, temperatures=temperatures, top_k=top_k, top_p=top_p)
        return pred

    @classmethod
    def multitaskPredict(cls, stream, cutoff_beat=10, n_words=400, temperatures=(1.1, 0.4), min_bars=12, top_k=24, top_p=0.7, mask_notes=True):
        # The multitaskModel includes three parts:
        # > NextWord/Autocomplete: predict the next word via Transformer-->similiar to the simplePredict
        # > Mask/Remix: mask some parts of the song and remix other portions
        #   -Note masking
        #   -Duration masking
        # > Seq2Seq/translation: Generate a Melody from chords or vice versa
        #   -New Melody generated from chords
        #   -Harmonization: generate chords for a melody

        # 1. NextWord/Autocomplete
        pred = cls.nw_predict_from_stream(stream=stream, cutoff_beat=cutoff_beat,
                                             n_words=n_words, temperatures=temperatures, top_k=top_k, top_p=top_p)

        # 2. Seq2Seq/translation
        # cannot do this easily since we dont have a MultiTrackItem-->therefore we cant easily differentiate between chords and melody
        #just hardcode predict a harmony(chords) for it
        pred = cls.s2s_predict_from_multitrackstream(multitrackStream=pred, cutoff_beat=cutoff_beat,
                                                   n_words=n_words, temperatures=temperatures, top_k=top_k, top_p=top_p, pred_melody=False)

        # 3. Mask/Remix
        # just using the same parameters as with the prediction (top_k, top_p, etc.)-->also masking everything-->section=None equals to everything
        pred = cls.mask_predict_from_stream(stream=pred, temperatures=temperatures,
                                               top_k=top_k, top_p=top_p, pred_notes=mask_notes, section=None)

        return pred

