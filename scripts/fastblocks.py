'''
Created on 25.07.2011

@author: erikwittkorn

//TODO
- collisioncheck before rotate (done!)
- reset of block ids
- graphics
- check if theres a solid line (done!)
- GUI
- points
- delete lines, when theres a incomplete line between them (done!?)
- animation when deleting blocks
- centered position after rotate (done!?)
- use dirtyrects (done!)
'''

import pygame, sys, os, re, random, time, copy
import xml.dom.minidom as dom
from pygame.compat import geterror
from pygame.locals import *

if not pygame.font: print ('Warning, fonts disabled')

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, '..','data')
animation = False

'helper function to load an image with a colorkey (transparent area)'
def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey)
        image.set_alpha(255)
    return image, image.get_rect()

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

    if keystate[K_DOWN]:
        playingField.moveActiveBlock("down")
        
    for event in events: 
        if event.type == QUIT: 
            sys.exit(0) 
        elif event.type == MOUSEBUTTONDOWN:
            playingField.spawnRandBlock()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playingField.moveActiveBlock("left")
                pygame.time.set_timer(USEREVENT+2,200)
            elif event.key == pygame.K_RIGHT:
                playingField.moveActiveBlock("right")
                'timer for moving a block with key pressed'
                pygame.time.set_timer(USEREVENT+2,200)
            elif event.key == pygame.K_SPACE:
                playingField.rotateActiveBlock()
        elif event.type == USEREVENT+1:
            playingField.update()
        
        elif event.type == USEREVENT+2:
            if keystate[K_LEFT]:
                playingField.moveActiveBlock("left")
            elif keystate[K_RIGHT]:
                playingField.moveActiveBlock("right")
            elif keystate[K_LEFT] & keystate[K_RIGHT] == False:
                pygame.time.set_timer(USEREVENT+2,0)
            
class Text(pygame.sprite.Sprite):
    # red ,green ,blue, yello,cyan,pink,grau,weis
    col=[(255,0,0),(0,255,0),(0,0,255),(255,255,0),(0,255,255),(255,0,255),(128,128,128),(255,255,255)]
    def __init__(self,font,text, pos,color):
        pygame.sprite.Sprite.__init__(self)
        self.color = self.col[color]
        self.font = font
        self.font.set_bold(True)
        self.image = self.font.render(text, True,self.color)
        self.rect = self.image.get_rect(center = pos)
        self.pos = pos
        
    def update(self,text):
        self.image = self.font.render(text, True,self.color)
        self.rect = self.image.get_rect(center = self.pos)

class Block(pygame.sprite.Sprite):
    
    def __init__(self,image):
        pygame.sprite.Sprite.__init__(self)
        self.imageName = image
        self.image, self.rect = load_image(image, -1)
        self.sprite = pygame.sprite.RenderPlain(self)
        self.id = 0
        
    def __del__(self):
        print "ICH WURDE ZERTSTOERT"


