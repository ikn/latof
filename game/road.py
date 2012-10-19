from random import randint

import pygame as pg

from conf import conf


class Car (object):
    def __init__ (self, road, img, crashed_img, pos):
        self.road = road
        self._img = img
        self._crashed_img = crashed_img
        self._objs = []
        self.rect = pg.Rect(pos, img.get_size())
        self.start()

    def _update_img (self):
        self.img = self._img if self.mode == 'moving' else self._crashed_img

    def _add_objs (self):
        # TODO
        pass

    def start (self):
        self.mode = 'moving'
        for o in self._objs:
            self.road.level.rm_obj(o)
        self._objs = []
        self._update_img()

    def stop (self):
        self.mode = 'stopped'
        self._add_objs()
        self._update_img()

    def crash (self):
        self.mode = 'crashed'
        self._add_objs()
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
        self._lane_mode = ['moving'] * n_lanes
        self._lane_stop_pos = [set() for i in xrange(n_lanes)]
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
        # mode is conf.CAR_GAP key
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
            self.add_car(lane)

    def pos_lane (self, y):
        y *= conf.TILE_SIZE[1]
        return sorted((abs(l - y), i)
                      for i, l in enumerate(conf.ROAD_LANES))[0][1]

    def _tile_x_front (self, lane, x):
        # returns the side of the tile with x-axis position x that cars in the
        # given lane will reach first
        return conf.TILE_SIZE[0] * (x + (self.lane_dirn(lane) == 1))

    def start (self, pos):
        lane = self.pos_lane(pos[1])
        self._lane_mode[lane] = 'moving'
        stop_pos = self._lane_stop_pos[lane]
        x = self._tile_x_front(lane, pos[0])
        if x in stop_pos:
            stop_pos.remove(x)

    def stop (self, pos):
        lane = self.pos_lane(pos[1])
        self._lane_mode[lane] = 'stopped'
        self._lane_stop_pos[lane].add(self._tile_x_front(lane, pos[0]))

    def crash (self, pos):
        self.stop(pos)
        #print 'crash', pos, pos[1] - self.tile_rect[1]

    def update (self):
        for lane, (lane_mode, stop_pos, (dirn, cars)) in \
            enumerate(zip(self._lane_mode, self._lane_stop_pos, self.cars)):
            stop_pos = max(stop_pos) if stop_pos else None
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
                if car.mode == 'moving':
                    r = car.rect
                    v = conf.CAR_SPEED
                    if lane_mode != 'moving':
                        front = car.front(dirn)
                        # stop before stop marker
                        if current_mode == 'moving':
                            stop = stop_pos
                            new_mode = lane_mode
                        else:
                            stop = front + v
                        # stop before next car
                        if prev is not None:
                            this_stop = prev.back(dirn) - \
                                        dirn * conf.CAR_GAP[lane_mode]
                            stop = dirn * min(dirn * stop, dirn * this_stop)
                        new_v = dirn * (stop - front)
                        if 0 <= new_v < v:
                            current_mode = new_mode
                            # velocity reduced: we're stopping
                            v = new_v
                            if v == 0:
                                # to make sure we only stop if every car in
                                # front has stopped - in case this car is
                                # faster than the one in front
                                car.set_mode(lane_mode)
                    r.move_ip(v * dirn, 0)
                prev = car
