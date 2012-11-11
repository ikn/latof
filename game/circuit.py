import pygame as pg

from conf import conf
import level as level_module


class CircuitPuzzle (object):
    def __init__ (self, level, conf):
        self.level = level
        self._initialised = False
        # each vertex is [wires, obj]
        # each wire is in the wires dict as
        #   (end0, end1): (axis, d)_to_other_end
        # obj is state ID or None
        w, h = self.size = conf['size']
        self.vertices = vs = [[[{}, None] for j in xrange(h)]
                              for i in xrange(w)]
        self._init_state = conf['states'][0]
        self.pos = list(self._init_state)
        for i, (x, y) in enumerate(conf['states']):
            vs[x][y][1] = i
        self._dirn = self._initial_dirn = conf['initial dirn']
        self._n_states = len(conf['states'])
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
        pts = conf['pts']
        for i in xrange(len(pts) - 1):
            x0, y0 = p = list(pts[i])
            x1, y1 = pf = list(pts[i + 1])
            axis = x1 == x0
            dirn = 1 if pf[axis] > p[axis] else -1
            while p != pf:
                p0 = tuple(p)
                p[axis] += dirn
                add(p0, tuple(p))
        # don't need to validate initial circuit
        self._need_check = self._checking = False
        self._initialised = True

    def _check (self):
        if self._initialised:
            #print 'start check'
            self._need_check = True
            self._checking = False

    def _add_wire (self, end0, end1):
        x0, y0 = end0 = tuple(end0)
        x1, y1 = end1 = tuple(end1)
        key = tuple(sorted((end0, end1)))
        vs = self.vertices
        axis = int(x0 == x1)
        d = 1 if end1[axis] > end0[axis] else -1
        vs[x0][y0][0][key] = (axis, d)
        vs[x1][y1][0][key] = (axis, -d)
        for x, y in (end0, end1):
            self._draw_tile(x, y)
        self._check()

    def _rm_wire (self, wire):
        wire = tuple(sorted(wire))
        for x, y in wire:
            del self.vertices[x][y][0][wire]
            self._draw_tile(x, y)
        self._check()

    def _toggle_wire (self, wire):
        wire = tuple(sorted(wire))
        if wire in self.vertices[wire[0][0]][wire[0][1]][0]:
            self._rm_wire(wire)
        else:
            self._add_wire(*wire)

    def step (self):
        x, y = pos = list(self.pos)
        from_dirn = None if self._dirn is None else ((self._dirn + 2) % 4)
        # get list of wires we can follow
        good_wires = []
        for wire, (axis, d) in self.vertices[x][y][0].iteritems():
            wire_dirn = axis + d + 1
            if from_dirn is None or wire_dirn != from_dirn:
                good_wires.append((axis, d, wire_dirn))
        # only move if we have exactly one choice
        if len(good_wires) == 1:
            # move along this wire
            axis, d, wire_dirn = good_wires[0]
            pos[axis] += d
            self._dirn = wire_dirn
            self.set_pos(pos)
        # else restart from power source
        else:
            self.set_pos(self._init_state)
            self._dirn = self._initial_dirn
        # handle circuit validity check
        state = self.vertices[self.pos[0]][self.pos[1]][1]
        if state == 0:
            if self._checking:
                # circuit check complete: see if we have everything
                if len(self._check_states) == self._n_states - 1:
                    # valid circuit
                    #print 'valid'
                    self._need_check = False
                    self._checking = False
                else:
                    # invalid circuit: check again
                    #print 'error'
                    self._check_states = set()
            elif self._need_check:
                # start a check this circuit
                self._checking = True
                self._check_states = set()
        elif isinstance(state, int) and self._checking:
            self._check_states.add(state)
        # return state
        if self._need_check:
            return conf.CIRCUIT_INITIAL_STATE
        elif isinstance(state, int):
            return state

    def set_pos (self, pos):
        orig_pos = self.pos
        self.pos = pos
        for x, y in (orig_pos, pos):
            self._draw_tile(x, y)

    def _click (self, evt):
        r = self.rect
        if not r.collidepoint(evt.pos):
            self.hide()
            return
        if evt.button in (1, 2, 3):
            x, y = evt.pos
            x -= r[0]
            y -= r[1]
            # get clicked tile
            s = self._tile_size
            hs = s / 2
            tx = x / s
            ty = y / s
            # get nearest wire
            dx = (y % s) - hs
            dy = (x % s) - hs
            axis = int(abs(dy) < abs(dx))
            d = 1 if (dx, dy)[not axis] > 0 else -1
            # check bounds
            wire = ((tx, ty), (tx + d, ty) if axis == 0 else (tx, ty + d))
            w, h = self.size
            for x, y in wire:
                if x < 0 or x >= w or y < 0 or y >= h:
                    # OoB
                    return
            # add/remove wire
            self._toggle_wire(wire)

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
        imgs = []
        if obj is not None:
            imgs.append(obj)
        if tuple(self.pos) == (tx, ty):
            imgs.append('pos')
        for ident in imgs:
            img = self.level.game.img(('circuit', '{0}.png'.format(ident)))
            w, h = img.get_size()
            sfc.blit(img, (centre[0] - w / 2, centre[1] - h / 2))
        self._overlay.update()
