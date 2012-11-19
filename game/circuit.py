import pygame as pg

from conf import conf
import level as level_module


class CircuitPuzzle (object):
    def __init__ (self, level, data):
        self.level = level
        self._initialised = False
        # each vertex is [wires, obj]
        # each wire is in the wires dict as
        #   (end0, end1): (axis, d)_to_other_end
        # obj is state ID or None
        w, h = data['size']
        draw_w = w
        w -= 1
        self.size = (w, h)
        self.vertices = vs = [[[{}, None] for j in xrange(h)]
                              for i in xrange(w)]
        self._init_state = data['states'][0]
        self.pos = list(self._init_state)
        for i, (x, y) in enumerate(data['states']):
            vs[x][y][1] = i
        self._dirn = self._initial_dirn = data['initial dirn']
        self._n_states = len(data['states'])
        self._state = conf.CIRCUIT_INITIAL_STATE
        # display
        self.rect = r = pg.Rect(data['rect'])
        self._tile_size = r[2] / draw_w
        self._sfc = pg.Surface(r.size)
        self._overlay = level_module.Overlay(level, self._sfc, r.topleft)
        self._need_check = self._checking = False
        for x in xrange(draw_w):
            for y in xrange(h):
                self._draw_tile(x, y)
        # add wires
        add = self._add_wire
        pts = data['pts']
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

    def _set_state (self, state):
        self._state = state
        self._draw_tile(self.size[0], self.size[1] - 1)

    def _check (self):
        if self._initialised:
            self._need_check = True
            self._checking = False
            self._set_state('error')
            self._draw_statuses()

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

    def _draw_statuses (self, *states):
        if not states:
            states = xrange(self._n_states)
        w = self.size[0]
        for state in states:
            self._draw_tile(w, state)

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
                    self._need_check = False
                    self._checking = False
                    self._set_state(state)
                else:
                    # invalid circuit: check again
                    check_states = self._check_states
                    self._check_states = set()
                    self._draw_statuses(*check_states)
            elif self._need_check:
                # start a check this circuit
                self._checking = True
                self._check_states = set()
                self._draw_statuses()
            else:
                self._set_state(state)
        elif isinstance(state, int):
            if self._checking:
                self._check_states.add(state)
                self._draw_statuses(state)
            elif not self._need_check:
                self._set_state(state)
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
        w, h = self.size
        sfc = self._sfc
        s = self._tile_size
        hs = s / 2
        x = tx * s
        y = ty * s
        centre = (x + hs, y + hs)
        # background
        sfc.fill((255, 255, 255), (x, y, s, s))
        if tx == w:
            obj = self._state if ty == h - 1 else ty
        else:
            # wires
            wires, obj = self.vertices[tx][ty]
            wires = wires.values()
            for axis in (0, 1):
                for d in (-1, 1):
                    if (axis, d) in wires:
                        line_w = 2
                        colour = (0, 0, 0)
                    else:
                        line_w = 1
                        colour = (150, 150, 150)
                    p = list(centre)
                    p[axis] += d * hs
                    pg.draw.line(sfc, colour, centre, p, line_w)
        # objects
        imgs = []
        if obj is not None:
            if obj == 0 and tx != w:
                imgs.append('arrow')
            imgs.append(obj)
            if tx == w and ty != h - 1:
                if self._checking:
                    got = ty == 0 or ty in self._check_states
                elif self._need_check:
                    got = False
                else:
                    got = True
                if got:
                    imgs.append('tick')
        if tuple(self.pos) == (tx, ty):
            imgs.append('pos')
        for ident in imgs:
            img = self.level.game.img(('circuit', '{0}.png'.format(ident)))
            img_w, img_h = img.get_size()
            sfc.blit(img, (centre[0] - img_w / 2, centre[1] - img_h / 2))
        self._overlay.update()
