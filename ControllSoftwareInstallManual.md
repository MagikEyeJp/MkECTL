# Install Controll Software

## environment
Ubuntu 18.4 LTS / Ubuntu 20.4 LTS
Python 3.6 or later
Qt の xcb プラットフォームプラグイン用に `libxcb-cursor0` が必要です。

## extract zip
Please extract .zip file of controller software to your faborite path.

Create a PATH or desktop file if you need it.


# USB Serial Device Setting
! Administrator privileges are required.

Copy the following files contained in the zip file into /etc/udev/Rules.d.

99-ft232c.rules

This is an udev rule that allows motor and relay board devices to be accessed by normal useraccount.

# Motor Setting

-- motordic.py 

serials = {'pan': 'KM-1S XXXXXXXX', 'tilt': 'KM-1S XXXXXXXX', 'slider': 'KM-1S XXXXXXXX', 'test': 'KM-1 XXXXXXXX'}

In the above section of motordic.py, the pan, tilt, and slider Replace the XXXXXXXX part with the serial number of each motor.

## PySide6 migration notes
Python GUI フレームワークを PySide6 に変更したことで、以下の点に注意してください。

* 起動時に `xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin` と表示された場合は、次を実行して不足しているパッケージを導入します。

```bash
sudo apt-get install libxcb-cursor0
```

* `QFont.setWeight()` の引数は `QFont.Weight` に変更されています。
* 旧 PyQt5 で使用していた `exec_()` メソッドは `exec()` に改名されました。


