"""
Created on Sat Sep  9 16:34:20 2023
@author: benjamon24_5
"""

import pygame
from pygame.locals import RLEACCEL
import random, math


# Define a Player object by extending pygame.sprite.Sprite
class Player(pygame.sprite.Sprite):
    def __init__(self, image, speed, max_x, max_y):
        super(Player, self).__init__()
        self.max_x = max_x
        self.max_y = max_y
        self.surf = pygame.image.load(image["file"]).convert()
        self.surf.set_colorkey(image["tcolor"], RLEACCEL)       
        self.rect = self.surf.get_rect(centery = self.max_y/2)
        self.speed = speed
        # 2 rect: one for the blit and one for the collisions
        # the collision rect is smaller because the player image doesn't fill the initial rect
        self.rect_blit = self.rect
        self.deflation = image["deflation"]
        self.rect = self.rect_blit.inflate(-self.deflation[0], -self.deflation[1])

        
    def move_up(self):
        self.rect_blit.move_ip(0, -self.speed)
        if self.rect_blit.top <= 0:
            self.rect_blit.top = 0

        
    def move_down(self):
        self.rect_blit.move_ip(0, self.speed)
        if self.rect_blit.bottom >= self.max_y:
            self.rect_blit.bottom = self.max_y      

        
    def move_left(self):
        self.rect_blit.move_ip(-self.speed, 0)
        if self.rect_blit.left < 0:
            self.rect_blit.left = 0

            
    def move_right(self):
        self.rect_blit.move_ip(self.speed, 0)
        if self.rect_blit.right > self.max_x:
            self.rect_blit.right = self.max_x

        
    def update(self):
        # the blit_rect has moved so we need to recreate the collision rect
        self.rect = self.rect_blit.inflate(-self.deflation[0], -self.deflation[1])

        
    def fire(self, color, speed, max_x, sound=None):
        # fire a laser (create a laser sprite at the tip of the player)
        if sound:
            sound.play()
        return Laser(self.rect.centery, self.rect.right, color, max_x, speed)
            
            
# Define the enemy object by extending pygame.sprite.Sprite
class Enemy(pygame.sprite.Sprite):
    def __init__(self, image, x, y, speeds=(5, 15)):
        super(Enemy, self).__init__()
        self.surf = pygame.image.load(image["file"]).convert()
        self.surf.set_colorkey(image["tcolor"], RLEACCEL)
        self.rect = self.surf.get_rect(center=(x, y))
        # the speed is randomly chosen between 2 values
        self.speed = random.randint(speeds[0], speeds[1])
        # 2 rect: one for the blit and one for the collisions
        # the collision rect is smaller because the player image doesn't fill the initial rect
        self.rect_blit = self.rect
        self.deflation = image["deflation"]
        self.rect = self.rect_blit.inflate(-self.deflation[0], -self.deflation[1])

    # Move the sprite based on speed
    # Remove the sprite when it passes the left edge of the screen   
    def update(self, targetx=0, targety=0):
        self.rect_blit.move_ip(-self.speed, 0) # moving to the left
        if self.rect_blit.right < 0:
            # the rect left the screen
            self.kill()
        # the blit_rect has moved so we need to recreate the collision rect
        self.rect = self.rect_blit.inflate(-self.deflation[0], -self.deflation[1])
            
# Extends Enemy, those are seeker misiles            
class SearchingEnemy(Enemy):
    def __init__(self, image, max_x, max_y, speeds=(5, 10)):
        super(SearchingEnemy, self).__init__(image, max_x, max_y, speeds)
        # the speed is randomly chosen between 2 values
        self.speedmax = random.randint(speeds[0], speeds[1])
        self.speedx = -self.speedmax # speedx won't change
        self.speedy = 0
        
            
    def update(self, targetx, targety):
        # speedy is set in function of the target position
        self.speedy = 0
        if self.rect_blit.centery < targety:
            # the further the target the bigger speedy
            self.speedy = int((targety - self.rect_blit.centery)/15) + 1
            if self.speedy >= self.speedmax:
                # speedy can't be bigger than speedmax
                self.speedy = self.speedmax -1
        if self.rect_blit.centery > targety: 
            self.speedy = int((targety - self.rect_blit.centery)/15) - 1
            if self.speedy <= -self.speedmax:
                self.speedy = -self.speedmax +1
        self.rect_blit.move_ip(self.speedx, self.speedy)
        # the blit_rect has moved so we need to recreate the collision rect
        self.rect = self.rect_blit.inflate(-self.deflation[0], -self.deflation[1])
        if self.rect_blit.right < 0:
            # the rect left the screen
            self.kill()   
            

# objects that will be in the background     
class BackgroundItem(pygame.sprite.Sprite):
    def __init__(self, image, max_x, max_y, speeds=(1, 4)):
        super(BackgroundItem, self).__init__()
        self.surf = pygame.image.load(image["file"]).convert()
        # the size of the object is randomly modified
        scale = random.uniform(0.5, 1.0) 
        self.surf = pygame.transform.scale(self.surf, (scale * image["size"][0], scale * image["size"][1]))
        self.surf.set_colorkey(image["tcolor"], RLEACCEL)
        self.rect = self.surf.get_rect(
            center=(
                random.randint(max_x + 20, max_x + 100),
                random.randint(0, max_y),
            )
        )
        self.speed = random.randint(*speeds)
    
    def update(self):
        self.rect.move_ip(-self.speed, 0) # moving to the left
        if self.rect.right < 0:
            # the rect left the screen
            self.kill()
            
