from conf import conf
from util import ir

#   object methods:
# Obj.interact(frog): perform basic action on object
# Obj.on_crash(frog, road): object has been hit by a car
# Obj.on_uncrash(frog, road): object has been removed from the road
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use_on_<ident(obj)>(frog, obj, pos): use held object on obj at pos
#   subclasses may implement event handlers
# Holdable.on_grab(): when this is grabbed; called before pos is set to None
#                     (but it might already be None)
# Holdable.on_drop(pos)

# every solid holdable object must become non-solid on crash

def ident (obj):
    if not isinstance(obj, type):
        obj = obj.__class__
    s = obj.__name__
    words = []
    i = 0
    for j, c in enumerate(s):
        if c.isupper() and j > i:
            words.append(s[i].lower() + s[i + 1:j])
            i = j
    if len(s) > i:
        words.append(s[i].lower() + s[i + 1:])
    return ' '.join(words)

def name (obj):
    if not isinstance(obj, type):
        obj = obj.__class__
    if hasattr(obj, 'name'):
        return obj.name
    return ident(obj)

def article (obj):
    if not isinstance(obj, basestring):
        obj = name(obj)
    return 'an' if obj[0].lower() in 'aeiou' else 'a'


# global / base classes


class Obj (object):
    desc = None
    solid = True
    holdable = False
    held = False

    def __init__ (self, level, pos = None):
        self.level = level
        self.pos = pos if pos is None else list(pos)

    def interact (self, frog):
        if self.desc is not None:
            self.level.say(self.desc)

    def replace (self, obj):
        if issubclass(obj, Obj):
            obj = obj(self.level)
        self.level.rm_obj(self)
        self.level.add_obj(obj, self.pos)
        obj.pos = self.pos


class OneTileObj (Obj):
    def __init__ (self, level, pos = None):
        Obj.__init__(self, level, pos)
        fn = ('obj', self.__class__.__name__.lower() + '.png')
        self.img = level.game.img(fn)
        self._offset = [ir(float(t_s - i_s) / 2) for t_s, i_s in
                           zip(conf.TILE_SIZE, self.img.get_size())]

    def set_img (self, img):
        self.img = img
        if not self.held:
            self.level.change_tile(self.pos)

    def draw (self, screen, pos = None):
        x, y = self.pos if pos is None else pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.img, (x * sx + ox, y * sy + oy))


class Holdable (OneTileObj):
    holdable = True
    # subclasses may set:
    #   squash_obj: Obj instance or subclass to replace with when put on the
    #               road
    #   squash_desc: what to say when put on the road
    squash_obj = None
    squash_desc = None

    def __init__ (self, *args, **kw):
        OneTileObj.__init__(self, *args, **kw)
        self.held = False
        if kw.get('held', False):
            self.grab()

    def on_grab (self):
        pass

    def grab (self):
        if not self.held:
            self.held = True
            # might not be on the ground
            if self.pos is not None:
                self.level.rm_obj(self)
            self.on_grab()
            self.pos = None

    def on_drop (self, pos):
        pass

    def drop (self, pos):
        if self.pos is None:
            self.held = False
            self.pos = list(pos)
            self.level.add_obj(self, pos)
            self.on_drop(pos)

    def replace (self, obj, drop_if_held = False):
        if self.held:
            frog = self.level.frog
            frog.destroy()
            if issubclass(obj, Obj):
                obj = obj(self.level)
            if drop_if_held:
                frog.drop(obj)
            else:
                frog.grab(obj)
        else:
            Obj.replace(self, obj)

    def on_crash (self, frog, road):
        if self.squash_desc is not None:
            self.level.say(self.squash_desc)
        if self.squash_obj is not None:
            self.replace(self.squash_obj)


class Edible (Holdable):
    # subclasses may set:
    #   drop_obj: Obj instance or subclass to drop after eating
    #   msg: what to say when eating (overrides default)
    drop_obj = None
    msg = None

    def use_on_frog (self, frog, obj, pos):
        frog.destroy()
        if self.msg is None:
            msg = 'I eat the {}.'.format(name(self))
        else:
            msg = self.msg
        self.level.say(msg)
        if self.drop_obj is not None:
            self.replace(self.drop_obj)


# level 0


class Fruit (Edible):
    squash_desc = 'What a waste.  It wasn\'t even mine...'

    def use_on_basket (self, frog, basket, pos):
        self.level.say('I put the {} back in the basket.'.format(name(self)))
        frog.destroy()
        basket.add(self.__class__)


class BananaPeel (Holdable):
    solid = False
    desc = 'The peel of a banana I ate.  Leaving it on the floor like that ' \
           'is probably dangerous.'

    def on_crash (self, frog, road):
        self.level.say('...Not sure why I thought that would do something.')


class SquashedBanana (OneTileObj):
    solid = False
    desc = 'Messy.'


