from platform import system
import os
from os.path import sep, expanduser, join as join_path
from collections import defaultdict
from glob import glob

import pygame as pg

import settings
from util import dd, ir


class Conf (object):

    IDENT = 'latof'
    USE_SAVEDATA = False
    USE_FONTS = True

    # save data
    SAVE = ()
    # need to take care to get unicode path
    if system() == 'Windows':
        try:
            import ctypes
            n = ctypes.windll.kernel32.GetEnvironmentVariableW(u'APPDATA', None, 0)
            if n == 0:
                raise ValueError()
        except Exception:
            # fallback (doesn't get unicode string)
            CONF_DIR = os.environ[u'APPDATA']
        else:
            buf = ctypes.create_unicode_buffer(u'\0' * n)
            ctypes.windll.kernel32.GetEnvironmentVariableW(u'APPDATA', buf, n)
            CONF_DIR = buf.value
        CONF_DIR = join_path(CONF_DIR, IDENT)
    else:
        CONF_DIR = join_path(os.path.expanduser(u'~'), '.config', IDENT)
    CONF = join_path(CONF_DIR, 'conf')

    # data paths
    DATA_DIR = ''
    IMG_DIR = DATA_DIR + 'img' + sep
    SOUND_DIR = DATA_DIR + 'sound' + sep
    MUSIC_DIR = DATA_DIR + 'music' + sep
    FONT_DIR = DATA_DIR + 'font' + sep

    # display
    WINDOW_ICON = None #IMG_DIR + 'icon.png'
    WINDOW_TITLE = 'Life and Times of Frog?'
    MOUSE_VISIBLE = dd(True) # per-backend
    FLAGS = 0
    FULLSCREEN = False
    RESIZABLE = False # also determines whether fullscreen togglable
    RES_W = (600, 600)
    RES_F = pg.display.list_modes()[0]
    RES = RES_W
    MIN_RES_W = (320, 180)
    ASPECT_RATIO = None

    # timing
    FPS = dd(60) # per-backend

    # debug
    PROFILE_STATS_FILE = '.profile_stats'
    DEFAULT_PROFILE_TIME = 5

    # input
    KEYS_NEXT = (pg.K_RETURN, pg.K_SPACE, pg.K_KP_ENTER)
    KEYS_BACK = (pg.K_ESCAPE, pg.K_BACKSPACE)
    KEYS_MINIMISE = (pg.K_F10,)
    KEYS_FULLSCREEN = (pg.K_F11, (pg.K_RETURN, pg.KMOD_ALT, True),
                    (pg.K_KP_ENTER, pg.KMOD_ALT, True))
    KEYS_LEFT = (pg.K_LEFT, pg.K_a, pg.K_q)
    KEYS_RIGHT = (pg.K_RIGHT, pg.K_d, pg.K_e)
    KEYS_UP = (pg.K_UP, pg.K_w, pg.K_z, pg.K_COMMA)
    KEYS_DOWN = (pg.K_DOWN, pg.K_s, pg.K_o)
    KEYS_DIRN = (KEYS_LEFT, KEYS_UP, KEYS_RIGHT, KEYS_DOWN)

    ACTION_SETS = {1: ('inspect', 'move'), 2: ('drop', 'move'),
                   3: ('grab', 'use', 'drop')}

    # audio
    MUSIC_AUTOPLAY = True # just pauses music
    MUSIC_VOLUME = dd(.2) # per-backend
    SOUND_VOLUME = .5
    EVENT_ENDMUSIC = pg.USEREVENT
    SOUND_VOLUMES = dd(1, crash = 1.5)
    # generate SOUNDS = {ID: num_sounds}
    SOUNDS = {}
    ss = glob(join_path(SOUND_DIR, '*.ogg'))
    base = len(join_path(SOUND_DIR, ''))
    for fn in ss:
        fn = fn[base:-4]
        for i in xrange(len(fn)):
            if fn[i:].isdigit():
                # found a valid file
                ident = fn[:i]
                if ident:
                    n = SOUNDS.get(ident, 0)
                    SOUNDS[ident] = n + 1

    # gameplay
    TILE_SIZE = (40, 40)
    LEVEL_SIZE = (RES[0] / TILE_SIZE[0], RES[1] / TILE_SIZE[1])
    FROG_MOVE_TIME = .1
    # road
    ROAD_POS = (0, 200)
    ROAD_SIZE = (600, 200)
    TILE_ROAD_POS = (0, 5)
    TILE_ROAD_SIZE = (15, 5)
    ROAD_LANES = (231, 275, 327, 375)
    ROAD_LANE_WIDTH = 40
    ROAD_DIRN = 1 # 1 for left, -1 for right
    CAR_SPEED = 600 # pixels per second
    CAR_SPEED_JITTER = 20 # mean variation of car speed (pixels per second)
    CAR_GAP = {'moving': 50, 'stopped': 5, 'crashed': 0}
    CAR_WEIGHTINGS = {
        'car0': (1, {
            'red': 1,
            'blue': 1,
            'yellow': .3
        }), 'van0': (.3, {
            'white': 1
        }), 'lorry0': (.2, {
            'blue': 1,
            'orange': .5
        })
    }
    CRASH_POS_JITTER = 50 # mean pixels displaced
    CRASH_FOLLOWTHROUGH = 30 # pixels moved past crash point
    # cutscenes
    b = (0, 0, 0)
    INIT_FADE = [b, (False, 1)]
    # each is (event_time, fade[, restore_control_time = event_time)
    RESTART = (1.5, [False, (b, 1), (b, 1.5), (False, 2.5)])
    PROGRESS = (1.5, [False, (b, 1), (b, 1.5), (False, 2.5)])
    END = (1, [False, (b, 1)])
    CRASH = (5, [False, (b, 1), (b, 11), (False, 12)], 3)
    CRASH_STOP_TRAFFIC_SND_TIME = 1

    # UI
    # per-backend, each a {key: value} dict to update fonthandler.Fonts with
    FONT = 'JacquesFrancois.ttf'
    MSG_FONT_SIZE = 17
    LABEL_FONT_SIZE = 13
    REQUIRED_FONTS = dd({
        'msg': (FONT, MSG_FONT_SIZE),
        'label': (FONT, LABEL_FONT_SIZE),
    })
    FONT_COLOUR = (255, 230, 200)
    UI_BG = (30, 20, 0, 150)
    UI_POS = {'msg': (0, 0), 'held': (RES[0] - TILE_SIZE[0], 0)}
    MSG_WIDTH = RES[0] - TILE_SIZE[0] - 5
    MSG_PADDING = (10, 3, 10, 5)
    LABEL_PADDING = (5, 1)
    LABEL_OFFSET = (10, -5)

    # levels
    LEVELS = [{
        'frog pos': (7, 12),
        'objs': {
            (3, 13): ('PuddleOfOil', 'Basket'),
            (2, 13): 'PicnicBlanket'
        }
    }, {
        'frog pos': (7, 12),
        'objs': {
            (10, 10): 'TrafficLight'
        }
    }]
    # level 1
    CIRCUIT = {
        'rect': (0, 400, 600, 200),
        'size': (15, 5),
        'pwr': (6, 4),
        'states': [(5, 4), (5, 3), (6, 3), (7, 3)],
        'initial dirn': 0,
        'wires': [((6, 4), (5, 4)), ((5, 4), (5, 3)), ((5, 3), (6, 3)),
                  ((6, 3), (7, 3)), ((7, 3), (7, 4)), ((7, 4), (6, 4))]
    }
    CIRCUIT_PWR_COLOUR = (0, 0, 0)
    CIRCUIT_STATE_COLOURS = [(0, 255, 0), (255, 150, 0), (255, 0, 0),
                             (255, 150, 0)]
    CIRCUIT_MOVE_TIME = .1
    CIRCUIT_INITIAL_STATE = 0
    TRAFFIC_LIGHT_STOP_STATES = (2,)


def translate_dd (d):
    if isinstance(d, defaultdict):
        return defaultdict(d.default_factory, d)
    else:
        # should be (default, dict)
        return dd(*d)
conf = dict((k, v) for k, v in Conf.__dict__.iteritems()
            if k.isupper() and not k.startswith('__'))
types = {
    defaultdict: translate_dd
}
if Conf.USE_SAVEDATA:
    conf = settings.SettingsManager(conf, Conf.CONF, Conf.SAVE, types)
else:
    conf = settings.DummySettingsManager(conf, types)
