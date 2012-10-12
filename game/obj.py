import pygame as pg

from conf import conf
from util import ir
import objhelpers

#   object methods:
# interact(): perform basic action on object
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use(obj): use held object on object obj


class Road (object):
    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        self.rect = pg.Rect(0 / sx, 200 / sy, 600 / sx, 200 / sy)

    def interact (self):
        self.level.say('a busy road.')


class Obj (object):
    def __init__ (self, level, pos = None, dirn = 1):
        self.level = level
        self.pos = pos if pos is None else list(pos)
        self.dirn = dirn
        img = level.game.img(self.__class__.__name__.lower() + '.png')
        self.imgs = [pg.transform.rotate(img, angle)
                     for angle in (90, 0, -90, -180)]
        self._offset = [ir(float(t_s - i_s) / 2) for t_s, i_s in
                        zip(conf.TILE_SIZE, img.get_size())]

    def draw (self, screen):
        x, y = self.pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.imgs[self.dirn], (x * sx + ox, y * sy + oy))


class Frog (Obj):
    def __init__ (self, *args, **kw):
        Obj.__init__(self, *args, **kw)
        self._last_pos = list(self.pos)
        self._queue_t = 0
        self._queue = []
        self._item = None

    def queue (self, f, *args, **kw):
        self._queue.append((f, args, kw))

    def _move (self, *dest):
        p = self.pos
        self.pos = dest
        for i in (0, 1):
            d = dest[i] - p[i]
            if d:
                self.dirn = i + (2 if d > 0 else 0)
                break
        return conf.FROG_MOVE_TIME

    def move (self, *dest):
        # queue individual move calls
        pass

    def _investigate (self, obj):
        if self._item is None:
            obj.interact()
        else:
            self._item.use(obj)

    def investigate (self, obj):
        if isinstance(obj, tuple):
            # empty location: just move there
            self.move(*obj)
        else:
            self.move(*obj.pos)
            self.queue(self._investigate, obj)

    def update (self):
        if self._queue_t <= 0:
            if self._queue:
                f, args, kw = self._queue.pop(0)
                self._queue_t = f(*args, **kw) or 1
        self._queue_t -= 1

    def pre_draw (self):
        l, p = self._last_pos, self.pos
        if l != p:
            self.level.change_tile(l, p)
            self._last_pos = p

    def draw (self, screen):
        x, y = self.pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.imgs[self.dirn], (x * sx + ox, y * sy + oy))


class Holdable (Obj):
    holdable = True

    def __init__ (self, *args, **kw):
        self.held = False
        if kw.get('held', False):
            self.grab()

    def grab (self):
        if not self.held:
            self.held = True
            self.level.change_tile(self.pos)
            self.level.rm_obj(self.pos)
            self.pos = None

    def drop (self, pos):
        if self.held:
            self.held = False
            self.level.change_tile(pos)
            self.level.add_obj(self, pos)
            self.pos = list(pos)

    def use (self, obj):
        return NotImplemented


class Static (Obj):
    holdable = False


class Basket (Static):
    def interact (self):
        self.level.say('it\'s a basket containing some things.')


class Banana (Holdable):
    def use (self, obj):
        if self.held and isinstance(obj, Frog):
            obj.destroy(self)
            obj.drop(BananaPeel(self.level))
            self.level.say('I eat the banana.')
