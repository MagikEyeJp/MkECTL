#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Reserved SyncClient

   synchronous client for communication with sensor in reserved mode

   Warning: This client must be used only within one thread!
"""

__author__ = "Ondra Fisar"
__copyright__ = "Copyright (c) 2017-2020, Magik-Eye Inc."

import json
import struct
from . import api
from . import reserved_api as resapi
from .sync_client import SyncClient


# ------------------------------------------------------------------------------

class ReservedSyncClient(SyncClient):
    """Reserved client for MagikEye sensors."""

    def __init__(self, bus):
        """Connect to the sensor.

        Arguments:
        See client.SyncClient
        """

        super().__init__(bus)
        self._default_frame_type = resapi.ReservedFrame

    # -------------------------------------------------------------------------

    def get_debug_images(self, num_images, frame_type, image_format="DEFAULT"):
        """Capture sequence of debug images (with detections too)

        Arguments:
        num_images: number of images in sequence
        frame_type: type of frame (See MkEAPI)    
        """

        imfmt = ReservedSyncClient.__get_imfmt(image_format)
        params = struct.pack('<IHB', num_images, frame_type, imfmt) + bytes(1)
        reply = self._send_and_check(api.Request(resapi.CMD_GET_DEBUG_IMAGES,
                                                 params=params),
                                     [api.STATUS_OK])

        ret_num, ret_imfmt = struct.unpack('<IB', reply.params[0:5])
        assert (ret_num == num_images)
        ret_image_format = resapi.REVMAP_IMAGE_FORMAT.get(ret_imfmt, "UNKNOWN")

        offset = 0
        out = []
        for i in range(ret_num):
            dbgim = resapi.DebugImage()
            (dbgim.frame.timer,
             dbgim.frame.seqn,
             ibytes,
             fbytes,
             dbgim.frame.frame_type,
             frame_num_data,
             dbgim.pattern,
             dbgim.frame.data_type) = struct.unpack('<QIIIHHHH', reply.payload[offset:(offset + 28)])

            offset += 32
            idata = reply.payload[offset:(offset + ibytes)]
            offset += ibytes
            fdata = reply.payload[offset:(offset + fbytes)]
            offset += fbytes

            dbgim.image = resapi.Image(timer=dbgim.frame.timer, image_id=None,
                                       data=idata, format=ret_image_format)
            dbgim.frame.parse_payload_only(frame_num_data, fdata)
            out.append(dbgim)

        return out

    # -------------------------------------------------------------------------

    def set_laser(self, pattern, duration=0, offset=0):
        """Turn on/off lasers.

        Arguments:
        pattern: binary mask of lasers state (0-off/1-on)
        duration: length of the strobe (may be no effect, depends on target sensor)
        offset: offset of the strobe  (may be no effect, depends on target sensor)
        """

        scidur = resapi.to_sci(duration)
        scioff = resapi.to_sci(offset)
        params = struct.pack('<Hbbbb', pattern, scidur[0], scidur[1], scioff[0], scioff[1]) + bytes(2)
        self._send_and_check(api.Request(resapi.CMD_SET_LASER, params=params),
                             [api.STATUS_OK])

    # -------------------------------------------------------------------------

    def get_laser(self):
        """Returns current mask of the state of the lasers."""

        reply = self._send_and_check(api.Request(resapi.CMD_GET_LASER),
                                     [api.STATUS_OK])

        (pattern, durman, durexp, offman, offexp) = struct.unpack('<Hbbbb', reply.params[0:6])
        return resapi.LaserSetup(pattern=pattern,
                                 duration=resapi.from_sci((durman, durexp)),
                                 offset=resapi.from_sci((offman, offexp)))

    # -------------------------------------------------------------------------

    def set_shutter(self, exposure_time):
        """Set exposure time of the sensor.

        Arguments:
        exposure_time: length of the exposure    
        """
        params = struct.pack('<I', exposure_time) + bytes(4)
        self._send_and_check(api.Request(resapi.CMD_SET_SHUTTER, params=params),
                             [api.STATUS_OK])

    # -------------------------------------------------------------------------

    def get_shutter(self):
        """Returns exposure time of the sensor."""
        reply = self._send_and_check(api.Request(resapi.CMD_GET_SHUTTER),
                                     [api.STATUS_OK])

        return struct.unpack('<I', reply.params[0:4])[0]

    # -------------------------------------------------------------------------

    def get_gain(self):
        """Returns gain (`analog` and `digital`) of the image sensor in dict."""
        reply = self._send_and_check(api.Request(resapi.CMD_GET_GAIN),
                                     [api.STATUS_OK])

        items = struct.unpack('<II', reply.params[0:8])

        return resapi.GainSetup(analog=items[0], digital=items[1])

    # -------------------------------------------------------------------------

    def set_gain(self, iso):
        """Set gaim of image sensor."""
        params = struct.pack('<I', iso) + bytes(4)
        self._send_and_check(api.Request(resapi.CMD_SET_GAIN,
                                         params=params),
                             [api.STATUS_OK])

    # -------------------------------------------------------------------------

    def get_image(self, avg_num=1, image_format="PGM", turn_off_lasers=False):
        """Get RAW image from device."""

        imfmt = ReservedSyncClient.__get_imfmt(image_format)
        flags = 0
        if turn_off_lasers:
            flags = flags | resapi.FLAGS_TURN_OFF_LASERS_AFTER
        params = struct.pack('<IBB', avg_num, flags, imfmt) + bytes(2)
        reply = self._send_and_check(api.Request(resapi.CMD_GET_IMAGE,
                                                 params=params),
                                     [api.STATUS_OK])

        timer, image_id, ret_imfmt = struct.unpack('<QIB', reply.params[0:13])
        ret_image_format = resapi.REVMAP_IMAGE_FORMAT.get(ret_imfmt, "UNKNOWN")

        return resapi.Image(timer=timer, image_id=image_id,
                            data=reply.payload, format=ret_image_format)

    # -------------------------------------------------------------------------

    def get_reserved_info(self):
        """Get reserved info."""
        reply = self._send_and_check(api.Request(resapi.CMD_GET_RESERVED_INFO),
                                     [api.STATUS_OK])

    # -------------------------------------------------------------------------

    def get_profile(self, policy_name=""):
        """Get current profile."""
        assert (type(policy_name) == str)

        params = bytes(policy_name, 'ascii')
        if len(params) > 8:
            raise RuntimeError("Policy name is too long")
        params += bytes(8 - len(params))
        reply = self._send_and_check(api.Request(resapi.CMD_GET_PROFILE,
                                                 params=params),
                                     [api.STATUS_OK])

        return json.loads(reply.payload.decode('ascii'))

    # -------------------------------------------------------------------------

    def set_profile(self, profile):
        """Set profile to the sensor."""
        self._send_and_check(resapi.PayloadRequest(resapi.CMD_SET_PROFILE,
                                                   payload=bytes(json.dumps(profile), 'ascii')),
                             [api.STATUS_OK])

    # -------------------------------------------------------------------------

    def get_stats(self):
        """Get runtime statistics."""

        reply = self._send_and_check(api.Request(resapi.CMD_GET_STATS),
                                     [api.STATUS_OK])

        return json.loads(reply.payload.decode('ascii'))

    # -------------------------------------------------------------------------

    def reset_stats(self):
        """Get runtime statistics."""

        reply = self._send_and_check(api.Request(resapi.CMD_RESET_STATS),
                                     [api.STATUS_OK])

    # -------------------------------------------------------------------------
    # STATIC CALLS ------------------------------------------------------------

    @staticmethod
    def __get_imfmt(image_format):
        imfmt = resapi.MAP_IMAGE_FORMAT.get(image_format.upper())
        if imfmt is None:
            raise RuntimeError("Unsupported image format: %s" % image_format)

        return imfmt

# -----------------------------------------------------------------------------
