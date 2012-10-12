import pygame as pg

from conf import conf
import obj


class Level (object):
    def __init__ (self, game, event_handler, ident = 0):
        self.game = game
        event_handler.add_event_handlers({
            pg.MOUSEBUTTONDOWN: self._click
        })
        self._road = obj.Road(self)
        # variables
        self.ident = ident
        self._changed = set()
        # level-specific
        self.init()

    def init (self):
        data = conf.LEVELS[self.ident]
        self.frog = obj.Frog(self, data['frog pos'], data.get('frog dirn', 1))
        self.objs = objs = {}
        for o, pos in data['objs'].iteritems():
            objs[tuple(pos)] = getattr(obj, o)(self, pos)
        self.dirty = True

    def _click (self, evt):
        pos = tuple(x / s for x, s in zip(evt.pos, conf.TILE_SIZE))
        if self._road.rect.collidepoint(pos):
            obj = self._road
            self._road.pos = pos
        else:
            obj = self.objs.get(pos, pos)
        self.frog.investigate(obj)

    def change_tile (self, *pos):
        self._changed.update(tuple(p) for p in pos)

    def add_obj (self, obj, pos):
        self.objs[tuple(pos)] = obj

    def rm_obj (self, pos):
        del self.objs[tuple(pos)]

    def say (self, msg):
        print msg

    def update (self):
        self.frog.update()

    def draw (self, screen):
        self.frog.pre_draw()
        bg = self.game.img('bg.png')
        if self.dirty:
            self.dirty = False
            self._changed = set()
            screen.blit(bg, (0, 0))
            for obj in self.objs.values():
                obj.draw(screen)
            self.frog.draw(screen)
            return True
        elif self._changed:
            changed = self._changed
            self._changed = set()
            sx, sy = conf.TILE_SIZE
            rects = []
            for x, y in changed:
                x *= sx
                y *= sy
                r = (x, y, sx, sy)
                rects.append(r)
                screen.blit(bg, (x, y), r)
            for obj in [self.frog]:
                if tuple(obj.pos) in changed:
                    obj.draw(screen)
            return rects
        else:
            return False