class CompleteBlock(): #TODO: Lookup Python Movable
    
    def __init__(self,height,width,numbers,image,blockSize):
        ' width and heigth and blocksize in pixel of the composed blocks'
        self.width = width
        self.height = height
        self.blockSize = blockSize
        
        ' numberstring from xml which defines the positions of the block'
        self.numbers = numbers
        self.collisonArray = []
        self.blocks = []
        self.blockIndices = []
        
        ' is the block stuck ? (no more movement)'
        self.stuck = False
        
        ' group of all block-sprites'
        self.allSprites = pygame.sprite.RenderUpdates()
        
        ' image and topleft coordinates of the whole block'
        self.imageName = image
        self.pos = [0,0]

        for i in range(self.height):
            row = []
            for j in self.numbers[i*self.width:i*self.width+self.width]:
                row.append(int(j))
            self.collisonArray.append(row)
                    
        for j in range(self.width):
            for i in range(self.height):
                if self.collisonArray[i][j] == 1:
                    self.blocks.append(Block(image))
                    self.blocks[-1].rect = self.blocks[-1].rect.move(j*blockSize,i*blockSize)
                    self.allSprites.add(self.blocks[-1].sprite)
    
    def setBlockIndex(self,index):
        for block in self.blocks:
            self.blockIndices.append(index)
            block.id = index
            index = index + 1
        return index

    def setSpawnPos(self,pos):
        self.pos = list(pos)
        #print pos
        for block in self.blocks:
            block.rect = block.rect.move(self.pos[0],self.pos[1])
            
    def move(self,dir,playingField,forced = False,steps = 1, intersect = None):
        oldRects = []
        newRects = []
        indices = []
        for i,block in enumerate(self.blocks):
            oldRects.append(block.rect)
            if intersect is None or block.id in intersect:
                if dir == "down":
                    newRects.append(block.rect.move(0,playingField.blockSize*steps))
                elif dir == "left":
                    newRects.append(block.rect.move(-playingField.blockSize*steps,0))
                elif dir == "right":
                    newRects.append(block.rect.move(playingField.blockSize*steps,0))
                elif dir == "up":
                    newRects.append(block.rect.move(0,-playingField.blockSize*steps))
                indices.append(i)

        if playingField.collides(oldRects,newRects,self.blockIndices) == False or forced == True:
            for j,i in enumerate(indices):
                self.blocks[i].rect = newRects[j]
            if dir == "down":
                self.pos[1] = self.pos[1] + playingField.blockSize*steps
            elif dir == "left":
                self.pos[0] = self.pos[0] - playingField.blockSize*steps
            elif dir == "right":
                self.pos[0] = self.pos[0] + playingField.blockSize*steps
            elif dir == "up":
                self.pos[1] = self.pos[1] - playingField.blockSize*steps
        elif playingField.collides(oldRects,newRects,self.blockIndices) == True and dir == "down": 
            self.stuck = True
            
    def rotate(self,playingField):
        tmpCollisionArray = []
        for i in range(self.width):
            row = []
            for j in range(self.height):
                row.append(self.collisonArray[self.height-1-j][i])
            tmpCollisionArray.append(row)
        
        oldRects = []
        for i in range(len(self.blocks)):
            oldRects.append(self.blocks[i].rect)

        counter = 0
        for j in range(self.height):
            for i in range(self.width):
                if tmpCollisionArray[i][j] == 1:
                    if counter == len(self.blocks)/2:
                        newPos = (oldRects[len(self.blocks)/2].topleft[0] - (self.pos[0] + j*self.blockSize) ,oldRects[len(self.blocks)/2].topleft[1] - (self.pos[1] + i*self.blockSize))
                    counter = counter + 1
        newRects = []
        blockCounter = 0
        for j in range(self.height):
            for i in range(self.width):
                if tmpCollisionArray[i][j] == 1:
                    'to move the rect in the right position, do it here ;)'
                    newRects.append(pygame.Rect(self.pos[0] + newPos[0], self.pos[1] + newPos[1],self.blocks[blockCounter].rect[2],self.blocks[blockCounter].rect[3]))
                    newRects[blockCounter] = newRects[blockCounter].move(j*self.blockSize,i*self.blockSize)
                    blockCounter = blockCounter + 1        

        if playingField.collides(oldRects,newRects,self.blockIndices) == False:
            self.collisonArray = tmpCollisionArray
            self.width, self.height = self.height, self.width
            for i in range(len(self.blocks)):
                self.blocks[i].rect = newRects[i]
        else:
            print "passt nicht"
                         
    def deleteBlocks(self,blockIndices):
        deletedBlockSprites = pygame.sprite.RenderUpdates()
        deletedBlocks = []
        for block in self.blocks:
            #print "id: " + str(block.id)
            if block.id in blockIndices:
                #print "weg"
                self.allSprites.remove(block.sprite)
                deletedBlockSprites.add(block.sprite)
                deletedBlocks.append(block)
        
        for block in deletedBlocks:
            self.blocks.remove(block)
        deletedBlocks = []
        
        return deletedBlockSprites
    
    def changeImage(self,indices,image):
        for block in self.blocks:
            if block.id in indices:
                block.image = image

    def __deepcopy__(self,dup):
        return CompleteBlock(copy.deepcopy(self.height, dup),copy.deepcopy(self.width, dup),copy.deepcopy(self.numbers, dup),copy.deepcopy(self.imageName, dup),copy.deepcopy(self.blockSize, dup))

