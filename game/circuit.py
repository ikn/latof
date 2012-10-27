import pygame as pg

from conf import conf
import level as level_module


class CircuitPuzzle (object):
    def __init__ (self, level, conf):
        self.level = level
        # each vertex is [wires, obj]
        # each wire is in the wires dict as
        #   (end0, end1): (axis, d)_to_other_end
        # obj is 'pwr', state ID or None
        w, h = self.size = conf['size']
        self.vertices = vs = [[[{}, None] for j in xrange(h)]
                              for i in xrange(w)]
        x, y = self.pwr = conf['pwr']
        vs[x][y][1] = 'pwr'
        self.pos = [x, y]
        for i, (x, y) in enumerate(conf['states']):
            vs[x][y][1] = i
        self._dirn = self._initial_dirn = conf['initial dirn']
        # display
        self.rect = r = pg.Rect(conf['rect'])
        self._tile_size = r[2] / w
        self._sfc = pg.Surface(r.size)
        self._overlay = level_module.Overlay(level, self._sfc, r.topleft)
        for x in xrange(w):
            for y in xrange(h):
                self._draw_tile(x, y)
        # add wires
        add = self._add_wire
        for wire in conf['wires']:
            add(*wire)


    def _add_wire (self, end0, end1):
        x0, y0 = end0 = tuple(end0)
        x1, y1 = end1 = tuple(end1)
        key = (end0, end1)
        vs = self.vertices
        axis = int(x0 == x1)
        d = 1 if end1[axis] > end0[axis] else -1
        vs[x0][y0][0][key] = (axis, d)
        vs[x1][y1][0][key] = (axis, -d)
        for x, y in (end0, end1):
            self._draw_tile(x, y)

    def step (self):
        x, y = pos = list(self.pos)
        from_dirn = (self._dirn + 2) % 4
        for wire, (axis, d) in self.vertices[x][y][0].iteritems():
            this_dirn = axis + d + 1
            if this_dirn != from_dirn:
                # move along this wire
                pos[axis] += d
                self._dirn = this_dirn
                self.set_pos(pos)
                return
        # restart from power source
        self.set_pos(self.pwr)
        self._dirn = self._initial_dirn

    def set_pos (self, pos):
        orig_pos = self.pos
        self.pos = pos
        for x, y in (orig_pos, pos):
            self._draw_tile(x, y)

    def _click (self, evt):
        r = self.rect
        p = evt.pos
        if not r.collidepoint(p):
            self.hide()
            return

    def _move_mouse (self, evt):
        r = self.rect
        p = evt.pos
        if not r.collidepoint(p):
            return True

    def show (self):
        self.level.grab_input(self._click, self._move_mouse)
        self._overlay.show()

    def hide (self):
        self.level.drop_input()
        self._overlay.hide()

    def _draw_tile (self, tx, ty):
        wires, obj = self.vertices[tx][ty]
        s = self._tile_size
        x = tx * s
        y = ty * s
        sfc = self._sfc
        sfc.fill((255, 255, 255), (x, y, s, s))
        hs = s / 2
        wires = wires.values()
        centre = (x + hs, y + hs)
        for axis in (0, 1):
            for d in (-1, 1):
                if (axis, d) in wires:
                    w = 2
                    colour = (0, 0, 0)
                else:
                    w = 1
                    colour = (150, 150, 150)
                p = list(centre)
                p[axis] += d * hs
                pg.draw.line(sfc, colour, centre, p, w)
        if obj is not None:
            c = conf.CIRCUIT_PWR_COLOUR if obj == 'pwr' else conf.CIRCUIT_STATE_COLOURS[obj]
            pg.draw.circle(sfc, c, centre, hs / 2)
        if tuple(self.pos) == (tx, ty):
            pg.draw.circle(sfc, (0, 0, 255), centre, hs / 3)
        self._overlay.set_sfc(sfc)
