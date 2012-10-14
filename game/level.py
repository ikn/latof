from math import ceil

import pygame as pg

from conf import conf
import obj as obj_module
from frog import Frog


class Level (object):
    def __init__ (self, game, event_handler, ident = 0):
        self.game = game
        event_handler.add_event_handlers({
            pg.MOUSEBUTTONDOWN: self._click
        })
        # variables
        self.ident = ident
        self._changed = set()
        self._changed_rects = set()
        # level-specific
        self.init()

    def init (self):
        self.game.clear_caches()
        data = conf.LEVELS[self.ident]
        sx, sy = conf.LEVEL_SIZE
        self.objs = objs = [[[] for j in xrange(sx)] for i in xrange(sy)]
        self._road = obj_module.Road(self)
        self.frog = Frog(self, data['frog pos'], data.get('frog dirn', 1))
        for pos, os in data['objs'].iteritems():
            if isinstance(os, basestring):
                os = (os,)
            objs[pos[0]][pos[1]] = [getattr(obj_module, obj)(self, pos)
                                    for obj in os]
        self.msg = None
        self.dirty = True

    def _click (self, evt):
        if evt.button in conf.ACTION_SETS:
            if self.msg is not None:
                self.change_rect(self.msg[1])
                self.msg = None
            pos = tuple(x / s for x, s in zip(evt.pos, conf.TILE_SIZE))
            self.frog.action(conf.ACTION_SETS[evt.button],
                             self.objs[pos[0]][pos[1]], pos)

    def change_tile (self, tile):
        self._changed.add(tuple(tile))
        sx, sy = conf.TILE_SIZE
        self._changed_rects.add((sx * tile[0], sy * tile[1], sx, sy))

    def change_rect (self, rect):
        sz = conf.TILE_SIZE
        x0, y0 = [int(x / s) for x, s in zip(rect[:2], sz)]
        x1, y1 = [int(ceil(float(rect[i] + rect[i + 2]) / s))
                  for i, s in enumerate(sz)]
        tiles = sum(([(i, j) for j in xrange(y0, y1)] for i in xrange(x0, x1)),
                    [])
        self._changed.update(tiles)
        r = (x0 * sz[0], y0 * sz[1], (x1 - x0) * sz[0], (y1 - y0) * sz[0])
        self._changed_rects.add(r)
        return tiles

    def add_obj (self, o, pos):
        self.objs[pos[0]][pos[1]].append(o)
        self.change_tile(pos)

    def rm_obj (self, obj, pos = None):
        if pos is None:
            pos = obj.pos
        self.objs[pos[0]][pos[1]].remove(obj)
        self.change_tile(pos)

    def say (self, msg):
        pad = conf.MSG_PADDING
        sfc = self.game.render_text(
            'main', msg, conf.FONT_COLOUR, width = conf.RES[0],
            bg = conf.FONT_BG, pad = pad
        )[0]
        assert self.msg is None, self.msg
        rect = pg.Rect((0, 0), sfc.get_size())
        tiles = self.change_rect(rect)
        self.msg = (sfc, rect, tiles)

    def update (self):
        self.frog.update()

    def _draw_objs (self, screen, objs):
        last = None
        # draw non-solid
        for o in objs:
            if isinstance(o, obj_module.Placeable):
                if o.solid:
                    last = o
                else:
                    o.draw(screen)
        # draw solid
        if last is not None:
            last.draw(screen)

    def draw (self, screen):
        bg = self.game.img('bg.png')
        draw_objs = self._draw_objs
        msg = self.msg is not None
        if msg:
            msg_sfc, msg_rect, msg_tiles = self.msg
            msg_offset = (-msg_rect[0], -msg_rect[1])
        if self.dirty:
            self.dirty = False
            # background
            screen.blit(bg, (0, 0))
            # objects
            for col in self.objs:
                for objs in col:
                    if objs:
                        draw_objs(screen, objs)
            # text
            if msg:
                screen.blit(msg_sfc, msg_rect)
            rtn = True
        elif self._changed:
            objs = self.objs
            sx, sy = conf.TILE_SIZE
            rects = []
            for tile in self._changed:
                x, y = tile
                this_objs = objs[x][y]
                x *= sx
                y *= sy
                r = pg.Rect(x, y, sx, sy)
                rects.append(r)
                screen.blit(bg, (x, y), r)
                draw_objs(screen, this_objs)
                # text
                if msg and tile in msg_tiles:
                    screen.blit(msg_sfc, (x, y), r.move(msg_offset))
            rtn = list(self._changed_rects)
        else:
            rtn = False
        self._changed = set()
        self._changed_rects = set()
        return rtn
