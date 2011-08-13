'''
Created on 25.07.2011

@author: erikwittkorn
'''
import pygame, sys, os, re, random, time, copy
import xml.dom.minidom as dom
from pygame.compat import geterror
from pygame.locals import *

main_dir = os.path.split(os.path.abspath(__file__))[0]
data_dir = os.path.join(main_dir, '../data')

screen_dims = (640,480)


def load_image(name, colorkey=None):
    fullname = os.path.join(data_dir, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print ('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0,0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image, image.get_rect()

def initialize(xmlName):
    tree = dom.parse(os.path.join(data_dir, xmlName))
    for entry in tree.firstChild.childNodes:
        if entry.nodeName == "playField":
            p_width = entry.getAttribute("width")
            p_height = entry.getAttribute("height")
        elif entry.nodeName == "blockSize":
            blockSize = entry.getAttribute("value")

    playingField = PlayingField(int(p_width),int(p_height),int(blockSize))
    
    for entry in tree.firstChild.childNodes:
        if entry.nodeName == "blocks":
            for block in entry.childNodes:
                if block.nodeName == "block":
                    b_numbers = block.firstChild.data.strip()
                    b_numbers = re.sub(r'[^10]', '', b_numbers)
                    b_height = block.getAttribute("height")
                    b_width = block.getAttribute("width")
                    b_image = block.getAttribute("image")
                    b_colorkey = block.getAttribute("colorkey")
                    #tmp = 
                    playingField.addBlock(CompleteBlock(int(b_height),int(b_width),b_numbers,"images/block.jpg",int(blockSize)))
                    
                    print "colorkey " + b_colorkey #TODO: individual colorkeys
    
    return playingField

def input(events,playingField):
    keystate = pygame.key.get_pressed()
    #if keystate[K_LEFT]:
     #   playingField.moveActiveBlock("left")
    for event in events: 
        if event.type == QUIT: 
            sys.exit(0) 
        elif event.type == MOUSEBUTTONDOWN:
            playingField.spawnRandBlock()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playingField.moveActiveBlock("left")
            elif event.key == pygame.K_RIGHT:
                playingField.moveActiveBlock("right")
            elif event.key == pygame.K_SPACE:
                playingField.rotateActiveBlock()
                
        elif event.type == USEREVENT+1:
            playingField.moveBlocksDown()
            #elif event.key == 100:
            #    playingField.moveActiveBlock("right")

class Block(pygame.sprite.Sprite):
    
    def __init__(self,image):
        pygame.sprite.Sprite.__init__(self)
        self.imageName = image
        self.image, self.rect = load_image(image, -1)
        self.sprite = pygame.sprite.RenderPlain(self)


class CompleteBlock(): #TODO: Lookup Python Movable
    
    def __init__(self,height,width,numbers,image,blockSize):

        self.width = width
        self.height = height
        self.numbers = numbers
        self.stuck = "false"
        self.allSprites = pygame.sprite.Group()
        self.blockSize = blockSize
        self.imageName = image
        self.blocks = []
        
        self.pos = [0,0]
        
        self.collisonArray = []
        for i in range(self.height):
            row = []
            for j in self.numbers[i*self.width:i*self.width+self.width]:
                row.append(int(j))
            self.collisonArray.append(row)
            
        print self.collisonArray
        
        for j in range(self.width):
            for i in range(self.height):
                if self.collisonArray[i][j] == 1:
                    self.blocks.append(Block(image))
                    self.blocks[-1].rect = self.blocks[-1].rect.move(j*blockSize,i*blockSize)
                    self.allSprites.add(self.blocks[-1].sprite)
                                        
        
    def update(self):
        #self.rect.topleft = (0,0)
        self.tat = 0
    
    def setSpawnPos(self,pos):
        self.pos = list(pos)
        print pos
        for block in self.blocks:
            block.rect = block.rect.move(self.pos[0],0)
            
    def move(self,dir,length,playField,playingField):
        oldRects = []
        newRects = []
        for block in self.blocks:
            oldRects.append(block.rect)
            if dir == "down":
                newRects.append(block.rect.move(0,length))
                self.pos[1] = self.pos[1] + length
            elif dir == "left":
                newRects.append(block.rect.move(-length,0).clamp(playField))
                self.pos[0] = self.pos[0] - length
            elif dir == "right":
                newRects.append(block.rect.move(length,0).clamp(playField))
                self.pos[0] = self.pos[0] + length
            elif dir == "up":
                newRects.append(block.rect.move(0,-length).clamp(playField))
                self.pos[1] = self.pos[1] - length
            
        if playingField.collides(oldRects,newRects) == "false":
            for i in range(len(self.blocks)):
                self.blocks[i].rect = newRects[i]
                
            
    def rotate(self):
        
        
        print "width: " + str(self.width) + "  height: " + str(self.height)
        print self.collisonArray
        
        tmpCollisionArray = []
        
        
        
        for i in range(self.width):
            row = []
            for j in range(self.height):
                print "i:: " + str(i) + "  j:: " + str(j)
                row.append(self.collisonArray[self.height-1-j][i])
            tmpCollisionArray.append(row)
        self.collisonArray = tmpCollisionArray
        
        print self.collisonArray
        self.width, self.height = self.height, self.width
        
        for i in range(len(self.blocks)):
            self.blocks[i].rect.topleft = tuple(self.pos)
        
        blockCounter = 0
        for j in range(self.width):
            for i in range(self.height):
                if self.collisonArray[i][j] == 1:
                    self.blocks[blockCounter].rect = self.blocks[-1].rect.move(j*self.blockSize,i*self.blockSize)
                    blockCounter = blockCounter + 1
            
        
    def __deepcopy__(self,dup):
        return CompleteBlock(copy.deepcopy(self.height, dup),copy.deepcopy(self.width, dup),copy.deepcopy(self.numbers, dup),copy.deepcopy(self.imageName, dup),copy.deepcopy(self.blockSize, dup))

class PlayingField:
    
    def __init__(self,height,width,blockSize):
        self.width = width
        self.height = height
        self.blockSize = blockSize
        self.blockList = []
        self.allSprites = pygame.sprite.Group()
        self.activeBlocks = []
        self.fieldSurface = pygame.Surface((self.width*self.blockSize,self.height*self.blockSize))
        self.playField = Rect(0,0,self.width*self.blockSize,self.height*self.blockSize)
        self.fieldSurface.fill((120,100,50))
        
        self.collisionArray = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(0)
            self.collisionArray.append(row)        

    def addBlock(self,block):
        self.blockList.append(block)
        
    def drawAllBlocks(self):
        self.fieldSurface.fill((120,100,50))
        blocks = self.allSprites.draw(self.fieldSurface)
        pygame.display.update(blocks)
    
    def spawnRandBlock(self):
        random.seed(time.time()*256)
        blocknumber = random.randint(0,len(self.blockList)-1)
        spawnWidth = 0
        if len(self.activeBlocks) != 0:
            for block in self.activeBlocks:
                spawnWidth += block.width
                print "Breite: " + str(block.width)
        dup = copy.deepcopy(self.blockList[blocknumber])
        self.activeBlocks.append(dup)
        print spawnWidth
        self.activeBlocks[-1].setSpawnPos((spawnWidth*self.blockSize,0))
        self.allSprites.add(self.activeBlocks[-1].allSprites)
        self.updateCollisionArray()
        
    def updateCollisionArray(self):
        for i in range(self.height):
            for j in range(self.width):
                self.collisionArray[i][j] = 0
        
        for block in self.activeBlocks:
            for lBlock in block.blocks:
                pos = lBlock.rect.topleft
                self.collisionArray[pos[1]/self.blockSize][pos[0]/self.blockSize] = 1
        print self.collisionArray
            
        
        
    def moveActiveBlock(self,dir):
        self.activeBlocks[-1].move(dir,self.blockSize,self.playField,self)
        self.drawAllBlocks()
        self.updateCollisionArray()
    
    def rotateActiveBlock(self):
        self.activeBlocks[-1].rotate()
        self.drawAllBlocks()
    
    def moveBlocksDown(self):
        for block in self.activeBlocks:
            if block.stuck != "true":
                block.move("down",self.blockSize,self.playField,self)
        self.drawAllBlocks()
        self.updateCollisionArray()
    
    def hasCollision(self,block,dir):
        self.bla = 0
                    
    def update(self):
        self.drawAllBlocks()
        
    def collides(self,oldRects,newRects):
        oldTuples = []
        for rect in oldRects:
            oldTuples.append((rect[0]/self.blockSize,rect[1]/self.blockSize))
        print oldTuples
        
        test = []
        for rect in newRects:
            x = rect[0]/self.blockSize
            y = rect[1]/self.blockSize
            print "xy" + str((x,y))
            if x<self.width and x >=0 and y<self.height and y >=0:
                if (x,y) not in oldTuples and self.collisionArray[x][y] == 1:
                    test.append("true")
                else:
                    test.append("false")
            else:
                print "stuck"
                return "true"
            
        if "true" in test:
            print "true"
            return "true"
        else:
            print "false"
            return "false"
                
def main():
    pygame.display.init()
    window = pygame.display.set_mode(screen_dims)
    pygame.display.set_caption('FastBlocks')
    screen = pygame.display.get_surface() 
    
    playingField = initialize("config.xml")
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((120,255,255))
    
    pygame.time.set_timer(USEREVENT+1, 1000)

    
    print len(playingField.blockList)
    
    playingField.spawnRandBlock()
    
    #allsprites = pygame.sprite.RenderPlain((playingField.blockList[0]))
               
    clock = pygame.time.Clock()
    screen.blit(background, (0, 0))
    
    while True:
        input(pygame.event.get(),playingField)
        #pygame.time.wait(600)
        
        
        playingField.update()
        screen.blit(playingField.fieldSurface, (50,50))
        pygame.display.flip()
        
        

if __name__ == "__main__":
    main()