class Banana (Fruit):
    desc = 'A yellow banana.'
    drop_obj = BananaPeel
    squash_obj = SquashedBanana


class SquashedOrange (OneTileObj):
    solid = False
    desc = 'Messy.'


class OrangePeel (Holdable):
    solid = False
    desc = 'The peel of an orange I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Orange (Fruit):
    desc = 'An orange.  (It\'s orange.)'
    drop_obj = OrangePeel
    squash_obj = SquashedOrange


class SquashedApple (OneTileObj):
    solid = False
    desc = 'Messy.'


class AppleCore (Holdable):
    desc = 'The core of an apple I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Apple (Fruit):
    desc = 'A red apple.'
    drop_obj = AppleCore
    squash_obj = SquashedApple


class SquashedBasket (OneTileObj):
    solid = False
    desc = 'I\'d rather not look in there.'


class LumpOfCoal (Holdable):
    desc = 'Who wouldn\'t take a lump of coal on a picnic?'

    def use_on_frog (self, frog, obj, pos):
        self.level.say('I eat the coal.  Just kidding!  Don\'t eat coal, '
                       'kids.')

    def use_on_basket (self, frog, basket, pos):
        self.level.say('I put the {} back in the basket.'.format(name(self)))
        frog.destroy()
        basket.add(self.__class__)


class Basket (Holdable):
    squash_obj = SquashedBasket
    squash_desc = 'Being a frog, wreaking havoc...what a life.'

    def __init__ (self, level, *args, **kw):
        Holdable.__init__(self, level, *args, **kw)
        self._full_img = self.img
        self._empty_img = level.game.img(('obj', 'emptybasket.png'))
        self.contents = [Apple, Banana, Orange, LumpOfCoal, Apple, Banana,
                         Orange, Apple, Banana, Orange]

    def interact (self, frog):
        if self.contents:
            msg = 'A basket of fruit.  '
            if frog.item is None:
                level = self.level
                obj = self.contents.pop(0)
                label = name(obj)
                msg += 'I take {} {}.'.format(article(label), label)
                if issubclass(obj, LumpOfCoal):
                    msg += '  Wait, what?'
                frog.grab(obj(level))
                if len(self.contents) == 0:
                    # empty: replace image
                    self.set_img(self._empty_img)
            else:
                msg += 'I would take something if my hands weren\'t full.'
        else:
            msg = 'The basket\'s empty now.  What a mess I\'ve made.'
        self.level.say(msg)

    def on_grab (self):
        x, y = self.pos
        objs = self.level.objs[x][y]
        if any(isinstance(o, PuddleOfOil) for o in objs):
            self.level.say('There\'s a puddle of oil under here...')

    def add (self, cls):
        self.contents.insert(0, cls)
        self.set_img(self._full_img)


class PicnicBlanket (Holdable):
    solid = False
    desc = 'A picnic blanket.  I don\'t tend to use those.'

    def dirty (self):
        self.level.say('The blanket is now ruined.  I\'m such an animal.')
        self.replace(OilyBlanket)

    def use_on_puddle_of_oil (self, frog, puddle, pos):
        self.dirty()

    def on_drop (self, pos):
        objs = self.level.objs[pos[0]][pos[1]]
        if any(isinstance(o, PuddleOfOil) for o in objs):
            self.dirty()


class OilyBlanket (Holdable):
    solid = False
    desc = 'The picnic blanket, now covered in oil.'

    def on_crash (self, frog, road):
        road.crash(self.pos)


class PuddleOfOil (OneTileObj):
    solid = False
    desc = 'A puddle of slippery oil.  Probably the work of humans.'


# level 1


class TrafficLight (OneTileObj):
    def __init__ (self, level, *args, **kwargs):
        OneTileObj.__init__(self, level, *args, **kwargs)
        if self.pos[1] < level.road.tile_rect[1]:
            lane = 0
        else:
            lane = len(conf.ROAD_LANES) - 1
        self._dirn = level.road.lane_dirn(lane)
        self._state = None
        initial = conf.CIRCUIT_INITIAL_STATE
        self._stopped = not (initial in conf.TRAFFIC_LIGHT_STOP_STATES)
        self.set_state(initial)
        level.tls.append(self)

    def set_state (self, state):
        old_state = self._state
        if old_state != state:
            self._state = state
            # TODO: update image
            # update whether stopped
            stop = state in conf.TRAFFIC_LIGHT_STOP_STATES
            if self._stopped != stop:
                self._stopped = stop
                road = self.level.road
                dirn = self._dirn
                lanes = [lane for lane in xrange(len(conf.ROAD_LANES))
                        if road.lane_dirn(lane) == dirn]
                if stop:
                    x = self.pos[0]
                    dirn = self._dirn
                    road.stop_lanes(*((lane, x - dirn) for lane in lanes))
                else:
                    road.start_lanes(*lanes)

    def interact (self, frog):
        self.level.circuit.show()
