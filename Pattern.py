import pygame
pygame.init()
from random import random, choice
from math import cos, sin, pi
from fractions import gcd

magenta = 255,0,255
black = 0, 0, 0
white = 255, 255, 255

width, height = (500, 500)
limit = min([width, height]) / 5

monitor = pygame.display.set_mode([width, height])

fps = 60
delay = 1000 // fps

flux = 0.5
stable = 20

bend = 0.3

class Pattern:
    def __init__(self):
        # A main object for the pattern
        self.symmetry = 6
        self.angle = 0
        self.spin = 0.25 + random()
        self.children = []
        self.changes = []
        self.complexity = 4
        self.goal = 0
        self.partitions = 1
        self.current = 0
        self.count = 0
        self.step = 0
        
        first_child = Line(3 * limit / 4, bend+(1-2*bend)*random(), self, self, random(), choice([1, -1]), limit)
        self.children.append(first_child)
        first_child.mutate()
        for i in range(3):
            new_child = Line(3 * limit / 8, bend+(1-2*bend)*random(), first_child, self, random(), choice([1, -1]), limit/2)
            first_child.children.append(new_child)
            new_child.mutate()

    def draw(self):
        # Draws the pattern in the center of the screen
        canvas = pygame.Surface([width, height])
        canvas.fill(magenta)
        for child in self.children:
            child.draw(canvas, width/2, height/2, self.angle)
        canvas.set_colorkey(magenta)
        for i in range(self.symmetry):
            angle = 360*i/self.symmetry
            for j in range(self.partitions):
                to_draw = pygame.transform.rotate(canvas, angle+j*self.current)
                pos = int((width - to_draw.get_width())/2)
                monitor.blit(to_draw, [pos, pos])
                    

    def change(self):
        # Changes the pattern according to existing plans
        self.angle += self.spin/fps
        if self.goal:
            self.current += self.step
            self.count -= 1
            if self.count == 0:
                self.symmetry = self.goal
                self.goal = 0
                self.step = 0
                self.current = 0
                self.partitions = 1
        previous = []
        to_update = []
        keep = []
        for item in self.changes:
            if item.act():
                to_update.append(item.target)
            else:
                keep.append(item)
        self.changes = keep
        for line in to_update:
            if not line.deleted:
                line.mutate()

    def plan(self):
        if random()*fps < 0.1:
            # Changes the symmetry of the pattern
            if not self.goal:
                while not self.goal or self.goal == self.symmetry:
                    self.goal = choice([4,6,8])
                self.current = 360/self.symmetry
                time = 5 *(1 + random())
                self.step = (360/self.goal - self.current)/time/fps
                self.count = int(time*fps)
                top = max([self.goal, self.symmetry])
                self.symmetry = gcd(self.symmetry, self.goal)
                self.partitions = top // self.symmetry
        if random()*fps < 1:
            # Changes the spin speed
            self.spin += 2 * random() - 1
            self.spin *= 0.9
        if not self.children:
            # "Reboots" the pattern if it has disappeared completely
            new_child = Line(0, 0, self, self, random(), choice([1, -1]), 100)
            self.changes.append(Change(new_child, "radius", 50, 0.5))
            self.children.append(new_child)

