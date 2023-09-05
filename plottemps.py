#!/usr/bin/env python
from docopt import docopt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import serial
import time
import configparser
import PyQt5

plt.rcParams['backend']='Qt5Agg'
max_x = 600  # デフォルトの最大時間(秒)
active = False
resized = False
INI_FILE = "plottemps.ini"


def execCmdline():
    """
    usage: plottemps.py [options]

    options:
        -f --file=<logfile>                plot log file
        -h --help                   show usage
        -d --device=<device>        receiver device name
        --version                   show version
    """

    args = (docopt(execCmdline.__doc__, version="1.0.0"))
    print(args)
    tempdata = {}

    conf = configparser.ConfigParser()
    conf.optionxform = str
    conf.read(INI_FILE)

    logfile = args.get("--file", None)
    device = args.get("--device", None)
    if device is None:
        device = conf.get("SETTINGS", "ReceiverDevice")

    # sensor list
    sensors = {}
    for k, v in conf.items("SENSORS"):
        ed, col = v.split(',')
        sensors[ed] = (k, col)

    if logfile is not None:
        read_plotdata(logfile, tempdata)
        fig, ax, _, _ = plot_data(tempdata, sensors)
        plt.show(block=True)
    else:
        # シリアルポートの設定
        # ser = serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=0.5)
        ser = serial.Serial(device, baudrate=115200, timeout=0.5)

        # ログファイル名
        now = datetime.now()
        fname = "templog_" + now.strftime('%Y%m%d_%H%M%S') + ".csv"

        # グラフ
        fig, ax, lt, ut = plot_data(tempdata, sensors)
        fig.show()
        plt.ion()
        global active
        global resized
        active = True
        resized = False
        fig.canvas.mpl_connect('close_event', on_close)
        fig.canvas.mpl_connect('resize_event', on_resize)
        # ax.margins(0.5)

        plotline = {}
        ann = {}
        starttime = datetime.now()

        while active:
            data = ser.readline().decode().strip()
            print(data)

            if data:
                new_data = log_temperature(data, fname)
                if new_data is not None:
                    # print(new_data)
                    ed, tim, temp = new_data
                    lst = tempdata.get(ed, None)
                    xvalue = (tim - starttime).total_seconds()
                    if lst is None:
                        tempdata[ed] = [(xvalue, temp)]
                        x, y = zip(*tempdata[ed])
                        col = 'blue'
                        lbl = ed
                        if ed in sensors:
                            lbl = sensors[ed][0]
                            col = sensors[ed][1]
                        plotline[ed], = ax.plot(x, y, color=col, label=lbl)
                        bbox = dict(boxstyle="round", fc="w", ec=col)
                        arrowprops = dict(
                            arrowstyle="-",
                            linestyle="--",
                            relpos=(0., 0.5),
                            connectionstyle="arc3,rad=0")
                        ann[ed] = ax.annotate(f"{y[-1]}", (x[-1], y[-1]), xycoords="data", textcoords=(ax.transAxes, ax.transData), xytext=(1.0, y[-1]), bbox=bbox, arrowprops=arrowprops, ha="left", va="center")
                        ax.legend()
                    else:
                        tempdata[ed].append((xvalue, temp))
                        x, y = zip(*tempdata[ed])
                        # ax.plot(x, y, color='blue')
                        plotline[ed].set_data(x, y)
                        ann[ed].set_text(f"{y[-1]}")
                        ann[ed].xy = (x[-1], y[-1])
                        ann[ed].set_y(y[-1])
                        # print(plotline[ed], x,y)
                    if resized:
                        plt.autoscale(True, 'both')
                        resized = False
                    ax.relim()
                    ax.autoscale_view()
                    x_min, x_max = ax.get_xlim()
                    y_min, y_max = ax.get_ylim()
                    print(y_min, y_max)
                    lt.set_text(f"{y_min:.1f}")
                    ut.set_text(f"{y_max:.1f}")
                    fig.canvas.draw_idle()

                    # print(y_min, y_max)
                    # ax.set_ylim(ymin = round(y_min), auto=True)
            fig.canvas.flush_events()
            time.sleep(.2)


def on_close(e):
    global active
    active = False

def on_resize(e):
    global resized
    resized = True

# 温度のみをログファイルに出力する関数
def log_temperature(data, fname):
    # 温度の項目を取り出す
    temp_item = [item for item in data.split(':') if item.startswith('te=')]
    ed_item = [item for item in data.split(':') if item.startswith('ed=')]
    ret = None
    if len(temp_item) == 1 and len(ed_item) == 1:
        # ed を取り出す
        ed = ed_item[0].split('=')[1]
        # 温度の項目から温度値を取り出す
        temperature = temp_item[0].split('=')[1]
        # 温度を小数点以下2桁にフォーマットする
        temperature = '{:.2f}'.format(float(temperature) / 100)
        # 現在の日付と時刻を取得する
        timestamp = datetime.now()
        # ログファイルに温度を書き込む
        with open(fname, "a") as f:
            f.write(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}, {ed}, {temperature}\n")
        ret = (ed, timestamp, float(temperature))

    return ret


def read_plotdata(logfile, data):
    min_time = None
    start_time = 0
    with open(logfile, 'r') as f:
        for line in f:
            timestamp_str, ed_str, temp_str = [x.strip() for x in line.strip().split(',')]
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            min_time = min(timestamp, min_time) if min_time is not None else timestamp
            seconds = (timestamp - min_time).total_seconds() - start_time
            if ed_str not in data:
                data[ed_str] = []
            if seconds >= 0:
                data[ed_str].append((seconds, float(temp_str)))


def plot_data(data, sensors):
    global max_x

    min_time = None
    range_sec = 0

    fig, ax = plt.subplots()
    plt.cla()
    fig.canvas.manager.set_window_title('plottemps')
    fig.suptitle('temperature')
    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Temperature (Celsius)")
    ax.grid(True, which='major', axis='both', linestyle='--', color='k')
    ax.grid(True, which='minor', axis='both', linestyle=':', color='k')
    ax.xaxis.set_major_locator(plt.MultipleLocator(3600))  # 横軸の目盛りを10分間隔にする
    ax.yaxis.set_major_locator(plt.MultipleLocator(1))  # 縦軸の目盛りを1度間隔にする
    ax.xaxis.set_minor_locator(plt.MultipleLocator(600))  # 横軸の補助目盛りを1分間隔にする
    ax.yaxis.set_minor_locator(plt.MultipleLocator(0.5))  # 縦軸の補助目盛りを0.5度間隔にする

    for ed, pd in data.items():
        x, y = zip(*pd)

        # グラフの範囲を設定
        max_x = max(max_x, x[-1])  # 最大時間を更新
        if range_sec > 0:
            ax.set_xlim(max(0, max_x - range_sec), max_x)
            ax.set_xlim(0, max_x)

        if ed in sensors:
            lbl = sensors[ed][0]
            col = sensors[ed][1]
        else:
            col = 'blue'
            lbl = ed

        ax.plot(x, y, color=col, label=lbl)

        #        ax.lines[0].set_data(x, y)
        ax.legend()
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw_idle()
        fig.canvas.flush_events()

    fig.autofmt_xdate()
    ymin, ymax = ax.get_ylim()
    lowertext = ax.text(0, 0, f"{ymin:.1f}", color='b', ha='right', va='top', transform=ax.transAxes)
    uppertext = ax.text(0, 1, f"{ymax:.1f}", color='b', ha='right', va='bottom', transform=ax.transAxes)

    return fig, ax, lowertext, uppertext


if __name__ == '__main__':
    execCmdline()
