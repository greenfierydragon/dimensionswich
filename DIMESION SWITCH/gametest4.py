import pygame, random
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
chimg = "CHEST1.png"
def main():
    global cameraX, cameraY
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
    pygame.display.set_caption("Dimension Switch!")
    timer = pygame.time.Clock()

    up = down = left = right = switch = False
    
    levels = ["1-2","1-2"]
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
        currentlevel.update(switch, screen)
        switch = False

        # update player, draw everything else
        currentlevel.player.update(up, down, left, right, running, currentlevel)


        for e in currentlevel.currentWorld.entities:
             screen.blit(e.image, currentlevel.camera.apply(e))

        for e in currentlevel.entities:
             screen.blit(e.image, currentlevel.camera.apply(e))

        myfont = pygame.font.SysFont("monospace", 20)
        
        coins = myfont.render(str(currentlevel.player.coins) + " Coins", 1, (255,255,0))
        screen.blit(coins, (1, 1))
       
        
      

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
        self.masterxvel = 0
        self.movespeed = 4
        self.lastsl = Slime(0,0,False)
        self.coins = 0
        self.hasKey = False

    def update(self, up, down, left, right, running, level):
        
        if up:
            # only jump if on the ground
            if self.onGround: self.yvel -= 10
        if down:
            pass
        if running:
            self.xvel = 6
       
        if left:
            self.xvel = -self.movespeed
            self.masterxvel = 0
        if right:
            self.xvel = self.movespeed
            self.masterxvel = 0
        if not self.onGround:
            # only accelerate with gravity if in the air
            self.yvel += 0.3
            # max falling speed
            if self.yvel > 100: self.yvel = 100
        if not(left or right):
            self.xvel = 0
        # increment in x direction

        if self.masterxvel > 0:
            self.xvel = self.masterxvel
        self.rect.left += self.xvel
        # do x-axis collisions
        self.collide(self.xvel, 0, level, down)
        # increment in y direction
        self.rect.top += self.yvel
        # assuming we're in the air
        self.onGround = False;
        # do y-axis collisions
        self.collide(0, self.yvel, level, down)

        if not Rect(-32,-32,32*(level.width + 2),32*(level.height + 2)).contains(self.rect):
            self.Respawn(level)

       

    def collide(self, xvel, yvel, level, down):
        for p in level.currentWorld.platforms:
            if pygame.sprite.collide_rect(self, p):

                if p.solid:
                    if xvel > 0:
                        self.rect.right = p.rect.left
                        #print "collide right"
                    if xvel < 0:
                        self.rect.left = p.rect.right
                        #print "collide left"
                    if yvel > 0:
                        self.rect.bottom = p.rect.top
                        self.onGround = True
                        self.yvel = 0
                    if yvel < 0:
                        self.rect.top = p.rect.bottom
                        
                if isinstance(p, ExitBlock):
                    print "done"
                    level.nextlevel()

                if isinstance(p, Block2):
                    if down:
                        p.Break(p, 0, level)

                    else:
                        p.Break(p, 1000, level)

                if isinstance(p, Chest) and self.hasKey:
                    p.opened(level)
                    self.hasKey = False
                    

                
                    
                        

                
                   
                    
        for s in level.currentWorld.spikes:
            if pygame.sprite.collide_rect(self, s):
                self.Respawn(level)

        for t in level.currentWorld.tumble:
            if pygame.sprite.collide_rect(self, t):
                if t.dark:
                    self.yvel =  -24
                    self.masterxvel = 8
                else:
                    self.rect.left = t.rect.left
                    self.rect.top = t.rect.top
        
        for sl in level.currentWorld.slime:
            if pygame.sprite.collide_rect(self, sl):
                if sl.dark:
                    self.movespeed = 12
                else:
                    self.movespeed = 0
                self.lastsl = sl
            
            if not pygame.sprite.collide_rect(self, self.lastsl):
                self.movespeed = 4

        for c in level.currentWorld.coins:
            if pygame.sprite.collide_rect(self, c):
                if not level.light:
                    self.Respawn(level)
                    print "Respawn"
                else:
                    c.collect(level)

        if pygame.sprite.collide_rect(self, level.currentWorld.key):
            level.currentWorld.key.collect(level)
            self.hasKey = True


    def Respawn(self, level):
        self.rect = Rect(32,32,21,31)
        level.light = True
        level.currentWorld = level.lightWorld
        level.bg.fill(Color("#008bff"))
        level.darkWorld.clear()
        level.darkWorld.generate(True)
        self.yvel = 0
                

