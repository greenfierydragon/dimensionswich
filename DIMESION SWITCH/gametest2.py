import pygame
from pygame import *
import cv2
import numpy as np

WIN_WIDTH = 800
WIN_HEIGHT = 640
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)

DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
DEPTH = 32
FLAGS = 0
CAMERA_SLACK = 30

def main():
    global cameraX, cameraY
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Dimension Switch!")
    timer = pygame.time.Clock()

    up = down = left = right = switch = False
    
    levels = ["1-1","1-2"]
    currentlevel = Level(levels, "008bff")

    

    while 1:
        timer.tick(60)

        running = False

        for e in pygame.event.get():
            if e.type == QUIT: raise SystemExit, "QUIT"
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                raise SystemExit, "ESCAPE"
            if e.type == KEYDOWN and e.key == K_UP:
                up = True
            if e.type == KEYDOWN and e.key == K_DOWN:
                down = True
            if e.type == KEYDOWN and e.key == K_LEFT:
                left = True
            if e.type == KEYDOWN and e.key == K_RIGHT:
                right = True
            if e.type == KEYDOWN and e.key == K_SPACE:
                switch = True

            if e.type == KEYUP and e.key == K_UP:
                up = False
            if e.type == KEYUP and e.key == K_DOWN:
                down = False
            if e.type == KEYUP and e.key == K_RIGHT:
                right = False
            if e.type == KEYUP and e.key == K_LEFT:
                left = False
            if e.type == KEYUP and e.key == K_SPACE:
                switch = False

        # draw background
        for y in range(32):
            for x in range(32):
                screen.blit(currentlevel.bg, (x * 32, y * 32))

        currentlevel.camera.update(currentlevel.player)
        currentlevel.update(switch)

        # update player, draw everything else
        currentlevel.player.update(up, down, left, right, running, currentlevel.platforms, currentlevel.spikes, currentlevel, currentlevel.tumble)
        
        for e in currentlevel.entities:
            screen.blit(e.image, currentlevel.camera.apply(e))

        pygame.display.update()

class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)

def simple_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    return Rect(-l+HALF_WIDTH, -t+HALF_HEIGHT, w, h)

def complex_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t, _, _ = -l+HALF_WIDTH, -t+HALF_HEIGHT, w, h

    l = min(0, l)                           # stop scrolling at the left edge
    l = max(-(camera.width-WIN_WIDTH), l)   # stop scrolling at the right edge
    t = max(-(camera.height-WIN_HEIGHT), t) # stop scrolling at the bottom
    t = min(0, t)                           # stop scrolling at the top
    return Rect(l, t, w, h)