class Line:
    def __init__(self, radius, arc, parent, host, attach, direction, maxr):
        # An object representing a single curved line segment
        self.radius = radius
        self.arc = arc
        self.parent = parent
        self.host = host
        self.children = []
        self.attach = attach
        self.direction = direction
        self.radius_grow = False
        self.arc_grow = False
        self.attach_grow = False
        self.maxr = maxr
        self.deleted = False

    def draw(self, surface, x, y, angle):
        # Draws the line and all lines attached to it
        draw_bend(surface, x, y, angle, self.radius, self.arc, self.direction)
        for child in self.children:
            if self.maxr != child.maxr*2:
                print(self.maxr, child.maxr)
                assert 0
            angled_x = self.radius*self.direction*(cos(2*pi*self.arc*child.attach)-1)
            angled_y = -self.radius*sin(2*pi*self.arc*child.attach)
            new_x = x + cos(angle)*angled_x + sin(angle)*angled_y
            new_y = y + cos(angle)*angled_y - sin(angle)*angled_x
            new_angle = angle + self.direction * self.arc * child.attach * 2 * pi
            child.draw(surface, new_x, new_y, new_angle)

    def delete(self):
        # Removes the line and attaches all child lines to its parent
        self.deleted = True
        self.host.complexity -= 1
        self.parent.children.remove(self)
        for child in self.children:
            child.double_maxr()
            child.attach = self.attach
            child.parent = self.parent
            self.parent.children.append(child)

    def double_maxr(self):
        # Doubles the allowed radius of all children (used when deleting)
        self.maxr *= 2
        for child in self.children:
            child.double_maxr()
    
    def mutate(self):
        # Plans changes to the line
        if random()*self.host.complexity*3 < flux*stable:
            # Adds a new branch
            self.host.complexity += 1
            new_child = Line(0, 0, self, self.host, random(), choice([1, -1]), self.maxr/2)
            time = 0.5 + 2 * random()
            self.children.append(new_child)
            new_child.mutate()
        if not self.radius_grow:
            # Changes the radius
            goal = (3 * random() + 1) * self.maxr / 4
            time = 0.5 + 2 * random()
            self.host.changes.append(Change(self, "radius", goal, time))
        if not self.arc_grow:
            # Changes the arc angle
            if random()*stable < flux*self.host.complexity:
                # Removes the line
                goal = 0
            else:
                goal = bend+(1-2*bend)*random()
            time = 0.5 + 2 * random()
            self.host.changes.append(Change(self, "arc", goal, time))
        if not self.attach_grow:
            # Changes where the line attaches to its parent
            goal = random()
            time = 0.5 + 2 * random()
            self.host.changes.append(Change(self, "attach", goal, time))

def draw_bend(surface, x, y, angle, radius, arc, direction):
    # The basic line drawing function
    corner_x = x + (-direction * cos(angle) - 1) * radius
    corner_y = y + (direction * sin(angle) - 1) * radius
    width = min([2, int(radius)])
    if direction == 1:
        pygame.draw.arc(surface, black, [corner_x, corner_y, 2*radius, 2*radius], angle, angle + pi * arc * 2, width)
    elif direction == -1:
        pygame.draw.arc(surface, black, [corner_x, corner_y, 2*radius, 2*radius], angle + pi * (1 - arc * 2), angle + pi, width)

class Change:
    # An object that keeps track of a planned change
    def __init__(self, target, kind, goal, time):
        self.target = target
        self.goal = goal
        self.kind = kind
        if kind == "radius":
            self.step = (goal - target.radius) / time / fps
            target.radius_grow = True
        elif kind == "arc":
            self.step = (goal - target.arc) / time / fps
            target.arc_grow = True
        elif kind == "attach":
            self.step = (goal - target.attach) / time / fps
            target.attach_grow = True
        self.count = int(time * fps)

    def act(self):
        # Enacts the change
        if self.kind == "radius":
            self.target.radius += self.step
        elif self.kind == "arc":
            self.target.arc += self.step
        elif self.kind == "attach":
            self.target.attach += self.step
        self.count -= 1
        if self.count == 0:
            if self.kind == "radius":
                self.target.radius_grow = False
            elif self.kind == "arc":
                self.target.arc_grow = False
                if self.goal == 0:
                    assert not self.target.deleted
                    self.target.delete()
                    return True
            elif self.kind == "attach":
                self.target.attach_grow = False
            return True
        return False

pattern = Pattern()

last_time = -delay
while True:
    monitor.fill(white)
    pattern.draw()
    pattern.change()
    pattern.plan()
    pygame.display.update()
    new_time = pygame.time.get_ticks()
    error = new_time - last_time - delay
    pygame.time.delay(max([0, delay - error]))
    last_time = new_time
    pygame.event.pump()

