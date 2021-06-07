# coding: utf-8

import sys
from time import sleep
from timeout_decorator import timeout
from threading import Thread, Lock

import pymkeapi

mutex = Lock()

class SensorDevice:
    def __init__(self):
        self.port = 'localhost'
        self.addr = 8888
        self.client = None
        self.clientDepth = None

    @timeout(10)  # https://qiita.com/toshitanian/items/133b42355b7867f5c458
    def open(self, addr='localhost', port=8888):
        mutex.acquire()

        self.addr = addr
        self.port = port
        if self.client:
            self.close()
            sleep(0.1)

        try:
            bus = pymkeapi.TcpBus(addr, port)
            self.client = pymkeapi.ReservedSyncClient(bus)
            self.clientDepth = pymkeapi.SyncClient(bus)
            if self.client.get_state() != pymkeapi.STATE_IDLE:
                self.client.set_state(pymkeapi.STATE_IDLE)
                sleep(0.1)
            self.client.set_state(pymkeapi.STATE_SERVICE)
            sleep(0.5)
        finally:
            mutex.release()

    def close(self):
        mutex.acquire()

        try:
            if self.client:
                self.client.set_state(pymkeapi.STATE_IDLE)
                self.client = None
        finally:
            mutex.release()

    def get_shutter(self):
        mutex.acquire()

        shutter = 0
        try:
            if self.client:
                shutter = self.client.get_shutter()
            return shutter
        finally:
            mutex.release()

    def set_shutter(self, shutter):
        mutex.acquire()

        try:
            if self.client:
                self.client.set_shutter(shutter)
        finally:
            mutex.release()

    def get_gainiso(self):
        mutex.acquire()

        gainiso = 0
        try:
            if self.client:
                gainiso = self.client.get_gain()
            return gainiso
        finally:
            mutex.release()

    # returns pymkeapi.reserved_api.GainSetup include analog, digital
    def set_gainiso(self, gainiso):
        mutex.acquire()

        try:
            if self.client:
                self.client.set_gain(gainiso)
        finally:
            mutex.release()

    # returns pymkeapi.reserved_api.LaserSetup include pattern, duration, offset
    def get_lasers(self):
        mutex.acquire()
        lasers = 0

        try:
            if self.client:
                lasers = self.client.get_laser()
            return lasers
        finally:
            mutex.release()

    def set_lasers(self, pattern):
        mutex.acquire()
        try:
            if self.client:
                self.client.set_laser(pattern)
        finally:
            mutex.release()

    def get_image(self, avgcount):
        mutex.acquire()
        # print('get_image Locked')

        image = None

        try:
            if self.client:
                image = self.client.get_image(avgcount, image_format="PNG")
            return image
        finally:
            # print('get_image released')
            mutex.release()

    def get_frame(self):
        mutex.acquire()

        frame = None
        try:
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
        finally:
            mutex.release()
