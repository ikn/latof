import pygame as pg

from conf import conf
from util import ir
import obj as obj_module


class Frog (obj_module.OneTileObj):
    name = 'Frog?'

    def __init__ (self, level, pos = None, dirn = 1):
        obj_module.OneTileObj.__init__(self, level, pos)
        self._last_pos = list(self.pos)
        self._last_dirn = self.dirn = dirn
        self.imgs = [pg.transform.rotate(self.img, angle)
                     for angle in (90, 0, -90, -180)]
        self._queue_t = 0
        self._queue = []
        self.item = None
        self.dead = False
        self.level.add_obj(self, self.pos)

    def stop (self):
        # cancel all queued actions
        self._queue = []

    def queue (self, f, *args, **kw):
        self._queue.append((f, args, kw))

    def dist (self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _next_to (self, obj, pos):
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
                        pos = tuple(p)
                        break
        return there, pos

    def _face (self, dest):
        p = self.pos
        for i in (0, 1):
            d = dest[i] - p[i]
            if d:
                self.dirn = i + (2 if d > 0 else 0)
                break

    def die (self):
        if not self.dead:
            self.dead = True
            self.level.game.play_snd('die')
            self.level.change_tile(self.pos)
            self.img = self.level.game.img(('obj', 'deadfrog.png'))
            self.level.restart()

    def on_crash (self, frog, road):
        self.die()

    def interact (self, frog):
        self.level.say('It\'s me!  I think...')

    def _move (self, dest):
        self._face(dest)
        self.pos = dest
        return ir(conf.FROG_MOVE_TIME * self.level.game.scheduler.timer.fps)

    def get_path (self, dest, extra_objs = ()):
        objs = set(extra_objs)
        objs.update(self.level.solid_objs(self))
        # get shortest path to dest
        road_tiles = self.level.road.tiles
        lane_moving = self.level.road.lane_moving
        sz = conf.LEVEL_SIZE
        pos = tuple(self.pos)
        dist = self.dist
        def weight (pos):
            w = 1
            if pos in road_tiles:
                w += 5 * lane_moving(pos[1])
            return w
        nearest = tot = dist(pos, dest)
        nearests = [(0, pos)]
        todo = {pos: (None, 0, tot, tot)}
        done = {}
        while True:
            # choose next tile
            if not todo:
                # no path exists
                if nearests:
                    # go to nearest tile instead
                    current = min(nearests)[1]
                    break
                else:
                    # do nothing
                    assert False, 'no possible path'
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
                    if pos[axis] < 0 or pos[axis] >= sz[axis] or pos in objs or pos in done:
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
                        if end == nearest:
                            nearests.append((start, pos))
                        elif end < nearest:
                            nearest = end
                            nearests = [(start, pos)]
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

    def move (self, dest, objs = ()):
        # remove any queued movement
        q = self._queue
        rm = []
        for item in q:
            if item[0] == self._move:
                rm.append(item)
        for item in rm:
            q.remove(item)
        # get path to take
        path = self.get_path(dest, objs)
        if path is False:
            # no possible path: don't move at all (shouldn't ever happen)
            return
        # queue moves
        for pos in path:
            self.queue(self._move, pos)

    def grab (self, obj):
        # destroys current item if any
        self.item = obj
        obj.grab()
        self.level.update_held()

    def destroy (self):
        self.item = None
        self.level.update_held()

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
                   and not any(o.solid for o in objs[x][y]):
                    success = True
                    break
            if success:
                pos = p
            else:
                msg = 'I can\'t find anywhere to drop this {}.'
                self.level.say(msg.format(obj_module.name(obj)))
                return
        # drop object
        self.item = None
        obj.drop(pos)
        self.level.update_held()

    def _do_action (self, action, obj, pos):
        if action == 'inspect':
            obj.interact(self)
        elif action == 'grab':
            self.grab(obj)
        elif action == 'drop':
            self.drop()
        elif action == 'use':
            if obj is None:
                name = 'ground'
            else:
                name = obj_module.ident(obj)
            method = 'use_on_' + name.replace(' ', '_')
            if not hasattr(self.item, method):
                msg = 'I don\'t know how to use this {} on that {}.'
                self.level.say(msg.format(obj_module.name(self.item), name))
            else:
                getattr(self.item, method)(self, obj, pos)

    def _action_with_pos (self, action, obj, pos, retry = False):
        next_to, new_pos = self._next_to(obj, pos)
        if next_to:
            self._face(new_pos)
            self._do_action(action, obj, new_pos)
            return
        if retry:
            self.level.say('I can\'t reach that.')
        else:
            # move there first, treating dest as obstacle
            self.move(pos, [pos])
            # queue another call here with retry = True
            self.queue(self._action_with_pos, action, obj, pos, True)

    def action (self, actions, objs, pos):
        obj = self.level.top_obj(objs)
        # go through actions and do the first we can
        actions = list(actions)
        on_fail = []
        while True:
            if actions:
                action = actions.pop(0)
            else:
                # nothing to do
                if on_fail:
                    self.level.say(on_fail[0])
                    return
            if action == 'inspect':
                if obj is None:
                    on_fail.append('There\'s nothing here.')
                else:
                    break
            if action == 'move':
                break
            if action == 'grab':
                if obj is None:
                    on_fail.append('There\'s nothing to pick up.')
                elif self.item is not None:
                    on_fail.append('I\'m already holding something.')
                elif not obj.holdable:
                    msg = 'I can\'t pick that {} up.'
                    on_fail.append(msg.format(obj_module.name(obj)))
                else:
                    break
            if action == 'drop':
                if self.item is None:
                    on_fail.append('I have nothing to drop.')
                elif obj is not None and obj.solid:
                    on_fail.append('I can\'t put this there: that {} is in '
                                   'the way.'.format(obj_module.name(obj)))
                else:
                    break
            if action == 'use':
                if self.item is None:
                    on_fail.append('I have nothing to use.')
                elif obj is None and not hasattr(self.item, 'use_on_ground'):
                    msg = 'I can\'t use this {} on the ground.'
                    on_fail.append(msg.format(obj_module.name(self.item)))
                else:
                    break
        if action == 'move':
            self.move(pos)
        elif action in ('inspect', 'grab', 'drop', 'use'):
            self._action_with_pos(action, obj, pos)

    def update (self):
        if self._queue_t <= 0:
            if self._queue:
                f, args, kw = self._queue.pop(0)
                self._queue_t = f(*args, **kw) or 1
        self._queue_t -= 1
        if self.pos[1] < self.level.road.tile_rect[1]:
            self.level.progress()
        else:
            l, p = self._last_pos, self.pos
            ld, d = self._last_dirn, self.dirn
            if l != p or ld != d:
                self.level.rm_obj(self, l)
                self.level.add_obj(self, p)
                self._last_pos = p
                self._last_dirn = d

    def draw (self, screen):
        if not self.dead:
            self.img = self.imgs[self.dirn]
        obj_module.OneTileObj.draw(self, screen)
