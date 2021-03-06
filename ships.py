from math import fabs
import pygame
import os
from settings import Settings
from turrets import *
from random import randint

class Ship(pygame.sprite.Sprite):
    def __init__(self, filename, team, dxy, xy):
        super().__init__()
        self.size = (150,150)
        self.original_image = pygame.image.load(os.path.join(Settings.path_ships, filename)).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, self.size)
        self.image = self.original_image
        self.rect = self.image.get_rect() 
        self.mouse = pygame.mouse.get_pos()
        self.dxy = dxy
        self.move = False
        self.rotated = False
        self.selected = False
        self.speed = 0
        self.rotation_speed = 1
        self.turrets = pygame.sprite.Group()
        self.team = team
        if self.team == 1:
            self.rect.center = xy
        else:
            self.rect.centerx = xy[0] + 800
            self.rect.centery = xy[1] + 800
        self.range = 500
        self.distance_x = randint(200, self.range)
        self.distance_y = randint(-100, self.range)
        self.aiming = False
        self.hull = 1000
        self.shields = 1000
        self.regeneration_rate = 1
        self.destroyed = False
        self.current_angle = 0
        self.stored_fighters = 0
        #for animation
        self.images = []
        self.imageindex = 0
        self.clock_time = pygame.time.get_ticks()
        self.animation_time = 50
        self.images.append(self.original_image) 

        self.waypoint_x = self.mouse[0] 
        self.waypoint_y = self.mouse[1]

        #check sprites
        self.appended_damaged = False

        #for spawning
        self.spawn_rect = pygame.Surface((500,500))  # the size of your rect
        self.spawn_rect.set_alpha(128)                # alpha level
        self.spawn_rect.fill((0,255,0))           # this fills the entire surface
        self.spawn_area = self.spawn_rect.get_rect(center = self.rect.center)
        self.jumped = False
        self.jump_rotation = False


    def update_sprite(self):
        if self.appended_damaged == False:
            if self.hull < 800:
                self.appended_damaged = True
                self.images.clear()
                for i in range(4):
                    bitmap = pygame.image.load(os.path.join(
                        self.path, self.name+f"_damaged{i}.png"))
                    scaled = pygame.transform.scale(bitmap,self.size)
                    self.images.append(scaled)

    def animate(self):
            if pygame.time.get_ticks() > self.clock_time:
                self.clock_time = pygame.time.get_ticks() + self.animation_time
                self.image = pygame.transform.rotate(self.original_image, int(self.current_angle))
                self.imageindex += 1
                if self.imageindex >= len(self.images):
                    self.imageindex = 0
                self.original_image = self.images[self.imageindex]

    def range_check(self, screen):
        self.range_circle = pygame.draw.circle(screen, (255, 0, 0), self.rect.center, self.range)
        
    def warp_area(self, screen):
        screen.blit(self.spawn_rect, (self.rect.centerx - 250,self.rect.centery - 250))
        self.spawn_area = self.spawn_rect.get_rect(center = self.rect.center)

    def update_target(self, target, group):
            self.shoot(target.rect.center, group)

    def regenerate(self):
        if self.shields < 1000:
            self.shields += self.regeneration_rate

    def get_range(self, target, group):
        if self.aiming == False:
            if self.range_circle.collidepoint(target.rect.center):
                self.aiming = True
                self.target = target
                self.target_group = group
            else:
                self.aiming = False
                self.target = None
                self.target_group = None

        if self.aiming == True:
            self.update_target(self.target, self.target_group)
            if not self.range_circle.collidepoint(self.target.rect.center) or self.target.destroyed or self.target_group == self.team:
                self.target = None
                self.target_group = None
                self.aiming = False

    def jump_in(self,dxy):
            dx = dxy[0]
            dy = dxy[1]
            self.rotate(dx,dy)
            if self.jump_rotation:
                if self.rect.centerx < dx:
                    self.rect.centerx += 50
                if self.rect.centerx > dx:
                    self.rect.centerx -= 50
                if self.rect.centery < dy:
                    self.rect.centery += 50
                if self.rect.centery > dy:
                    self.rect.centery -= 50

                if self.rect.collidepoint(dxy):
                    self.jumped = True

    def mark(self, screen):
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

    def draw_healthbar(self, screen):
        pygame.draw.rect(screen, (0, 0, 255), (self.rect.centerx - 50, self.rect.centery - 61, self.shields *0.1, 3))
        pygame.draw.rect(screen, (0, 255, 0), (self.rect.centerx - 50, self.rect.centery - 58, self.hull* 0.1, 3))

    def draw(self, screen):
        if self.selected:
            self.create_waypoint(screen)
            self.mark(screen)

        self.draw_turrets(screen)
        screen.blit(self.image, self.rect)
        self.draw_healthbar(screen)
        

    def draw_turrets(self, screen):
        for turret in self.turrets:
            turret.draw(screen)

    def update(self, offset):
        if self.jumped == False:
            self.jump_in((self.dxy[0] + offset[0],self.dxy[1] - offset[1]))
    
        self.rect.centerx = self.rect.centerx + offset[0]
        self.rect.centery = self.rect.centery - offset[1]
        self.waypoint_x = self.waypoint_x + offset[0]
        self.waypoint_y = self.waypoint_y - offset[1]
        self.animate()
        if self.selected:
            self.mouse_actions()
            
        for turret in self.turrets:
            turret.update(self.rect.center)
      
        if self.rotated:
            self.rotate(self.waypoint_x, self.waypoint_y)

        if self.move:            
            if self.rect.centerx < self.waypoint_x:
                self.rect.centerx += self.speed
            if self.rect.centerx > self.waypoint_x:
                self.rect.centerx -= self.speed
            if self.rect.centery < self.waypoint_y:
                self.rect.centery += self.speed
            if self.rect.centery > self.waypoint_y:
                self.rect.centery -= self.speed


            if self.waypoint_circle.collidepoint(self.rect.center):
                self.move = False
                self.rotated = False

            
        
        self.regenerate()
        self.check_death()

    def mouse_actions(self):
        rightclick = pygame.mouse.get_pressed() == (0, 0, 1)
        leftclick = pygame.mouse.get_pressed() == (0, 1, 0)
        if rightclick:
            self.move = False
            self.rotated = True
            self.waypoint_x = pygame.mouse.get_pos()[0]
            self.waypoint_y = pygame.mouse.get_pos()[1]
            
        if leftclick:
            self.mouse = pygame.mouse.get_pos()
            for turret in self.turrets:
                turret.shoot(self.mouse[0], self.mouse[1])

    def create_waypoint(self, screen):
        self.waypoint_circle = pygame.draw.circle(screen, (255, 255, 0), (self.waypoint_x,self.waypoint_y), 5)
        
    def shoot(self, target, target_group):
        for turret in self.turrets:
            turret.shoot(target, target_group)

    def check_death(self):
        if self.hull <= 0:
            self.destroyed = True
            self.kill()

    def rotate(self, dx,dy):
        rel_x, rel_y = dx - self.rect.centerx, dy - self.rect.centery
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) -90
        if self.current_angle < angle:
            self.current_angle = self.current_angle + self.rotation_speed
        elif self.current_angle > angle:
            self.current_angle = self.current_angle - self.rotation_speed

        self.image = pygame.transform.rotate(self.original_image, int(self.current_angle))
        self.rect = self.image.get_rect(center=self.rect.center)
        
        if self.jumped:
            if self.current_angle < angle + self.rotation_speed and self.current_angle > angle - self.rotation_speed:
                self.move = True
                self.rotated = False
        else:
            if self.current_angle < angle + self.rotation_speed and self.current_angle > angle - self.rotation_speed:
                self.jump_rotation = True

