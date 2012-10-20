from random import randint

import pygame as pg

from conf import conf
from obj import Obj


class Road (object):
    def __init__ (self, level):
        self.level = level
        self.rect = pg.Rect(conf.ROAD_POS, conf.ROAD_SIZE)
        self.tile_rect = pg.Rect(conf.TILE_ROAD_POS, conf.TILE_ROAD_SIZE)
        self.tiles = level.rect_tiles(self.rect)
        self.car_img = self.level.game.img(('car', '0.png'))
        self.car_crashed_img = self.car_img
        n_lanes = len(conf.ROAD_LANES)
        self.cars = [(self.lane_dirn(i), []) for i in xrange(n_lanes)]
        self._modes = ['moving'] * n_lanes
        self._stopping = [False] * n_lanes
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
        x0, y0, w, h = self.rect
        dirn, cars = self.cars[lane]
        iw, ih = self.car_img.get_size()

        if x is None:
            gap = conf.CAR_GAP[mode]
            if cars:
                x = cars[-1].rect[0] - dirn * (iw + gap)
            else:
                # choose a random position at the front
                if dirn == 1:
                    mn = w - iw - gap
                    mx = w - 1
                else:
                    mn = 1 - iw
                    mx = gap
                x = randint(mn, mx)
        y = conf.ROAD_LANES[lane] - ih / 2

        cars.append(Car(self, self.car_img, self.car_crashed_img, (x, y)))

    def fill_lane (self, lane, mode = 'moving'):
        dirn, cars = self.cars[lane]
        while not cars or self.needs_car(dirn, cars[-1].rect):
            self.add_car(lane, mode = mode)

    def pos_lanes (self, y):
        s = conf.TILE_SIZE[1]
        y0 = y * s
        y1 = y0 + s
        h = conf.ROAD_LANE_WIDTH / 2
        for lane, lane_y in enumerate(conf.ROAD_LANES):
            if y0 < lane_y + h and y1 > lane_y - h:
                yield lane

    def _tile_x_front (self, lane, x):
        # returns the side of the tile with x-axis position x that cars in the
        # given lane will reach first
        return conf.TILE_SIZE[0] * (x + (self.lane_dirn(lane) == 1))

    def lane_moving (self, y):
        stopping = self._stopping
        for lane in self.pos_lanes(y):
            if stopping[lane] is False:
                return True
        return False

    def start (self, pos):
        # calls guarantee that they called stop or crash at this position
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
            stopping[lane] = self._tile_x_front(lane, pos[0])

    def crash (self, pos):
        return
        print 'crash', pos
        modes = self._modes
        stopping = self._stopping
        for lane in self.pos_lanes(pos[1]):
            modes[lane] = 'crashed'
            stopping[lane] = 200

    def update (self):
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
                    v = conf.CAR_SPEED / self.level.game.scheduler.timer.fps
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
    def __init__ (self, road, img, crashed_img, pos):
        self.road = road
        self.img = self._img = img
        self._crashed_img = crashed_img
        self._objs = []
        self.rect = pg.Rect(pos, img.get_size())
        self.mode = 'moving'

    def _update_img (self):
        self.img = self._crashed_img if self.mode == 'crashed' else self._img

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
            self._update_img()

    def stop (self):
        if self.mode == 'moving':
            self.mode = 'stopped'
            self._add_objs(StoppedCar)
            self._update_img()

    def crash (self):
        if self.mode != 'crashed':
            self.mode = 'crashed'
            self._add_objs(CrashedCar)
            self._update_img()

    def set_mode (self, mode):
        {
            'moving': self.start,
            'stopped': self.stop,
            'crashed': self.crash
        }[mode]()

    def front (self, dirn):
        r = self.rect
        return (r[0] + r[2]) if dirn == 1 else r[0]

    def back (self, dirn):
        r = self.rect
        return r[0] if dirn == 1 else (r[0] + r[2])

    def draw (self, screen):
        screen.blit(self.img, self.rect)


class StoppedCar (Obj):
    desc = 'A stopped car.'


class CrashedCar (Obj):
    desc = 'A crashed car.'
