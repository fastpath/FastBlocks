'''
Created on 25.07.2011

@author: erikwittkorn

//TODO
- collisioncheck before rotate (done!)
- reset of block ids (done!?)
- graphics (done!?)
- check if theres a solid line (done!)
- GUI
- show a foreshadowing block on the ground
- points (done?!)
- highscore (done!)
- game over screen (done?!)
- blocks become faster over time (done!?)
- delete lines, when theres a incomplete line between them (done!?)
- animation when deleting blocks (done!?)
- centered position after rotate (done!?)
- use dirtyrects (done!)
'''

import pygame, sys, os, re, random, time, copy
import xml.dom.minidom as dom
from pygame.locals import *
from gamelogic import *
from inputtext import Input

'main dir without py2exe'
main_dir = os.path.split(os.path.abspath(__file__))[0]
'main dir with py2exe'
#main_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
data_dir = os.path.join(main_dir,'data')

if not pygame.font: print ('Warning, fonts disabled')

nameInput = False

class ConfigError(KeyError): pass

class Config:
    """ A utility for configuration """
    def __init__(self, options, *look_for):
        assertions = []
        for key in look_for:
            if key[0] in options.keys(): exec('self.'+key[0]+' = options[\''+key[0]+'\']')
            else: exec('self.'+key[0]+' = '+key[1])
            assertions.append(key[0])
        for key in options.keys():
            if key not in assertions: raise ConfigError(key+' not expected as option')

'get the resolution for the game window'
def getScreenDims(xmlName):
    tree = dom.parse(os.path.join(data_dir, xmlName))
    for entry in tree.firstChild.childNodes:
        if entry.nodeName == "screenDims":
            scr_x = entry.getAttribute("x")
            scr_y = entry.getAttribute("y")
    return (int(scr_x),int(scr_y))

'parsing of config-xml'
def initialize(xmlName):
    tree = dom.parse(os.path.join(data_dir, xmlName))
    for entry in tree.firstChild.childNodes:
        if entry.nodeName == "screenDims":
            scr_x = entry.getAttribute("x")
            scr_y = entry.getAttribute("y")
        elif entry.nodeName == "playField":
            p_width = entry.getAttribute("width")
            p_height = entry.getAttribute("height")
            p_x = entry.getAttribute("x")
            p_y = entry.getAttribute("y")
        elif entry.nodeName == "blockSize":
            blockSize = entry.getAttribute("value")

    playingField = PlayingField(int(p_height),int(p_width),(int(p_x),int(p_y)),(int(scr_x),int(scr_y)),int(blockSize))
    
    'the playingField gets its blocks'
    for entry in tree.firstChild.childNodes:
        if entry.nodeName == "blocks":
            for block in entry.childNodes:
                if block.nodeName == "block":
                    b_numbers = block.firstChild.data.strip()
                    b_numbers = re.sub(r'[^10]', '', b_numbers)
                    b_height = block.getAttribute("height")
                    b_width = block.getAttribute("width")
                    b_image = block.getAttribute("image")
                    b_colorkey = block.getAttribute("colorkey")  #TODO: individual colorkeys
                    playingField.blockList.append(CompleteBlock(int(b_height),int(b_width),b_numbers,b_image,int(blockSize)))
                elif block.nodeName == "crossBlock":
                    cb_image = block.getAttribute("image")
                    playingField.crossBlock = Block(cb_image)
    
    return playingField

