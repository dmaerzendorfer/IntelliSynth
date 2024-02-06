import pygame.midi
import midi.midio.MidiMetadata as MidiMetadata



#Type 1 == Input Type 0 == Output
def findDevice(deviceType):
    for deviceId in range(pygame.midi.get_count()):
        deviceInfo = pygame.midi.get_device_info(deviceId)
        if deviceInfo[2] == deviceType:
            if deviceType == 1 and deviceInfo[1] in MidiMetadata.acceptedInputDeviceList:
                return deviceId
            elif deviceType == 0 and deviceInfo[1] in MidiMetadata.acceptedOutputDeviceList:
                return deviceId
    return -1
