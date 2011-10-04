'''
Created on 01.10.2011

@author: Ecki
The great Controller for all game Logic

'''
import pygame, sys, os, random, time, copy
from text import Text
from pygame.compat import geterror
from pygame.locals import *

'main dir without py2exe'
main_dir = os.path.split(os.path.abspath(__file__))[0]
'main dir with py2exe'
#main_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
data_dir = os.path.join(main_dir,'data')

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

'Sprite-Class for a single Block - will be part of the CompleteBlock'
class Block(pygame.sprite.Sprite):
    
    def __init__(self,image):
        pygame.sprite.Sprite.__init__(self)
        self.imageName = image
        self.image, self.rect = load_image(image, -1)
        self.standardImage = self.image
        self.sprite = pygame.sprite.RenderPlain(self)
        self.id = 0
        
    def __del__(self):
        print "ICH WURDE ZERTSTOERT"

'Container and Controller of the single Block Sprites'
class CompleteBlock(): #TODO: Lookup Python Movable
    def __init__(self,height,width,numbers,image,blockSize):
        ' width and height and blocksize in pixel of the composed blocks'
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

        ' creating the Array which defines, where the single blocks are'
        for i in range(self.height):
            row = []
            for j in self.numbers[i*self.width:i*self.width+self.width]:
                row.append(int(j))
            self.collisonArray.append(row)
        
        ' moving the single block-Sprites to the right position according to the collisionArray'
        for j in range(self.width):
            for i in range(self.height):
                if self.collisonArray[i][j] == 1:
                    self.blocks.append(Block(image))
                    self.blocks[-1].rect = self.blocks[-1].rect.move(j*blockSize,i*blockSize)
                    self.allSprites.add(self.blocks[-1].sprite)
    
    'assigning a unique index for every block and returns the last index-value'
    def setBlockIndex(self,index):
        for block in self.blocks:
            self.blockIndices.append(index)
            block.id = index
            index += 1
        return index

    'setting the position where the block should spawn'
    def setSpawnPos(self,pos):
        self.pos = list(pos)
        for block in self.blocks:
            block.rect = block.rect.move(self.pos[0],self.pos[1])
    
    '''
    moves all blocks
    dir - "left","right","down" - movedirection
    playingField - needed for collision testing
    forced - True,False - whether there should be checked for collisions
    steps - number of steps (size of blocksize) to move in one direction
    intersect - blockindices, which should be moved
    '''
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
    
    'rotating the whole block 90 degrees around the center block'
    def rotate(self,playingField):
        'creating the rotated data for collisionArray and block-Rects'
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

        'collision check for the "new" block'
        if playingField.collides(oldRects,newRects,self.blockIndices) == False:
            self.collisonArray = tmpCollisionArray
            self.width, self.height = self.height, self.width
            for i in range(len(self.blocks)):
                self.blocks[i].rect = newRects[i]
    
    'deleting the block with the specified ids'
    def deleteBlocks(self,blockIndices):
        deletedBlockSprites = pygame.sprite.RenderUpdates()
        deletedBlocks = []
        for block in self.blocks:
            if block.id in blockIndices:
                self.allSprites.remove(block.sprite)
                deletedBlockSprites.add(block.sprite)
                deletedBlocks.append(block)
        
        for block in deletedBlocks:
            self.blocks.remove(block)
        deletedBlocks = []
        
        delete = False
        if len(self.blocks) == 0:
            delete = True
        
        return deletedBlockSprites, delete
    
    'changing the image of specified blocks'
    def changeImage(self,indices,image):
        for block in self.blocks:
            if block.id in indices:
                block.image = image
                #print "chanage change change"
    
    'changing the image back to normal for specified blocks'
    def changeToOldImage(self,indices):
        for block in self.blocks:
            if block.id in indices:
                block.image = block.standardImage

    'copy constructor'
    def __deepcopy__(self,dup):
        return CompleteBlock(copy.deepcopy(self.height, dup),copy.deepcopy(self.width, dup),copy.deepcopy(self.numbers, dup),copy.deepcopy(self.imageName, dup),copy.deepcopy(self.blockSize, dup))

