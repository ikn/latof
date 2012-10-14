from conf import conf
from util import ir

#   object methods:
# Obj.interact(frog): perform basic action on object
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use_on_<name(obj)>(frog, obj, pos): use held object on obj at pos
#   subclasses may implement event handlers
# Holdable.on_grab(): when this is grabbed; called before pos is set to None
#                     (but it might already be None)
# Holdable.on_drop(pos)

def name (obj):
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


class Road (Obj):
    desc = 'A busy road.'

    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        for i in xrange(600 / sx):
            for j in xrange(200 / sy, 400 / sy):
                level.add_obj(self, (i, j))


class OneTileObj (Obj):
    def __init__ (self, level, pos = None):
        Obj.__init__(self, level, pos)
        self.img = level.game.img(self.__class__.__name__.lower() + '.png')
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
            self.level.add_obj(self, pos)
            self.pos = list(pos)
            self.on_drop(pos)


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
        drop = self.drop_obj
        if isinstance(drop, Obj):
            frog.drop(drop)
        elif drop is not None:
            frog.drop(drop(self.level))


# level 0


class Fruit (Edible):
    def use_on_basket (self, frog, basket, pos):
        msg = 'I put the {} back in the basket.'.format(name(self))
        self.level.say(msg)
        frog.destroy()
        basket.add_fruit(self.__class__)


class BananaPeel (Holdable):
    solid = False
    desc = 'The peel of a banana I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Banana (Fruit):
    desc = 'A yellow banana.'
    drop_obj = BananaPeel


class OrangePeel (Holdable):
    solid = False
    desc = 'The peel of an orange I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Orange (Fruit):
    desc = 'An orange.  (It\'s orange.)'
    drop_obj = OrangePeel


class AppleCore (Holdable):
    solid = True
    desc = 'The core of an apple I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Apple (Fruit):
    desc = 'A red apple.'
    drop_obj = AppleCore


class Basket (Holdable):
    fruit = list(sum(zip(*([f] * 3 for f in (Apple, Banana, Orange))), ()))

    def __init__ (self, level, *args, **kw):
        Holdable.__init__(self, level, *args, **kw)
        self._full_img = self.img
        self._empty_img = level.game.img('emptybasket.png')

    def interact (self, frog):
        if self.fruit:
            msg = 'A basket of fruit.  '
            if frog.item is None:
                level = self.level
                fruit = self.fruit.pop(0)
                label = name(fruit)
                msg += 'I take {} {}.'.format(article(label), label)
                frog.grab(fruit(level))
                if len(self.fruit) == 0:
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

    def add_fruit (self, cls):
        self.fruit.insert(0, cls)
        self.set_img(self._full_img)


class PicnicBlanket (Holdable):
    solid = False
    desc = 'A picnic blanket.  I don\'t tend to use those.'

    def use_on_puddle_of_oil (self, frog, puddle, pos):
        self.level.say('The blanket is now ruined.  I\'m such an animal.')
        frog.grab(OilyBlanket(self.level))


class OilyBlanket (Holdable):
    solid = False
    desc = 'The picnic blanket, now covered in oil.'

    def use_on_road (self, frog, road, pos):
        frog.drop(self, pos)


class PuddleOfOil (OneTileObj):
    solid = False
    desc = 'A puddle of slippery oil.  This would have posed a hazard to me ' \
           'before I realised I was self-aware.'
