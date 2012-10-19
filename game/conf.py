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
    MUSIC_VOLUME = dd(.5) # per-backend
    SOUND_VOLUME = .5
    EVENT_ENDMUSIC = pg.USEREVENT
    SOUND_VOLUMES = dd(1)
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
    ROAD_POS = (0, 200)
    ROAD_SIZE = (600, 200)
    TILE_ROAD_POS = (0, 5)
    TILE_ROAD_SIZE = (15, 5)
    ROAD_LANES = (231, 275, 327, 375)
    ROAD_LANE_WIDTH = 40
    ROAD_DIRN = 1 # 1 for left, -1 for right
    CAR_SPEED = 600 # pixels per second
    CAR_GAP = {'moving': 50, 'stopped': 5, 'crashed': 0}
    FROG_MOVE_TIME = .1
    INIT_FADE = [(0, 0, 0), (False, 1)]
    RESTART_TIME = 1.5
    RESTART_FADE = [False, ((0, 0, 0), 1), ((0, 0, 0), 1.5), (False, 2.5)]

    # UI
    # per-backend, each a {key: value} dict to update fonthandler.Fonts with
    FONT_SIZE = 17
    REQUIRED_FONTS = dd({'main': ('JacquesFrancois.ttf', FONT_SIZE)})
    FONT_COLOUR = (255, 230, 200)
    UI_BG = (30, 20, 0, 150)
    UI_POS = {'msg': (0, 0), 'held': (RES[0] - TILE_SIZE[0], 0)}
    MSG_WIDTH = RES[0] - TILE_SIZE[0] - 5
    MSG_PADDING = (10, 3, 10, 5)

    # levels
    LEVELS = [{
        'frog pos': (7, 12),
        'objs': {
            (3, 13): ('PuddleOfOil', 'Basket'),
            (3, 12): 'PicnicBlanket'
        }
    }]


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
