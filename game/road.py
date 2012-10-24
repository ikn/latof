from random import randint, expovariate as expo

import pygame as pg

from conf import conf
from util import ir, randsgn, weighted_rand
from obj import Obj


class Road (object):
    def __init__ (self, level):
        self.level = level
        self.rect = pg.Rect(conf.ROAD_POS, conf.ROAD_SIZE)
        self.tile_rect = pg.Rect(conf.TILE_ROAD_POS, conf.TILE_ROAD_SIZE)
        self.tiles = level.rect_tiles(self.rect)
        load_img = level.game.img
        n_lanes = len(conf.ROAD_LANES)
        self.cars = [[self.lane_dirn(i), []] for i in xrange(n_lanes)]
        self._modes = ['moving'] * n_lanes
        self._stopping = [False] * n_lanes
        # load images
        self.img_weightings = ws = []
        self.car_imgs = imgs = []
        self.car_crashed_imgs = crashed_imgs = []
        for model, (m_weight, colours) in conf.CAR_WEIGHTINGS.iteritems():
            for c, c_weight in colours.iteritems():
                ws.append(m_weight * c_weight)
                for ext, dest in (('', imgs), ('-crashed', crashed_imgs)):
                    img = load_img(('car', model + '-' + c + ext + '.png'))
                    flipped = pg.transform.flip(img, True, False)
                    dest.append((img, flipped))
        # add cars
        for lane in xrange(n_lanes):
            self.fill_lane(lane)

    def lane_dirn (self, lane):
        return conf.ROAD_DIRN * (1 if lane < len(conf.ROAD_LANES) / 2 else -1)

    def needs_car (self, dirn, last_rect):
        if dirn == 1:
            return last_rect[0] >= 0
        else:
            return last_rect[0] + last_rect[2] <= self.rect[2]

    def oob (self, dirn, rect):
        if dirn == 1:
            return rect[0] >= self.rect[2]
        else:
            return rect[0] + rect[2] <= 0

    def add_car (self, lane, x = None, mode = 'moving'):
        # x is the front of the car
        x0, y0, w, h = self.rect
        dirn, cars = self.cars[lane]
        imgs = (self.car_crashed_imgs if mode == 'crashed' else self.car_imgs)
        imgs = imgs[weighted_rand(self.img_weightings)]
        iw, ih = imgs[0].get_size()

        if x is None:
            gap = conf.CAR_GAP[mode]
            if cars:
                # start after last car
                x = cars[-1].back(dirn) - dirn * gap
                if dirn == 1:
                    x -= iw
            else:
                # choose a random position at the front
                if dirn == 1:
                    mn = w - iw - gap
                    mx = w - 1
                else:
                    mn = 1 - iw
                    mx = gap
                x = randint(mn, mx)
        elif dirn == 1:
            x -= iw
        y = conf.ROAD_LANES[lane] - ih / 2

        cars.append(Car(self, imgs[dirn == 1], (x, y)))

    def fill_lane (self, lane, mode = 'moving', x = None):
        dirn, cars = self.cars[lane]
        if not cars:
            self.add_car(lane, x, mode)
        while self.needs_car(dirn, cars[-1].rect):
            self.add_car(lane, mode = mode)

    def clear_lane (self, lane):
        for car in self.cars[lane][1]:
            car.destroy()
        self.cars[lane][1] = []

    def pos_lanes (self, y):
        s = conf.TILE_SIZE[1]
        y0 = y * s
        y1 = y0 + s
        h = conf.ROAD_LANE_WIDTH / 2
        for lane, lane_y in enumerate(conf.ROAD_LANES):
            if y0 < lane_y + h and y1 > lane_y - h:
                yield lane

    def _tile_x_back (self, lane, x):
        # returns the side of the tile with x-axis position x that cars in the
        # given lane will reach last
        return conf.TILE_SIZE[0] * (x + (self.lane_dirn(lane) == 1))

    def lane_moving (self, y):
        stopping = self._stopping
        for lane in self.pos_lanes(y):
            if stopping[lane] is False:
                return True
        return False

    def start (self, pos):
        modes = self._modes
        stopping = self._stopping
        for lane in self.pos_lanes(pos[1]):
            modes[lane] = 'moving'
            stopping[lane] = False

    def stop (self, pos):
        modes = self._modes
        stopping = self._stopping
        for lane in self.pos_lanes(pos[1]):
            modes[lane] = 'stopped'
            stopping[lane] = self._tile_x_back(lane, pos[0])

    def _jitter_clamp (self, x, lb, ub, lane):
        s = conf.TILE_SIZE[1]
        lb = s * lb + 1
        ub = s * (ub + 1) - 1
        inv_mean = 1. / conf.CRASH_POS_JITTER
        x = min(max(ir(x + randsgn() * expo(inv_mean)), lb), ub)
        tile_x = ((x - 1) if lane < 2 else x) / s
        return (tile_x, x)

    def _crash (self, pos):
        # generate stop positions (front-most tiles)
        n_lanes = len(conf.ROAD_LANES)
        tile_stop = [0] * n_lanes
        stop = [0] * n_lanes
        origin = next(self.pos_lanes(pos[1]))
        lane_bounds = [(0, 13), (0, 12), (2, 14), (1, 14)]
        # generate tile bounds
        r = self.tile_rect
        bounds = {}
        lane_tiles = [[] for i in xrange(n_lanes)]
        tile_lanes = {}
        for y in xrange(r[1], r[1] + r[3]):
            lanes = list(self.pos_lanes(y))
            for lane in lanes:
                lane_tiles[lane].append(y)
            tile_lanes[y] = lanes
            lb = max(lane_bounds[lane][0] for lane in lanes)
            ub = min(lane_bounds[lane][1] for lane in lanes)
            bounds[y] = (lb, ub)
        # set origin lane position
        x = conf.TILE_SIZE[0] * pos[0] + \
            conf.CRASH_FOLLOWTHROUGH * self.lane_dirn(origin)
        tile_stop[origin], stop[origin] = self._jitter_clamp(
            x, *lane_bounds[origin], lane = origin
        )
        # set other lane positions
        for d in (-1, 1):
            lane = origin + d
            x = stop[origin]
            while 0 <= lane <= 3:
                lb, ub = lane_bounds[lane]
                # set bounds to make sure the direction switchover leaves a
                # path through
                if d == 1 and lane == 2 and origin <= 1:
                    lbs = [lb]
                    tiles = lane_tiles[lane]
                    tiles.append(min(tiles) - 1)
                    related = set(sum((tile_lanes[y] for y in tiles), []))
                    for l in related:
                        if l > lane:
                            lbs.append(tile_stop[l] + 2)
                    lb = max(lbs)
                    for l in related:
                        if l < lane:
                            this_lb, this_ub = lane_bounds[l]
                            lane_bounds[l] = (max(lb, this_lb), ub, this_ub)
                            for this_y in lane_tiles[l]:
                                this_lb, this_ub = bounds[this_y]
                                bounds[this_y] = (max(lb, this_lb), ub, this_ub)
                elif d == -1 and lane == 1 and origin >= 2:
                    ubs = [ub]
                    tiles = lane_tiles[lane]
                    tiles.append(max(tiles) + 1)
                    related = set(sum((tile_lanes[y] for y in tiles), []))
                    for l in related:
                        if l > lane:
                            ubs.append(tile_stop[l] - 2)
                    ub = min(ubs)
                    for l in related:
                        if l < lane:
                            this_lb, this_ub = lane_bounds[l]
                            lane_bounds[l] = (this_lb, min(ub, this_ub))
                            for this_y in lane_tiles[l]:
                                this_lb, this_ub = bounds[this_y]
                                bounds[this_y] = (this_lb, min(ub, this_ub))
                # decide randomish position inside bounds
                tile_stop[lane], x = self._jitter_clamp(x, lb, ub, lane)
                stop[lane] = x
                lane += d
        # crash everything
        modes = self._modes
        stopping = self._stopping
        for lane, x in zip(xrange(n_lanes), stop):
            self.clear_lane(lane)
            modes[lane] = 'crashed'
            stopping[lane] = x
            self.fill_lane(lane, 'crashed', x)

    def crash (self, pos):
        game = self.level.game
        game.linear_fade(*conf.CRASH_FADE)
        game.scheduler.add_timeout(self._crash, (pos,),
                                   seconds = conf.CRASH_TIME)
        self.level.cutscene(conf.CRASH_CTRL_TIME)

    def update (self):
        fps = self.level.game.scheduler.timer.fps
        speed = ir(float(conf.CAR_SPEED) / fps)
        speed_jitter = float(conf.CAR_SPEED_JITTER) / fps
        for lane, (lane_mode, stopping, (dirn, cars)) in \
            enumerate(zip(self._modes, self._stopping, self.cars)):
            # remove OoB cars
            if cars and self.oob(dirn, cars[0].rect):
                cars.pop(0)
            # add cars if needed
            if not cars or self.needs_car(dirn, cars[-1].rect):
                self.add_car(lane)
            # move cars
            prev = None
            new_mode = current_mode = 'moving'
            for car in cars:
                if lane_mode == 'moving':
                    car.start()
                if car.mode == 'moving':
                    r = car.rect
                    front = car.front(dirn)
                    v = speed + max(1 - speed,
                                    randsgn() * ir(expo(1 / speed_jitter)))
                    stop = front + dirn * v
                    # stop before stop marker
                    if lane_mode != 'moving' and current_mode == 'moving':
                        if dirn * front <= dirn * stopping:
                            stop = stopping
                        new_mode = lane_mode
                    # stop before next car
                    if prev is not None:
                        this_stop = prev.back(dirn) - \
                                    dirn * conf.CAR_GAP[current_mode]
                        stop = dirn * min(dirn * stop, dirn * this_stop)
                    new_v = dirn * (stop - front)
                    if new_v < v:
                        # velocity reduced
                        v = max(0, new_v)
                        if v == 0 and \
                           (current_mode == 'moving' or prev.mode != 'moving'):
                            # to make sure we only stop if every car in front
                            # has stopped - in case this car is faster than the
                            # one in front
                            car.set_mode(new_mode)
                        current_mode = new_mode
                    r.move_ip(v * dirn, 0)
                else:
                    new_mode = current_mode = car.mode
                prev = car


