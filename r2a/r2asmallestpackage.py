import json
from r2a.ir2a import IR2A
from math import ceil
from player.parser import parse_mpd

class R2ASmallestPackage(IR2A):
    def __init__(self, id):
        IR2A.__init__(self, id)
        self.videoRates = []
        self.worstWait = 0
        self.buffer = 0

    def handle_xml_request(self, msg):
        self.send_down(msg)

    def handle_xml_response(self, msg):
        mpd = parse_mpd(msg.get_payload())
        self.videoRates = mpd.get_qi()
        self.worstWait =  ceil(self.videoRates[-1]/self.videoRates[0])
        self.adjust_buffer()
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        minimumSize = self.videoRates[0] * self.buffer
        chosenQ = self.videoRates[0]
        for rate in self.videoRates:
            if rate > minimumSize:
                break
            chosenQ = rate
        msg.add_quality_id(chosenQ)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        self.buffer = self.whiteboard.get_amount_video_to_play()
        self.send_up(msg)
    
    def adjust_buffer(self):
        with open("dash_client.json","r+") as configFile:
            initConfig = json.load(configFile)
            initConfig["max_buffer_size"] = self.worstWait + 5
            configFile.seek(0)
            json.dump(initConfig,configFile,indent=4)
            configFile.truncate()

    def initialize(self):
        pass

    def finalization(self):
        pass