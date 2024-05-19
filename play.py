#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 17 20:20:36 2023
@author: benjamon24_5
"""
# Import the pygame module
import pygame
import time, random, json
from sprites import Player, Enemy, SearchingEnemy, BackgroundItem, Trapez, DeathStar 

# Import pygame.locals for easier access to key coordinates
# Updated to conform to flake8 and black standards
from pygame.locals import (
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    K_SPACE,
    KEYDOWN,
    QUIT,
    K_i,
    K_p
)



# Those are the different phases of the game
INITIAL_PHASE = 0 # only missiles
TUNNEL_PHASE = 1 # tunnel phase 
BOSS_PHASE = 2 # deathstar phase
END_PHASE = 3 # for later: explosion of the deathstar

# override of usual collision function to avoid an object to be considered as colliding with itself
def collide_if_not_self(left, right):
    if left is right:
        return False
    else:
        return pygame.sprite.collide_rect(left, right) 

# given a sprite with the method contains
# checks whether any corner of a rect is contained in the sprite
# used to check collisions with trapez or deathstar
def collide_rect_corners(sprect, spcontains):
    if spcontains.contains(sprect.rect.left, sprect.rect.top):
        return True
    if spcontains.contains(sprect.rect.left, sprect.rect.bottom):
        return True
    if spcontains.contains(sprect.rect.right, sprect.rect.top):
        return True
    if spcontains.contains(sprect.rect.right, sprect.rect.bottom):
        return True
    return False

# returns a new trapez object stuck on top of the screen given the coordinates of the 2 bottom corners
def top_trapez(p1, p2, color=(0, 0, 0)):
    x1 = p1[0]
    x2 = p2[0]
    y1 = p1[1]
    y2 = p2[1]
    return Trapez(x2 - x1, y1, y2, 0, x1, 0, color=color) 

# returns a new trapez object stuck on the bottom of the screen given the coordinates of the 2 top corners
def bottom_trapez(p1, p2, screen_height, color=(0, 0, 0)):
    x1, x2, y1, y2 = p1[0], p2[0], p1[1], p2[1]
    if y1 > y2:
        return Trapez(x2 - x1, screen_height - y1, screen_height - y2, y2 - y1, x1, y2, color=color)
    return Trapez(x2 - x1, screen_height - y1, screen_height - y2, y2 - y1, x1, y1, color=color) 
            
############
# running the game
############
def run(config, screen):   
   
    # Define constants for the screen width and height
    SCREEN_WIDTH = config['window_width']
    SCREEN_HEIGHT = config['window_height']
    
    # start phase
    # should be initial phase except for testing
    phase = INITIAL_PHASE
    #phase = BOSS_PHASE
    #phase = TUNNEL_PHASE

    won = None # whether the user won
    
    # background
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))    
    starry_sky = pygame.image.load(config["images"]["starry_sky"]["file"]).convert()
    starry_sky = pygame.transform.scale(starry_sky, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
    # Setup the clock for a decent framerate
    clock = pygame.time.Clock()
       
    # whether the user is invicible - meant for testing
    invicible = False
    
    pause = False

    # Load all sound files
    if config['sound']: 
        move_up_sound = pygame.mixer.Sound(config['sounds']['up'])
        move_down_sound = pygame.mixer.Sound(config['sounds']['down'])
        laser_sound = pygame.mixer.Sound(config['sounds']['laser'])
        hit_sound = pygame.mixer.Sound(config['sounds']['hit'])
        destruction_sound = pygame.mixer.Sound(config['sounds']['destruction'])
        small_destruction_sound = pygame.mixer.Sound(config['sounds']['small_destruction'])
    else: 
        move_up_sound = None
        move_down_sound = None
        laser_sound = None
        hit_sound = None
        destruction_sound = None
        small_destruction_sound = None
    
    # Create a custom event for adding a new enemy
    ADDENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(ADDENEMY, config['event_timers']['enemy'])
    # Create a custom event for adding a new searching enemy
    ADD_SEARCHING_ENEMY = pygame.USEREVENT + 3
    pygame.time.set_timer(ADD_SEARCHING_ENEMY, config['event_timers']['searching_enemy'])
    
    # Create a custom event for adding a new background object
    ADDBKG = pygame.USEREVENT + 2
    pygame.time.set_timer(ADDBKG, config['event_timers']['bkg_object'])
    
    # Creating the player sprite
    player = Player(config['images']["player"], 
                    config['speeds']['player'],
                    SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # the deathstar will be created in phase 3
    deathstar = None
    
    # creating the trapez tunnel phase
    top_tunnel = config["top_tunnel"]
    top_tunnel = [(elt[0], min(elt[1], SCREEN_HEIGHT-60)) for elt in top_tunnel]
    
    if "bottom_tunnel" in config:
        bottom_tunnel = config["bottom_tunnel"]
        bottom_tunnel = [(elt[0], elt[1]) for elt in bottom_tunnel]
    else:
        # if the bottom tunnel is not defined in the config 
        # we just build a set of trapez parallel to the top ones (but shifted)
        bottom_tunnel = [(p[0]+100, min(p[1]+300,SCREEN_HEIGHT-10)) for p in top_tunnel]
        
    # shifting the tunnel so as they start outside the screen
    top_tunnel = [(x + SCREEN_WIDTH, y) for (x, y) in top_tunnel]
    bottom_tunnel = [(x + SCREEN_WIDTH, y) for (x, y) in bottom_tunnel]
   
    
    # Create groups to hold different kinds of sprites
    # and a group for all sprites for rendering
    lasers = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    tunnel = pygame.sprite.Group()
    deathstars = pygame.sprite.Group()

    bkgs = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    
    # counting the frames to decide when moving to the next phase
    framenb = 0
   
    tunnel_created = False # to keep track whether the tunnel has been created     
    # Variable to keep the main loop running
    running = True
    # Main loop
    while running:
        
        # counting the time to decide when moving to the next phase
        framenb += 1
        secondnb = framenb / (config["fps"])
        
        ################
        #### PHASES ####
        ################
        # moving to tunnel phase
        if (secondnb > config["initial_phase_time"]) and (phase == INITIAL_PHASE):
            phase = TUNNEL_PHASE
        # creating the tunnel if not done
        if (phase == TUNNEL_PHASE) and (tunnel_created == False):
            i = 0
            while i < len(top_tunnel)-1:
                p1 = top_tunnel[i]
                p2 = top_tunnel[i+1]
                t = top_trapez(p1, p2, color=config["colors"]["trapez"])
                all_sprites.add(t)
                tunnel.add(t)
                i += 1
            i = 0
            while i < len(bottom_tunnel)-1:
                p1 = bottom_tunnel[i]
                p2 = bottom_tunnel[i+1]
                t = bottom_trapez(p1, p2, SCREEN_HEIGHT, color=config["colors"]["trapez"])
                all_sprites.add(t)
                tunnel.add(t)
                i += 1
            tunnel_created = True
            
        # moving to deathstat phase
        if (phase == TUNNEL_PHASE) and (len(tunnel.sprites()) == 0):
            phase = BOSS_PHASE
        # creating the deathstar if not done
        if (deathstar == None) and (phase == BOSS_PHASE):
            deathstar = DeathStar(config['images']["deathstar"], 
                                  max_x=SCREEN_WIDTH, max_y=SCREEN_HEIGHT,
                                  hit_sound=hit_sound, destruction_sound=destruction_sound, max_hits=config["max_hits"])
            all_sprites.add(deathstar)
            deathstars.add(deathstar)
            
        ###############
        ### EVENTS ####
        ###############
        # Look at every event in the queue
        for event in pygame.event.get():
            # Did the user hit a key?
            if event.type == KEYDOWN:
                # Was it the Escape key? If so, stop the loop.
                if event.key == K_ESCAPE:
                    running = False
                # Space key for shooting lasers
                if event.key == K_SPACE:
                    l = player.fire(config['colors']['laser'],
                                    config['speeds']['laser'],
                                    SCREEN_WIDTH,
                                    laser_sound)
                    all_sprites.add(l)
                    lasers.add(l)
                # cheat mode to become invicible (for testing)
                if event.key == K_i:
                    invicible = not invicible
                
                if event.key == K_p:
                    pause = not pause
                    
            # Did the user click the window close button? If so, stop the loop.
            elif event.type == QUIT:
                running = False
            
            # add ennemies on a regular basis
            elif (event.type == ADDENEMY) and (not pause):
                # Create the new enemy and add it to sprite groups
                if (phase == INITIAL_PHASE) or (phase == TUNNEL_PHASE):
                    # enemies are created outside the screen
                    x = random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100)
                    y = random.randint(0, SCREEN_HEIGHT)
                elif phase == BOSS_PHASE:
                    # enemies are launched from the deathstar
                    x = deathstar.rect.centerx
                    y = random.randint(deathstar.rect.top, deathstar.rect.bottom)
                new_enemy = Enemy(config['images']["enemy"], x, y,
                                  speeds=(config['speeds']['enemy'][0], config['speeds']['enemy'][1]))
                # adding in sprite group
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
                
            # add searching ennemies on a regular basis
            elif (event.type == ADD_SEARCHING_ENEMY) and (not pause):
                # Create the new enemy and add it to sprite groups
                if (phase == INITIAL_PHASE) or (phase == TUNNEL_PHASE):
                    x = random.randint(SCREEN_WIDTH + 20, SCREEN_WIDTH + 100)
                    y = random.randint(0, SCREEN_HEIGHT)
                elif phase == BOSS_PHASE:
                    x = deathstar.rect.centerx
                    y = random.randint(deathstar.rect.top, deathstar.rect.bottom)
                new_enemy = SearchingEnemy(config['images']["enemy"], x, y,
                                           speeds=(config['speeds']['searching_enemy'][0], config['speeds']['searching_enemy'][1]))
                enemies.add(new_enemy)
                all_sprites.add(new_enemy)
                
            # creating background objects on a regular basis
            elif (event.type == ADDBKG) and (not pause):
                item = config["background"][random.randint(0, len(config["background"])-1)]
                # Create the new object and add it to sprite groups
                new_bkg = BackgroundItem(config['images'][item],
                                  SCREEN_WIDTH, SCREEN_HEIGHT,
                                  speeds=(config['speeds']['background'][0], config['speeds']['background'][1]))
                bkgs.add(new_bkg)
                
        ######################
        #### PRESSED KEYS ####
        ######################
        # Get the set of keys pressed and check for user input
        pressed_keys = pygame.key.get_pressed()
        
        # moving the player
        if pressed_keys[K_UP]:
            player.move_up()
        if pressed_keys[K_DOWN]:
            player.move_down()
        if pressed_keys[K_LEFT]:
            player.move_left()
        if pressed_keys[K_RIGHT]:
            player.move_right()
            
        ##########################
        #### UPDATE POSITIONS ####
        ##########################
        if pause == False:
            player.update()
            bkgs.update()
            lasers.update() 
            enemies.update(player.rect.centerx, player.rect.centery)
            tunnel.update()
            if deathstar: 
                deathstar.update()
        
        ###################
        #### RENDERING ####
        ###################
        # background
        screen.fill(config['colors']['bkg'])
        background.blit(starry_sky, starry_sky.get_rect())
        for entity in bkgs:
            background.blit(entity.surf, entity.rect)
            
        background.set_alpha(200)
        screen.blit(background, background.get_rect())
                
        # Draw all sprites
        for entity in all_sprites:
            screen.blit(entity.surf, entity.rect_blit)
        screen.blit(player.surf, player.rect_blit)
            
        ##############
        #### FLIP ####
        ##############
        pygame.display.flip()
           
        ####################            
        #### Collisions ####
        ####################
        # destroying enemies
        if pygame.sprite.groupcollide(enemies, lasers, True, True) \
        or pygame.sprite.groupcollide(enemies, enemies, True, True, collided=collide_if_not_self):
            if config['sound']: small_destruction_sound.play()            
        pygame.sprite.groupcollide(enemies, tunnel, True, False, collided=collide_rect_corners)
        pygame.sprite.groupcollide(lasers, tunnel, True, False, collided=collide_rect_corners)
        
        # destroying the player --> GAME OVER
        if invicible == False:
            if pygame.sprite.spritecollideany(player, enemies) \
            or pygame.sprite.spritecollideany(player, tunnel, collided=collide_rect_corners)\
            or pygame.sprite.spritecollideany(player, deathstars, collided=collide_rect_corners): 
                
                # GAME OVER
                player.kill()
                if config['sound']: 
                    move_up_sound.stop()
                    move_down_sound.stop()
                    destruction_sound.play()
                    destruction_sound.fadeout(3000)
                # sleep before GAME OVER
                time.sleep(2)
                won = False
                running = False
        
        # hitting/destroying the deathstar
        if pygame.sprite.groupcollide(lasers, deathstars, True, False, collided=collide_rect_corners):
            if deathstar.hit():
                if config['sound']:
                    move_up_sound.stop()
                    move_down_sound.stop()
                    destruction_sound.play()
                    destruction_sound.fadeout(3000)
                time.sleep(3)
                won = True
                running = False

        # Ensure program maintains a rate of 30 frames per second
        clock.tick(config['fps'])
        
    # returning wether the user won
    return won

    
# if the file is ran standalone
if __name__ == "__main__":
     
    # reading the config file
    f = open('config.json', 'r')
    config = json.load(f)    
    f.close
    
    # Initialize pygame
    pygame.init()
    # Setup for sounds. Defaults are good.
    if config['sound']: pygame.mixer.init()
    
    # Load and play background music
    if config['sound']: pygame.mixer.music.load(config['sounds']['music'])
    if config['sound']: pygame.mixer.music.play(loops=-1)
    
    # Create the screen object
    screen = pygame.display.set_mode((config['window_width'], config['window_height']))
    
    # running the game
    try:        
        run(config, screen) 
    except Exception as e:
        pygame.quit()
        raise e
    
    # clean exit
    pygame.mixer.music.stop()
    if config['sound']: pygame.mixer.quit()
    pygame.quit()