import pygame as pg

from conf import conf
import obj as obj_module


class Frog (obj_module.Placeable):
    def __init__ (self, level, pos = None, dirn = 1):
        obj_module.Placeable.__init__(self, level, pos)
        self._last_pos = list(self.pos)
        self._last_dirn = self.dirn = dirn
        self.imgs = [pg.transform.rotate(self.img, angle)
                     for angle in (90, 0, -90, -180)]
        self._queue_t = 0
        self._queue = []
        self.item = None
        self.level.add_obj(self, self.pos)

    def queue (self, f, *args, **kw):
        self._queue.append((f, args, kw))

    def _face (self, dest):
        p = self.pos
        for i in (0, 1):
            d = dest[i] - p[i]
            if d:
                self.dirn = i + (2 if d > 0 else 0)
                break

    def dist (self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _move (self, dest):
        self._face(dest)
        self.pos = dest
        return conf.FROG_MOVE_TIME

    def get_path (self, dest, all_objs, objs = ()):
        # get shortest path to dest
        sz = conf.LEVEL_SIZE
        pos = tuple(self.pos)
        dist = self.dist
        weight = lambda pos: 1 + (pos in all_objs)
        tot = dist(pos, dest)
        todo = {pos: (None, 0, tot, tot)}
        done = {}
        while True:
            # choose next tile
            if not todo:
                # no path exists
                return False
            tot, current, current_start = min((tot, pos, start)
                for (pos, (parent, start, end, tot)) in todo.iteritems())
            # mark this tile as done
            done[current] = todo[current]
            del todo[current]
            if current == dest:
                # success
                break
            # find empty adjacent tiles
            for axis in (0, 1):
                for d in (-1, 1):
                    pos = list(current)
                    pos[axis] += d
                    pos = tuple(pos)
                    if pos[axis] < 0 or pos[axis] >= sz[axis] or pos in objs \
                       or pos in done:
                        # out of bounds or non-empty or already considered
                        continue
                    # found one
                    start = current_start + weight(pos)
                    if pos in todo:
                        # already stored: update start/parent only if necessary
                        parent, stored_start, end, tot = todo[pos]
                        if start >= stored_start:
                            continue
                    else:
                        end = dist(pos, dest)
                    # store
                    todo[pos] = (current, start, end, start + end)
        # construct the path
        path = [current]
        while True:
            current = done[current][0]
            if current is None:
                break
            path.append(current)
        path.reverse()
        return path[1:] # first item will be the current position

    def move (self, dest, objs):
        # remove any queued movement
        q = self._queue
        rm = []
        for item in q:
            if item[0] == self._move:
                rm.append(item)
        for item in rm:
            q.remove(item)
        all_objs = objs
        for x, col in enumerate(self.level.objs):
            for y, os in enumerate(col):
                for o in os:
                    if o.solid and o is not self:
                        all_objs.append((x, y))
                        break
        # first ignore all objects
        path = self.get_path(dest, all_objs)
        if path is False:
            # no possible path: don't move at all (shouldn't ever happen)
            return
        # now unignore every object we didn't cross
        objs += [pos for pos in all_objs if pos not in path]
        # now unignore each object we cross in turn until we get no further
        while True:
            # get first object
            found = False
            for i, pos in enumerate(path):
                if pos in all_objs:
                    objs.append(pos)
                    found = True
                    break
            if not found:
                # no objects crossed: path is good
                break
            # get path
            last_path, path = path, self.get_path(dest, all_objs, objs)
            if path is False:
                # this is as far as we can go: use the last path up to the last
                # object we removed
                path = last_path[:i]
                break
        # queue moves
        for pos in path:
            self.queue(self._move, pos)

    def interact (self, frog):
        self.level.say('it\'s me!  I think...')

    def _investigate (self, obj, pos, use):
        if use:
            if self.item is not None:
                if obj is None:
                    self.drop()
                else:
                    self.item.use(self, obj, pos)
            elif isinstance(obj, obj_module.Holdable):
                self.grab(obj)
        else:
            obj.interact(self)

    def investigate (self, objs, pos, use, done = False):
        # select solid obj or uppermost (last) obj
        solid = [o for o in objs if o.solid]
        if solid:
            obj = solid[0]
        elif objs:
            obj = objs[-1]
        else:
            obj = None
        if obj is not None or use:
            # check if in an adjacent tile
            there = False
            if self.dist(self.pos, pos) <= 1:
                there = True
            elif obj is not None:
                all_objs = self.level.objs
                sx, sy = conf.LEVEL_SIZE
                for axis in (0, 1):
                    for d in (-1, 1):
                        p = list(self.pos)
                        p[axis] += d
                        x, y = p
                        if x >= 0 and y >= 0 and x < sx and y < sy \
                           and obj in all_objs[x][y]:
                            there = True
                            break
            if there:
                self._face(pos)
                self._investigate(obj, pos, use)
                return
        if done:
            print 'couldn\'t move to object'
        else:
            # move there (if using or there's an object, treat dest as obstacle
            # even if it's empty or non-solid)
            self.move(pos, [pos] if use or obj is not None else [])
            if obj is not None or use:
                # queue another call here with done = True
                self.queue(self.investigate, objs, pos, use, done = True)

    def grab (self, obj):
        if self.item is None:
            self.item = obj
            obj.grab()
        else:
            self.level.say('I\'m already holding something.')

    def destroy (self):
        self.item = None

    def drop (self, obj = None, pos = None):
        if obj is None:
            obj = self.item
        else:
            # set this as our item in case we can't drop it anywhere
            assert self.item is None
            self.item = obj
        if obj is None:
            return
        if pos is None:
            # find a place to put the object
            pos = self.pos
            objs = self.level.objs
            sx, sy = conf.LEVEL_SIZE
            success = False
            df_axis = self.dirn % 2
            df_sgn = 1 if self.dirn > 1 else -1
            ds_axis = (df_axis + 1) % 2
            for d_sideways, d_facing in [(0, 1), (-1, 0), (1, 0), (-1, 1),
                                         (1, 1), (-1, -1), (1, -1), (0, -1)]:
                p = list(pos)
                p[df_axis] += d_facing * df_sgn
                p[ds_axis] += d_sideways
                x, y = p
                if x >= 0 and y >= 0 and x < sx and y < sy \
                   and not objs[x][y]:
                    success = True
                    break
            if success:
                pos = p
            else:
                self.level.say('I can\'t find anywhere to drop this')
                return
        # drop object
        self.item = None
        obj.drop(pos)

    def update (self):
        if self._queue_t <= 0:
            if self._queue:
                f, args, kw = self._queue.pop(0)
                self._queue_t = f(*args, **kw) or 1
        self._queue_t -= 1
        l, p = self._last_pos, self.pos
        ld, d = self._last_dirn, self.dirn
        if l != p or ld != d:
            self.level.rm_obj(self, l)
            self.level.add_obj(self, p)
            self._last_pos = p
            self._last_dirn = d

    def draw (self, screen):
        self.img = self.imgs[self.dirn]
        obj_module.Placeable.draw(self, screen)