class PlayingField:
    
    def __init__(self,height,width,pos,screenDims,blockSize):
        self.width = width
        self.height = height
        self.pos = pos 
        
        self.blockSize = blockSize
        self.blockList = []
        self.allSprites = pygame.sprite.RenderUpdates()
        
        self.deletedBlocks = pygame.sprite.RenderUpdates()
        self.activeBlocks = []
        self.crossBlock = None
        self.nextBlockId = -1
        self.nextBlockText = False
        self.nextBlock = False
        self.blockIndex = 1
         
        
        self.linesText = False
        self.linesCount = 0
        self.scoreText = False
        self.score = 0
        
        fbg_image, rect = load_image("images/fullbackground.bmp")
        bg_image,rect = load_image("images/background.bmp")
        pv_image,rect = load_image("images/preview.bmp")
        
        'Appearance of the whole game screen'
        self.background = pygame.Surface((self.width*self.blockSize,self.height*self.blockSize))
        self.background.blit(bg_image,(0,0))
        self.preview = pygame.Surface((4*self.blockSize,4*self.blockSize))
        self.preview.blit(pv_image,(0,0))
        self.fieldSurface2 = pygame.Surface(screenDims)
        self.fieldSurface2.blit(fbg_image,(0,0))
        self.fieldSurface2.blit(self.background,self.pos)
        self.fieldSurface2.blit(self.preview, (self.pos[0] + self.width*self.blockSize + self.blockSize,self.pos[1] ))
        
        self.collisionArray = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(0)
            self.collisionArray.append(row)        

    def spawnRandBlock(self):
        if self.nextBlockId == -1:
            random.seed(time.time()*256)
            self.nextBlockId = random.randint(0,len(self.blockList)-1)
        
        dup = copy.deepcopy(self.blockList[self.nextBlockId])
        self.activeBlocks.append(dup)
        self.activeBlocks[-1].setSpawnPos(((self.width/2)*self.blockSize+self.pos[0],0+self.pos[1]))
        self.allSprites.add(self.activeBlocks[-1].allSprites)
        self.blockIndex = self.activeBlocks[-1].setBlockIndex(self.blockIndex)
        self.updateCollisionArray()
        
        random.seed(time.time()*256)
        self.nextBlockId = random.randint(0,len(self.blockList)-1)
        
        if self.nextBlock != False:
            self.allSprites.remove(self.nextBlock.allSprites)
            self.deletedBlocks.add(self.nextBlock.allSprites)
        
        self.nextBlock = copy.deepcopy(self.blockList[self.nextBlockId])
        self.nextBlock.setSpawnPos((self.pos[0] + self.width*self.blockSize + self.blockSize,self.pos[1] ))
        self.allSprites.add(self.nextBlock.allSprites)
        
        #print "nextBlockId: " + str(self.nextBlockId)
        
    def updateCollisionArray(self):
        for i in range(self.height):
            for j in range(self.width):
                self.collisionArray[i][j] = 0
        
        #print self.collisionArray
        
        for block in self.activeBlocks:
            for lBlock in block.blocks:
                pos = lBlock.rect.topleft
                #print "x: " + str((pos[1]-self.pos[1])/self.blockSize) + " y: " + str((pos[0]-self.pos[0])/self.blockSize)
                self.collisionArray[(pos[1]-self.pos[1])/self.blockSize][(pos[0]-self.pos[0])/self.blockSize] = lBlock.id
                

    def moveActiveBlock(self,dir):
        if self.activeBlocks[-1].stuck != True:
            self.activeBlocks[-1].move(dir,self)
        self.updateCollisionArray()
    
    def rotateActiveBlock(self):
        if self.activeBlocks[-1].stuck != True:
            self.activeBlocks[-1].rotate(self)
        self.updateCollisionArray()
    
    def moveBlocksDown(self):
        for block in self.activeBlocks:
            if block.stuck != True:
                block.move("down",self)
    
    def update(self):

        if animation == False:        
            self.moveBlocksDown()
            stuck = True
            for block in self.activeBlocks:
                if block.stuck == False:
                    stuck = False
            
            if stuck == True:
                lines = self.checkReadyLines()
                deletedLinesCount = 0
                if len(lines)>0:
                    deletedLinesCount = self.deleteReadyLines(lines)
                    self.linesCount = self.linesCount + deletedLinesCount
                self.score = self.score + 15 + 50 * deletedLinesCount
                self.spawnRandBlock()
            self.updateCollisionArray()
            
            if pygame.font:
                if self.scoreText == False:
                    font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
                    self.scoreText = Text(font,"Score: " + str(self.score),((self.width+4)*self.blockSize + self.blockSize - 10,self.pos[1] + self.height/3*self.blockSize+18),0)
                    self.allSprites.add(self.scoreText)
                else:
                    self.scoreText.update("Score: " + str(self.score))
                #if self.nextBlockText == False:
                #    font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
                #    self.nextBlockText = Text(font,"NextBlockId: " + str(self.nextBlockId),((self.width-3)/2*self.blockSize,self.pos[1] + self.height*self.blockSize+18*2),0)
                #    self.allSprites.add(self.nextBlockText)
                #else:
                #    self.nextBlockText.update("NextBlockId: " + str(self.nextBlockId))
                if self.linesText == False:
                    font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
                    self.linesText = Text(font,"Lines: " + str(self.linesCount),((self.width+4)*self.blockSize + self.blockSize -10,self.pos[1] + self.height/3*self.blockSize+18*2),0)
                    self.allSprites.add(self.linesText)
                else:
                    self.linesText.update("Lines: " + str(self.linesCount))
            else:
                print "trololololololol"
        
    def collides(self,oldRects,newRects,indices):
        oldTuples = []
        for rect in oldRects:
            oldTuples.append((rect[0]/self.blockSize,rect[1]/self.blockSize))
        test = []
        for rect in newRects:
            x = (rect[0]-self.pos[0])/self.blockSize
            y = (rect[1]-self.pos[1])/self.blockSize
            if x<self.width and x >=0 and y<self.height and y >=0:
                if self.collisionArray[y][x] not in indices and self.collisionArray[y][x] > 0:
                    test.append(True)
                else:
                    test.append(False)
            else:
                #print "stuck"
                return True
            
        if True in test:
            return True
        else:
            return False

    def checkReadyLines(self):
        lines = []
        for i,row in enumerate(self.collisionArray):
            check = False
            for blockIndex in row:
                if blockIndex == 0:
                    check = True
            if check == False:
                lines.append(i)
        return lines
    
    def deleteReadyLines(self,lines):
        for lineIndex in lines:
            line = self.collisionArray[lineIndex]
            #print "Line: " + str(line)
            for block in self.activeBlocks:
                blockIndices = [i for i in line if i in block.blockIndices]
                block.changeImage(blockIndices,self.crossBlock.image)
                #print "Blockindices: " + str(blockIndices)
                self.deletedBlocks.add(block.deleteBlocks(blockIndices))

        #print "kollisionen  " + str(lines)
        downerList = []
        batch = 0
        for i in range(len(lines)):
            if len(lines)-2-i >= 0:
                #downerList = self.collisionArray[lines[len(lines)-2-i]:lines[len(lines)-1-i]]
                diff = lines[len(lines)-1-i] - lines[len(lines)-2-i]
                #downerList.append(diff)
                
                if ( diff > 1):
                    for j in range(diff-1):
                        #print "AHA  index: " + str(lines[len(lines)-2-i]+j+1) + " content " + str(self.collisionArray[lines[len(lines)-2-i]+j+1])
                        downerList.append(self.collisionArray[lines[len(lines)-2-i]+j+1])
                        downerList[-1].extend([i+1+batch])
                        #print "Special  " + str(lines[len(lines)-2-i]+j+1) + " diff " + str(diff) + " verschub = " + str(i+1+batch)
                        #print "SPECIAL"
                batch = batch + diff - 1
                        
                    
        #print "hihi   " + str(lines[len(lines)-1-i])
        #print self.collisionArray
        #print "downerList : " + str(downerList)
            
        upperList = self.collisionArray[0:lines[0]]
        #print "upper  " + str(upperList)
            
        for block in self.activeBlocks:
            intersectsUpper = []
                
            downUpper = False
            downDowner = False
            for row in upperList:
                #print "indices  " + str(block.blockIndices)
                #print "row      " + str(row)
                intersectsUpper.extend(list(set(block.blockIndices) & set(row)))
                if len(intersectsUpper)>0:
                    downUpper = True
            if downerList != False:
                for row in downerList:
                    intersectsDowner = []
                    intersectsDowner.extend(list(set(block.blockIndices) & set(row[:-1])))
                    if len(intersectsDowner)>0:
                        block.move("down",self,True,row[-1],intersectsDowner)    
                
            if downUpper:
                block.move("down",self,True,len(lines),intersectsUpper)
                    
        self.allSprites.remove(self.deletedBlocks)
        #print self.collisionArray
        
        return len(lines)
                
def main():
    pygame.init()
    screen_dims = getScreenDims("config.xml")
    
    pygame.display.init()
    
    window = pygame.display.set_mode(screen_dims)
    pygame.display.set_caption('FastBlocks')
    screen = pygame.display.get_surface() 
    playingField = initialize("config.xml")
    
    'timer for moving the blocks down and check and delete ready lines'
    pygame.time.set_timer(USEREVENT+1, 500)

    playingField.spawnRandBlock()
    clock = pygame.time.Clock()
    
    screen.blit(playingField.fieldSurface2, (0, 0))
    pygame.display.flip()    
    while True:
        input(pygame.event.get(),playingField)
        if len(playingField.deletedBlocks) > 0:
            playingField.deletedBlocks.clear(screen, playingField.fieldSurface2)
            playingField.deletedBlocks.empty()

        playingField.allSprites.clear(screen, playingField.fieldSurface2)
        dirtyRects = playingField.allSprites.draw(screen)
        pygame.display.update(dirtyRects)
        clock.tick(40)
        
        
        

if __name__ == "__main__":
    main()