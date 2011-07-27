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

class CompleteBlock(pygame.sprite.Sprite): #TODO: Lookup Python Movable
    
    def __init__(self,height,width,numbers,image):
        pygame.sprite.Sprite.__init__(self)
        self.imageName = image
        self.image, self.rect = load_image(image, -1)
        self.width = width
        self.height = height
        self.numbers = numbers
        
        self.sprite = pygame.sprite.RenderPlain(self)
        
        print "Numbers: " + self.numbers
        
        self.collisonArray = []
        for i in range(self.height):
            row = self.numbers[i*self.width:i*self.width+self.width]
            
            self.collisonArray.append(row)
        
        print self.collisonArray
        
    def update(self):
        #self.rect.topleft = (0,0)
        self.tat = 0
    
    def setSpawnPos(self,pos):
        self.rect.topleft = pos
        
    def __deepcopy__(self,dup):
        return CompleteBlock(copy.deepcopy(self.height, dup),copy.deepcopy(self.width, dup),copy.deepcopy(self.numbers, dup),copy.deepcopy(self.imageName, dup))

class PlayingField:
    
    def __init__(self,height,width,blockSize):
        self.width = width
        self.height = height
        self.blockSize = blockSize
        self.blockList = []
        self.allSprites = pygame.sprite.Group()
        self.activeBlocks = []
        self.fieldSurface = pygame.Surface((self.width*self.blockSize,self.height*self.blockSize))

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
        dup = copy.deepcopy(self.blockList[blocknumber])
        self.activeBlocks.append(dup)
        print spawnWidth
        self.activeBlocks[-1].setSpawnPos((spawnWidth*self.blockSize,0))
        self.allSprites.add(self.activeBlocks[-1].sprite)

def input(events,playingField): 
    for event in events: 
        if event.type == QUIT: 
            sys.exit(0) 
        else: 
            if event.type == MOUSEBUTTONDOWN:
                playingField.spawnRandBlock()

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
                    
                    playingField.addBlock(CompleteBlock(int(b_height),int(b_width),b_numbers,b_image))
                    
                    print "colorkey " + b_colorkey #TODO: individual colorkeys
    
    return playingField
    

def main():
    pygame.display.init()
    window = pygame.display.set_mode(screen_dims)
    pygame.display.set_caption('FastBlocks')
    screen = pygame.display.get_surface() 
    
    playingField = initialize("config.xml")
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((120,255,255))
    

    
    print len(playingField.blockList)
    
    playingField.spawnRandBlock()
    
    allsprites = pygame.sprite.RenderPlain((playingField.blockList[0]))
               
    clock = pygame.time.Clock()
    
    while True:
        input(pygame.event.get(),playingField)
        clock.tick(60)
        screen.blit(background, (0, 0))
        screen.blit(playingField.fieldSurface, (50,50))
        playingField.drawAllBlocks()
        
        pygame.display.flip()
        
        

if __name__ == "__main__":
    main()