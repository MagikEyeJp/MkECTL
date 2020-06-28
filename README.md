


# Documentation for the calibration machine of MagikEye

## Operating environment
- Ubuntu xxx
- Python 3.6.9 or newer

First, check if the project `keiganGUI` exists at 
`\home\bin`
then go to terminal and you can run this command:
`python3 bin/keiganGUI/keiganGUI.py`

Then, you will see the main window like the image below.

## Main Window ("KeiganGUI")
<!-- 
![keiganGUI](https://github.com/NarinOka/keiganGUI/blob/master/GUI_snapshots/keiganGUI_window_documentation.png)  
-->
<img src = "GUI_snapshots/keiganGUI_window_documentation.png" width = "480">  

This window mainly consists of 3 parts, **Robot Control**, **IR Light Control**, and **Scripting**.
### Robot Control
In this part, you can configure and move the motors. There are three motors in the calibration robot: **Slider**, **Pan**, and **Tilt**. 
The function of each numbered widgets in the GUI is as follows: 

1. `Initialize Button` initializes all of the three motors and open the port of IR lights. This button will be disabled after finishing initialization.  
<img src = "flowchart/keiganGUI_1.png" width = "360"> 

2. `Set Slider Origin Button` can set the origin point of the slider motor. When finished, information message will be popped up so be patient until then.  
<img src = "flowchart/keiganGUI_2.png" width = "360"> 

3. `FREE all motors Button` releases the restrain states of all motors. Holding torque will be reduced while the configuration of motors will be maintained.  
<img src = "flowchart/keiganGUI_3.png" width = "360"> 

4. `REBOOT all motors Button`, on the other hand, turns off all motors and the configuration will not be maintained. If you want to use motors again, you should click `Initialize Button`.  
<img src = "flowchart/keiganGUI_4.png" width = "360"> 

5. This `Progress Bar` can be used when you want to check the progress of 
- motor initialization (when clicked ①)
- going to origin (when clicked ⑫)

6. In this part (`Motor Positions`), you can input specify the position of each motor in the spin box. Notice that the unit of value for Slider, Pan, and Tilt are mm, deg, and deg respectively. If you click <img src = "GUI_icons/exec.png" width = "12"> buttons, you can send a command to each motor and the robot will change the posture by moving the motor.  
<img src = "flowchart/keiganGUI_6.png" width = "360"> 

7. `Save Button` allows you to save motor positions as indicated in the spin boxes in `Motor Positions`. Sets of motor positions will be stored in the combo box ⑧.  
<img src = "flowchart/keiganGUI_7.png" width = "360"> 

8. `Saved Positions` stores motor positions which you saves. You can choose a set of motor positions from the combo box, and move motors by clicking <img src = "GUI_icons/exec.png" width = "12"> button.  
<img src = "flowchart/keiganGUI_8.png" width = "360"> 

9. `Set speed` allows you to change the rotation speed of each motor.  
<img src = "flowchart/keiganGUI_9.png" width = "360"> 

10. In `Preset`, firstly choose a motor ID from the combo box and type a value which you want to set as the motor's current position. The text of the label indicating the unit will be changed depending on the motor ID.  
<img src = "flowchart/keiganGUI_10.png" width = "360"> 

11. `SET Origin Button` sets the current positions of all motors origin (0, 0, 0).  
<img src = "flowchart/keiganGUI_11.png" width = "360"> 

12. `GO TO Origin Button` moves all motors to the point of origin.  
<img src = "flowchart/keiganGUI_12.png" width = "360"> 

13. In `Current Pos.`, you can check the current positions of all motors.  

### IR Light Control
14. You can control lights (L1 and L2) respectively. By clicking <img src = "GUI_icons/lightON.png" width = "12">, the light will be turned on. On the other hand, <img src = "GUI_icons/lightOFF.png" width = "12"> button allows you to turn off the light.   
<img src = "flowchart/keiganGUI_14.png" width = "360"> 

### Scripting
15. The name of a script you chose will be shown here.  

16. If you click `Select Script tool button`, file dialog will be opened and you can select a script. Choose a file with extension <u>.txt</u>.
<img src = "flowchart/keiganGUI_16.png" width = "360"> 

17. If `Continue Script button` is clicked, the selected script will be resumed where you left off last session. If you haven't clicked ⑱, this button has the same role as ⑱. 
<img src = "flowchart/keiganGUI_17.png" width = "360"> 

18. If `Execute Script button` is clicked, the selected script will be executed from the beginning. Acquired data while scripting will be saved in a different folder so as not to overwrite the existing data.  
<img src = "flowchart/keiganGUI_18.png" width = "360"> 

### Other
19. By clicking `Sensor Window button`, the sensor window will appear.  
<img src = "flowchart/keiganGUI_19.png" width = "360"> 

20. `MagikEye button` is a button for performing a demonstration of the calibration machine. The robot will move along a demo-script.  
<img src = "flowchart/keiganGUI_20.png" width = "360"> 

## Sub Window ("Sensor Window")
<img src = "GUI_snapshots/Sensor_window_documentation.png" width = "480">  

You can directly control the state of sensor devices through this window.
It mainly consists of 3 parts, **RPi address**, **Camera Control**, and **Laser Control**.

### RPi address
1. Before connecting sensors, specify the IP address and port number. The format is <u>(IP address):(port number)</u>.You can also specify only IP address. In that case, port number will be set as default(8888). 
<img src = "flowchart/SensorWindow_1.png" width = "360"> 

### Camera Control
In this part, you can change parameters of a camera, get images.

2. You can change `Shutter Speed` of the camera. Notice that the unit of the value is <u>μs</u>.  
<img src = "flowchart/SensorWindow_2.png" width = "360"> 

3. You can specify the `number of frames` for averaging image.   
<img src = "flowchart/SensorWindow_3.png" width = "360"> 

4. You can change `ISO value` by both selecting from the combo box and typing a number. 
<img src = "flowchart/SensorWindow_4.png" width = "360"> 

5. You can `preview` an image from the camera. `1` button is for normal image, and `#` button is for averaged image.  
<img src = "flowchart/SensorWindow_5.png" width = "360"> 

6. You can `preview and save` an image from the camera. Function of each button is same as ⑤.   
<img src = "flowchart/SensorWindow_6.png" width = "360"> 


### Laser Control
In this part, you can control lasers and check the state.

7. You can set a laser pattern by clicking buttons. `EVEN` button is for turning on even-numbered lasers, `ODD` for odd-numbered, <img src = "GUI_icons/lightON.png" width = "12"> for all lasers, and <img src = "GUI_icons/lightOFF.png" width = "12"> for turning off all lasers.  
<img src = "flowchart/SensorWindow_7-8.png" width = "360"> 

8. You can set a laser pattern by specifying with a 4-digit hexadecimal number. The flowchart is same as ⑦.  

9. You can check the current laser patten. Lasers are from No.1 to No.16.  


### Other
10. Here, you will see `Sensor Image` by clicking buttons in ⑤ or ⑥.   

11. You can check the status of the camera. A message will be shown if there is a trial to connect to sensors, or parameters are changed.  

12. By clicking `Reconnect button`, you can reconnect to sensors.  
<img src = "flowchart/SensorWindow_12.png" width = "360"> 

## Scripting Window ("Progress")
<img src = "GUI_snapshots/Scripting_window_documentation.png" width = "240">  

While scripting, this window will appear.

1. You can check the progress in detail. The number of <u>(processed lines) / (total lines)</u> in the script is indicated. The progress percentage is also indicated in the progress bar below. 

2. This is a `command name` being processed.

3. By clicking `Stop button`, this window will be closed and the process of scripting will be interrupted.

