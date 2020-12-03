# coding: utf-8

import sys
from time import sleep
import pymkeapi

class SensorDevice:
    def __init__(self):
        self.port = 'localhost'
        self.addr = 8888
        self.client = None
        self.clientDepth = None

    def open(self, addr='localhost', port=8888):
        self.addr = addr
        self.port = port
        if self.client:
            self.close()
            sleep(0.1)
        bus = pymkeapi.TcpBus(addr, port)
        self.client = pymkeapi.ReservedSyncClient(bus)
        self.clientDepth = pymkeapi.SyncClient(bus)
        if self.client.get_state() != pymkeapi.STATE_IDLE:
            self.client.set_state(pymkeapi.STATE_IDLE)
            sleep(0.1)
        self.client.set_state(pymkeapi.STATE_SERVICE)
        sleep(0.5)

    def close(self):
        if self.client:
            self.client.set_state(pymkeapi.STATE_IDLE)
            self.client = None

    def get_shutter(self):
        shutter = 0
        if self.client:
            shutter = self.client.get_shutter()
        return shutter

    def set_shutter(self, shutter):
        if self.client:
            self.client.set_shutter(shutter)

    def get_gainiso(self):
        gainiso = 0
        if self.client:
            gainiso = self.client.get_gain()
        return gainiso

    # returns pymkeapi.reserved_api.GainSetup include analog, digital
    def set_gainiso(self, gainiso):
        if self.client:
            self.client.set_gain(gainiso)

    # returns pymkeapi.reserved_api.LaserSetup include pattern, duration, offset
    def get_lasers(self):
        lasers = 0
        if self.client:
            lasers = self.client.get_laser()
        return lasers

    def set_lasers(self, pattern):
        if self.client:
            self.client.set_laser(pattern)

    def get_image(self, avgcount):
        image = None
        if self.client:
            image = self.client.get_image(avgcount, image_format="PNG")
        return image

    def get_frame(self):
        frame = None
        if self.clientDepth:
            if self.client.get_state() != pymkeapi.STATE_IDLE:
                self.client.set_state(pymkeapi.STATE_IDLE)
                sleep(0.5)
            self.clientDepth.set_state(pymkeapi.STATE_DEPTH_SENSOR)
            sleep(0.5)

            frame = self.clientDepth.get_frame(pymkeapi.FRAME_TYPE_2)

            self.clientDepth.set_state(pymkeapi.STATE_IDLE)
            sleep(0.5)
            self.client.set_state(pymkeapi.STATE_SERVICE)
            sleep(0.5)
            print(frame.lut3d, frame.uid)

        return frame

