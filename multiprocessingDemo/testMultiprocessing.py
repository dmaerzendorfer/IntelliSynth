from multiprocessing import Process, Pipe, Event

from array import array
import multiprocessing
import time
import random
import sys

#for the metronome sound
import winsound


def predict(stream, pipe):
    p_output, p_input = pipe
    #start the prediction
    for note in stream:
        #push new notes into the pipe
        print(f"\tPredicted note: {note * 2}")
        sys.stdout.flush()
        p_input.send(note * 2)
        time.sleep(1)
    
    #once finished push 'DONE' into the pipe
    print(f"\tPrediction is complete: sending DONE")
    sys.stdout.flush()
    p_input.send('DONE')
    time.sleep(1)
    
def listen(seconds) -> array:
    capture=[]
    random.seed(time.time())
    
    for i in range(seconds):
        print(f"listening: {i}")
        capture.append(random.randint(0,100))
        time.sleep(1)
        
    return capture


def infiniteMetronome(bpm: int, tickEvent: Event):
    frequency = 440  # Set Frequency To 440 Hertz
    
    beatDuration = 60 / bpm

    beep_duration = 200  # Set Duration To 200 ms 
    
    
    while True:
        #let others know I am about to beep (like a sheep)
        tickEvent.set()
        tickEvent.clear()
        
        winsound.Beep(frequency, beep_duration)
        #alternatively use the ASCII-Bell, also works on linux
        #print("\a")
        time.sleep(beatDuration - beep_duration/1000)
        

if __name__ == '__main__':
    #sets how new processes are generated (spawn/fork/forkserver)
    multiprocessing.set_start_method('spawn')

    #pipes are unidirectional with two endpoints
    p_output, p_input = Pipe()

    listen_time = 10
    buffer_time = 5
    metronome_bpm = 80
    
    #start the metronome in a thread and just let it run the whole time, everytime it ticks it sends an event
    tickEvent = Event()
    metronomeProcess = Process(target=infiniteMetronome, args=(metronome_bpm, tickEvent))
    print(f"\tstarting the metronome with {metronome_bpm}bpm")
    metronomeProcess.daemon = True
    metronomeProcess.start()


    while True:
        #start to listen
        print(f"start to listen for {listen_time} seconds")
        capturedStream = listen(listen_time)
        #create a predictionProcess which puts its prediction into the pipe
        predictionProcess = Process(target=predict, args=(capturedStream, (p_output, p_input)))
        
        #set the process as a daemon, so its stoppen when the main ends
        #also prevents it from creating processes itself
        predictionProcess.daemon = True
        print("\tstart the prediction process")
        predictionProcess.start()

        #the main process listens for another 10seconds and then starts playing the prediction
        print(f"listen for {buffer_time} more seconds")
        listen(buffer_time)
        #start the prediction on a metronome tick to assure at least some synchrony
        tickEvent.wait()
        print("start playing the prediction")
        while True:
            #recv() blocks until there is smth to read
            note = p_output.recv()
            if note == 'DONE':
                break
            else:
                print(f"Main-Process read: {note}")
                #pretend to play the note by sleeping 1 second
                time.sleep(1)
        
        #once the prediction and its playing is done we restart the cycle 
        #here the process is terminated and a new one is created for the next iteration
        #could be changed to just have one process
        #would need a second pipe for sending the capturedStream tho (or smth similiar)
        #better use join since the pipe could be damaged by terminate! 
        predictionProcess.join()