'handler for key-input and timers'
def input(events,playingField):
    keystate = pygame.key.get_pressed()

    if keystate[K_DOWN] and len(playingField.activeBlocks)>0:
        playingField.moveActiveBlock("down")
        
    for event in events: 
        if event.type == QUIT: 
            sys.exit(0) 
        #elif event.type == MOUSEBUTTONDOWN:
        #    playingField.spawnRandBlock()
        elif event.type == pygame.KEYDOWN and len(playingField.activeBlocks)>0:
            if event.key == pygame.K_LEFT and playingField.paused == False:
                playingField.moveActiveBlock("left")
                pygame.time.set_timer(USEREVENT+2,150)
            elif event.key == pygame.K_RIGHT and playingField.paused == False:
                playingField.moveActiveBlock("right")
                'timer for moving a block with key pressed'
                pygame.time.set_timer(USEREVENT+2,150)
            elif event.key == pygame.K_SPACE and playingField.paused == False:
                playingField.rotateActiveBlock()
            elif event.key == pygame.K_p and playingField.paused == False:
                playingField.paused = True
            elif event.key == pygame.K_p and playingField.paused == True:
                playingField.paused = False
                
        
        if event.type == USEREVENT+1 and playingField.resetCheck == False and playingField.paused == False:
            'comes at level speed to move the blocks down and update status'
            playingField.update()
        elif event.type == USEREVENT+2 and playingField.paused == False:
            'comes when moving a block to enable smooth moving'
            if keystate[K_LEFT]:
                playingField.moveActiveBlock("left")
            elif keystate[K_RIGHT]:
                playingField.moveActiveBlock("right")
            elif keystate[K_LEFT] & keystate[K_RIGHT] == False:
                pygame.time.set_timer(USEREVENT+2,0)
        elif event.type == USEREVENT+3:
            '''comes when lines are deleted and controls the animation steps
                3 - change the block-image to crossBlock
                2 - change the image back to normal
                1 - change it to crossBlock
                0 - delete the line and update everything'''
            if playingField.animationCount == 0:
                deletedLinesCount = playingField.deleteReadyLines()
                playingField.linesCount = playingField.linesCount + deletedLinesCount
                playingField.spawnRandBlock()
                playingField.updateCollisionArray()
                playingField.animation = False
                playingField.animationCount = 3
                pygame.time.set_timer(USEREVENT+3,0)
            elif playingField.animationCount in (3,2,1):
                playingField.animationCount -= 1
                playingField.animateLines()
        elif event.type == USEREVENT+4:
            'comes when the round ended and the highscore-text appears'
            playingField.paused = False
            playingField.allSprites.remove(playingField.gameOverText)
            playingField.allSprites.remove(playingField.gameOverPointsText)
            playingField.resetCheck = True
            pygame.time.set_timer(USEREVENT+4,0)
        elif event.type == USEREVENT+5:
            'comes every 90 seconds to make the gamespeed faster'
            if playingField.speed != 100:
                playingField.speed = playingField.speed - 100;
            pygame.time.set_timer(USEREVENT+1,playingField.speed)


               
def main():
    pygame.init()
    screen_dims = getScreenDims("config.xml")
    pygame.display.init()

    window = pygame.display.set_mode(screen_dims)
    pygame.display.set_caption('FastBlocks')
    screen = pygame.display.get_surface() 
    playingField = initialize("config.xml")
    


    clock = pygame.time.Clock()
    'textbox for name input'
    txtbx = Input(maxlength=8, color=(255,230,230), prompt='Your name: ', y=screen_dims[1]/2-170, x=30, font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 45))
    screen.fill((0,0,0))
    txtbx.draw(screen)
    pygame.display.flip()
    nameInput = True
    while nameInput:
        events = pygame.event.get()
        for event in events:
            # close it x button si pressed
            if event.type == QUIT: return
        nameInput,userName = txtbx.update(events)
        # blit txtbx on the sceen
        screen.fill((0,0,0))
        txtbx.draw(screen)
        # refresh the display
        pygame.display.flip()
        clock.tick(40)

    playingField.spawnRandBlock()
    screen.blit(playingField.fieldSurface2, (0, 0))
    pygame.display.flip()

    playingField.userNameText.update(userName)

    'timer for moving the blocks down and check and delete ready lines'
    pygame.time.set_timer(USEREVENT+1, playingField.speed)
    'timer for accelerating the movement speed'
    pygame.time.set_timer(USEREVENT+5, 90000)
    screen.blit(playingField.fieldSurface2, (0, 0))
    pygame.display.flip()
    while True:
        
        while playingField.animation == True:
            input(pygame.event.get(),playingField)
            playingField.allSprites.clear(screen, playingField.fieldSurface2)
            dirtyRects = playingField.allSprites.draw(screen)
            pygame.display.update(dirtyRects)
            clock.tick(40)
        
        if playingField.resetCheck == True:
            screen.blit(playingField.fieldSurface2, (0, 0))
            pygame.display.flip()
            playingField.spawnRandBlock()
            playingField.allSprites.add(playingField.highScoreText)
            playingField.allSprites.add(playingField.scoreText)
            playingField.allSprites.add(playingField.linesText)
            playingField.allSprites.add(playingField.levelText)
            pygame.time.set_timer(USEREVENT+1, playingField.speed)
            pygame.time.set_timer(USEREVENT+5, 90000)
            playingField.resetCheck = False

        input(pygame.event.get(),playingField)
        if len(playingField.deletedBlocks) > 0:
            playingField.deletedBlocks.clear(screen, playingField.fieldSurface2)
            playingField.deletedBlocks.empty()

        txtbx.draw(screen)

        playingField.allSprites.clear(screen, playingField.fieldSurface2)
        dirtyRects = playingField.allSprites.draw(screen)
        
        pygame.display.update(dirtyRects)
        clock.tick(40)
        
        #print "fps " + str(clock.get_fps())

if __name__ == "__main__":
    main()