class Platform(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.rect = Rect(x, y, 32, 32)
        self.dark = dark

        def update(self):
            pass

class Spike(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.solid = True
        self.image = pygame.image.load("SPIKE1.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)
        self.dark = dark

class Spike2(Entity):
    def __init__(self, x, y, dark):
        Entity.__init__(self)
        self.solid = True
        self.image = pygame.image.load("SPIKE2.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)
        self.dark = dark


    def update(self):
        pass

class ExitBlock(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y, dark)
        self.solid = False
        self.image = pygame.image.load("end.png")
        

class Block1(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y, dark)
        self.solid = True
        self.image = pygame.image.load("BLOCK1.png")
        self.image.convert()

class Block2(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y, dark)
        self.solid = True
        self.image = pygame.image.load("BLOCK2.png")
        self.image.convert()
        self.breaktime = 100
        self.done = False
        self.t1 = 0

    def Break(self, p, time, level):

         if not self.done:
             self.t1 = pygame.time.get_ticks()
             #print self.t1
             self.done = True
         t2 = pygame.time.get_ticks()
         if t2 - self.t1 >=  time:
              p.kill()
              level.currentWorld.platforms.remove(p)
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
                   #print "tumbleweed collide"

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
        Platform.__init__(self, x, y, dark)
        self.solid = True
        self.image = pygame.image.load("CHEST1.png")
        self.image.convert() 
        if dark:
            self.content = random.randint(0, 100)
            
        else:
            self.content = random.randint(90, 100)
        if self.content > 91 and dark: 
            self.coincontent = random.randint(512, 2048)
        elif self.content > 91:
            self.coincontent = random.randint(1, 128)
        else:
            self.coincontent = 0

    def opened(self, level):
        if self.coincontent > 0:
            level.player.coins += self.coincontent
        else:
            level.player.Respawn(level)
        self.image = pygame.image.load("CHEST2.png")
        self.image.convert()
        
            


class movingPlatform(Platform):
    def __init__(self, x, y, dark):
        Platform.__init__(self, x, y, dark)
        self.origin = Rect(x,y,32,32)
        print self.origin.top
        print self.origin.left
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
            #print "platout"
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
        #print "collected"
        self.kill()
        level.currentWorld.coins.remove(self)
        level.player.coins += 1

class Key(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.image = pygame.image.load("key.png")
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

    def collect(self, level):
        #print "collected"
        self.kill()
        
        
        

        
    

        
class Level:
    def __init__(self, levels, bgcolour):
   
        self.levelname = levels[0]
        
        x = y = 0
        
        mapimg = cv2.imread(self.levelname + ".png")
        mapheight, mapwidth, c = mapimg.shape
        self.player = Player(32, 32)
      

        self.bg = Surface((32,32))
        self.bg.convert()
        self.bg.fill(Color("#008bff"))
        self.light = True
                
        self.lightWorld = World(self.levelname + ".png", False)
        self.darkWorld = World(self.levelname + "dark.png", True)
        self.currentWorld = self.lightWorld

        self.entities = pygame.sprite.Group()
        self.width = mapwidth
        self.height = mapheight

        total_level_width  = mapwidth*32
        total_level_height = mapheight*32
        self.camera = Camera(complex_camera, total_level_width, total_level_height)
        self.entities.add(self.player)
        

    def switch(self):
        
        if self.light:
            
            self.light = False
            self.currentWorld = self.darkWorld
            self.bg.fill(Color("#530c77"))
            self.darkWorld.clear()
            self.darkWorld.generate(True)
            
            

        elif not self.light:
            
            self.light = True
            self.currentWorld = self.lightWorld
            self.bg.fill(Color("#008bff"))
        

    def update(self, switch, screen):
        
        if switch:
            
            self.switch()

        

        for t in self.currentWorld.tumble:
            t.update(self.currentWorld.platforms, self.currentWorld.spikes)
        for p in self.currentWorld.movingPlat:
            p.update()

       
        
            

        


    def nextlevel(self):
        self.name = self.levels[1]
        self.buildlight()
        self.player.rect = Rect(32, 32, 21, 31)

        

class World():
     def __init__(self, name, dark):
        self.levelname = name
        self.dark = dark
        self.platforms = []
        self.movingPlat = []
        self.spikes = []
        self.tumble = []
        self.coins = []
        self.slime = []
        self.entities = pygame.sprite.Group()
        self.generate(self.dark)

     def generate(self, dark):
        x = y = 0
        mapimg = cv2.imread(self.levelname)
        mapx = 0
        mapy = 0
        mapheight, mapwidth, c = mapimg.shape
    
    
        # build the level
        for mapy in range(0,(mapheight)):
            for mapx in range(0,(mapwidth)):
                px = mapimg[mapy,mapx]
                
                if px[0] == 0 and px[1] == 0 and px[2] == 0:
                    p = Block1(x, y, dark)
                    self.platforms.append(p)
                    self.entities.add(p)
                if px[0] == 0 and px[1] == 0 and px[2] == 255:
                  
                    s = Spike(x,y,dark)
                    self.spikes.append(s)
                    self.entities.add(s)
                if px[0] == 255 and px[1] == 0 and px[2] == 0:
                    e = ExitBlock(x,y, dark)
                    self.platforms.append(e)
                    self.entities.add(e)
                if px[0] == 23 and px[1] == 23 and px[2] == 23:
                    p = Block2(x,y, dark)
                    self.platforms.append(p)
                    self.entities.add(p)
                if px[0] == 0 and px[1] == 1 and px[2] == 255:
                   
                    s = Spike2(x,y, dark)
                    self.spikes.append(s)
                    self.entities.add(s)
                if px[0] == 0 and px[1] == 255 and px[2] == 0:
                  
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
                if px[0] == 191 and px[1] == 191 and px[2] == 191:
                        c = Coin(x, y, dark)
                        self.coins.append(c)
                        self.entities.add(c)
                if px[0] == 0 and px[1] == 128 and px[2] == 255:
                        self.key = Key(x,y)
                        self.entities.add(self.key)
                        print "key"
                

            
                x += 32
            y += 32
            x = 0 


     def clear(self):
        self.platforms = []
        self.movingPlat = []
        self.spikes = []
        self.tumble = []
        self.coins = []
        self.slime = []
        self.entities = pygame.sprite.Group()
        


if __name__ == "__main__":
    main()
