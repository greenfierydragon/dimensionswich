import pygame, random
from pygame import *
from pygame.locals import *
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
    
    levels = ["1-1","1-2","1-3","1-4"]
    currentlevel = Level(levels)

    

    while 1:
        timer.tick(60)

        running = False
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.load("music.wav")
            pygame.mixer.music.set_volume(0.30)
            pygame.mixer.music.play(-1)

        for e in pygame.event.get():
            if e.type == QUIT: raise SystemExit, "QUIT"
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                raise SystemExit, "ESCAPE"
            if e.type == KEYDOWN and e.key == K_UP:
                up = True
                jump = pygame.mixer.Sound("jump.wav")
                jump.set_volume(0.10)
                jump.play()
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
            if e.type == KEYDOWN and e.key == K_s:
			    Shop(currentlevel.player.coins, screen)

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
            if Rect(0, 0, WIN_WIDTH, WIN_HEIGHT).colliderect(currentlevel.camera.apply(e)):
                
            
                screen.blit(e.image, currentlevel.camera.apply(e))
            else:
                pass
            
        for e in currentlevel.entities:
             screen.blit(e.image, currentlevel.camera.apply(e))

        

        

        myfont = pygame.font.SysFont("monospace", 20)
        
        coins = myfont.render(str(currentlevel.player.coins) + " Coins", 1, (255,255,0))
        screen.blit(coins, (1, 1))
        yvel = myfont.render(str(currentlevel.player.yvel) + " yvel", 1, (255,255,0))
        screen.blit(yvel, (1, 20))

        
      

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
            if self.onGround:
                self.yvel -= 10
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
            if pygame.sprite.collide_rect(self, p) and Rect(0, 0, WIN_WIDTH, WIN_HEIGHT).colliderect(level.camera.apply(p)):

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
                    self.beat = pygame.mixer.Sound("end.wav")
                    self.beat.play()
                    level.nextlevel()
                    
                if isinstance(p, Block2):
                    if down:
                        p.Break(p, 0, level)

                    else:
                        p.Break(p, 1000, level)

                if isinstance(p, Chest) and self.hasKey:
                    p.opened(level)
                    self.hasKey = False

                if isinstance(p, movingPlatform) and yvel != 0:
                    
                    if (yvel - p.yvel) > 0:
                        self.rect.bottom = p.rect.top
                        self.onGround = True
                        self.yvel = p.yvel
                    if (yvel - p.yvel) < 0:
                        self.rect.top = p.rect.bottom

                
                    
                        

                
                   
                    
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
        self.deadsound = pygame.mixer.Sound("dead.wav")
        self.deadsound.play()        

                
class Sprite(Entity):
    def __init__(self, x, y, width, height, dark):
        Entity.__init__(self)
        self.rect = Rect(x, y, width, height)
        self.dark = dark

        def update(self):
            pass