class PlayingField:
    
    def __init__(self,height,width,pos,screenDims,blockSize):
        self.width = width
        self.height = height
        self.pos = pos 
        self.screenDims = screenDims
        
        self.blockSize = blockSize
        self.blockList = []
        self.allSprites = pygame.sprite.RenderUpdates()
        
        self.deletedBlocks = pygame.sprite.RenderUpdates()
        self.activeBlocks = []
        self.lines = []
        self.crossBlock = None
        self.nextBlockId = -1
        self.nextBlockText = False
        self.nextBlock = False
        self.blockIndex = 1
         
        'all the information and their texts'
        self.linesText = False         
        self.linesCount = 0
        self.scoreText = False
        self.score = 0
        self.highScoreText = False
        self.highScore = 0
        self.speedText = False
        self.speed = 600
        self.gameOverText = False
        self.gameOverPointsText = False
        self.userNameText = False
        if pygame.font:
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'feasfbrg.ttf'), 74)
            self.gameOverText = Text(font,"GameOver!!",(self.screenDims[0]/2,self.screenDims[1]/2-74),0)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'feasfbrg.ttf'), 48)
            self.gameOverPointsText = Text(font,"Youre Highscore:",(self.screenDims[0]/2,self.screenDims[1]/2),0)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
            self.levelText = Text(font,"Level: " + str(7-self.speed/100),((self.width+4)*self.blockSize + self.blockSize - 10,self.pos[1] + self.height/3*self.blockSize + 150),2)
            self.allSprites.add(self.levelText)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
            self.scoreText = Text(font,"Score: " + str(self.score),((self.width+4)*self.blockSize + self.blockSize - 10,self.pos[1] + self.height/3*self.blockSize+18 + 150),2)
            self.allSprites.add(self.scoreText)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 28)
            self.linesText = Text(font,"Lines: " + str(self.linesCount),((self.width+4)*self.blockSize + self.blockSize -10,self.pos[1] + self.height/3*self.blockSize+18*2 + 150),2)
            self.allSprites.add(self.linesText)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 26)
            self.highScoreText = Text(font,"Best: " + str(self.highScore),((self.width+4)*self.blockSize + self.blockSize -10,self.pos[1] + self.height/3*self.blockSize+18*3 + 150),0)
            self.allSprites.add(self.highScoreText)
            
            font = pygame.font.Font(os.path.join(data_dir,'fonts', 'acknowtt.ttf'), 32)
            self.userNameText = Text(font,"username",((self.width+4)*self.blockSize + self.blockSize -10,self.pos[1] + self.height/3*self.blockSize+18*8 + 150),0)
            self.allSprites.add(self.userNameText)
        else:
            print "Fonts und Texte leider nicht verfuegbar :("
        
        self.animation = False
        self.animationCount = 3
        self.resetCheck = False
        self.paused = False
        
        fbg_image, rect = load_image("images/fullbackground.bmp")
        bg_image,rect = load_image("images/background.bmp")
        pv_image,rect = load_image("images/preview.bmp")
        
        'Appearance of the whole game screen'
        self.background = pygame.Surface((self.width*self.blockSize,self.height*self.blockSize))
        self.background.blit(bg_image,(0,0))
        self.preview = pygame.Surface((4*self.blockSize,4*self.blockSize))
        self.preview.blit(pv_image,(0,0))
        self.fieldSurface2 = pygame.Surface(self.screenDims)
        self.fieldSurface2.blit(fbg_image,(0,0))
        self.fieldSurface2.blit(self.background,self.pos)
        self.fieldSurface2.blit(self.preview, (self.pos[0] + self.width*self.blockSize + self.blockSize,self.pos[1] ))
        
        self.collisionArray = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(0)
            self.collisionArray.append(row)
            
    def reset(self):
        self.paused = True
        print "Reset"
        self.allSprites = pygame.sprite.RenderUpdates()
        self.deletedBlocks = pygame.sprite.RenderUpdates()
        for block in self.activeBlocks:
            sprites, delete = block.deleteBlocks(block.blockIndices)
            self.deletedBlocks.add(sprites)
        self.activeBlocks = []
        self.lines = []
        self.nextBlockId = -1
        self.nextBlock = False
        self.blockIndex = 1
        self.speed = 600
        
        self.linesCount = 0
        if self.score > self.highScore:
            self.highScore = self.score
            self.gameOverPointsText.update("Highscore: " + str(self.highScore) + " :D")
            self.allSprites.add(self.gameOverPointsText)
            self.highScoreText.update("Best: " + str(self.highScore))
        self.score = 0
        
        self.animation = False
        self.animationCount = 3
        
        self.allSprites.add(self.gameOverPointsText)
        self.allSprites.add(self.gameOverText)
        self.allSprites.add(self.userNameText)

        fbg_image, rect = load_image("images/fullbackground.bmp")
        bg_image,rect = load_image("images/background.bmp")
        pv_image,rect = load_image("images/preview.bmp")
        
        pygame.time.set_timer(USEREVENT+5, 0)
        pygame.time.set_timer(USEREVENT+4, 5000)

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
        previewPos = (self.pos[0] + self.width*self.blockSize + self.blockSize + self.blockSize,self.pos[1] );
        if self.nextBlock.height != 4:
            previewPos = (self.pos[0] + self.width*self.blockSize + self.blockSize + self.blockSize,self.pos[1] + self.blockSize);
        self.nextBlock.setSpawnPos(previewPos)
        self.allSprites.add(self.nextBlock.allSprites)
        
    def updateCollisionArray(self):
        for i in range(self.height):
            for j in range(self.width):
                self.collisionArray[i][j] = 0

        for block in self.activeBlocks:
            for lBlock in block.blocks:
                pos = lBlock.rect.topleft
                if self.collisionArray[(pos[1]-self.pos[1])/self.blockSize][(pos[0]-self.pos[0])/self.blockSize] == 0:
                    self.collisionArray[(pos[1]-self.pos[1])/self.blockSize][(pos[0]-self.pos[0])/self.blockSize] = lBlock.id
                else:
                    self.reset()

    def moveActiveBlock(self,dir):
        if self.activeBlocks[-1].stuck != True and self.paused==False:
            self.activeBlocks[-1].move(dir,self)
        self.updateCollisionArray()
    
    def rotateActiveBlock(self):
        if self.activeBlocks[-1].stuck != True and self.paused==False:
            self.activeBlocks[-1].rotate(self)
        self.updateCollisionArray()
    
    def moveBlocksDown(self):
        for block in self.activeBlocks:
            if block.stuck != True:
                block.move("down",self)
    
    def update(self):
        if self.animation == False and len(self.activeBlocks) > 0: 
            self.lines = []    
            self.moveBlocksDown()
            stuck = True
            for block in self.activeBlocks:
                if block.stuck == False:
                    stuck = False
            
            if stuck == True:
                self.lines = self.checkReadyLines()
                deletedLinesCount = 0
                if len(self.lines)>0:
                    self.animateLines()
                if self.animation == False:
                    self.score = self.score + 15 + 50 * deletedLinesCount
                    self.spawnRandBlock()
            self.updateCollisionArray() 

            if self.scoreText != False:
                self.scoreText.update("Score: " + str(self.score))
            if self.linesText != False:
                self.linesText.update("Lines: " + str(self.linesCount))
            if self.levelText != False:
                self.levelText.update("Level: " + str(7-self.speed/100))

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
    
    def deleteReadyLines(self):
        indices = []
        for lineIndex in self.lines:
            indices.extend(self.collisionArray[lineIndex])

        deleteIndices = []
        for i,block in enumerate(self.activeBlocks):
            sprites, delete = block.deleteBlocks(indices)
            self.deletedBlocks.add(sprites)
            if delete:
                deleteIndices.append(i)
        
        for offset, index in enumerate(deleteIndices):
            index -= offset
            del self.activeBlocks[index]

        downerList = []
        batch = 0
        for i in range(len(self.lines)):
            if len(self.lines)-2-i >= 0:
                diff = self.lines[len(self.lines)-1-i] - self.lines[len(self.lines)-2-i]
                if ( diff > 1):
                    for j in range(diff-1):
                        downerList.append(self.collisionArray[self.lines[len(self.lines)-2-i]+j+1])
                        downerList[-1].extend([i+1+batch])
                batch = batch + diff - 1

        upperList = self.collisionArray[0:self.lines[0]]

        for block in self.activeBlocks:
            intersectsUpper = []         
            downUpper = False
            for row in upperList:
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
                block.move("down",self,True,len(self.lines),intersectsUpper)
                    
        self.allSprites.remove(self.deletedBlocks)
        
        return len(self.lines)
    
    def animateLines(self):
        indices = []
        for line in self.lines:
            indices.extend(self.collisionArray[line])
        if self.animationCount == 3:
            for block in self.activeBlocks:
                block.changeImage(indices,self.crossBlock.image)
            pygame.time.set_timer(USEREVENT+3, 75)
            self.animation = True
        elif self.animationCount in (2,0):
            for block in self.activeBlocks:
                block.changeToOldImage(indices)
        elif self.animationCount == 1:
            for block in self.activeBlocks:
                block.changeImage(indices,self.crossBlock.image)