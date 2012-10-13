import pygame as pg

from conf import conf
import obj
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
        # level-specific
        self.init()

    def init (self):
        data = conf.LEVELS[self.ident]
        sx, sy = conf.LEVEL_SIZE
        self.objs = objs = [[[] for j in xrange(sx)] for i in xrange(sy)]
        self._road = obj.Road(self)
        self.frog = Frog(self, data['frog pos'], data.get('frog dirn', 1))
        for o, pos in data['objs'].iteritems():
            objs[pos[0]][pos[1]].append(getattr(obj, o)(self, pos))
        self.dirty = True

    def _click (self, evt):
        if evt.button in (1, 3):
            pos = tuple(x / s for x, s in zip(evt.pos, conf.TILE_SIZE))
            self.frog.investigate(self.objs[pos[0]][pos[1]], pos,
                                  evt.button == 3)

    def _change_tile (self, *pos):
        self._changed.update(tuple(p) for p in pos)

    def add_obj (self, o, pos):
        self.objs[pos[0]][pos[1]].append(o)
        self._change_tile(pos)

    def rm_obj (self, o, pos):
        self.objs[pos[0]][pos[1]].remove(o)
        self._change_tile(pos)

    def say (self, msg):
        print msg

    def update (self):
        self.frog.update()

    def _draw_objs (self, screen, objs):
        last = None
        # draw non-solid
        for o in objs:
            if isinstance(o, obj.DrawSelf):
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
        if self.dirty:
            self.dirty = False
            self._changed = set()
            screen.blit(bg, (0, 0))
            for col in self.objs:
                for objs in col:
                    if objs:
                        draw_objs(screen, objs)
            return True
        elif self._changed:
            changed = self._changed
            objs = self.objs
            self._changed = set()
            sx, sy = conf.TILE_SIZE
            rects = []
            for x, y in changed:
                this_objs = objs[x][y]
                x *= sx
                y *= sy
                r = (x, y, sx, sy)
                rects.append(r)
                screen.blit(bg, (x, y), r)
                draw_objs(screen, this_objs)
            return rects
        else:
            return False