#ship types  

class Carrier(Ship):
    def __init__(self, filename, team, dxy, xy):
        super().__init__(filename, team, dxy, xy)
        self.size = (150,150)
        self.turrets.add(Dualies(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.speed = 2
        self.stored_fighters = 3
        self.name = "carrier"
        self.path = Settings.path_carrier
        for i in range(4):
            bitmap = pygame.image.load(os.path.join(
                Settings.path_carrier, f"carrier{i}.png")).convert_alpha()
            scaled = pygame.transform.scale(bitmap,self.size)
            self.images.append(scaled)

class Assault(Ship):
    def __init__(self, filename, team, dxy, xy):
        super().__init__(filename, team, dxy, xy)
        self.size = (150,150)
        self.speed = 2
        self.turrets.add(Dualies(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.turrets.add(Breacher(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.range = 500
        self.name = "assault"
        self.path = Settings.path_assault
        for i in range(4):
            bitmap = pygame.image.load(os.path.join(
                Settings.path_assault, f"assault{i}.png")).convert_alpha()
            scaled = pygame.transform.scale(bitmap,self.size)
            self.images.append(scaled)

    def speed_up(self):
        self.speed += 1

class Conqueror(Ship):
    def __init__(self, filename, team, dxy, xy):
        super().__init__(filename, team,  dxy, xy)
        self.size = (150,150)
        self.speed = 1
        self.name = "conqueror"
        self.path = Settings.path_conqueror
        for i in range(3):
            bitmap = pygame.image.load(os.path.join(self.path, f"conqueror{i+1}.png")).convert_alpha()
            scaled = pygame.transform.scale(bitmap, self.size)
            self.images.append(scaled)
            
class Dreadnought(Ship):
    def __init__(self, filename, team,  dxy, xy):
        super().__init__(filename, team,  dxy, xy)
        self.size = (500, 1000)
        self.speed = 1
        self.turrets.add(Dualies(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.turrets.add(Breacher(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.range = 2000
        self.hull = 10000
        self.shields = 10000
        self.name = "dreadnought"
        self.path = Settings.path_dreadnought
        self.images.clear()
        for i in range(3):
            bitmap = pygame.image.load(os.path.join(
                Settings.path_dreadnought, f"dreadnought{i}.png")).convert_alpha()
            scaled = pygame.transform.scale(bitmap,self.size)
            self.images.append(scaled)

class Frigate(Ship):
    def __init__(self, filename, team,  dxy, xy):
        super().__init__(filename, team,  dxy, xy)
        self.size = (150,150)
        self.speed = 2
        self.turrets.add(Dualies(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.turrets.add(Breacher(randint(self.rect.left,self.rect.right), randint(self.rect.top, self.rect.bottom)))
        self.range = 500
        self.name = "frigate"
        self.path = Settings.path_frigate
        for i in range(3):
            bitmap = pygame.image.load(os.path.join(
                Settings.path_frigate, f"frigate{i}.png")).convert_alpha()
            scaled = pygame.transform.scale(bitmap,self.size)
            self.images.append(scaled)