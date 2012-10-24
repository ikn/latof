class CircuitPuzzle (object):
    def __init__ (self, conf):
        # each vertex is [wires, obj]
        # each wire is in the wires dict as
        #   (end0, end1): (axis, d)_to_other_end
        # obj is 'pwr', state ID or None
        w, h = self.size = conf['size']
        self.vertices = vs = [[[{}, None] for j in xrange(h + 1)]
                              for i in xrange(w + 1)]
        x, y = self.pwr = conf['pwr']
        vs[x][y][1] = 'pwr'
        self.pos = [x, y]
        for i, (x, y) in enumerate(conf['states']):
            vs[x][y][1] = i
        self._dirn = self._initial_dirn = conf['initial dirn']
        self._add_wire((6, 5), (5, 5))
        self._add_wire((5, 5), (4, 5))
        self._add_wire((4, 5), (4, 4))

    def _add_wire (self, end0, end1):
        x0, y0 = end0 = tuple(end0)
        x1, y1 = end1 = tuple(end1)
        key = (end0, end1)
        vs = self.vertices
        axis = int(x0 == x1)
        d = 1 if end1[axis] > end0[axis] else -1
        vs[x0][y0][0][key] = (axis, d)
        vs[x1][y1][0][key] = (axis, -d)

    def step (self):
        x, y = pos = self.pos
        from_dirn = (self._dirn + 2) % 4
        for wire, (axis, d) in self.vertices[x][y][0].iteritems():
            this_dirn = axis + d + 1
            if this_dirn != from_dirn:
                # move along this wire
                #print 'move', pos,
                pos[axis] += d
                #print pos, this_dirn
                self._dirn = this_dirn
                return
        #print 'restart', self.pos,
        self.pos = list(self.pwr)
        self._dirn = self._initial_dirn
        #print self.pos, self._dirn
