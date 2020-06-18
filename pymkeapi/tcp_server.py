#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""TCP MkE API Server example
"""

__author__ = "Ondra Fisar"
__copyright__ = "Copyright (c) 2017-2020, Magik-Eye Inc."

import socket, select
import struct
import time
import sys
import imageio
import json
import traceback
import threading

import pymkeapi.api as api
import pymkeapi.reserved_api as resapi


CMD_DYNAMIC_FIST = 2000
CMD_DYNAMIC_LAST = 2999


# ------------------------------------------------------------------------------

class Error(api.Error):
    def __init__(self, ret_code, message=''):
        super().__init__(message, ret_code, -1)


# ------------------------------------------------------------------------------

class Request(api.Request):

    def parse(self, data):
        """Parse reply from given data.
        Returns tuple:
        [0]: status of parsing (True/False)
        [1]: required/used size of data.
        """
        if len(data) < Request._PACKET_LEN:
            return False, Request._PACKET_LEN

        if not data.startswith(Request._MAGIC_HEAD):
            raise RuntimeError("Received BAD magic: " + str(data[0:len(Request._MAGIC_HEAD)]))

        self.cmd = int(data[8:12])
        self.seq_id, = struct.unpack('<I', data[12:16])
        self.params = bytes(data[16:24])

        if CMD_DYNAMIC_FIST <= self.cmd <= CMD_DYNAMIC_LAST:
            payload_size, = struct.unpack('<I', self.params[:4])
            self.params = self.params[4:]
        else:
            payload_size = 0

        if len(data) < (Request._PACKET_LEN + payload_size):
            return (False, Request._PACKET_LEN + payload_size)

        self.payload = bytes(data[24:24 + payload_size])

        return True, Request._PACKET_LEN + payload_size


# ------------------------------------------------------------------------------

class Reply(api.Reply):

    def __init__(self, request, ret_code=api.STATUS_OK,
                 params=bytes(), payload=bytes()):
        super().__init__()

        self.cmd = request.cmd
        self.seq_id = request.seq_id
        self.ret_code = ret_code
        assert (len(params) < Reply._PARAMS_LEN)
        self.params = params + bytes(Reply._PARAMS_LEN - len(params))
        self.payload = payload

        assert (type(self.cmd) == int)
        assert (type(self.seq_id) == int)
        assert (type(self.ret_code) == int)
        assert (type(self.params) == bytes)
        assert (type(self.payload) == bytes)

    def assemble(self):
        cmd_retcode_b = bytes("%04d%04d" % (self.cmd, self.ret_code), 'ascii')
        seqid_payload_b = struct.pack('<II', self.seq_id, len(self.payload))
        return Reply._MAGIC_HEAD + cmd_retcode_b + seqid_payload_b + self.params + self.payload


# ------------------------------------------------------------------------------

class Image(resapi.Image):

    def __init__(self, timer, image_id, image):
        super().__init__(timer, image_id, data=image, format="<numpy.ndarray>")

    def get_image(self):
        assert (self.format == "<numpy.ndarray>")
        return self.data


# ------------------------------------------------------------------------------

class Frame(resapi.ReservedFrame):

    def __init__(self, timer, seqn, data_type, frame_type, uid, lut3d,
                 lutid=None, uv=None, det=None, bwidth=None, sigma=None, resp=None):
        self.timer = timer
        self.seqn = seqn
        self.data_type = data_type
        self.frame_type = frame_type
        self.uid = uid
        self.lut3d = lut3d
        if lutid is None and frame_type > api.FRAME_TYPE_1:
            self.lutid = [[0, 0] for i in range(len(uid))]
        else:
            self.lutid = lutid

    def __assemble_frame1(self, idx):
        return struct.pack("<Hhhh", self.uid[idx], self.lut3d[idx][0],
                           self.lut3d[idx][1], self.lut3d[idx][2])

    def __assemble_frame2(self, idx):
        return self.__assemble_frame1(idx) + struct.pack("<HH", self.lutid[idx])

    def assemble(self):
        params = struct.pack("<QQIHH", self.timer, self.seqn, self.data_type,
                             self.frame_type, len(self.uid))
        payload = ()


# ------------------------------------------------------------------------------

class DebugImage(resapi.DebugImage):

    def assemble(self):
        raise NotImplementedError()


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class TcpServer:

    __slots__ = '__sock', '__addr', '__conn'
    POSIX_TIME = round(time.time())

    # -------------------------------------------------------------------------

    def __init__(self, host, port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__addr = (host, port)
        self.__sock.setblocking(False)
        self.__sock.bind(self.__addr)
        self.__conn = None

    # -------------------------------------------------------------------------

    def listen(self):
        print("Start listening on %s:%d" % self.__addr)
        self.__sock.listen(1)

        try:
            while True:
                # Wait for a connection
                conn, addr = self.__sock.accept()
                self._serve_client(conn, addr)
        finally:
            self.__sock.close()

    # -------------------------------------------------------------------------

    def _serve_client(self, conn, addr):
        self._client_connected(conn, addr)

        buff = bytes()
        req = Request(None)
        while True:
            (parsed, req_len) = req.parse(buff)
            if parsed:
                reply = self._dispatch(req)
                self.send_reply(reply)
                buff = buff[req_len:]
                req = Request(None)
            else:
                data = conn.recv(req_len - len(buff))
                if not data:
                    break
                buff += data

        self._client_disconnected(conn, addr)
        conn.close()

    # -------------------------------------------------------------------------

    def listen_select(self):
        print("Start listening on %s:%d" % self.__addr)
        self.__sock.listen(5)

        ins = [self.__sock]
        outs = []
        buff_in = {}
        buff_out = {}

        while ins:
            readable, writeable, exceptional = select.select(ins, outs, ins)

            for s in readable:
                if s is self.__sock:
                    conn, addr = s.accept()
                    conn.setblocking(0)
                    ins.append(conn)
                    buff_in[conn] = bytes()
                    buff_out[conn] = bytes()
                    self._client_connected(conn, addr)
                else:
                    data = s.recv(1024)
                    if not data:
                        del buff_in[s]
                        del buff_out[s]
                        if s in outs:
                            outs.remove(s)
                        ins.remove(s)
                        self._client_disconnected(s, ('xxx', 0))
                        s.close()
                        continue

                    buff_in[s] += data

                    while True:
                        req = Request(None)
                        (parsed, req_len) = req.parse(buff_in[s])
                        if parsed:
                            reply = self._dispatch(req)
                            buff_in[s] = buff_in[s][req_len:]
                            buff_out[s] += reply.assemble()
                            if s not in outs:
                                outs.append(s)
                        else:
                            break

            for s in writeable:
                if s not in buff_out:
                    continue
                s.send(buff_out[s])
                buff_out[s] = bytes()
                outs.remove(s)

            for s in exceptional:
                del buff_in[s]
                del buff_out[s]
                if s in outs:
                    outs.remove(s)
                ins.remove(s)
                self._client_disconnected(s, ('xxx', 0))
                s.close()

    # ------    

    def send_reply(self, reply):
        if self.__conn is None:
            raise IOError("No connection estabilished")
        self.__conn.send(reply.assemble())

    def terminate(self, terminate_type):
        raise api.Error(api.STATUS_CLIENT_REQUEST_DOES_NOT_APPLY)

    def get_device_info(self):
        return api.DeviceInfo(unit_id=b'',
                              device_id=0)

    def get_fw_info(self):
        return api.FwInfo(posixtime=TcpServer.POSIX_TIME,
                          git_commit=0,
                          fw_version=(0, 0, 0),
                          sys_version=(0, 0, 0))

    def get_policy(self):
        return ""

    def set_policy(self, policy_name):
        raise api.Error(api.STATUS_CLIENT_MALFORMED_REQUEST)

    def list_policies(self):
        return []

    def get_state(self):
        return api.STATE_IDLE

    def set_state(self, new_state):
        if new_state == api.STATE_IDLE:
            raise api.Error(api.STATUS_CLIENT_REQUEST_DOES_NOT_APPLY)
        else:
            raise api.Error(api.STATUS_CLIENT_MALFORMED_REQUEST)

    def start_frame_push(self, frame_type, request):
        raise NotImplementedError()

    def stop_frame_push(self, seq_id):
        raise NotImplementedError()

    def get_frame(self, frame_type):
        raise NotImplementedError()

    def get_shutter(self):
        raise NotImplementedError()

    def set_shutter(self, shutter_us):
        raise NotImplementedError()

    def get_gain(self):
        raise NotImplementedError()

    def set_gain(self, iso):
        raise NotImplementedError()

    def get_laser(self):
        raise NotImplementedError()

    def set_laser(self, pattern, duration=0, offset=0):
        raise NotImplementedError()

    def get_image(self, num_avg, flags=0):
        raise NotImplementedError()

    def get_debug_images(self, frame_type, num):
        raise NotImplementedError()

    def get_stats(self):
        return {}

    def get_profile(self, policy_name=''):
        return {}

    def set_profile(self, profile):
        raise NotImplementedError()

    # ------    

    def _client_connected(self, conn, addr):
        #        assert(self.__conn is None)
        print("Connection from %s:%d" % addr)
        self.__conn = conn

    def _client_disconnected(self, conn, addr):
        #        assert(conn == self.__conn)
        print("Disconnect from %s:%d" % addr)
        self.__conn = None

    def _dispatch(self, request):
        func = TcpServer._CMD_MAP.get(request.cmd)
        print(request)

        if func is None:
            return Reply(request, api.STATUS_CLIENT_ILLEGAL_REQUEST_TYPE)
        else:
            try:
                return func(self, request)
            except api.Error as e:
                print("[ApiError %d] %s" % (e.ret_code, str(e)), file=sys.stderr)
                traceback.print_exc()
                return Reply(request, ret_code=e.ret_code)
            #            except NotImplementedError as e:
            #                print("[NotImplemented]")
            #                return Reply(request, ret_code=resapi.STATUS_SERVER_ERROR)
            except Exception as e:
                print("[%s] %s" % (str(type(e)), str(e)))
                traceback.print_exc()
                return Reply(request, ret_code=api.STATUS_SERVER_ERROR)
            except:
                print("[UNKNOWN ERROR]")
                traceback.print_exc()
                return Reply(request, ret_code=api.STATUS_SERVER_ERROR)

    # ------    

    def __reply_terminate(self, request):
        terminate_type, = struct.unpack('<I', request.params[0:4])
        self.terminate(terminate_type)
        return Reply(request)

    def __reply_fw_info(self, request):
        info = self.get_fw_info()
        params = struct.pack("<qI", info.posixtime, info.git_commit)
        params += struct.pack("<BBB", *info.fw_version)
        params += struct.pack("<BBB", *info.sys_version)

        return Reply(request, params=params)

    def __reply_dev_info(self, request):
        info = self.get_device_info()
        params = struct.pack("<H", info.device_id) + info.unit_id[:8]
        return Reply(request, params=params)

    def __reply_get_state(self, request):
        params = struct.pack("<I", self.get_state())
        return Reply(request, params=params)

    def __reply_set_state(self, request):
        new_state, = struct.unpack('<I', request.params[0:4])
        self.set_state(new_state)
        return Reply(request)

    def __reply_get_policy(self, request):
        params = bytes(self.get_policy()[:8], 'ascii')
        return Reply(request, params=params)

    def __reply_set_policy(self, request):
        policy_name = str(request.params, 'ascii')
        self.set_policy(policy_name)
        return Reply(request)

    def __reply_list_policies(self, request):
        policies = self.list_policies()
        params = struct.pack('<I', len(policies))
        payload = b'\0'.join([bytes(p, 'ascii') for p in policies])
        return Reply(request, params=params, payload=payload)

    def __reply_start_frame_push(self, request):
        frame_type, = struct.unpack('<H', request.params[:2])
        self.start_frame_push(frame_type, request)
        return Reply(request, ret_code=api.STATUS_DATA_WILL_START)

    def __reply_stop_frame_push(self, request):
        self.stop_frame_push()
        return Reply(request)

    def __reply_get_frame(self, request):
        frame_type, = struct.unpack('<H', request.params[:2])
        self.get_frame(frame_type)
        # TBD: how to convert ImageFrame into DataGram Frame
        return Reply(request)

    def __reply_get_shutter(self, request):
        params = struct.pack('<I', self.get_shutter())
        return Reply(request, params=params)

    def __reply_set_shutter(self, request):
        shutter, = struct.unpack('<I', request.params[:4])
        self.set_shutter(shutter)
        return Reply(request)

    def __reply_get_gain(self, request):
        gain = self.get_gain()
        params = struct.pack('<II', gain.analog, gain.digital)
        return Reply(request, params=params)

    def __reply_set_gain(self, request):
        iso, = struct.unpack('<I', request.params[:4])
        self.set_gain(iso)
        return Reply(request)

    def __reply_get_laser(self, request):
        laser = self.get_laser()
        duration = resapi.to_sci(laser.duration)
        offset = resapi.to_sci(laser.offset)
        params = struct.pack('<H', laser.pattern)
        params += struct.pack('<bb', *duration)
        params += struct.pack('<bb', *offset)
        return Reply(request, params=params)

    def __reply_set_laser(self, request):
        pattern, = struct.unpack('<H', request.params[:2])
        duration = struct.unpack('<bb', request.params[2:4])
        offset = struct.unpack('<bb', request.params[4:6])
        self.set_laser(pattern,
                       resapi.from_sci(duration),
                       resapi.from_sci(offset))
        return Reply(request)

    def __reply_get_image(self, request):
        num_avg, flags, fmt = struct.unpack('<IBB', request.params[:6])
        im = self.get_image(num_avg, flags)
        if fmt == resapi.IMAGE_FORMAT_DEFAULT:
            fmt = resapi.IMAGE_FORMAT_PGM
        sfmt = resapi.REVMAP_IMAGE_FORMAT.get(fmt)
        if sfmt is None:
            raise api.Error(api.STATUS_CLIENT_MALFORMED_REQUEST)
        data = imageio.imwrite(uri='<bytes>', im=im.get_image(), format=sfmt)
        params = struct.pack('<QIB', im.timer, im.image_id, fmt)
        print(data[:50])
        return Reply(request, params=params, payload=data)

    def __reply_get_debug_images(self, request):
        num, frame_type, fmt = struct.unpack('<IHB', request.params[:7])
        dbgs = self.get_debug_images(frame_type, num)
        if fmt == resapi.IMAGE_FORMAT_DEFAULT:
            fmt = resapi.IMAGE_FORMAT_PGM
        sfmt = resapi.REVMAP_IMAGE_FORMAT.get(fmt)
        if sfmt is None:
            raise api.Error(api.STATUS_CLIENT_MALFORMED_REQUEST)

        payload = bytes()
        for d in dbgs:
            im_data = imageio.imwrite(uri='<bytes>', im=d.image.get_image(), format=sfmt)
            frm_data = d.frame.assemble()
            subheader = struct.pack('<QIIIHHHH', d.image.timer,
                                    d.image.image_id, len(im_data), len(frm_data),
                                    d.frame.frame_type, len(d.frame.uid),
                                    d.pattern, d.frame.data_type) + bytes(4)
            payload += subheader
            payload += im_data
            payload += frm_data

        params = struct.pack('<IB', num, fmt)
        return Reply(request, params=params, payload=payload)

    def __reply_get_stats(self, request):
        return Reply(request, payload=bytes(json.dumps(self.get_stats()), 'utf8'))

    def __reply_get_reserved_info(self, request):
        return Reply(request)

    def __reply_get_profile(self, request):
        policy_name = str(request.params, 'ascii')
        return Reply(request, payload=bytes(json.dumps(self.get_profile(policy_name)), 'utf8'))

    def __reply_set_profile(self, request):
        self.set_profile(str(request.payload, 'utf8'))
        return Reply(request)

    _CMD_MAP = {api.CMD_TERMINATE: __reply_terminate,
                api.CMD_GET_FIRMWARE_INFO: __reply_fw_info,
                api.CMD_GET_DEVICE_INFO: __reply_dev_info,
                api.CMD_GET_STATE: __reply_get_state,
                api.CMD_SET_STATE: __reply_set_state,
                api.CMD_GET_POLICY: __reply_get_policy,
                api.CMD_SET_POLICY: __reply_set_policy,
                api.CMD_LIST_POLICIES: __reply_list_policies,
                api.CMD_START_FRAME_PUSH: __reply_start_frame_push,
                api.CMD_STOP_FRAME_PUSH: __reply_stop_frame_push,
                api.CMD_GET_FRAME: __reply_get_frame,

                resapi.CMD_GET_SHUTTER: __reply_get_shutter,
                resapi.CMD_SET_SHUTTER: __reply_set_shutter,
                resapi.CMD_GET_GAIN: __reply_get_gain,
                resapi.CMD_SET_GAIN: __reply_set_gain,
                resapi.CMD_GET_LASER: __reply_get_laser,
                resapi.CMD_SET_LASER: __reply_set_laser,
                resapi.CMD_GET_IMAGE: __reply_get_image,
                resapi.CMD_GET_DEBUG_IMAGES: __reply_get_debug_images,
                resapi.CMD_GET_STATS: __reply_get_stats,
                resapi.CMD_GET_RESERVED_INFO: __reply_get_reserved_info,
                resapi.CMD_GET_PROFILE: __reply_get_profile,
                resapi.CMD_SET_PROFILE: __reply_set_profile
                }


if __name__ == "__main__":
    server = TcpServer('127.0.0.1', 8888)
    server.listen_select()

