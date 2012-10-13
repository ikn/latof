from conf import conf
from util import ir
import objhelpers

#   object methods:
# Obj.interact(): perform basic action on object
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use(obj, pos): use held object on object obj at pos
#   subclasses may implement event handlers
# Holdable.on_grab()
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
    holdable = False
    desc = None
    solid = True

    def __init__ (self, level, pos = None):
        self.level = level
        self.pos = pos if pos is None else list(pos)

    def interact (self, frog):
        if self.desc is not None:
            self.level.say(self.desc)


class Road (Obj):
    desc = 'a busy road.'

    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        for i in xrange(600 / sx):
            for j in xrange(200 / sy, 400 / sy):
                level.add_obj(self, (i, j))


class Placeable (Obj):
    def __init__ (self, level, pos = None):
        Obj.__init__(self, level, pos)
        self.img = level.game.img(self.__class__.__name__.lower() + '.png')
        self._offset = [ir(float(t_s - i_s) / 2) for t_s, i_s in
                           zip(conf.TILE_SIZE, self.img.get_size())]

    def draw (self, screen):
        x, y = self.pos
        sx, sy = conf.TILE_SIZE
        ox, oy = self._offset
        screen.blit(self.img, (x * sx + ox, y * sy + oy))


class Holdable (Placeable):
    holdable = True

    def __init__ (self, *args, **kw):
        Placeable.__init__(self, *args, **kw)
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
            self.pos = None
            self.on_grab()

    def on_drop (self, pos):
        pass

    def drop (self, pos):
        if self.pos is None:
            self.held = False
            self.level.add_obj(self, pos)
            self.pos = list(pos)
            self.on_drop(pos)

    def use (self, frog, obj, pos):
        self.level.say('I won\'t gain anything from doing that')


class Edible (Holdable):
    # subclasses may set:
    #   drop_obj: Obj instance or subclass to drop after eating
    #   msg: what to say when eating (overrides default)
    drop_obj = None
    msg = None

    def use (self, frog, obj, pos):
        if self.held and obj is frog:
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


class BananaPeel (Holdable):
    solid = False
    desc = 'the peel of a banana I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Banana (Edible):
    desc = 'a yellow banana.'
    drop_obj = BananaPeel


class OrangePeel (Holdable):
    solid = False
    desc = 'the peel of an orange I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Orange (Edible):
    desc = 'an orange.  (It\'s orange.)'
    drop_obj = OrangePeel


class AppleCore (Holdable):
    solid = False
    desc = 'the core of an apple I ate.  Frogs can\'t be fined for ' \
           'littering, but it still makes me feel bad.'


class Apple (Edible):
    desc = 'a red apple.'
    drop_obj = AppleCore


class Basket (Holdable):
    fruit = list(sum(zip(*([f] * 3 for f in (Apple, Banana, Orange))), ()))

    def interact (self, frog):
        msg = 'a basket of fruit.  '
        if frog.item is None:
            level = self.level
            fruit = self.fruit.pop(0)
            label = name(fruit)
            msg += 'I take {} {}.'.format(article(label), label)
            frog.grab(fruit(level))
            if len(self.fruit) == 0:
                # empty: replace with EmptyBasket
                p = self.pos
                level.rm_obj(self, p)
                level.add_obj(EmptyBasket(level, p), p)
        else:
            msg += 'I would take something if my hands weren\'t full.'
        self.level.say(msg)

    def on_grab (self):
        self.level.say('there\'s a puddle of oil under here...')


class EmptyBasket (Holdable):
    desc = 'the basket\'s empty now.  What a mess I\'ve made.'

    def on_grab (self):
        self.level.say('there\'s a puddle of oil under here...')


class PicnicBlanket (Holdable):
    solid = False
    desc = 'a picnic blanket.  I don\'t tend to use those.'

    def use (self, frog, obj, pos):
        if isinstance(obj, PuddleOfOil):
            level = self.level
            level.say('the blanket is now ruined.  I\'m such an animal.')
            frog.destroy()
            frog.grab(OilyBlanket(level))


class OilyBlanket (Holdable):
    solid = False
    desc = 'the picnic blanket, now covered in oil.'

    def use (self, frog, obj, pos):
        if isinstance(obj, Road):
            frog.drop(self, pos)


class PuddleOfOil (Placeable):
    solid = False
    desc = 'a puddle of slippery oil.  This would have posed a hazard to me' \
           'before I realised I was self-aware.'