class Car (object):
    def __init__ (self, road, img, pos):
        self.road = road
        self.img = self._img = img
        self._objs = []
        self.rect = pg.Rect(pos, img.get_size())
        self.mode = 'moving'

    def front (self, dirn):
        r = self.rect
        return (r[0] + r[2]) if dirn == 1 else r[0]

    def back (self, dirn):
        r = self.rect
        return r[0] if dirn == 1 else (r[0] + r[2])

    def _add_objs (self, cls):
        if self._objs:
            self._rm_objs()
        os = self._objs
        level = self.road.level
        add = level.add_obj
        for pos in level.rect_tiles(self.rect):
            obj = cls(level, pos)
            add(obj, pos)
            os.append(obj)

    def _rm_objs (self):
        rm = self.road.level.rm_obj
        for o in self._objs:
            rm(o)
        self._objs = []

    def start (self):
        if self.mode == 'stopped':
            self.mode = 'moving'
            for o in self._objs:
                self.road.level.rm_obj(o)
            self._rm_objs()

    def stop (self):
        if self.mode == 'moving':
            self.mode = 'stopped'
            self._add_objs(StoppedCar)

    def crash (self):
        if self.mode != 'crashed':
            self.mode = 'crashed'
            self._add_objs(CrashedCar)

    def set_mode (self, mode):
        {
            'moving': self.start,
            'stopped': self.stop,
            'crashed': self.crash
        }[mode]()

    def destroy (self):
        self._rm_objs()

    def draw (self, screen):
        screen.blit(self.img, self.rect)


class StoppedCar (Obj):
    desc = 'A stopped car.'


class CrashedCar (Obj):
    desc = 'A crashed car.'
