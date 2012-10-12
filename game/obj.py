import pygame as pg

from conf import conf
from util import ir
import objhelpers

#   object methods:
# interact(): perform basic action on object
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use(obj): use held object on object obj


class Road (object):
    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        for i in xrange(600 / sx):
            for j in xrange(200 / sy, 400 / sy):
                level.add_obj(self, (i, j))

    def interact (self):
        self.level.say('a busy road.')


class Obj (object):
    def __init__ (self, level, pos = None, dirn = 1):
        self.level = level
        self.pos = pos if pos is None else list(pos)
        self.dirn = dirn
        img = level.game.img(self.__class__.__name__.lower() + '.png')
        self.imgs = [pg.transform.rotate(img, angle)
                     for angle in (90, 0, -90, -180)]
        self._offset = [ir(float(t_s - i_s) / 2) for t_s, i_s in
                        zip(conf.TILE_SIZE, img.get_size())]

    def draw (self, screen):
        x, y = self.pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.imgs[self.dirn], (x * sx + ox, y * sy + oy))


class Frog (Obj):
    def __init__ (self, *args, **kw):
        Obj.__init__(self, *args, **kw)
        self._last_pos = list(self.pos)
        self._queue_t = 0
        self._queue = []
        self._item = None
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

    def move (self, dest):
        # remove any queued movement
        q = self._queue
        rm = []
        for item in q:
            if item[0] == self._move:
                rm.append(item)
        for item in rm:
            q.remove(item)
        all_objs = list(self.level.objs)
        all_objs.remove(tuple(self.pos))
        # first ignore all objects
        path = self.get_path(dest, all_objs)
        if path is False:
            # no possible path: don't move at all (shouldn't ever happen)
            return
        # now unignore every object we didn't cross
        objs = [pos for pos in all_objs if pos not in path]
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

    def interact (self):
        self.level.say('it\'s me!  I think...')

    def _investigate (self, obj, pos):
        if self._item is None:
            if hasattr(obj, 'interact'):
                obj.interact()
        else:
            self._item.use(obj)

    def investigate (self, obj, pos, done = False):
        if not isinstance(obj, tuple):
            # check if in an adjacent tile
            there = False
            if self.dist(self.pos, pos) <= 1:
                there = True
            else:
                objs = self.level.objs
                for axis in (0, 1):
                    for d in (-1, 1):
                        p = list(self.pos)
                        p[axis] += d
                        if objs.get(tuple(p)) == obj:
                            there = True
                            break
            if there:
                self._face(pos)
                self._investigate(obj, pos)
                return
        if done:
            print 'couldn\'t move to object'
        else:
            # move there
            self.move(pos)
            if obj is not None:
                # queue another call here with done = True
                self.queue(self.investigate, obj, pos, True)

    def grab (self, obj):
        if self._item is None:
            self._item = obj
            obj.grab()
        else:
            self.level.say('I\'m already holding something.')

    def destroy (self):
        self._item = None

    def drop (self, obj = None):
        if obj is None:
            obj = self._item
        if obj is not None:
            # find a place to put the object
            # TODO
            #self.level.add_obj(obj, pos)
            pass

    def update (self):
        if self._queue_t <= 0:
            if self._queue:
                f, args, kw = self._queue.pop(0)
                self._queue_t = f(*args, **kw) or 1
        self._queue_t -= 1
        l, p = self._last_pos, self.pos
        if l != p:
            self.level.rm_obj(l)
            self.level.add_obj(self, p)
            self._last_pos = p

    def draw (self, screen):
        x, y = self.pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.imgs[self.dirn], (x * sx + ox, y * sy + oy))


class Holdable (Obj):
    holdable = True

    def __init__ (self, *args, **kw):
        self.held = False
        if kw.get('held', False):
            self.grab()

    def grab (self):
        if not self.held:
            self.held = True
            self.level.rm_obj(self.pos)
            self.pos = None

    def drop (self, pos):
        if self.held:
            self.held = False
            self.level.add_obj(self, pos)
            self.pos = list(pos)

    def use (self, obj):
        return NotImplemented


class Static (Obj):
    holdable = False


class Basket (Static):
    def interact (self):
        self.level.say('it\'s a basket containing some things.')


class Banana (Holdable):
    def use (self, obj):
        if self.held and isinstance(obj, Frog):
            obj.destroy()
            obj.drop(BananaPeel(self.level))
            self.level.say('I eat the banana.')