class Entity(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

class Player(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.xvel = 0
        self.yvel = 0
        self.onGround = False
        self.image = pygame.image.load("WIZ1.png")
        self.image.convert()
        self.rect = Rect(x, y, 21, 31)
        self.movespeed = 4
        self.lastsl = Slime(0,0,False)

    def update(self, up, down, left, right, running, platforms, spikes, level, tumble):
        
        if up:
            # only jump if on the ground
            if self.onGround: self.yvel -= 10
        if down:
            pass
        if running:
            self.xvel = 6
        if left:
            self.xvel = -self.movespeed
        if right:
            self.xvel = self.movespeed
        if not self.onGround:
            # only accelerate with gravity if in the air
            self.yvel += 0.3
            # max falling speed
            if self.yvel > 100: self.yvel = 100
        if not(left or right):
            self.xvel = 0
        # increment in x direction
        self.rect.left += self.xvel
        # do x-axis collisions
        self.collide(self.xvel, 0, platforms, spikes, level, down, tumble)
        # increment in y direction
        self.rect.top += self.yvel
        # assuming we're in the air
        self.onGround = False;
        # do y-axis collisions
        self.collide(0, self.yvel, platforms, spikes, level, down, tumble)

        if not Rect(-32,-32,32*72,32*42).contains(self.rect):
            self.Respawn(level)

       

    def collide(self, xvel, yvel, platforms, spikes, level, down, tumble):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, ExitBlock):
                    print "done"
                    level.nextlevel()

                if isinstance(p, Block2):
                    print "touching"
                    if down:
                        p.Break(p, 0, level)

                    else:
                        p.Break(p, 1000, level)
                    
                    
                   

                if p.solid:
                    if xvel > 0:
                        self.rect.right = p.rect.left
                        print "collide right"
                    if xvel < 0:
                        self.rect.left = p.rect.right
                        print "collide left"
                    if yvel > 0:
                        self.rect.bottom = p.rect.top
                        self.onGround = True
                        self.yvel = 0
                    if yvel < 0:
                        self.rect.top = p.rect.bottom
                    
        for s in spikes:
            if pygame.sprite.collide_rect(self, s):
                self.Respawn(level)

        for t in tumble:
            if pygame.sprite.collide_rect(self, t):
                if t.dark:
                    self.yvel =  -24
                else:
                    self.rect.left = t.rect.left
                    self.rect.top = t.rect.top
        
        for sl in level.slime:
            if pygame.sprite.collide_rect(self, sl):
                if sl.dark:
                    self.movespeed = 12
                else:
                    self.movespeed = 0
                self.lastsl = sl
            
            if not pygame.sprite.collide_rect(self, self.lastsl):
                self.movespeed = 4

        for c in level.coins:
            if pygame.sprite.collide_rect(self, c):
                if not level.light:
                    self.Respawn(level)
                    print "Respawn"
                else:
                    c.collect(level)
        

    def Respawn(self, level):
        self.rect = Rect(32,32,21,31)
        level.buildlight()
                

class Platform(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.rect = Rect(x, y, 32, 32)

        def update(self):
            pass

class Spike(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.solid = True
        self.image = pygame.image.load("SPIKE1.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

class Spike2(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.solid = True
        self.image = pygame.image.load("SPIKE2.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)   


    def update(self):
        pass

class ExitBlock(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)
        self.solid = False
        self.image = pygame.image.load("end.png")
        

class Block1(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)
        self.solid = True
        self.image = pygame.image.load("BLOCK1.png")
        self.image.convert()

class Block2(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)
        self.solid = True
        self.image = pygame.image.load("BLOCK2.png")
        self.image.convert()
        self.breaktime = 100
        self.done = False
        self.t1 = 0

    def Break(self, p, time, level):

         if not self.done:
             self.t1 = pygame.time.get_ticks()
             print self.t1
             self.done = True
         t2 = pygame.time.get_ticks()
         if t2 - self.t1 >=  time:
              p.kill()
              level.platforms.remove(p)
              self.prevtime = self.t1
              self.done = False

class Tumbleweed(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.dark = dark
        
        self.rect = Rect(x, y, 32, 32)
        if dark:
            self.image = pygame.image.load("TUMWEED2.png")
            self.xvel = 5
            self.yvel = 0
        else:
            self.image = pygame.image.load("TUMWEED1.png")
            self.xvel = 2
            self.yvel = 0
        self.image.convert()


    def update(self, platforms, spikes):

          
          self.rect.left += self.xvel
          for p in platforms:
               if pygame.sprite.collide_rect(self, p):
                   self.xvel = -self.xvel
                   print "tumbleweed collide"

          for s in spikes:
              if pygame.sprite.collide_rect(self, s):
                   self.xvel = -self.xvel

        
        
class Slime(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.dark = dark
        self.rect = Rect(x, y, 32, 5)
        self.image = pygame.image.load("SLIME.png")
        self.image.convert()

class Chest(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y)
        self.dark = dark
        self.solid = True
        self.image = pygame.image.load("CHEST1.png")
        self.image.convert()


class movingPlatform(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y)
        self.origin = Rect(x,y,32,32)
        print self.origin.top
        print self.origin.left
        self.dark = dark
        self.solid = True
        self.image = pygame.image.load("PLAT.png")
        self.image.convert()

        if dark:
            self.yvel = 2
        else:
            self.yvel = -2

    def update(self):
        self.rect.top += self.yvel
        if not Rect(-32,-32,32*72,32*42).contains(self.rect):
            print "platout"
            self.rect = Rect(self.origin.left, self.origin.right, 32, 32)

class Coin(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.dark = dark
        if dark:
            self.image = pygame.image.load("COIN2.png")
        else:
            self.image = pygame.image.load("COIN1ANO1.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)
        

    def collect(self, level):
        print "collected"
        self.kill()
        level.coins.remove(self)
        
        

        
    

        
class Level:
    def __init__(self, levels, bgcolour):
        self.bg = Surface((32,32))
        self.bg.convert()
        self.bg.fill(Color("#008bff"))
        self.levels = levels
        self.levelname = levels[0]
        self.light = True
        self.platforms = []
        self.spikes = []
        self.tumble = []
        self.coins = []
   
        
        x = y = 0
        print self.levelname + ".png"
        mapimg = cv2.imread(self.levelname + ".png")
        mapheight, mapwidth, c = mapimg.shape
        self.player = Player(32, 32)
        print mapwidth, mapheight

        
                

        self.buildlight()
        self.firstGen(False)
        self.firstGen(True)


        


        total_level_width  = mapwidth*32
        total_level_height = mapheight*32
        self.camera = Camera(complex_camera, total_level_width, total_level_height)
        self.entities.add(self.player)
        

    def buildlight(self):
        name = self.levelname + ".png"
        self.buildlevel(name, False)
        self.bg.fill(Color("#008bff"))
                
            
            
          

    def builddark(self):
        name = self.levelname + "dark.png"
        self.buildlevel(name, True)
        self.bg.fill(Color("#530c77"))
        

    def buildlevel(self, name, dark):
        self.platforms = []
        self.spikes = []
        self.tumble = []
        self.slime = []
        self.movingPlat = []
        self.entities = pygame.sprite.Group()
        self.entities.add(self.player)
        x = y = 0
        mapimg = cv2.imread(name)
        mapx = 0
        mapy = 0
        mapheight, mapwidth, c = mapimg.shape
        print mapwidth, mapheight

    
    
        # build the level
        for mapy in range(0,(mapheight)):
            for mapx in range(0,(mapwidth)):
                px = mapimg[mapy,mapx]
                
                if px[0] == 0 and px[1] == 0 and px[2] == 0:
                    p = Block1(x, y)
                    self.platforms.append(p)
                    self.entities.add(p)
                if px[0] == 0 and px[1] == 0 and px[2] == 255:
                    print "hi"
                    s = Spike(x,y)
                    self.spikes.append(s)
                    self.entities.add(s)
                if px[0] == 255 and px[1] == 0 and px[2] == 0:
                    e = ExitBlock(x,y)
                    self.platforms.append(e)
                    self.entities.add(e)
                if px[0] == 23 and px[1] == 23 and px[2] == 23:
                    p = Block2(x,y)
                    self.platforms.append(p)
                    self.entities.add(p)
                if px[0] == 0 and px[1] == 1 and px[2] == 255:
                    print "darkspike"
                    s = Spike2(x,y)
                    self.spikes.append(s)
                    self.entities.add(s)
                if px[0] == 0 and px[1] == 255 and px[2] == 0:
                    print "Tumbleweed"
                    t = Tumbleweed(x,y, dark)
                    self.tumble.append(t)
                    self.entities.add(t)
                if px[0] == 255 and px[1] == 0 and px[2] == 255:
                    sl = Slime(x, y, dark)
                    self.slime.append(sl)
                    self.entities.add(sl)
                if px[0] == 64 and px[1] == 64 and px[2] == 64:
                    c = Chest(x, y, dark)
                    self.platforms.append(c)
                    self.entities.add(c)
                if px[0] == 128 and px[1] == 128 and px[2] == 128:
                    p = movingPlatform(x, y, dark)
                    self.platforms.append(p)
                    self.movingPlat.append(p)
                    self.entities.add(p)

            
                x += 32
            y += 32
            x = 0

            for c in self.coins:
               self.entities.add(c) 



    def firstGen(self, dark):
        x = y = 0
        mapimg = cv2.imread(self.levelname + "dark.png")
        
            
        mapx = 0
        mapy = 0
        mapheight, mapwidth, c = mapimg.shape

        
        for mapy in range(0,(mapheight)):
            for mapx in range(0,(mapwidth)):
                px = mapimg[mapy,mapx]

                if px[0] == 191 and px[1] == 191 and px[2] == 191:
                    c = Coin(x, y, dark)
                    self.coins.append(c)
                    self.entities.add(c)

                x += 32
                
            y += 32
            x = 0
            


    def switch(self):
        
        if self.light:
            print "dark"
            self.light = False
            self.builddark()

        elif not self.light:
            print "light"
            self.light = True
            self.buildlight()

    def update(self, switch):
        
        if switch:
            
            self.switch()

        for t in self.tumble:
            t.update(self.platforms, self.spikes)
        for p in self.movingPlat:
            p.update()

    def nextlevel(self):
        self.name = self.levels[1]
        self.buildlight()
        self.player.rect = Rect(32, 32, 21, 31)
        


if __name__ == "__main__":
    main()
