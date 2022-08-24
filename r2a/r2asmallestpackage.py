from r2a.ir2a import IR2A
from collections import deque
from math import ceil
from time import perf_counter
from player.parser import parse_mpd

class R2ASmallestPackage(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.videoRates = []
        self.requestTime = 0
        self.worstWait = 0
        self.pastThroughputs = deque(maxlen=10)
        self.playing = False
        self.buffer = 0

    def handle_xml_request(self, msg):
        self.requestTime = perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        t = perf_counter() - self.requestTime
        self.pastThroughputs.append(msg.get_bit_length() / t)

        mpd = parse_mpd(msg.get_payload())
        self.videoRates = mpd.get_qi()
        self.worstWait =  ceil(self.videoRates[-1]/self.videoRates[0])
        self.whiteboard.add_max_buffer_size = self.worstWait
        
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        if self.buffer:
            minimumSize = self.videoRates[0] * self.buffer
        else:
            minimumSize = self.videoRates[0]

        if self.buffer < self.worstWait:
            for rate in self.videoRates:
                if rate > minimumSize:
                    break
                chosenQ = rate
        else:
            chosenQ = self.videoRates[-1]
        
        msg.add_quality_id(chosenQ)
        self.requestTime = perf_counter()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = perf_counter() - self.requestTime
        self.pastThroughputs.append(msg.get_bit_length() / t)
        
        self.buffer = self.whiteboard.get_amount_video_to_play()
        
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
