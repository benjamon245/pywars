# -*- coding: utf-8 -*-
"""
Created on Fri Aug 11 15:16:59 2023
@author: benjamon24_5
"""

import play
import pygame
import time, json

# Import pygame.locals for easier access to key coordinates
from pygame.locals import (
    RLEACCEL,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

# reading the config file
f = open('config.json', 'r')
config = json.load(f)
f.close


# Define constants for the screen width and height
SCREEN_WIDTH = config['window_width']
SCREEN_HEIGHT = config['window_height']


# Sprite for the Play button
class Button(pygame.sprite.Sprite):
    def __init__(self, centerx, centery):
        super(Button, self).__init__()
        # writing on the surface
        # defining 2 surfaces depending whether the button is on
        font = pygame.font.SysFont(None, 75) 
        self.surf_green = font.render('Play -->', True, (233, 233, 233), (10, 75, 75))
        self.surf_blue = font.render('Play -->', True, (233, 233, 233), (0, 75, 125))
        self.surf = self.surf_green
        
        self.rect = self.surf.get_rect()
        self.rect.centery = centery
        self.rect.centerx = centerx
        self.green = True # whether the button is on
        
    def toggle(self):
        # toggle the button
        if self.green:
            self.surf = self.surf_blue
            self.green = False
        else:
            self.surf = self.surf_green
            self.green = True
            
            
# Initialize pygame
pygame.init()
# Setup for sounds. Defaults are good.
if config['sound']: 
    pygame.mixer.init()
    # Load and play background music
    pygame.mixer.music.load(config['sounds']['music'])
    pygame.mixer.music.play(loops=-1)

# Setup the clock for a decent framerate
clock = pygame.time.Clock()

try:
    
    # surfaces for the titles
    font = pygame.font.SysFont(None, 75) 
    try_my_game = font.render('Try my game!', True, (233, 233, 233), (0, 0, 0))
    try_my_game.set_colorkey((0, 0, 0), RLEACCEL)
    game_over = font.render('Game Over...', True, (233, 233, 233), (0, 0, 0))
    game_over.set_colorkey((0, 0, 0), RLEACCEL)
    congrats = font.render('Congrats!!!', True, (233, 233, 233), (0, 0, 0))
    congrats.set_colorkey((0, 0, 0), RLEACCEL)
    
    # first title is "Try my game"
    title = try_my_game
    
    # Create the screen object
    # The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # background set-up
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))    
    starry_sky = pygame.image.load(config["images"]["starry_sky"]["file"]).convert()
    starry_sky = pygame.transform.scale(starry_sky, (SCREEN_WIDTH, SCREEN_HEIGHT))
    background.blit(starry_sky, starry_sky.get_rect())
    background.set_alpha(100)
    screen.blit(background, background.get_rect())
    
    # button
    button = Button(SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
    
    # Variable to keep the main loop running
    running = True
    
    # Main loop
    while running:
        # Look at every event in the queue
        for event in pygame.event.get():
            # Did the user hit a key?
            if event.type == KEYDOWN:
                # Was it the Escape key? If so, stop the loop.
                if event.key == K_ESCAPE:
                    running = False
            # Did the user click the window close button? If so, stop the loop.
            elif event.type == QUIT:
                running = False
    
            # Did the user click
            elif (event.type == pygame.MOUSEBUTTONUP) and (event.button == 1):
                # getting the position of the mouse
                pos = pygame.mouse.get_pos()
        
                if button.rect.collidepoint(pos):
                    # is the click on the button?
                    
                    # toggle the button
                    button.toggle()
                    screen.blit(button.surf, button.rect)
                    pygame.display.flip()
                    
                    # sleep 0.5s and launch the game
                    time.sleep(0.5)
                    won = play.run(config, screen)
                    
                    if won is None:
                        title = try_my_game
                    elif won: # the user won
                        title = congrats
                    else:
                        title = game_over
                                          
        # blit title and button and flip
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 200)))
        screen.blit(button.surf, button.rect)
        pygame.display.flip()
        # Ensure program maintains a rate of 30 frames per second
        clock.tick(config['fps'])
        
    # clean exit
    if config['sound']: 
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    pygame.quit()
    
except Exception as e:
    pygame.quit() # clean quit
    raise e