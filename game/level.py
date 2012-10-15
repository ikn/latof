from math import ceil

import pygame as pg

from conf import conf
import obj as obj_module
from frog import Frog


class Road (object):
    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        self.rect = pg.Rect(0, 200 / sy, 600 / sx, 200 / sy)

    def crash (self, pos):
        print 'crash', pos


class Level (object):
    def __init__ (self, game, event_handler, ident = 0):
        self.game = game
        event_handler.add_event_handlers({
            pg.MOUSEBUTTONDOWN: self._click
        })
        # variables
        self._last_ident = self.ident = ident
        self._changed = set()
        self._changed_rects = set()
        self._held_sfc = pg.Surface(conf.TILE_SIZE).convert_alpha()
        self._held_sfc.fill(conf.UI_BG)
        # level-specific
        self.game.linear_fade(*conf.INIT_FADE)
        self.init()

    def init (self):
        if self.ident != self._last_ident:
            self.game.clear_caches()
        data = conf.LEVELS[self.ident]
        sx, sy = conf.LEVEL_SIZE
        self.objs = objs = [[[] for j in xrange(sx)] for i in xrange(sy)]
        self._road = Road(self)
        self.frog = Frog(self, data['frog pos'], data.get('frog dirn', 1))
        for pos, os in data['objs'].iteritems():
            if isinstance(os, basestring):
                os = (os,)
            objs[pos[0]][pos[1]] = [getattr(obj_module, obj)(self, pos)
                                    for obj in os]
        self.ui = {}
        self.update_held()
        self.dirty = True

    def restart (self):
        self.game.linear_fade(*conf.RESTART_FADE)
        self.game.scheduler.add_timeout(self.init, seconds = conf.RESTART_TIME)

    def _click (self, evt):
        if evt.button in conf.ACTION_SETS:
            if 'msg' in self.ui:
                self.change_rect(self.ui['msg'][1])
                del self.ui['msg']
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

    def add_obj (self, obj, pos):
        self.objs[pos[0]][pos[1]].append(obj)
        self.change_tile(pos)
        if self._road.rect.collidepoint(pos) and hasattr(obj, 'on_road'):
            obj.on_road(self.frog, self._road)

    def rm_obj (self, obj, pos = None):
        if pos is None:
            pos = obj.pos
        self.objs[pos[0]][pos[1]].remove(obj)
        self.change_tile(pos)

    def _add_ui (self, ident, sfc):
        rect = pg.Rect(conf.UI_POS[ident], sfc.get_size())
        tiles = self.change_rect(rect)
        if ident in self.ui:
            self.change_rect(self.ui[ident][1])
        self.ui[ident] = (sfc, rect, tiles)

    def update_held (self):
        sfc = self._held_sfc
        if self.frog.item is not None:
            sfc = sfc.copy()
            self.frog.item.draw(sfc, (0, 0))
        self._add_ui('held', sfc)

    def say (self, msg):
        sfc = self.game.render_text(
            'main', msg, conf.FONT_COLOUR, width = conf.MSG_WIDTH,
            bg = conf.UI_BG, pad = conf.MSG_PADDING
        )[0]
        self._add_ui('msg', sfc)

    def update (self):
        self.frog.update()

    def _draw_objs (self, screen, objs):
        last = None
        # draw non-solid
        for o in objs:
            if isinstance(o, obj_module.OneTileObj):
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
        ui = self.ui
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
            for sfc, rect, tiles in ui.itervalues():
                screen.blit(sfc, rect)
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
                for sfc, rect, ui_tiles in ui.itervalues():
                    if tile in ui_tiles:
                        screen.blit(sfc, (x, y), r.move(-rect[0], -rect[1]))
            rtn = list(self._changed_rects)
        else:
            rtn = False
        self._changed = set()
        self._changed_rects = set()
        return rtn
