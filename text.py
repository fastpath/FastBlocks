'''
Created on 01.10.2011

@author: Ecki
'''
import pygame

'Class for updatable Text with position and a color'
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