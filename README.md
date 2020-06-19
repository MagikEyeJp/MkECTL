

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
![keiganGUI](https://github.com/NarinOka/keiganGUI/blob/master/GUI_snapshots/keiganGUI_window_documentation.png)  
This window mainly consists of 3 parts, **Robot Control**, **IR Light Control**, and **Scripting**.
### Robot Control
In this part, you can configure and move the motors. There are three motors in the calibration robot: **Slider**, **Pan**, and **Tilt**. 
The function of each numbered widgets in the GUI is as follows: 

1. `Initialize Button` initializes all of the three motors and open the port of IR lights. 

2. `Set Slider Origin Button` can set the origin point of the slider motor. When finished, information message will be popped up so be patient until then.

3. `FREE all motors Button` releases the restrain states of all motors. Holding torque will be reduced while the configuration of motors will be maintained.

4. `REBOOT all motors Button`, on the other hand, turns off all motors and the configuration will not be maintained. If you want to use motors again, you should click `Initialize Button`.

5. This `Progress Bar` can be used when you want to check the progress of 
- motor initialization (when clicked ①)
- going to origin (when clicked ⑫)

6. In this part (`Motor Positions`), you can input specify the position of each motor in the spin box. Notice that the unit of value for Slider, Pan, and Tilt are mm, deg, and deg respectively. If you click buttons with the icon of play <img src = "https://github.com/NarinOka/keiganGUI/blob/master/GUI_icons/exec.png" width = "12">, you can send a command to each motor and the robot will change the posture by moving the motor. 

7. `Save Button` allows you to save motor positions as indicated in the spin boxes in `Motor Positions`. Sets of motor positions will be stored in the combo box ⑧.

8. `Saved Positions`



### IR Light Control


### Scripting


## Sub Window ("Sensor Window")

## Scripting Window ("Progress")
