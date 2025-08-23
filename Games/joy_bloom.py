import math, random, sys, time, json, os
import pygame

# =======================
# CONFIG
# =======================
WINDOW_W, WINDOW_H = 960, 600
GAME_DURATION_SEC = 120
BACKGROUND_COLOR = (20, 22, 28)
HUD_COLOR = (240, 240, 240)
FLOWER_VARIANTS = [
    (255, 183, 197), (255, 221, 148),
    (182, 255, 182), (173, 216, 255), (220, 200, 255)
]

MIN_FLOWER_SIZE, MAX_FLOWER_SIZE = 14, 26
SPAWN_EVERY_MIN, SPAWN_EVERY_MAX = 250, 550
MAX_FLOWERS_ON_SCREEN = 100

TITLE = "Joy Bloom"
VERSION = "v1.0"
EDITOR = "By Joy"

# sound/music files (place in same folder)
CLICK_SOUND = "Games/click.wav"
POP_SOUND = "Games/pop.wav"
BGM = "Games/bgm.mp3"
SCORES_FILE = "highscores.json"

# =======================
# UTIL
# =======================
def load_highscore():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f).get("highscore", 0)
    return 0

def save_highscore(score):
    current = load_highscore()
    if score > current:
        with open(SCORES_FILE, "w") as f:
            json.dump({"highscore": score}, f)

# =======================
# FLOWER
# =======================
class Flower:
    def __init__(self, x, y, size, color):
        self.x, self.y = x, y
        self.size = size
        self.color = color
        angle = random.uniform(0, 2*math.pi)
        speed = random.uniform(0.1, 0.35)
        self.vx = math.cos(angle)*speed
        self.vy = math.sin(angle)*speed
        self.wobble_t = random.uniform(0,1000)
        self.wobble_speed = random.uniform(0.01, 0.03)
        self.wobble_amp = random.uniform(0.5,2.0)
        self.pixel_coords = [(0,0),(1,0),(-1,0),(0,1),(0,-1)]
        extent = self.size*3
        self.rect = pygame.Rect(self.x-extent/2,self.y-extent/2,extent,extent)
        self.popping, self.pop_t = False,0

    def update(self, dt):
        if self.popping:
            self.pop_t += dt; return
        self.wobble_t += self.wobble_speed
        wobble_x = math.sin(self.wobble_t)*self.wobble_amp
        wobble_y = math.cos(self.wobble_t*0.8)*self.wobble_amp
        self.x += (self.vx + wobble_x*0.02)*(dt*60)
        self.y += (self.vy + wobble_y*0.02)*(dt*60)
        margin = self.size*2
        if self.x<margin or self.x>WINDOW_W-margin: self.vx*=-1
        if self.y<margin or self.y>WINDOW_H-margin: self.vy*=-1
        extent=self.size*3
        self.rect.x,self.rect.y=self.x-extent/2,self.y-extent/2

    def draw(self,surf):
        if self.popping:
            t=min(self.pop_t/0.25,1.0)
            scale=1+t*1.2; alpha=max(0,255-int(t*255))
            self._draw_pixels(surf,scale,alpha)
        else: self._draw_pixels(surf,1.0,255)

    def _draw_pixels(self,surf,scale,alpha):
        base=pygame.Color(*self.color)
        outline=(int(base.r*0.6),int(base.g*0.6),int(base.b*0.6))
        s=max(2,int(self.size*scale))
        for(px,py) in self.pixel_coords:
            rect=pygame.Rect(int(self.x+px*s-s/2),int(self.y+py*s-s/2),s,s)
            pygame.draw.rect(surf,(*self.color,alpha),rect)
            pygame.draw.rect(surf,outline,rect,1)
        # center
        cs=int(s*0.6)
        c_rect=pygame.Rect(int(self.x-cs/2),int(self.y-cs/2),cs,cs)
        pygame.draw.rect(surf,(250,240,150,alpha),c_rect)

    def contains_point(self,pos): return self.rect.collidepoint(pos)
    def pop(self): self.popping=True; self.pop_t=0

