# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import math
import numpy as np
from numpy import linalg as LA

#キャリブレーションに適切なdistを設定する
def getbeta(z1, z2):
    return (1/z1)-(1/z2)

def delta(z, beta):
    return beta * z**2 / (1 - beta * z)

def tangent_angle(u: np.ndarray, v: np.ndarray):
    i = np.inner(u, v)
    n = LA.norm(u) * LA.norm(v)
    c = i / n
    return np.rad2deg(np.arccos(np.clip(c, -1.0, 1.0)))

def diff_angle(a, b):
    theta = tangent_angle(a, b)
    c = a - b
    c_norm = c / LA.norm(c)
    ans = c_norm * theta

    return ans[0], ans[1]


#カメラの角度を決める
def camera_angle(dist, cw, ch, pw, ph, sw, sh, camera_fov_w, camera_fov_h):
    px1 = -pw / 2
    sx2 = sw / 2
    py1 = -ph / 2
    sy2 = sh / 2
    cp = np.array([pw/2, ph/2, dist])
    cf = np.array([dist*math.tan(math.radians(camera_fov_w/2)), dist*math.tan(math.radians(camera_fov_h/2)), dist])
    pat_dif = diff_angle(cp, cf)

    cs2 = np.array([-sw / 2, -sh / 2, dist])
    cf2 = np.array([-cf[0], -cf[1], dist])
    spa_dif = diff_angle(cs2, cf2)

    if (cs2[0] < cf2[0] and cs2[1] < cf2[1]):
        ans = pat_dif
    else:
        ans = spa_dif

    cs = np.array([sw / 2, sh / 2, dist])
    cc = np.array([dist*math.tan(math.radians(ans[0])), dist*math.tan(math.radians(ans[1])), dist])
    area_dif = diff_angle(cc, cs)

    # print(cp, cf, pat_dif, cs2, cf2, spa_dif, ans, area_dif)
    print(area_dif)

    return ans[0], ans[1], area_dif[0], area_dif[1]

#カメラ画角とキャリブレーション有効範囲を比較
    #ｘ方向について
    #if px1 + cw > sx2:

    #else:
    # angle_pan = math.degrees(math.atan((dist*math.tan(math.radians(camera_fov_h/2))-ph/2)/(-dist*math.tan(math.radians(camera_fov_w/2))+pw/2)))
    # angle_tilt = math.degrees(math.atan((-dist*math.tan(math.radians(camera_fov_w/2))+pw/2)/(-dist*math.tan(math.radians(camera_fov_h/2))-ph/2)))
    #
    #
    #
    #
    # return (angle_pan, angle_tilt)

if __name__=='__main__':
  targets = {
      "Galileo":{"panel_w":420, "panel_h":300, "space_w":280, "space_h":180},
      "Newton":{"panel_w":800, "panel_h":600, "space_w":520, "space_h":340},
  }
  #camera_fov_w = 55.0 /2
  #camera_fov_h = 43.0 /2
  camera_fov_w = 67.72 #UF1-8
  camera_fov_h = 53.41

  target_name = "Galileo"
  pw = targets[target_name]["panel_w"] + 20
  ph = targets[target_name]["panel_h"] + 20
  sw = targets[target_name]["space_w"] - 20
  sh = targets[target_name]["space_h"] - 20

  # 150から1000までを適切に10等分するbetaを得る
  first_position = 150
  last_position = 1000
  interval = 5
  dist = first_position
  beta = getbeta(first_position,last_position)/interval

  for i in range (interval +1):
    increment = delta(dist, beta)
    #print(increment)

    cw = 2 * dist * math.tan(math.radians(camera_fov_w / 2))
    ch = 2 * dist * math.tan(math.radians(camera_fov_h / 2))

    cpos = camera_angle(dist, cw, ch, pw, ph, sw, sh,camera_fov_w, camera_fov_h)
    pan = cpos[0]
    tilt = cpos[1]
    area_x = cpos[2]
    area_y = cpos[2]

    #print("mov", 921-dist, ", ", pan, ", ", tilt)

    print("mov", dist-139, ", ", pan, ", ", tilt)
    print("snap ${pattern1_target_image}, 1")
    print("mov", dist-139, ", ", -pan, ", ", tilt)
    print("snap ${pattern1_target_image}, 1")
    print("mov", dist-139, ", ", pan, ", ", -tilt)
    print("snap ${pattern1_target_image}, 1")
    print("mov", dist-139, ", ", -pan, ", ", -tilt)
    print("snap ${pattern1_target_image}, 1")
    dist = dist + increment
    # print(dist)