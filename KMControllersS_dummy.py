#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 10 16:50:24 2017

@author: takata@innovotion.co.jp
"""
import serial,struct,threading
import time
from time import sleep
from enum import Enum

def float2bytes(float_value):
    float_value=float(float_value)
    return struct.pack("!f", float_value)

def bytes2float(byte_array):
    return struct.unpack('!f',byte_array)[0]

def uint8_t2bytes(uint8_value):
    uint8_value=int(uint8_value)
    if uint8_value>256-1:
        uint8_value=256-1
    return struct.pack("B",uint8_value)

def uint16_t2bytes(uint16_value):
    uint16_value=int(uint16_value)
    if uint16_value>256**2-1:
        uint16_value=256**2-1
    val1=int(uint16_value/256)
    val2=uint16_value-val1*256
    return struct.pack("BB",val1,val2)

def bytes2uint16_t(ba):
    return struct.unpack("BB",ba)[0]

def bytes2uint8_t(ba):
    return struct.unpack("B",ba)[0]

def bytes2int16_t(ba):
    return struct.unpack(">h",ba)[0]

def uint32_t2bytes(uint32_value):
    uint32_value=int(uint32_value)
    if uint32_value>256**4-1:
        uint32_value=256**4-1
    val1=int(uint32_value/256**3)
    val2=int((uint32_value-val1*256**3)/256**2)
    val3=int((uint32_value-val1*256**3-val2*256**2)/256)
    val4=uint32_value-val1*256**3-val2*256**2-val3*256
    return struct.pack("BBBB",val1,val2,val3,val4)

class Controller:
    def __init__(self):
        self.scaling_rate = 1.0
        self.scaling_offset = 0.0

    def run_command(self,val,characteristics):
        print(val,characteristics)

    # Settings
    def maxSpeed(self,max_speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the maximum speed of rotation to the 'max_speed' in rad/sec.
        """
        command=b'\x02'
        values=float2bytes(max_speed)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def minSpeed(self,min_speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the minimum speed of rotation to the 'min_speed' in rad/sec.
        """
        command=b'\x03'
        values=float2bytes(min_speed)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def curveType(self,curve_type,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the acceleration or deceleration curve to the 'curve_type'.
        typedef enum curveType =
        {
            CURVE_TYPE_NONE = 0, // Turn off Motion control
            CURVE_TYPE_TRAPEZOID = 1, // Turn on Motion control with trapezoidal curve
        }
        """

        command=b'\x05'
        values=uint8_t2bytes(curve_type)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def acc(self,_acc,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the acceleration of rotation to the positive 'acc' in rad/sec^2.
        """
        command=b'\x07'
        values=float2bytes(_acc)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def dec(self,_dec,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the deceleration of rotation to the positive 'dec' in rad/sec^2.
        """
        command=b'\x08'
        values=float2bytes(_dec)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def maxTorque(self,max_torque,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the maximum torque to the positive 'max_torque' in N.m.
        """
        command=b'\x0E'
        values=float2bytes(max_torque)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def qCurrentP(self,q_current_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Proportional gain to the postiive 'q_current_p'.
        """
        command=b'\x18'
        values=float2bytes(q_current_p)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def qCurrentI(self,q_current_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Integral gain to the positive 'q_current_i'.
        """
        command=b'\x19'
        values=float2bytes(q_current_i)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def qCurrentD(self,q_current_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the q-axis current PID controller's Differential gain to the postiive 'q_current_d'.
        """
        command=b'\x1A'
        values=float2bytes(q_current_d)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def speedP(self,speed_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Proportional gain to the positive 'speed_p'.
        """
        command=b'\x1B'
        values=float2bytes(speed_p)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def speedI(self,speed_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Integral gain to the positive 'speed_i'.
        """
        command=b'\x1C'
        values=float2bytes(speed_i)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def speedD(self,speed_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed PID controller's Deferential gain to the positive 'speed_d'.
        """
        command=b'\x1D'
        values=float2bytes(speed_d)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def positionP(self,position_p,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x1E'
        values=float2bytes(position_p)
        self.run_command(command+identifier+values+crc16,'motor_settings')


    def positionI(self,position_i,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x1F'
        values=float2bytes(position_i)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def positionD(self,position_d,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x20'
        values=float2bytes(position_d)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def posControlThreshold(self, threshold, identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the position PID controller's Proportional gain to the positive 'position_p'.
        """
        command=b'\x21'
        values=float2bytes(threshold)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def resetPID(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset all the PID parameters to the firmware default settings.
        """
        command=b'\x22'
        self.run_command(command+identifier+crc16,'motor_settings')

    def lowPassFilter(self, filtertype, value, identifier=b'\x00\x00', crc16=b'\x00\x00'):  #from ver1.99a filtertype:0:Current 1:Velocity 2:Position
        """
        Set the PID low pass filter factor.
        """
        command = b'\x27'
        values = uint8_t2bytes(filtertype)+float2bytes(value)
        print(values)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def measureInterval(self,interval,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        interface settings.  bit7:button bit4:I2C bit3:USB bit0:BLE
        """
        command=b'\x2C'
        values=uint8_t2bytes(interval)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def measureByDefault(self,flag,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        interface settings.
        """
        command=b'\x2D'
        values=uint8_t2bytes(flag)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def interface(self,flag,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        interface settings.
        """
        # command=b'\x2E'
        # values=uint8_t2bytes(flag)
        # self.run_command(command+identifier+values+crc16,'motor_settings')

        ########## dummy ##########
        if flag == 8:
            print('Using USBController')
        else:
            print('Choose 8 to use USBController')

    def limitCurrent(self,current,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the Current limit.
        """
        command=b'\x33'
        values=float2bytes(current)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def ownColor(self,red,green,blue,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the own LED color.
        """
        command=b'\x3A'
        values=uint8_t2bytes(red)+uint8_t2bytes(green)+uint8_t2bytes(blue)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def readRegister(self,register,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        '''
        Read a specified setting (register).
        '''
        command=b'\x40'
        values=uint8_t2bytes(register)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def saveAllRegisters(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Save all settings (registers) in flash memory.
        """
        command=b'\x41'
        self.run_command(command+identifier+crc16,'motor_settings')

    def resetRegister(self,register,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset a specified register's value to the firmware default setting.
        """
        command=b'\x4E'
        values=uint8_t2bytes(register)
        self.run_command(command+identifier+values+crc16,'motor_settings')

    def resetAllRegisters(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset all registers' values to the firmware default setting.
        """
        command=b'\x4F'
        self.run_command(command+identifier+crc16,'motor_settings')

    # Motor Action
    def disable(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Disable motor action.
        """
        command=b'\x50'
        self.run_command(command+identifier+crc16,'motor_control')

    def enable(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enable motor action.
        """
        # command=b'\x51'
        # self.run_command(command+identifier+crc16,'motor_control')

        ########## dummy ##########
        print(self.port + ' was enabled.')


    def speed(self,speed,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the speed of rotation to the positive 'speed' in rad/sec.
        """
        # command=b'\x58'
        # values=float2bytes(speed)
        # self.run_command(command+identifier+values+crc16,'motor_control')

        ########## dummy ##########
        # print(self.port + ' speed = ' + str(speed))
        print(self.port + ' speed was changed.')

    def presetPosition(self,position,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Preset the current absolute position as the specified 'position' in rad. (Set it to zero when setting origin)
        """
        command=b'\x5A'
        values=float2bytes(position)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def runForward(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Rotate the motor forward (counter clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x60'
        self.run_command(command+identifier+crc16,'motor_control')

    def runReverse(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Rotate the motor reverse (clock-wise) at the speed set by 0x58: speed.
        """
        command=b'\x61'
        self.run_command(command+identifier+crc16,'motor_control')

    def moveTo(self,position,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Move the motor to the specified absolute 'position' at the speed set by 0x58: speed.
        """
        command=b'\x66'
        values=float2bytes(position)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def moveBy(self,distance,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Move motor by the specified relative 'distance' from the current position at the speed set by 0x58: speed.
        """
        command=b'\x68'
        values=float2bytes(distance)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def free(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop the motor's excitation
        """
        command=b'\x6C'
        self.run_command(command+identifier+crc16,'motor_control')

    def stop(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Decelerate the speed to zero and stop.
        """
        command=b'\x6D'
        self.run_command(command+identifier+crc16,'motor_control')

    def holdTorque(self,torque,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Keep and output the specified torque.
        """
        command=b'\x72'
        values=float2bytes(torque)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def doTaskSet(self,index,repeating,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Do taskset at the specified 'index' 'repeating' times.
        """
        command=b'\x81'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def preparePlaybackMotion(self,index,repeating,option,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Prepare to playback motion at the specified 'index' 'repeating' times.
        """
        command=b'\x86'
        values=uint16_t2bytes(index)+uint32_t2bytes(repeating)+uint8_t2bytes(option)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def startPlaybackMotion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start to playback motion in the condition of the last preparePlaybackMotion.
        """
        command=b'\x87'
        self.run_command(command+identifier+crc16,'motor_control')

    def stopPlaybackMotion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop to playback motion.
        """
        command=b'\x88'
        self.run_command(command+identifier+crc16,'motor_control')

    # Queue
    def pause(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Pause the queue until 0x91: resume is executed.
        """
        command=b'\x90'
        self.run_command(command+identifier+crc16,'motor_control')

    def resume(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Resume the queue.
        """
        command=b'\x91'
        self.run_command(command+identifier+crc16,'motor_control')

    def wait(self,time,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Wait the queue or pause the queue for the specified 'time' in msec and resume it automatically.
        """
        command=b'\x92'
        values=uint32_t2bytes(time)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def reset(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reset the queue. Erase all tasks in the queue. This command works when 0x90: pause or 0x92: wait are executed.
        """
        command=b'\x95'
        self.run_command(command+identifier+crc16,'motor_control')

    # Taskset
    def startRecordingTaskset(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start recording taskset at the specified 'index' in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA0'
        values=uint16_t2bytes(index)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def stopRecordingTaskset(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop recording taskset.
        This command works while 0xA0: startRecordingTaskset is executed.
        """
        command=b'\xA2'
        values=uint16_t2bytes(index)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def eraseTaskset(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase taskset at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 49 (50 in total).
        """
        command=b'\xA3'
        values=uint16_t2bytes(index)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def eraseAllTaskset(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase all tasksets in the flash memory.
        """
        command=b'\xA4'
        self.run_command(command+identifier+crc16,'motor_control')

    # Teaching
    def prepareTeachingMotion(self,index,time,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Prepare teaching motion by specifying the 'index' in the flash memory and recording 'time' in milliseconds.
        In the case of KM-1, index value is from 0 to 9 (10 in total).  Recording time cannot exceed 65408 [msec].
        """
        command=b'\xAA'
        values=uint16_t2bytes(index)+uint32_t2bytes(time)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def startTeachingMotion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Start teaching motion in the condition of the last prepareTeachingMotion.
        This command works when the teaching index is specified by 0xAA: prepareTeachingMotion.
        """
        command=b'\xAB'
        self.run_command(command+identifier+crc16,'motor_control')

    def stopTeachingMotion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Stop teaching motion.
        """
        command=b'\xAC'
        self.run_command(command+identifier+crc16,'motor_control')

    def eraseMotion(self,index,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase motion at the specified index in the flash memory.
        In the case of KM-1, index value is from 0 to 9 (10 in total).
        """
        command=b'\xAD'
        values=uint16_t2bytes(index)
        self.run_command(command+identifier+values+crc16,'motor_control')

    def eraseAllMotion(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Erase all motion in the flash memory.
        """
        command=b'\xAE'
        self.run_command(command+identifier+crc16,'motor_control')

    # LED
    def led(self,ledState,red,green,blue,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Set the LED state (off, solid, flash and dim) and color intensity (red, green and blue).
        typedef enum ledState =
        {
            LED_STATE_OFF = 0, // LED off
            LED_STATE_ON_SOLID = 1, // LED solid
            LED_STATE_ON_FLASH = 2, // LED flash
            LED_STATE_ON_DIM = 3 // LED dim
        }
        """
        command=b'\xE0'
        values=uint8_t2bytes(ledState)+uint8_t2bytes(red)+uint8_t2bytes(green)+uint8_t2bytes(blue)
        self.run_command(command+identifier+values+crc16,"motor_control")

    # IMU
    def enableIMU(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enable the IMU and start notification of the measurement values.
        This command is only available for BLE (not implemented on-wired.)
        When this command is executed, the IMU measurement data is notified to BLE IMU Measuement characteristics.
        """
        command=b'\xEA'
        self.run_command(command+identifier+crc16,'motor_control')

    def disableIMU(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Disable the IMU and stop notification of the measurement values.
        """
        command=b'\xEB'
        self.run_command(command+identifier+crc16,'motor_control')

    # System
    def reboot(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Reboot the system.
        """
        command=b'\xF0'
        self.run_command(command+identifier+crc16,'motor_control')

    def enableCheckSum(self,identifier=b'\x00\x00',crc16=b'\x6f\x43'):
        """
        Enable Check Sum.
        """
        command=b'\xF3'
        flag=b'\x01'
        self.run_command(command+identifier+flag+crc16,'motor_control')

    def disableCheckSum(self,identifier=b'\x00\x00',crc16=b'\xe6\x52'):
        """
        Enable Check Sum.
        """
        command=b'\xF3'
        flag=b'\x00'
        self.run_command(command+identifier+flag+crc16,'motor_control')

    def enterDeviceFirmwareUpdate(self,identifier=b'\x00\x00',crc16=b'\x00\x00'):
        """
        Enter the device firmware update mode.
        Enter the device firmware update mode or bootloader mode. It goes with reboot.
        """
        command=b'\xFD'
        self.run_command(command+identifier+crc16,'motor_control')

    # motor measurement should be override
    def read_motor_measurement(self):
        position = 0.0
        velocity = 0.0
        torque = 0.0
        return position, velocity, torque

    # user defined coodinate API
    def set_scaling(self, rate, offset):
        self.scaling_rate = rate
        self.scaling_offset = offset

    def get_scaling(self):
        return self.scaling_rate, self.scaling_offset

    def moveTo_scaled(self, position):
        """
        Move the motor to the specified absolute 'position' in user defined coordinate.
        """
        abs_position = (position - self.scaling_offset) * self.scaling_rate
        print(abs_position)
        self.moveTo(abs_position)

    def read_scaled_position(self):
        (position, velocity, torque) = self.read_motor_measurement()
        try:
            scaled_position = (position / self.scaling_rate) + self.scaling_offset
        except ZeroDivisionError as e:
            scaled_position = 0.0
        return scaled_position

# ------ USB Controller
class LogStatus(Enum):
    IDLE = 0
    START = 1
    LOGGING = 2
    FINISHED = 3

def recv_thread(obj):
    # When use from Matlab, don't enable python print in thread. (or MATLAB shutdown.)
    header = b'\x00\x00\xaa\xaa'
    index = 0
    logstarttime = 0
    recvtime = 0
    data = bytearray(b'\x00'*270)
    obj.m_alive = True

    while obj.m_alive and obj.serial is not None:
        rd = obj.serial.read(1)
        if len(rd) == 0:
            continue
        d = rd[0]
        if d == 0x00 and index == 0:
            recvtime = time.time()
        data[index] = d
        index += 1
        if index <= len(header):
            if d != header[index - 1]:
                if d == b'\x00':
                    index = (1, 2, 2, 1)[index-1]
                    #print('re index',index)
                else:
                    index = 0
        elif index >= (data[4] + 8) or index >= 256 + 8:
            # decode measure value
            [pre, length, kind] = struct.unpack_from('>LBB', data)
            [post] = struct.unpack_from('>H', data[index-2:])
            if pre == 0x0000aaaa and post == 0x0d0a:
                if kind == 0xb4 and length == 14:  # motor measurement
                    [pos, velo, trq] = struct.unpack_from('>fff', data[6:])
                    obj.m_lock.acquire()
                    #print(f"[motor measurement] pos:{pos:+.8f} velocity:{velo:+.8f} torque:{trq:+.8f}")
                    obj.m_position = pos
                    obj.m_velocity = velo
                    obj.m_torque = trq
                    # logging
                    if obj.m_log_status == LogStatus.START:
                        obj.m_log_index = 0
                        obj.m_log_data = []
                        logstarttime = recvtime
                        obj.m_log_status = LogStatus.LOGGING

                    if  obj.m_log_status == LogStatus.LOGGING:
                        if obj.m_log_index < obj.m_log_index_max:
                            obj.m_log_data.append((recvtime - logstarttime, pos, velo, trq))
                            obj.m_log_index += 1
                        else:
                            obj.m_log_status = LogStatus.FINISHED

                    obj.m_lock.release()
                elif kind == 0xb5 and length == 16:  # firmware1.8B not support IMU on serial interface
                    #print("[IMU measurement]", end="")
                    [acc_x, acc_y, acc_z, temp, gyro_x, gyro_y, gyro_z] = struct.unpack_from('>hhhhhhh', data[6:])
                    obj.m_lock.acquire()
                    #print("acc_x:", acc_x, " acc_y:", acc_y, " acc_z:", acc_z, "temp:", temp, "gyro_x:", gyro_x, "gyro_y:", gyro_y, "gyro_z:", gyro_z)
                    obj.m_acc_x = acc_x
                    obj.m_acc_y = acc_y
                    obj.m_acc_z = acc_z
                    obj.m_temp = temp
                    obj.m_gyro_x = gyro_x
                    obj.m_gyro_y = gyro_y
                    obj.m_gyro_z = gyro_z
                    obj.m_lock.release()
                elif kind == 0xbe and length == 13:  # error code
                    [tid, cmd, err, info] = struct.unpack_from('>HBLL', data[6:])
                    #print(f"[error] cmd:{cmd:2x} errcode:{err:4x} info:{info:4x}")
                    obj.m_lock.acquire()
                    obj.m_errcmd = cmd
                    obj.m_errcode = err
                    obj.m_errinfo = info
                    obj.m_lock.release()
                elif kind == 0x40 and length >= 5:  # read register
                    [tid, reg] = struct.unpack_from('>HB', data[6:])
                    value = data[9:index - 4]
                    #print(f"[register] reg(0x{reg:2x})=", binascii.hexlify(value))
                    obj.m_lock.acquire()
                    obj.m_reg = reg
                    obj.m_regvalue = value
                    obj.m_lock.release()
                #else:
                #    print("[other]", end="")
                #    print(binascii.hexlify(data[0:index]))
            index = 0


class USBController(Controller):
    def __init__(self, port='/dev/ttyUSB0', serialnum='KM-1 CS9B#B12'):
        super().__init__()
        # print('init port')
        self.port = port
        # self.serial = serial.Serial(port, 115200, 8, 'N', 1, 0.5, False, True)
        # self.serial = serial.Serial(port, 115200, 8, 'N', 1, 0.5, False, True, None, False, None, None)
        # motor measurement value
        self.m_position = 0
        self.m_velocity = 0
        self.m_torque = 0
        # IMU measurement value
        self.m_acc_x = 0
        self.m_acc_y = 0
        self.m_acc_z = 0
        self.m_temp = 0
        self.m_gyro_x = 0
        self.m_gyro_y = 0
        self.m_gyro_z = 0
        # error info
        self.m_errcmd = 0
        self.m_errcode = 0
        self.m_errinfo = 0
        # register value
        self.m_reg = 0
        self.m_regvalue = b''
        # measure log
        self.m_log_status = LogStatus.IDLE
        self.m_log_index = 0
        self.m_log_index_max = 0
        self.m_log_data = []
        #threading
        # self.m_lock = threading.RLock()
        # self.m_th = threading.Thread(target=recv_thread, args=(self,), daemon=True)
        # self.m_alive = False
        # self.m_th.start()
        # sleep(.1)
        # while not self.m_alive:
        #     print('wait')
        #     sleep(.1)
        # print('init port end')

        ########## dummy ##########
        self.id = port
        self.serial = serialnum


    def __del__(self):
        self.close()

    def close(self):
        # self.m_lock.acquire()
        # self.m_alive = False
        # self.m_th.join()
        # if self.serial is not None:
        #     self.serial.close()
        #     self.serial = None
        # self.m_lock.release()

        ########## dummy ##########
        print(self.port + 'was closed.')

    def run_command(self,val,characteristics=None):
        self.serial.write(val)

    def getpos(self):
        self.m_lock.acquire()
        ret = self.m_position
        self.m_lock.release()
        return ret

    def getvelocity(self):
        self.m_lock.acquire()
        ret = self.m_velocity
        self.m_lock.release()
        return ret

    def gettorque(self):
        self.m_lock.acquire()
        ret = self.m_torque
        self.m_lock.release()
        return ret

    def read_motor_measurement(self):
        self.m_lock.acquire()
        position = self.m_position
        velocity = self.m_velocity
        torque = self.m_torque
        self.m_lock.release()
        return (position, velocity, torque)

    def start_log(self, nums):
        self.m_log_index = 0
        self.m_log_index_max = nums
        self.m_log_data = []
        self.m_log_status = LogStatus.START
        return

    def getRegister(self, reg):
        self.m_reg = -1
        self.m_value = b''
        self.readRegister(reg)
        for w in range(100):
            sleep(.01)
            self.m_lock.acquire()
            readreg = self.m_reg
            readval = self.m_regvalue
            self.m_lock.release()
            if readreg >= 0:
                break
        if reg == readreg and len(readval) > 0:
            ret = readval
        else:
            ret = b''
        return ret

    def __read_float_reg(self, r):
        return struct.unpack_from('>f', self.getRegister(r))

    def __read_uint8_reg(self, r):
        return struct.unpack_from('>B', self.getRegister(r))

    def __read_uint16_reg(self, r):
        return struct.unpack_from('>H', self.getRegister(r))

    def __read_rgb_data(self, r):
        return struct.unpack_from('>BBB', self.getRegister(r))

    def read_maxSpeed(self):
        return self.__read_float_reg(0x02)

    def read_minSpeed(self):
        return self.__read_float_reg(0x03)

    def read_curveType(self):
        return self.__read_uint8_reg(0x05)

    def read_acc(self):
        return self.__read_float_reg(0x07)

    def read_dec(self):
        return self.__read_float_reg(0x08)

    def read_maxTorque(self):
        return self.__read_float_reg(0x0E)

    def read_reg16(self):
        return self.__read_uint8_reg(0x16)

    def read_reg17(self):
        return self.__read_uint8_reg(0x17)

    def read_qCurrentP(self):
        return self.__read_float_reg(0x18)

    def read_qCurrentI(self):
        return self.__read_float_reg(0x19)

    def read_qCurrentD(self):
        return self.__read_float_reg(0x1A)

    def read_speedP(self):
        return self.__read_float_reg(0x1B)

    def read_speedI(self):
        return self.__read_float_reg(0x1C)

    def read_speedD(self):
        return self.__read_float_reg(0x1D)

    def read_positionP(self):
        return self.__read_float_reg(0x1E)

    def read_positionI(self):
        return self.__read_float_reg(0x1F)

    def read_positionD(self):
        return self.__read_float_reg(0x20)

    def read_posControlThreshold(self):
        return self.__read_float_reg(0x21)

    def read_reg25(self):
        return self.__read_float_reg(0x25)

    def read_lowPassFilter(self):                   #from version 1.99a
        return struct.unpack_from('>fff', self.getRegister(0x27))

    def read_motorMeasureInterval(self):
        return self.__read_uint8_reg(0x2c)

    def read_motorMeasureByDefault(self):
        return self.__read_uint8_reg(0x2d)

    def read_interface(self):
        return self.__read_uint8_reg(0x2e)

    def read_limitCurrent(self):
        return self.__read_float_reg(0x33)

    def read_ownColor(self):
        return self.__read_rgb_data(0x3A)

    def read_reg3c(self):
        return self.__read_uint8_reg(0x3c)

    def read_reg3d(self):
        return self.__read_uint8_reg(0x3d)

    def read_reg3e(self):
        return self.__read_uint8_reg(0x3e)

    def read_SN(self):
        return self.getRegister(0x46)

    def read_FWVER(self):
        return self.getRegister(0x47)

    def read_toSpeed(self):
        return self.__read_float_reg(0x58)

    def read_reg5b(self):
        return self.__read_float_reg(0x5b)

    def read_toPosition(self):
        return self.__read_float_reg(0x66)

    def read_holdTorque(self):
        return self.__read_float_reg(0x72)

    def read_reg9a(self):
        return self.getRegister(0x9a)

    def read_rega7(self):
        return self.getRegister(0xa7)

    def read_regb1(self):
        return self.__read_uint16_reg(0xb1)

    def read_motorMeasurement(self):
        return self.readRegister(0xb4)

    def read_imuMeasurement(self):
        return self.readRegister(0xb5)

    def read_regc0(self):
        return self.__read_uint8_reg(0xc0)

    def read_led(self):
        return struct.unpack_from('>BBBB', self.getRegister(0xe0))

    def read_regf3(self):
        return self.__read_uint8_reg(0xf3)

    def read_SerialNo(self):
        return self.getRegister(0xfa)

