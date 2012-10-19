from math import ceil

import pygame as pg

from conf import conf
import obj as obj_module
from frog import Frog
from road import Road

TILE_SIZE = conf.TILE_SIZE
LEVEL_SIZE = conf.LEVEL_SIZE


class Overlay (object):
    def __init__ (self, level, sfc, pos):
        self.level = level
        self.sfc = sfc
        self.rect = pg.Rect(pos, sfc.get_size())
        self.tiles = []

    def _update (self):
        self.tiles = self.level.change_rect(self.rect)

    def _set_rect (self, r1):
        level = self.level
        r0 = self.rect
        self.rect = r1
        r = r0.union(r1)
        if r0[2] * r0[3] + r1[2] * r1[3] < r[2] * r[3]:
            level.change_rect(r0)
            self.tiles = level.change_rect(r1)
        else:
            level.change_rect(r)
            self.tiles = level.rect_tiles(r)

    def show (self):
        os = self.level.overlays
        if self not in os:
            os.append(self)
            self._update()
        return self

    def hide (self):
        os = self.level.overlays
        if self in os:
            os.remove(self)
            self._update()
            self.tiles = []

    def set_sfc (self, sfc):
        self.sfc = sfc
        self._set_rect(pg.Rect(pos, sfc.get_size()))

    def move (self, dx, dy):
        self._set_rect(self.rect.move(dx, dy))

    def draw (self, screen):
        screen.blit(self.sfc, self.rect)


class Level (object):
    def __init__ (self, game, event_handler, ident = 0):
        self.game = game
        event_handler.add_event_handlers({
            pg.MOUSEBUTTONDOWN: self._click,
            pg.MOUSEMOTION: self._move_mouse
        })
        self._held_sfc = pg.Surface(TILE_SIZE).convert_alpha()
        self._held_sfc.fill(conf.UI_BG)
        self._last_ident = self.ident = ident
        self._finished = False
        self.game.linear_fade(*conf.INIT_FADE)
        self.init()

    def init (self):
        self._changed = set()
        self._changed_rects = []
        self.overlays = []
        self.ui = {}
        self.dirty = True
        if self.ident != self._last_ident:
            self.game.clear_caches()
        data = conf.LEVELS[self.ident]
        sx, sy = LEVEL_SIZE
        self.objs = objs = [[[] for j in xrange(sx)] for i in xrange(sy)]
        self.road = Road(self)
        self.frog = Frog(self, data['frog pos'], data.get('frog dirn', 1))
        for pos, os in data['objs'].iteritems():
            if isinstance(os, basestring):
                os = (os,)
            objs[pos[0]][pos[1]] = [getattr(obj_module, obj)(self, pos)
                                    for obj in os]
        self.update_held()

    def restart (self):
        if not self._finished:
            self.game.linear_fade(*conf.RESTART_FADE)
            self.game.scheduler.add_timeout(self.init,
                                            seconds = conf.RESTART_TIME)

    def progress (self):
        self.ident += 1
        if self.ident >= len(conf.LEVELS):
            self.end()
        else:
            self.init()

    def end (self):
        if not self._finished:
            self._finished = True
            self.game.linear_fade(False, ((0, 0, 0), 1), persist = True)
            self.game.scheduler.add_timeout(self.game.quit_backend,
                                            seconds = 1)

    def _move_mouse (self, evt):
        pass

    def _click (self, evt):
        if evt.button in conf.ACTION_SETS:
            if 'msg' in self.ui:
                self.ui['msg'].hide()
            pos = tuple(x / s for x, s in zip(evt.pos, TILE_SIZE))
            self.frog.action(conf.ACTION_SETS[evt.button],
                             self.objs[pos[0]][pos[1]], pos)

    def change_tile (self, tile):
        self._changed.add(tuple(tile))

    def rect_tiles (self, rect):
        sx, sy = TILE_SIZE
        x, y, w, h = rect
        x0 = int(x / sx)
        y0 = int(y / sy)
        x1 = int(ceil(float(x + w) / sx))
        y1 = int(ceil(float(y + h) / sy))
        w, h = LEVEL_SIZE
        tiles = []
        for i in xrange(x0, x1):
            if 0 <= i < w:
                for j in xrange(y0, y1):
                    if 0 <= j < h:
                        tiles.append((i, j))
        return tiles

    def change_rect (self, rect):
        tiles = self.rect_tiles(rect)
        self._changed.update(tiles)
        self._changed_rects.append(rect)
        return tiles

    def add_obj (self, obj, pos):
        self.objs[pos[0]][pos[1]].append(obj)
        self.change_tile(pos)
        if self.road.tile_rect.collidepoint(pos) and \
           self.road.lane_moving(pos[1]) and hasattr(obj, 'on_crash'):
            obj.on_crash(self.frog, self.road)

    def rm_obj (self, obj, pos = None):
        if pos is None:
            pos = obj.pos
        self.objs[pos[0]][pos[1]].remove(obj)
        self.change_tile(pos)

    def _add_ui (self, ident, sfc, pos = None):
        if pos is None:
            pos = conf.UI_POS[ident]
        ui = self.ui
        if ident in ui:
            ui[ident].hide()
        ui[ident] = Overlay(self, sfc, pos).show()

    def _rm_ui (self, ident):
        ui = self.ui
        if ident in ui:
            overlay = ui[ident]
            del ui[ident]
            overlay.hide()

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
        self.road.update()
        self._changed.update(self.road.tiles)

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

    def draw_cars (self, screen):
        for dirn, cars in self.road.cars:
            for car in cars:
                car.draw(screen)

    def draw (self, screen):
        bg = self.game.img('bg.png')
        draw_objs = self._draw_objs
        overlays = self.overlays
        road = self.road
        if self.dirty:
            self.dirty = False
            # background
            screen.blit(bg, (0, 0))
            # objects
            for col in self.objs:
                for objs in col:
                    if objs:
                        draw_objs(screen, objs)
            # moving cars
            self.draw_cars(screen)
            # overlays
            for overlay in overlays:
                overlay.draw(screen)
            rtn = True
        else:
            # draw changed tiles
            rects = self._changed_rects
            in_road_rect = road.tile_rect.collidepoint
            objs = self.objs
            sx, sy = TILE_SIZE
            todo_os = set()
            # draw bg and objs
            screen.blit(bg, road.rect, road.rect)
            for x, y in road.tiles:
                draw_objs(screen, objs[x][y])
                for overlay in overlays:
                    if (x, y) in overlay.tiles:
                        todo_os.add(overlay)
            for tile in self._changed:
                if in_road_rect(tile):
                    continue
                x, y = tile
                this_objs = objs[x][y]
                x *= sx
                y *= sy
                r = (x, y, sx, sy)
                screen.blit(bg, (x, y), r)
                draw_objs(screen, this_objs)
                # add to changed rects
                rects.append(r)
                # add overlays
                for overlay in overlays:
                    if tile in overlay.tiles:
                        todo_os.add(overlay)
            self.draw_cars(screen)
            rects.append(road.rect)
            # draw overlays
            for overlay in todo_os:
                overlay.draw(screen)
            rtn = rects
        self._changed = set()
        self._changed_rects = []
        return rtn