# laser shots fired by the player            
class Laser(pygame.sprite.Sprite):
    def __init__(self, centery, left, color, max_x, speed):
        super(Laser, self).__init__()
        self.surf = pygame.Surface((5, 3))
        self.surf.fill(color)
        self.rect = self.surf.get_rect()
        self.rect.centery = centery
        self.rect.left = left
        self.speed = speed 
        self.max_x = max_x
        self.rect_blit = self.rect
        
    def update(self):
        self.rect_blit.move_ip(self.speed, 0) # moving to the right
        if self.rect_blit.left > self.max_x: # the rect left the screen
            self.kill()
            
            
# those trapez shapes are used to build the tunnel in PHASE 2            
class Trapez (pygame.sprite.Sprite):
    def __init__(self, width, lefth, righth, deltay=0, x=0, y=0, color=(0, 0, 0), speed=3):
        # left top corner defined by x and y
        # lefth and righth are the left and right heights
        # deltay defines where the right edge starts. It can be negative
        super(Trapez, self).__init__()
        self.width = width
        self.lefth = lefth
        self.righth = righth
        self.deltay = deltay
        self.x = x
        self.y = y
        self.color = color
        # the surface must be big enough to contain the trapez shape
        self.surf = pygame.Surface((width, max(righth + deltay, lefth, righth)))
        self.surf.fill((255, 255, 255))
        # Let's draw the trapez in the surface
        if deltay >= 0: 
            self.rect = pygame.draw.polygon(self.surf, color, [(0,0), (width, deltay), (width, righth + deltay), (0, lefth)])
        else:
            self.rect = pygame.draw.polygon(self.surf, color, [(0,-deltay), (width, 0), (width, righth), (0, lefth - deltay)])
        self.surf.set_colorkey((255, 255, 255), RLEACCEL)
        self.rect.top = y
        self.rect.left = x
        self.rect_blit = self.rect
        self.speed = speed
        
            
    def contains(self, px, py):
        # returns whether the point (px, py) is in the trapez
        
        self.x = self.rect.left
        
        if (self.x > px) or (px > self.x + self.width):
            return False
        
        x1, x2 = self.x, self.x + self.width
        
        if self.deltay >= 0:
            y1 = self.y
            y2 = self.y + self.deltay
        else:
            y1 = self.y - self.deltay
            y2 = self.y
        pymax = y1 + (px - x1) * (y2 - y1) / (x2 - x1)
        if py < pymax:
            return False
        
        if self.deltay >= 0:
            y1 = self.y + self.lefth
            y2 = self.y + self.deltay + self.righth
        else:
            y1 = self.y - self.deltay + self.lefth
            y2 = self.y + self.righth
        pymin = y1 + (px - x1) * (y2 - y1) / (x2 - x1)
        if py > pymin:
            return False
        
        return True
    
    
    def update(self):
        self.rect_blit.move_ip(-self.speed, 0) # move to the left
        if self.rect_blit.right < 0:
            self.kill()


# This is the final boss in the PHASE 3        
class DeathStar(pygame.sprite.Sprite):
    def __init__(self, image, min_x=500, max_x=1000, max_y=1000, speed_x=3, speed_y=10, hit_sound=None, destruction_sound=None, max_hits=10):
        super(DeathStar, self).__init__()
        self.radius = image["radius"]
        self.max_hits = max_hits
        self.surf = pygame.image.load(image["file"]).convert()
        self.surf = pygame.transform.scale(self.surf, (self.radius * 2, self.radius * 2))
        self.surf.set_colorkey(image["tcolor"], RLEACCEL)
        self.rect = self.surf.get_rect(center= (max_x + self.radius, max_y / 2))
        self.rect_blit = self.rect
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.max_x = max_x
        self.max_y = max_y
        self.upward = True # whether the deathstar is moving up
        self.hits = 0 # how many times the deathstar has been hit
        self.hit_sound = hit_sound
        self.destruction_sound = destruction_sound
        # a red disk - partially transparent - is put on top of the deathstar to make it redder when hit
        self.disk = self.surf.copy()
        pygame.draw.circle(self.disk, (255,0,0), self.disk.get_rect().center, self.radius)
        self.disk.set_alpha(15) # opacity of the red disk
       
        
    def update(self):
        if self.rect.left > self.max_x - 300:
            self.rect.move_ip(-self.speed_x, 0)
        else:
            if self.upward:
                self.rect.move_ip(0, -self.speed_y)
            else: 
                self.rect.move_ip(0, self.speed_y)
            if self.rect.top < 0:
                self.upward = False
            if self.rect.bottom > self.max_y:
                self.upward = True
                
    def hit(self):
        # the deathstar is hit, returns True is the deathstar is destroyed
        self.hits += 1 
        if self.hit_sound: self.hit_sound.play()
        red_step = int(self.max_hits / 10) # how many hits make the deathstar redder
        if self.hits % red_step == 0:
            # we make the deathstar redder
            self.surf.blit(self.disk, self.disk.get_rect())
        if self.hits >= self.max_hits : # the deathstar is destroyed
            self.surf.blit(self.disk, self.disk.get_rect())
            self.kill()
            return True
        return False
            
    def contains(self, px, py):
        # returns whether the point (px, py) is in the disk formed by the deathstar
        dx = self.rect.centerx - px
        dy = self.rect.centery - py
        dist = math.sqrt(dx**2 + dy**2)
        return dist <= self.radius 