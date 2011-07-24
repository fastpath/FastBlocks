'''
Created on 25.07.2011

@author: erikwittkorn
'''
import pygame, sys, os
from pygame.locals import *
screen_dims = (640,480)

def input(events): 
   for event in events: 
      if event.type == QUIT: 
         sys.exit(0) 
      else: 
         print event 
 
def main():
    pygame.display.init()
    window = pygame.display.set_mode(screen_dims)
    pygame.display.set_caption('FastBlocks')
    screen = pygame.display.get_surface() 
    
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((255,230,255))
    
    screen.blit(background, (0, 0))
    pygame.display.flip()
    
    while True: 
        input(pygame.event.get()) 

if __name__ == "__main__":
    main()