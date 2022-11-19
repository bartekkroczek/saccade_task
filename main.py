#!/usr/bin/env python
# -*- coding: latin-1 -*-

"""
Psychopy procedure for antisaccade and prosaccade task.
Fill free to use, but remember to cite.
"""
from __future__ import annotations

import atexit
import codecs
import copy
import csv
import random
from datetime import datetime
from os.path import join
from typing import List, Tuple, Any

import yaml
from psychopy import visual, event, logging, gui, core

from Adaptives.NUpNDown import NUpNDown
from misc.screen_misc import get_screen_res, get_frame_rate

__author__ = "Bartek Kroczek"
__copyright__ = "Copyright 2022, Cognitive Processes Labolatory at Jagiellonian University, Cracow, Poland"
__credits__ = ["Bartek Kroczek", "Adam Chuderski"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Bartek Kroczek"
__email__ = "bartek.kroczek@doctoral.uj.edu.pl"
__status__ = "Preparation"

# GLOBALS

LAST_STIM = ''
RESULTS = list()
RESULTS.append(['PART_ID', 'Block_no', 'Trial_no', 'Block_type', 'Trial_type', 'CSI', 'Stim_letter', 'Key_pressed',
                'letter_choose', 'Rt', 'Corr', 'Stimulus Time'])


@atexit.register
def save_beh_results() -> None:
    now = datetime.now()
    path = join('results', f'{PART_ID}_{now.strftime("%d-%m-%Y_%H-%M-%S")}_beh.csv')
    with open(path, 'w', encoding='utf-8') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def show_image(win: visual.Window, file_name: str, size: List[int, int], key: str = 'f7') -> None:
    """

    Args:
        win: psychopy.visual.window object. Main procedure window.
        file_name: Name of a picture to display.
        size: X and Y dim size for picture, in Pixels.
        key: Which key terminate image and moves procedures forward.

    Returns:
        None.

    """
    image = visual.ImageStim(win=win, image=file_name, interpolate=True, size=size)
    image.draw()
    win.flip()
    clicked = event.waitKeys(keyList=[key, 'return', 'space'])
    if clicked[0] == key:
        logging.critical('Experiment finished by user! {} pressed.'.format(clicked))
        exit(0)
    win.flip()


def read_text_from_file(file_name: str, insert: str = '') -> str:
    """
    Method that read message from text file, and optionally add some dynamically generate info
    Args:
        file_name: Name of a file to display
        insert: Addon

    Returns:
        String contains message to display on screen.
    """

    if not isinstance(file_name, str):
        abort_with_error('Problem with file reading, filename must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key: str = 'f7') -> None:
    """
    Check if user wants to terminate a procedure.
    Args:
        key: Key that terminates

    Returns:
        None.
    """
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win: visual.Window, file_name: str, insert: str = '', key: str = 'f7') -> None:
    """
    Display info on screen.
    Args:
        key: Key that terminates procedure
        win: Procedure main window.
        file_name: String contains name of a file to display.
        insert: Optional msg to add into message.

    Returns:
        None.
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    clicked = event.waitKeys(keyList=['f7', 'return', 'space'])
    if clicked[0] == key:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err: str) -> None:
    """
    Log error, rise exception
    Args:
        err: Error message.

    Returns:
        None.
    """
    logging.critical(err)
    raise Exception(err)


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global
    # === Dialog popup ===
    info = {'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Saccade task.')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    # === Procedure init ===
    PART_ID = info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.LogFile(join('results', PART_ID + '.log'), level=logging.INFO)  # errors logging

    clock: core.Clock = core.Clock()
    conf: dict = yaml.load(open('config.yaml', encoding='utf-8'), Loader=yaml.SafeLoader)

    win = visual.Window(list(SCREEN_RES.values()), fullscr=True, monitor='testMonitor', units='pix',
                        screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE: int = get_frame_rate(win)
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText('Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    # === stimuli preparation ===
    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    que = visual.Circle(win, radius=conf['QUE_RADIUS'], fillColor=conf['QUE_COLOR'], lineColor=conf['QUE_COLOR'])
    stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])
    mask = visual.ImageStim(win, image=join('images', 'mask4.png'), size=(conf['STIM_SIZE'], conf['STIM_SIZE']))
    separator = [' ' * conf['REACTION_KEYS_SEP']] * len(conf['REACTION_KEYS'])
    question_frame = visual.TextStim(win, text="".join(["".join(x) for x in zip(conf['STIM_LETTERS'], separator)]),
                                     height=30,
                                     pos=(100, -300), color=conf['FIX_CROSS_COLOR'], wrapWidth=10000)
    question_label = visual.TextStim(win, text="".join(["".join(x) for x in zip(conf['REACTION_KEYS'], separator)]),
                                     height=30, pos=(100, -330), color=conf['FIX_CROSS_COLOR'], wrapWidth=10000)
    trial_no = 1

    show_info(win, join('.', 'messages', 'hello.txt'))
    show_info(win, join('.', 'messages', 'before_training.txt'))

    # === Training ===
    for block_no, (no_trials, stim_time, block_type) in enumerate(conf['TRAINING_BLOCKS'], start=1):
        show_info(win, join('.', 'messages', f'before_{block_type}_block.txt'))
        for _ in range(no_trials):
            csi = random.choice(conf['CSI_POSSIBLE'])
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, block_type, fix_cross, csi, que, stim,
                                                                   clock, question_frame, question_label, mask,
                                                                   stim_time)
            RESULTS.append(
                [PART_ID, block_no, trial_no, block_type, 'train', csi, stim_letter, key_pressed, choice, rt, corr,
                 stim_time])
            feedb = "Poprawnie" if corr else "Niepoprawnie"
            feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])
            feedb.draw()
            win.flip()
            core.wait(1)
            win.flip()
            trial_no += 1

    # === Adaptively stim times ===
    start_stim_times = dict()
    for block_type in conf['ADAPTIVE_BLOCKS']:
        adaptive = NUpNDown(start_val=conf[f'START_STIM_TIME_{block_type}'], max_revs=conf['MAX_REVS'],
                            n_up=conf['N_UP'], n_down=conf['N_DOWN'])
        show_info(win, join('.', 'messages', f'before_{block_type}_block.txt'))
        for idx, stim_time in enumerate(adaptive, 1):
            csi = random.choice(conf['CSI_POSSIBLE'])
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, block_type, fix_cross, csi, que, stim,
                                                                   clock, question_frame, question_label, mask,
                                                                   stim_time)
            adaptive.set_corr(corr)
            RESULTS.append(
                [PART_ID, '-', trial_no, block_type, 'adaptive', csi, stim_letter, key_pressed, choice, rt, corr,
                 stim_time])
            feedb = "Poprawnie" if corr else "Niepoprawnie"
            feedb = visual.TextStim(win, text=feedb, height=50, color=conf['FIX_CROSS_COLOR'])
            feedb.draw()
            win.flip()
            core.wait(1)
            win.flip()

            trial_no += 1
        start_stim_times[block_type] = adaptive.get_curr_val()

    # === Experiment ===
    show_info(win, join('.', 'messages', 'before_experiment.txt'))
    for block_no, (no_trials, block_type) in enumerate(random.choice(conf['EXP_BLOCKS']), start=1):
        stim_times = copy.copy(start_stim_times)
        show_info(win, join('.', 'messages', f'before_{block_type}_block.txt'))
        for _ in range(conf['INTRA_BLOCK_TRAINING']):
            csi = random.choice(conf['CSI_POSSIBLE'])
            stim_time = int(1.5 * stim_times[block_type])
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, block_type, fix_cross, csi, que, stim,
                                                                   clock, question_frame, question_label, mask,
                                                                   stim_time)
            RESULTS.append(
                [PART_ID, block_no, trial_no, block_type, 'intra_train', csi, stim_letter, key_pressed, choice, rt,
                 corr,
                 stim_time])
            trial_no += 1
            # jitter after trial
            wait_time_in_secs: float = random.choice(range(*conf['REST_TIME_RANGE'])) / conf['FRAME_RATE']
            core.wait(wait_time_in_secs)
        csi_list = random.choices(conf['CSI_POSSIBLE'], k=no_trials)  # sampling WITH replacement
        last_trial_corr: bool = False

        # csi works functionally as a jitter in a range 400-800 ms, but is recorded for future testings.
        for csi in csi_list:
            stim_time = stim_times[block_type]
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, block_type, fix_cross, csi, que, stim,
                                                                   clock, question_frame, question_label, mask,
                                                                   stim_time)
            RESULTS.append([PART_ID, block_no, trial_no, block_type, 'exp', csi, stim_letter, key_pressed, choice, rt,
                            corr, stim_time])
            trial_no += 1
            #  2-Up/1-down Adaptation WITH LIMIT OF TRIALS
            # it was far easier to add it manually than make third nesting loop and make new class for NupNDownWTHLIMIT
            if corr and last_trial_corr:
                last_trial_corr = False
                stim_times[block_type] -= 1
            elif corr and (not last_trial_corr):
                last_trial_corr = True
            elif not corr:
                last_trial_corr = False
                stim_times[block_type] += 1
            # jitter after trial
            wait_time_in_secs: float = random.choice(range(*conf['REST_TIME_RANGE'])) / conf['FRAME_RATE']
            core.wait(wait_time_in_secs)

        show_image(win, join('images', 'break.jpg'), size=[SCREEN_RES['width'], SCREEN_RES['height']])

        # === Cleaning time ===
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(win: visual.Window, conf: dict, block_type: str, fix_cross, csi: int, que, stim, clock: core.Clock,
              question_frame: visual.TextStim, question_label: visual.TextStim, mask, stim_time: int
              ) -> Tuple[str | Any, float | Any, Any, str | Any, bool]:
    global LAST_STIM
    que_pos = random.choice([-conf['STIM_SHIFT'], conf['STIM_SHIFT']])  # Que on left or right side of a screen
    if block_type == 'AS':  # stim and mask on the opposite side of que
        stim.pos = [-que_pos, 0]
        mask.pos = [-que_pos, 0]
    elif block_type == 'PS':  # stim, mask and que on this same side of a screen
        stim.pos = [que_pos, 0]
        mask.pos = [que_pos, 0]
    else:
        raise ValueError('Only prosaccadic and antysaccadic trials suported.')

    stim.text = random.choice(conf['STIM_LETTERS'].replace(LAST_STIM, ''))
    LAST_STIM = stim.text

    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()

    for _ in range(csi):
        win.flip()

    for _ in range(conf['QUE_FREQ']):  # que is not static, it is blinking and moving on a screen
        if _ % 2 == 0:
            que.pos = [que_pos + conf['QUE_SHIFT'], 0]
        else:
            que.pos = [que_pos - conf['QUE_SHIFT'], 0]
        for _ in range(conf['QUE_SPEED']):
            que.draw()
            win.flip()

    win.callOnFlip(clock.reset)
    event.clearEvents()

    for _ in range(stim_time):
        stim.draw()
        win.flip()

    reaction: List = []  # Prev errors from zero iterations of a loop below
    for _ in range(conf['MASK_TIME']):
        reaction = event.getKeys(keyList=list(conf['REACTION_KEYS']), timeStamped=clock)
        if reaction:
            break
        mask.draw()
        win.flip()

    if not reaction:
        question_frame.draw()
        question_label.draw()
        win.flip()
        reaction = event.waitKeys(keyList=list(conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME'] / 60,
                                  timeStamped=clock)
    if reaction:
        key_pressed, rt = reaction[0]
        choice = dict(zip(conf['REACTION_KEYS'], conf['STIM_LETTERS']))[key_pressed]
        corr = stim.text == choice
    else:
        key_pressed = 'no_key'
        rt = -1.0
        corr = False
        choice = 'no_letter'
    win.flip()

    return key_pressed, rt, stim.text, choice, corr


if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
