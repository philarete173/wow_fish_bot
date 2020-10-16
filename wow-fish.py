import sys, psutil, pyautogui, pyaudio, time, math, audioop, cv2
import numpy as np
from pywinauto import Application
from collections import deque

pyautogui.FAILSAFE = True

frame = [530, 490, 1370, 790] #frame on screen to search bobber
loc = [0, 0]
hex_color = 'D33A11'


def wowForFront():
    print('Searching for WoW process..')
    for pid in psutil.pids():
        if psutil.Process(pid).name().lower() == 'wow.exe':
            print('Found WoW')
            app = Application().connect(process=pid)
            app.top_window().set_focus()
            pyautogui.moveTo(960, 540, duration=1)


def firstPersonView():
    pyautogui.PAUSE = 0.5
    for _ in range(5):
        pyautogui.keyDown('end')
        pyautogui.keyUp('end')
    for _ in range(5):
        pyautogui.keyDown('home')
        pyautogui.keyUp('home')


def imagesearch(image, precision=0.8):
    im = pyautogui.screenshot()
    img_rgb = np.array(im)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(image, 0)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < precision:
        return [-1, -1]
    return max_loc


def checkBagSlots():
    print('Checking for empty bag slot...')
    pyautogui.hotkey('shift', 'b')
    slot_pos = imagesearch('images/slot.png')
    pyautogui.hotkey('shift', 'b')
    if slot_pos[0] != -1:
        print('There is empty slot in the bag')
        return True
    else:
        print('The bag is full')
        return False


def listenOutput(seconds):
    CHUNK = 1024  # CHUNKS of bytes to read each time from mic
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 48000
    THRESHOLD = 1500  # The threshold intensity that defines silence and noise signal (an int. lower than THRESHOLD is silence).
    SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where only silence is recorded. When this time passes the recording finishes and the file is delivered.
    #Open stream
    p = pyaudio.PyAudio()
    for i in range(0, p.get_host_api_count()):
        host_api_info = p.get_host_api_info_by_index(i)
        if 'WASAPI' in host_api_info['name']:
            output_device = p.get_device_info_by_index(host_api_info['defaultOutputDevice'])

    stream = p.open(format = FORMAT,
                    channels = output_device['maxOutputChannels'],
                    rate = int(output_device["defaultSampleRate"]),
                    input = True,
                    frames_per_buffer = CHUNK,
                    input_device_index = output_device["index"],
                    as_loopback = True)

    cur_data = ''  # current chunk  of audio data
    rel = int(RATE / CHUNK)
    slid_win = deque(maxlen=SILENCE_LIMIT * rel)

    success = False
    listening_start_time = time.time()
    print('Well, now we are listening for loud sounds...')
    while success == False:
        try:
            cur_data = stream.read(CHUNK)
            slid_win.append(math.sqrt(abs(audioop.avg(cur_data, 4))))
            if (sum([x > THRESHOLD for x in slid_win]) > 0):
                print('I heart something!')
                success = True
                break
            if time.time() - listening_start_time > seconds:
                print('I don\'t hear anything already {} seconds!'.format(seconds))
                break
        except:
            break
    stream.close()
    p.terminate()
    return success


def searchBobber(x1, y1, x2, y2, color, precision=0.8):
    start_time_search = time.time()
    width = x2 - x1
    height = y2 - y1
    while True:
        im = pyautogui.screenshot(region=(x1, y1, width, height))
        img = np.array(im)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2HSV)

        r = int(color[:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:], 16)
        h_min = np.array((b-20, g-20, r-20), np.uint8)
        h_max = np.array((b+20, g+20, r+20), np.uint8)
        #h_min = np.array((5, 20, 20), np.uint8) # feralas min
        #h_max = np.array((10, 30, 30), np.uint8) # feralas max
        mask = cv2.inRange(img_rgb, h_min, h_max)

        moments = cv2.moments(mask, 1)
        dM01 = moments['m01']
        dM10 = moments['m10']
        dArea = moments['m00']

        b_x = 0
        b_y = 0
        if dArea > 0:
            b_x = int(dM10 / dArea)
            b_y = int(dM01 / dArea)

        if [b_x, b_y] != [0, 0]:
            print('Found something similar!')
            return [b_x, b_y]
        if time.time() - start_time_search > 5:
            print('I can\'t find the bobber!')
            return [b_x, b_y]


if __name__ == '__main__':
    wowForFront()
    firstPersonView()
    empty_slot = checkBagSlots()
    catches = 0
    attempts = 1
    print('Let\'s start fishing!')
    while empty_slot:
        print('Attempt {}'.format(attempts))
        pyautogui.keyDown('1')
        pyautogui.keyUp('1')
        time.sleep(2)
        print('Searching for bobber...')
        loc = searchBobber(frame[0], frame[1], frame[2], frame[3], hex_color)
        if loc[0] != 0:
            bite = listenOutput(30)
            if bite:
                pyautogui.rightClick(x=loc[0] + frame[0], y=loc[1] + frame[1], duration=0.2)
                catches += 1
                time.sleep(2)
                loc = [0, 0]
            if catches % 20 == 0:
                empty_slot = checkBagSlots()
        attempts += 1
    if empty_slot == False:
        print('That\'s all, there was {} attempts with {} catches, quiting...'.format(attempts, catches))
        sys.exit()
