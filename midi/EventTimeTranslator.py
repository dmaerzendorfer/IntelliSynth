class EventTimeTranslator:
    @staticmethod
    def msToDt(milliseconds, bpm):
        return milliseconds / ((60000000 / bpm / 1024) / 1000)

    @staticmethod
    def dtToMs(deltaTicks, bpm):
        return deltaTicks * ((60000000 / bpm / 1024) / 1000)
