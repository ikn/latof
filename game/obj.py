from conf import conf
from util import ir
import objhelpers

#   object methods:
# Obj.interact(): perform basic action on object
# Holdable.grab(): pick up object
# Holdable.drop(pos): drop held object at pos
# Holdable.use(obj, pos): use held object on object obj at pos

def name (obj):
    s = obj.__class__.__name__
    words = []
    i = 0
    for j, c in enumerate(s):
        if c.isupper():
            words.append(s[i:j])
            i = j
    return ' '.join(words)

def article (obj):
    if not isinstance(obj, basestring):
        obj = name(obj)
    return 'an' if obj[0] in 'aeiou' else 'a'


class Obj (object):
    def __init__ (self, level, pos = None):
        self.level = level
        self.pos = pos if pos is None else list(pos)


class Road (Obj):
    solid = True

    def __init__ (self, level):
        self.level = level
        sx, sy = conf.TILE_SIZE
        for i in xrange(600 / sx):
            for j in xrange(200 / sy, 400 / sy):
                level.add_obj(self, (i, j))

    def interact (self, frog):
        self.level.say('a busy road.')


class DrawSelf (Obj):
    solid = True

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


class Static (DrawSelf):
    holdable = False


class Holdable (DrawSelf):
    holdable = True

    def __init__ (self, *args, **kw):
        Obj.__init__(self, *args, **kw)
        self.held = False
        if kw.get('held', False):
            self.grab()

    def grab (self):
        if not self.held:
            self.held = True
            self.level.rm_obj(self, self.pos)
            self.pos = None

    def drop (self, pos):
        if self.held:
            self.held = False
            self.level.add_obj(self, pos)
            self.pos = list(pos)


class Autograb (Holdable):
    def interact (self, frog):
        frog.grab(self)


class Edible (Autograb):
    def eat (self, obj, drop = None):
        # drop is Obj instance or Obj subclass or None
        if self.held and isinstance(obj, Frog):
            obj.destroy()
            if isinstance(drop, Obj):
                obj.drop(drop)
            elif drop is not None:
                obj.drop(drop(self.level))
            self.level.say('I eat the {}.'.format(name(self)))


class Basket (Static):
    def interact (self, frog):
        self.level.say('it\'s a basket containing some things.')


class Banana (Edible):
    def use (self, obj, pos):
        self.eat(obj, BananaPeel)


class BananaPeel (Autograb):
    pass


class Orange (Edible):
    def use (self, obj, pos):
        self.eat(obj, OrangePeel)


class OrangePeel (Autograb):
    pass


class Apple (Edible):
    def use (self, obj, pos):
        self.eat(obj, AppleCore)


class AppleCore (Autograb):
    pass
