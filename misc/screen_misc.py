from collections import OrderedDict

from psychopy import logging


def get_screen_res():
    """
    Function that check current screen resolution. Raise OSError if can't recognise OS!
    * :return: (width, height) tuple with screen resolution.
    """
    import platform

    system = platform.system()
    if 'Linux' in system:
        import subprocess
        import re

        output = subprocess.Popen('xrandr | grep "\*" | cut -d" " -f4', shell=True, stdout=subprocess.PIPE)
        output = str(output.communicate()[0])[2:-3]
        valid_res = lambda x: re.match('^\d{3,4}x\d{3,4}$', x)
        if not valid_res(output):
            output = subprocess.Popen('xdpyinfo | grep dimensions | cut -d" " -f7', shell=True, stdout=subprocess.PIPE)
            output = str(output.communicate()[0])[2:-3]
        if not valid_res(output):
            logging.ERROR('OS ERROR - no way of determine screen res')
            raise OSError(
                "Humanity need more time to come up with efficient way of checking screen resolution of your hamster")
        width, height = map(int, output.split('x'))
    elif 'Windows' in system:
        from win32api import GetSystemMetrics

        width = int(GetSystemMetrics(0))
        height = int(GetSystemMetrics(1))
    else:  # can't recognise OS
        logging.ERROR('OS ERROR - no way of determine screen res')
        raise OSError("get_screen_res function can't recognise your OS")
    logging.info('Screen res set as: {}x{}'.format(width, height))
    return OrderedDict(width=width, height=height)


def get_frame_rate(win, legal_frame_rates=None):
    frame_rate = int(round(win.getActualFrameRate(nIdentical=30, nMaxFrames=200)))
    logging.info("Detected framerate: {} frames per sec.".format(frame_rate))
    if legal_frame_rates:
        assert frame_rate in legal_frame_rates, 'Illegal frame rate : {}.'.format(frame_rate)
    return frame_rate