class Spike(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
        self.solid = True
        self.dark = dark

        if dark:
            self.image = pygame.image.load("SPIKE2.png")
        else:
            self.image = pygame.image.load("SPIKE1.png")
        self.image.convert()
        

class ExitBlock(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
        self.solid = False
        self.image = pygame.image.load("end.png")
        

class Block1(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
        self.solid = True
        self.image = pygame.image.load("BLOCK1.png")
        self.image.convert()

class Block2(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
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

class Tumbleweed(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
        self.dark = dark
        self.onGround = True
        self.yvel = 0
        
        
        if dark:
            self.image = pygame.image.load("TUMWEED2.png")
            self.xvel = 5
            self.yvel = 0
        else:
            self.image = pygame.image.load("TUMWEED1.png")
            self.xvel = 2
            self.yvel = 0
        self.image.convert()
        


    def update(self, level):
        
        if Rect(0, 0, WIN_WIDTH, WIN_HEIGHT).colliderect(level.camera.apply(self)):
            if not self.onGround:
                # only accelerate with gravity if in the air
                self.yvel += 0.3
                # max falling speed
                if self.yvel > 100: self.yvel = 100
            # increment in x direction

            # do x-axis collisions
            self.collide(self.xvel, 0, level)
            # increment in y direction
            self.rect.top += self.yvel
            # assuming we're in the air
            self.onGround = False;
            # do y-axis collisions
            self.collide(0, self.yvel, level)
          
            self.rect.left += self.xvel
        

    def collide(self, xvel, yvel, level):
        for p in level.currentWorld.platforms:
            if pygame.sprite.collide_rect(self, p):

                if p.solid:
                    if xvel > 0:
                        self.xvel = -self.xvel
                        #print "collide right"
                    if xvel < 0:
                        self.xvel = -self.xvel
                        #print "collide left"
                    if yvel > 0:
                        self.rect.bottom = p.rect.top
                        self.onGround = True
                        self.yvel = 0
                    if yvel < 0:
                        self.rect.top = p.rect.bottom

        
        
class Slime(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 5, dark)
        self.dark = dark
        
        self.image = pygame.image.load("SLIME.png")
        self.image.convert()

class Chest(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
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
        self.openedmusic = pygame.mixer.Sound("open.wav")
        self.openedmusic.play()
            


class movingPlatform(Sprite):
    def __init__(self, x, y, dark):
        Sprite.__init__(self, x, y, 32, 32, dark)
        self.origin = Rect(x,y,32,32)
        print self.origin.top
        print self.origin.left
        self.solid = False
        self.image = pygame.image.load("PLAT.png")
        self.image.convert()

        if dark:
            self.yvel = 2
        else:
            self.yvel = -2

    def update(self, level):
        self.rect.top += self.yvel
        if not Rect(-32,-32,32*(level.width + 2),32*(level.height + 2)).contains(self.rect):
            #print "platout"
            self.rect = Rect(self.origin.left, self.origin.top, 32, 32)
            #self.rect = self.origin
            

class Coin(Sprite):
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
        
class Shop():
    def __init__(self, coins, screen):
        coins
        print "shop"
        self.img1 = pygame.image.load("UNLOCK.png")
        self.rect = Rect(768, 608, 32, 32)
        screen.blit(self.img1, self.rect1)
		    
        
    
	
        
        
        

        
    

        
class Level:
    def __init__(self, levels):

        self.levels = levels
        try:
            self.id = 0
            self.levelname = levels[self.id]
        except:
            self.myfont = pygame.font.SysFont("monospace", 100)
            self.text = self.myfont.render("concratulations you beat the game!", 1, (255,255,0))
            screen.blit(text, (400, 320))
        
			
        
        self.init()
        
    def init(self):
        mapimg = pygame.image.load(self.levelname + ".png")
        self.shop = False
        
        mapwidth = mapimg.get_width()
        mapheight = mapimg.get_height()
        
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
    def shop(self):
	    self.shop = True
	    self.inshop()
    def inshop(self):
        while self.shop:
            self.bg.fill(Color("#442600"))
   

    
    def switch(self):
        
        if self.light:
            
            
            if not self.shop:
                self.bg.fill(Color("#530c77"))
                self.light = False
            self.currentWorld = self.darkWorld
            self.darkWorld.clear()
            self.darkWorld.generate(True)
            
            
            

        elif not self.light:
            
            
            if not self.shop:
                self.bg.fill(Color("#008bff"))
                self.light = True
            self.currentWorld = self.lightWorld
        else:
            self.inshop()

        

    def update(self, switch, screen):
        
        if switch:
            
            self.switch()
        if self.shop:
			self.bg.fill(Color("#442600"))
			self.swich()
			

        

        for t in self.currentWorld.tumble:
            t.update(self)
        for p in self.currentWorld.movingPlat:
            p.update(self)
        for mimicker in self.currentWorld.mimicker:
            mimicker.update(self)

       
        
            

        


    def nextlevel(self):
        self.id += 1
        self.levelname = self.levels[self.id]
        self.init()
        

        

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
        self.mimicker = []
        self.entities = pygame.sprite.Group()
        self.generate(self.dark)

     def generate(self, dark):
        x = y = 0
        mapimg = pygame.image.load(self.levelname)
        mapArray = pygame.PixelArray(mapimg)
        mapx = 0
        mapy = 0
        mapwidth = mapimg.get_width()
        mapheight = mapimg.get_height()
    
    
        # build the level
        for mapy in range(0,(mapheight)):
            for mapx in range(0,(mapwidth)):
                
                if mapArray[mapx,mapy] == mapimg.map_rgb(0, 0, 0):
                    p = Block1(x, y, dark)
                    self.platforms.append(p)
                    self.entities.add(p)
                if mapArray[mapx,mapy] == mapimg.map_rgb(255, 0, 0):
                    s = Spike(x,y,dark)
                    self.spikes.append(s)
                    self.entities.add(s)
                if mapArray[mapx,mapy] == mapimg.map_rgb(0, 0, 255):
                    e = ExitBlock(x,y, dark)
                    self.platforms.append(e)
                    self.entities.add(e)
                if mapArray[mapx,mapy] == mapimg.map_rgb(23, 23, 23):
                    p = Block2(x,y, dark)
                    self.platforms.append(p)
                    self.entities.add(p)
                if mapArray[mapx,mapy] == mapimg.map_rgb(255, 1, 0):
                    s = Spike(x,y, dark)
                    self.spikes.append(s)
                    self.entities.add(s)
                if mapArray[mapx,mapy] == mapimg.map_rgb(0, 255, 0):
                    t = Tumbleweed(x,y, dark)
                    self.tumble.append(t)
                    self.entities.add(t)
                if mapArray[mapx,mapy] == mapimg.map_rgb(255, 0, 255):
                    sl = Slime(x, y, dark)
                    self.slime.append(sl)
                    self.entities.add(sl)
                if mapArray[mapx,mapy] == mapimg.map_rgb(64, 64, 64):
                    c = Chest(x, y, dark)
                    self.platforms.append(c)
                    self.entities.add(c)
                if mapArray[mapx,mapy] == mapimg.map_rgb(128, 128, 128):
                    p = movingPlatform(x, y, dark)
                    self.platforms.append(p)
                    self.movingPlat.append(p)
                    self.entities.add(p)
                if mapArray[mapx,mapy] == mapimg.map_rgb(191, 191, 191):
                        c = Coin(x, y, dark)
                        self.coins.append(c)
                        self.entities.add(c)
                if mapArray[mapx,mapy] == mapimg.map_rgb(255, 128, 0):
                        self.key = Key(x,y)
                        self.entities.add(self.key)
                

            
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