# =======================
# SCENES
# =======================
MENU, GAME, GAME_OVER, SETTINGS, SCORES, CREDITS = range(6)

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption(TITLE)
        self.screen=pygame.display.set_mode((WINDOW_W,WINDOW_H))
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("arial",24)
        self.big_font=pygame.font.SysFont("arial",48,bold=True)
        self.state=MENU
        self.score=0
        self.highscore=load_highscore()
        self.flowers=[]
        self.start_time=0
        self.last_spawn=0
        self.next_spawn=400
        # sounds/music
        self.click_snd=pygame.mixer.Sound(CLICK_SOUND)
        self.pop_snd=pygame.mixer.Sound(POP_SOUND)
        if os.path.exists(BGM): pygame.mixer.music.load(BGM); pygame.mixer.music.play(-1)

    def run(self):
        while True:
            dt=self.clock.tick(60)/1000
            for e in pygame.event.get():
                if e.type==pygame.QUIT: pygame.quit(); sys.exit()
                if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                    self.handle_click(e.pos)
            self.update(dt)
            self.draw()

    def handle_click(self,pos):
        if self.state==MENU:
            self.click_snd.play()
            y=WINDOW_H//2-100
            if self.button_rect("Play",y).collidepoint(pos): self.start_game()
            elif self.button_rect("Settings",y+60).collidepoint(pos): self.state=SETTINGS
            elif self.button_rect("High Scores",y+120).collidepoint(pos): self.state=SCORES
            elif self.button_rect("Credits",y+180).collidepoint(pos): self.state=CREDITS

        elif self.state==GAME:
            for f in reversed(self.flowers):
                if not f.popping and f.contains_point(pos):
                    f.pop(); self.score+=1; self.pop_snd.play(); break

        elif self.state==GAME_OVER:
            self.click_snd.play()
            if self.button_rect("Play Again",WINDOW_H//2+40).collidepoint(pos):
                self.start_game()
            elif self.button_rect("Main Menu",WINDOW_H//2+100).collidepoint(pos):
                self.state=MENU

        elif self.state in (SETTINGS,SCORES,CREDITS):
            self.click_snd.play()
            if self.button_rect("Back",WINDOW_H-80).collidepoint(pos): self.state=MENU

    def start_game(self):
        self.state=GAME; self.score=0; self.flowers=[]
        self.start_time=time.time(); self.last_spawn=0; self.next_spawn=400

    def update(self,dt):
        if self.state==GAME:
            elapsed=time.time()-self.start_time
            time_left=max(0,GAME_DURATION_SEC-elapsed)
            self.last_spawn+=dt*1000
            if len(self.flowers)<MAX_FLOWERS_ON_SCREEN and self.last_spawn>self.next_spawn:
                self.last_spawn=0; self.next_spawn=random.randint(SPAWN_EVERY_MIN,SPAWN_EVERY_MAX)
                size=random.randint(MIN_FLOWER_SIZE,MAX_FLOWER_SIZE)
                color=random.choice(FLOWER_VARIANTS)
                x=random.randint(size*3,WINDOW_W-size*3)
                y=random.randint(40+size*3,WINDOW_H-size*3)
                self.flowers.append(Flower(x,y,size,color))
            for f in self.flowers: f.update(dt)
            self.flowers=[f for f in self.flowers if not(f.popping and f.pop_t>=0.25)]
            if time_left<=0:
                self.state=GAME_OVER
                save_highscore(self.score)
                self.highscore=load_highscore()

    def button_rect(self,text,y):
        surf=self.font.render(text,True,(255,255,255))
        rect=surf.get_rect(center=(WINDOW_W//2,y))
        return rect

    def draw_button(self,text,y):
        rect=self.button_rect(text,y)
        pygame.draw.rect(self.screen,(80,80,80),rect.inflate(20,10))
        surf=self.font.render(text,True,(255,255,255))
        self.screen.blit(surf,rect)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)
        if self.state==MENU:
            title=self.big_font.render(TITLE,True,(255,255,255))
            self.screen.blit(title,(WINDOW_W//2-title.get_width()//2,100))
            y=WINDOW_H//2-100
            self.draw_button("Play",y)
            self.draw_button("Settings",y+60)
            self.draw_button("High Scores",y+120)
            self.draw_button("Credits",y+180)
            footer=self.font.render(f"{VERSION} | {EDITOR}",True,(200,200,200))
            self.screen.blit(footer,(10,WINDOW_H-30))

        elif self.state==GAME:
            for f in self.flowers: f.draw(self.screen)
            elapsed=time.time()-self.start_time
            time_left=max(0,GAME_DURATION_SEC-elapsed)
            score_surf=self.font.render(f"Score: {self.score}",True,HUD_COLOR)
            time_surf=self.font.render(f"Time: {int(time_left//60)}:{int(time_left%60):02d}",True,HUD_COLOR)
            self.screen.blit(score_surf,(10,10))
            self.screen.blit(time_surf,(WINDOW_W-100,10))

        elif self.state==GAME_OVER:
            over=self.big_font.render("Time!",True,(255,255,255))
            self.screen.blit(over,(WINDOW_W//2-over.get_width()//2,200))
            final=self.font.render(f"Final Score: {self.score}",True,(220,220,220))
            self.screen.blit(final,(WINDOW_W//2-final.get_width()//2,270))
            hs=self.font.render(f"High Score: {self.highscore}",True,(255,215,0))
            self.screen.blit(hs,(WINDOW_W//2-hs.get_width()//2,310))
            self.draw_button("Play Again",WINDOW_H//2+40)
            self.draw_button("Main Menu",WINDOW_H//2+100)

        elif self.state==SETTINGS:
            txt=self.big_font.render("How To",True,(255,255,255))
            self.screen.blit(txt,(WINDOW_W//2-txt.get_width()//2,150))
            c1=self.font.render("Click on the flowers to pop them and get a high score.",True,(220,220,220))
            self.draw_button("Back",WINDOW_H-80)

        elif self.state==SCORES:
            txt=self.big_font.render("High Scores",True,(255,255,255))
            self.screen.blit(txt,(WINDOW_W//2-txt.get_width()//2,150))
            hs=self.font.render(f"High Score: {self.highscore}",True,(255,215,0))
            self.screen.blit(hs,(WINDOW_W//2-hs.get_width()//2,250))
            self.draw_button("Back",WINDOW_H-80)

        elif self.state==CREDITS:
            txt=self.big_font.render("Credits",True,(255,255,255))
            self.screen.blit(txt,(WINDOW_W//2-txt.get_width()//2,150))
            c1=self.font.render("Made with Joy 🌸",True,(220,220,220))
            self.screen.blit(c1,(WINDOW_W//2-c1.get_width()//2,230))
            self.draw_button("Back",WINDOW_H-80)

        pygame.display.flip()

if __name__=="__main__":
    Game().run()
