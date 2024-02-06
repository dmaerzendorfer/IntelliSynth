from multiprocessing import Process, Event, Pipe
import multiprocessing
from interface.opusprime import OpusPrime
from midi.MidiPlayback import MidiPlayback as MidiPlayback
from midi.MidiCapture import MidiCapture as MidiCapture
import midi.MidiMetronome as MidiMetronome


def doMetronome(metronome: MidiMetronome, tickEvent: Event):
    metronome.tickInfinite(tickEvent)


if __name__ == '__main__':
    #sets how new processes are generated (spawn/fork/forkserver)
    multiprocessing.set_start_method('fork')

    metronome = None
    metronomeProcess = None
    metronomeChannel = 6
    tickEvent = Event()
    
    bpm = 120
    beats = 16
    playbackChannel = 2
    
    #pipes are unidirectional with two endpoints
    p_output, p_input = Pipe()
    dryBeats = 16
    
    #for the prediction
    n_words = 150
    cutoff_beat = None
    temperatures=(1.1, 0.4)
    top_k=24
    top_p=0.7
    
    
    midiCaptureDevice = MidiCapture(bpm=bpm, beats=beats, playbackChannel=playbackChannel)
    playBackDevice = MidiPlayback.instance(bpm=80)
    musicPredictor = OpusPrime()
    musicPredictor.initMultitaskMusicautobot()
    
    #start the metronome in a process and just let it run the whole time, everytime it ticks it sends an event
    metronome = MidiMetronome.MidiMetronome(playBackDevice, bpm, channel=6)
    metronomeProcess = Process(target=doMetronome, args=[metronome, tickEvent])
    metronomeProcess.daemon = True
    print("starting the metronome")
    metronomeProcess.start()
    
    while True:
            #start to listen
            capturedStream = midiCaptureDevice.createStreamFromLiveInput()
            #capturedStream.show()
            
            #create a predictionProcess which puts its prediction into the pipe
            predictionProcess = Process(target=musicPredictor.nw_predict_from_stream_process, args=(capturedStream, (p_output, p_input), n_words, cutoff_beat, temperatures, top_k, top_p))
            
            #set the process as a daemon, so its stoppen when the main ends
            #also prevents it from creating processes itself
            predictionProcess.daemon = True
            print("\tstart the prediction process")
            predictionProcess.start()
    
            #the main process listens for another while and then starts playing the prediction
            print(f"listen for {dryBeats} Beats")
            midiCaptureDevice.dryPlaybackBeats(dryBeats)
            
            #before starting to play the prediciton
            #we wait for a metronome tick to stay somewhat synchronized
            tickEvent.wait()
            print("start playing the prediction")
            while True:
               
                #recv() blocks until there is smth to read
                music_item = p_output.recv()

                if music_item == 'DONE':
                    break
                else:
                    #play the prediction
                    playBackDevice.playEvents(music_item.stream, playbackChannel)
                    
            #once the prediction and its playing is done we restart the cycle 
            #here the process is terminated and a new one is created for in next iteration
            predictionProcess.terminate()