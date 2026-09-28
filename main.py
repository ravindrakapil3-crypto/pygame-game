import pygame
import random
import math
import array
import json
import os
import sys
pygame.init()
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    pass

WIDTH, HEIGHT = 460, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird: TITAN EDITION")
clock = pygame.time.Clock()

def get_font(size, bold=True):  
    for name in ["Segoe UI", "Arial", "Helvetica", "Trebuchet MS", "DejaVu Sans"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

FONT_TINY = get_font(13, bold=False)
FONT_SMALL = get_font(17, bold=True)
FONT_MEDIUM = get_font(24, bold=True)
FONT_LARGE = get_font(38, bold=True)
FONT_TITLE = get_font(48, bold=True)

# ----------------- PROCEDURAL AUDIO SYNTHESIZER ---------------
class SoundManager:
    def __init__(self):
        self.enabled = True
        self.music_enabled = True
        self.sample_rate = 22050
        self.sounds = {}
        self.bgm_sound = None
        self.bgm_channel = None
        self.init_sounds()
        self.init_procedural_bgms()

    def generate_wave(self, duration, wave_func, volume=0.3):
        try:
            num_samples = int(duration * self.sample_rate)
            buf = array.array('h')
            for i in range(num_samples):
                t = i / self.sample_rate
                val = wave_func(t, duration)
                sample = int(32767 * volume * max(-1.0, min(1.0, val)))
                buf.append(sample)
                buf.append(sample)
            return pygame.mixer.Sound(buf)
        except Exception:
            return None

    def init_sounds(self):
        self.sounds['jump'] = self.generate_wave(0.12, lambda t, d: math.sin(2 * math.pi * (380 + (t / d) * 460) * t) * math.exp(-3.5 * t / d), volume=0.25)
        self.sounds['score'] = self.generate_wave(0.15, lambda t, d: math.sin(2 * math.pi * (784 + (100 if t > d * 0.5 else 0)) * t) * math.exp(-3.0 * t / d), volume=0.28)
        self.sounds['gem'] = self.generate_wave(0.20, lambda t, d: math.sin(2 * math.pi * [880, 1108, 1318, 1760][min(int(t / (d / 4)), 3)] * t) * (1.0 - t/d), volume=0.3)
        self.sounds['graze'] = self.generate_wave(0.15, lambda t, d: (math.sin(2 * math.pi * (900 - (t / d) * 300) * t) + (random.random() * 2 - 1) * 0.25) * math.sin(math.pi * (t / d)), volume=0.28)
        self.sounds['shoot'] = self.generate_wave(0.14, lambda t, d: math.sin(2 * math.pi * (850 - (t / d) * 550) * t) * math.exp(-4.0 * t / d), volume=0.32)
        self.sounds['explosion'] = self.generate_wave(0.35, lambda t, d: ((random.random() * 2 - 1) * 0.7 + math.sin(2 * math.pi * max(40, 160 - (t / d) * 120) * t) * 0.3) * math.exp(-3.5 * t / d), volume=0.45)
        self.sounds['dash'] = self.generate_wave(0.25, lambda t, d: math.sin(2 * math.pi * (300 + (t / d) * 700) * t) * (1.0 - t/d), volume=0.35)
        self.sounds['fanfare'] = self.generate_wave(0.35, lambda t, d: math.sin(2 * math.pi * [523, 659, 783, 1046][min(int(t / (d / 4)), 3)] * t) * (1.0 - t/d), volume=0.35)
        self.sounds['thunder'] = self.generate_wave(0.5, lambda t, d: (random.random() * 2 - 1) * math.exp(-2.0 * t / d) * 0.6, volume=0.5)

    def init_procedural_bgms(self):
        try:
            bpm = 114
            beat_sec = 60.0 / bpm
            total_sec = 4 * 4 * beat_sec
            num_samples = int(total_sec * self.sample_rate)
            buf = array.array('h')
            bass_chords = [[261.63, 329.63, 392.00], [196.00, 246.94, 293.66], [220.00, 261.63, 329.63], [174.61, 220.00, 261.63]]
            lead_melody = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 392.00, 440.00, 523.25, 659.25, 587.33, 523.25, 440.00, 392.00, 523.25]

            for i in range(num_samples):
                t = i / self.sample_rate
                bar = int(t / (4 * beat_sec)) % 4
                melody_idx = int(t / (beat_sec * 0.5)) % len(lead_melody)
                chord = bass_chords[bar]
                arp_idx = int(t * 8) % len(chord)
                bass_val = math.sin(2 * math.pi * chord[arp_idx] * 0.5 * t) * math.exp(-4.0 * ((t * 8) % 1.0)) * 0.11
                lead_val = math.sin(2 * math.pi * lead_melody[melody_idx] * t) * math.exp(-3.0 * ((t * 2) % 1.0)) * 0.08
                tot = max(-1.0, min(1.0, bass_val + lead_val))
                sample = int(32767 * tot)
                buf.append(sample); buf.append(sample)
            self.bgm_sound = pygame.mixer.Sound(buf)
        except Exception:
            self.bgm_sound = None

    def play(self, key):
        if self.enabled and key in self.sounds and self.sounds[key]:
            self.sounds[key].play()

    def start_music(self):
        if self.music_enabled and self.bgm_sound:
            try:
                self.bgm_channel = self.bgm_sound.play(loops=-1)
                if self.bgm_channel: self.bgm_channel.set_volume(0.35)
            except Exception:
                pass

audio = SoundManager()
audio.start_music()

# ----------------- CONSTANTS & SKINS -----------------
STATE_START, STATE_PLAYING, STATE_SHOP, STATE_PAUSED, STATE_GAMEOVER = 0, 1, 2, 3, 4
GROUND_HEIGHT = 90
GROUND_Y = HEIGHT - GROUND_HEIGHT

WEATHER_SUNNY, WEATHER_RAIN, WEATHER_SNOW, WEATHER_SAKURA = 0, 1, 2, 3

SKINS = [
    {"name": "Sunny Gold", "body": (250, 195, 35), "outline": (210, 135, 15), "wing": (235, 155, 20), "glow": (255, 230, 100), "beak": (245, 85, 20)},
    {"name": "Cyber Neon", "body": (30, 230, 255), "outline": (10, 120, 190), "wing": (255, 50, 160), "glow": (0, 255, 255), "beak": (255, 240, 50)},
    {"name": "Phoenix Flame", "body": (255, 70, 30), "outline": (180, 20, 10), "wing": (255, 180, 20), "glow": (255, 100, 30), "beak": (255, 220, 50)},
    {"name": "Midnight Shadow", "body": (90, 70, 150), "outline": (40, 30, 80), "wing": (160, 110, 240), "glow": (180, 120, 255), "beak": (255, 120, 180)},
]

HATS = [
    {"name": "No Hat"}, {"name": "Crown"}, {"name": "Viking"}, {"name": "Wizard"}, {"name": "Cyber Visor"}
]

SAVE_PATH = os.path.join(os.path.dirname(__file__), "flappy_titan_save.json")
def load_save():
    default = {"high_score": 0, "total_gems": 0, "selected_skin": 0, "selected_hat": 0, "dash_lvl": 1, "plasma_lvl": 1, "magnet_lvl": 1, "achievements": []}
    try:
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, "r") as f: default.update(json.load(f))
    except Exception: pass
    return default

def save_data(data):
    try:
        with open(SAVE_PATH, "w") as f: json.dump(data, f)
    except Exception: pass

SAVE_DATA = load_save()

# ----------------- WEATHER & ENVIRONMENT -----------------
class WeatherEngine:
    def __init__(self):
        self.current_weather = WEATHER_SUNNY
        self.weather_timer = 20.0
        self.particles = []
        self.lightning_flash = 0

    def update(self, dt):
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.current_weather = random.choice([WEATHER_SUNNY, WEATHER_RAIN, WEATHER_SNOW, WEATHER_SAKURA])
            self.weather_timer = random.uniform(25.0, 45.0)
            self.particles.clear()

        if self.current_weather == WEATHER_RAIN:
            if random.random() < 0.6:
                self.particles.append({"x": random.randint(-50, WIDTH), "y": -10, "vx": 3.5, "vy": random.uniform(12, 17), "type": "rain", "life": 1.2})
            if random.random() < 0.005:
                self.lightning_flash = 220
                audio.play('thunder')
        elif self.current_weather == WEATHER_SNOW:
            if random.random() < 0.4:
                self.particles.append({"x": random.randint(0, WIDTH), "y": -10, "vx": random.uniform(-0.8, 0.8), "vy": random.uniform(1.5, 3.2), "type": "snow", "life": 4.5, "phase": random.uniform(0, 6.28)})
        elif self.current_weather == WEATHER_SAKURA:
            if random.random() < 0.35:
                self.particles.append({"x": random.randint(-20, WIDTH), "y": -10, "vx": random.uniform(1.2, 2.5), "vy": random.uniform(2.0, 4.0), "type": "sakura", "life": 3.8, "phase": random.uniform(0, 6.28)})

        for p in self.particles:
            if p["type"] == "snow":
                p["phase"] += dt * 3
                p["x"] += p["vx"] + math.sin(p["phase"]) * 0.8
                p["y"] += p["vy"]
            elif p["type"] == "sakura":
                p["phase"] += dt * 4
                p["x"] += p["vx"] + math.sin(p["phase"]) * 1.2
                p["y"] += p["vy"]
            else:
                p["x"] += p["vx"]; p["y"] += p["vy"]
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0 and p["y"] < GROUND_Y]

        if self.lightning_flash > 0:
            self.lightning_flash = max(0, self.lightning_flash - int(800 * dt))

    def draw(self, surf):
        for p in self.particles:
            if p["type"] == "rain":
                pygame.draw.line(surf, (180, 220, 255, 180), (p["x"], p["y"]), (p["x"] + 4, p["y"] + 12), 2)
            elif p["type"] == "snow":
                pygame.draw.circle(surf, (255, 255, 255, 220), (int(p["x"]), int(p["y"])), 3)
            elif p["type"] == "sakura":
                s = pygame.Surface((8, 6), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (255, 180, 210, 230), (0, 0, 8, 6))
                surf.blit(s, (int(p["x"]), int(p["y"])))

        if self.lightning_flash > 0:
            f_surf = pygame.Surface((WIDTH, HEIGHT))
            f_surf.fill((240, 245, 255)); f_surf.set_alpha(self.lightning_flash)
            surf.blit(f_surf, (0, 0))

class Environment:
    def __init__(self):
        self.time_of_day = 0.0
        self.cycle_speed = 0.003
        self.clouds = [[random.randint(0, WIDTH), random.randint(30, 220), random.uniform(0.3, 0.9), random.randint(28, 50)] for _ in range(6)]
        self.stars = [[random.randint(0, WIDTH), random.randint(0, GROUND_Y - 50), random.uniform(0.5, 2.0), random.uniform(0, math.pi*2)] for _ in range(35)]
        self.mountains = [(0, HEIGHT - 180)] + [(x, random.randint(HEIGHT - 280, HEIGHT - 200)) for x in range(40, WIDTH + 70, 60)] + [(WIDTH + 60, HEIGHT), (0, HEIGHT)]
        self.city = [{"x": x, "w": random.randint(28, 55), "h": random.randint(90, 180)} for x in range(0, WIDTH + 80, 50)]

    def update(self, dt, speed_scale=1.0):
        self.time_of_day = (self.time_of_day + self.cycle_speed * dt) % 1.0
        for c in self.clouds:
            c[0] -= c[2] * speed_scale
            if c[0] < -100: c[0], c[1] = WIDTH + random.randint(20, 80), random.randint(30, 220)

    def draw(self, surf):
        t = self.time_of_day
        if t < 0.25: top_c, bot_c, orb_c, is_night = (95, 175, 245), (185, 230, 255), (255, 245, 170), False
        elif t < 0.45:
            prog = (t - 0.25) / 0.20
            top_c = (int(95 - prog * 55), int(175 - prog * 105), int(245 - prog * 135))
            bot_c = (int(185 + prog * 60), int(230 - prog * 110), int(255 - prog * 175))
            orb_c, is_night = (255, 140, 60), False
        elif t < 0.75: top_c, bot_c, orb_c, is_night = (15, 18, 42), (35, 38, 75), (240, 245, 255), True
        else:
            prog = (t - 0.75) / 0.25
            top_c = (int(15 + prog * 80), int(18 + prog * 157), int(42 + prog * 203))
            bot_c = (int(35 + prog * 150), int(38 + prog * 192), int(75 + prog * 180))
            orb_c, is_night = (255, 220, 130), False

        for y in range(0, GROUND_Y, 4):
            frac = y / float(GROUND_Y)
            r = int(top_c[0] + (bot_c[0] - top_c[0]) * frac)
            g = int(top_c[1] + (bot_c[1] - top_c[1]) * frac)
            b = int(top_c[2] + (bot_c[2] - top_c[2]) * frac)
            pygame.draw.rect(surf, (r, g, b), (0, y, WIDTH, 4))

        orb_y = 90 + int(math.sin(self.time_of_day * math.pi * 2) * 40)
        orb_x = int(WIDTH * 0.78)
        glow_s = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (*orb_c, 40), (60, 60), 55)
        pygame.draw.circle(glow_s, (*orb_c, 90), (60, 60), 38)
        surf.blit(glow_s, (orb_x - 60, orb_y - 60))
        pygame.draw.circle(surf, orb_c, (orb_x, orb_y), 24)

        if is_night:
            pygame.draw.circle(surf, (200, 210, 235), (orb_x - 6, orb_y - 4), 6)
            for sx, sy, radius, phase in self.stars:
                twinkle = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005 + phase)
                s_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (255, 255, 255, int(220 * twinkle)), (4, 4), int(radius * twinkle) + 1)
                surf.blit(s_surf, (sx - 4, sy - 4))

        pygame.draw.polygon(surf, (45, 60, 85) if is_night else (140, 160, 185), self.mountains)
        b_color = (25, 30, 50) if is_night else (100, 125, 145)
        win_color = (255, 235, 140) if is_night else (200, 230, 245)
        for b in self.city:
            by = GROUND_Y - b["h"]
            pygame.draw.rect(surf, b_color, (b["x"], by, b["w"], b["h"]))
            for wy in range(by + 12, GROUND_Y - 15, 22):
                if wy % 3 == 0 or is_night: pygame.draw.rect(surf, win_color, (b["x"] + 6, wy, 6, 8))

        c_color = (70, 75, 110, 180) if is_night else (255, 255, 255, 220)
        for cx, cy, _, size in self.clouds:
            cloud_surf = pygame.Surface((size * 3, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(cloud_surf, c_color, (int(size), int(size)), int(size * 0.65))
            pygame.draw.circle(cloud_surf, c_color, (int(size * 1.5), int(size * 0.8)), int(size * 0.55))
            pygame.draw.circle(cloud_surf, c_color, (int(size * 0.6), int(size * 0.9)), int(size * 0.5))
            pygame.draw.rect(cloud_surf, c_color, (int(size * 0.4), int(size * 0.7), int(size * 1.4), int(size * 0.5)))
            surf.blit(cloud_surf, (int(cx), int(cy)))

# ----------------- PARTICLES & TOASTS -----------------
class ParticleSystem:
    def __init__(self):
        self.particles, self.float_texts, self.achieve_toast = [], [], None

    def emit_jump_dust(self, x, y, color):
        for _ in range(6):
            self.particles.append({"x": x - 10, "y": y + 10, "vx": random.uniform(-2.8, -0.6), "vy": random.uniform(0.4, 2.5), "life": 1.0, "decay": 0.06, "size": random.randint(3, 6), "color": color, "type": "circle"})

    def emit_sparkles(self, x, y, color, count=14):
        for _ in range(count):
            ang, spd = random.uniform(0, math.pi*2), random.uniform(1.5, 5.5)
            self.particles.append({"x": x, "y": y, "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd, "life": 1.0, "decay": 0.04, "size": random.randint(2, 5), "color": color, "type": "spark"})

    def emit_explosion(self, x, y, count=25):
        for _ in range(count):
            ang, spd = random.uniform(0, 6.28), random.uniform(2, 7)
            col = random.choice([(255, 80, 20), (255, 200, 40), (255, 255, 100)])
            self.particles.append({"x": x, "y": y, "vx": math.cos(ang)*spd, "vy": math.sin(ang)*spd, "life": 1.0, "decay": 0.035, "size": random.randint(4, 9), "color": col, "type": "circle"})

    def emit_confetti(self, count=45):
        colors = [(255, 80, 80), (80, 220, 255), (255, 230, 50), (120, 255, 100), (255, 120, 230)]
        for _ in range(count):
            self.particles.append({"x": random.randint(20, WIDTH - 20), "y": random.randint(50, HEIGHT // 2), "vx": random.uniform(-3.0, 3.0), "vy": random.uniform(-6.0, -1.0), "life": 1.0, "decay": 0.02, "size": random.randint(4, 7), "color": random.choice(colors), "type": "confetti"})

    def add_floating_text(self, text, x, y, color=(255, 255, 255), scale=1.0):
        self.float_texts.append({"text": text, "x": x, "y": y, "vy": -1.8, "life": 1.0, "color": color, "scale": scale})

    def show_achievement(self, title, desc):
        audio.play('fanfare')
        self.achieve_toast = {"title": title, "desc": desc, "timer": 4.0, "y": -80}

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]
            if p["type"] == "confetti": p["vy"] += 0.18
            p["life"] -= p["decay"]
        self.particles = [p for p in self.particles if p["life"] > 0]

        for ft in self.float_texts:
            ft["y"] += ft["vy"]; ft["life"] -= 0.025
        self.float_texts = [ft for ft in self.float_texts if ft["life"] > 0]

        if self.achieve_toast:
            self.achieve_toast["timer"] -= dt
            if self.achieve_toast["timer"] > 0.5: self.achieve_toast["y"] += (20 - self.achieve_toast["y"]) * 0.15
            else: self.achieve_toast["y"] -= 6
            if self.achieve_toast["timer"] <= 0: self.achieve_toast = None

    def draw(self, surf):
        for p in self.particles:
            alpha = int(p["life"] * 255); rad = max(1, int(p["size"] * p["life"]))
            c = p["color"]
            if p["type"] == "spark":
                s = pygame.Surface((rad * 4, rad * 4), pygame.SRCALPHA)
                pygame.draw.polygon(s, (*c, alpha), [(rad*2, 0), (rad*4, rad*2), (rad*2, rad*4), (0, rad*2)])
                surf.blit(s, (int(p["x"]) - rad*2, int(p["y"]) - rad*2))
            elif p["type"] == "confetti":
                s = pygame.Surface((rad * 2, rad), pygame.SRCALPHA); s.fill((*c, alpha))
                surf.blit(s, (int(p["x"]), int(p["y"])))
            else:
                s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, alpha), (rad, rad), rad)
                surf.blit(s, (int(p["x"]) - rad, int(p["y"]) - rad))

        for ft in self.float_texts:
            font = FONT_MEDIUM if ft["scale"] > 1.1 else FONT_SMALL
            txt = font.render(ft["text"], True, ft["color"])
            out = font.render(ft["text"], True, (20, 20, 20))
            w, h = txt.get_width() + 6, txt.get_height() + 6
            t_s = pygame.Surface((w, h), pygame.SRCALPHA)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]: t_s.blit(out, (dx + 3, dy + 3))
            t_s.blit(txt, (3, 3)); t_s.set_alpha(int(ft["life"] * 255))
            surf.blit(t_s, (int(ft["x"]) - w // 2, int(ft["y"]) - h // 2))

        if self.achieve_toast:
            ty = int(self.achieve_toast["y"])
            t_rect = pygame.Rect(WIDTH // 2 - 160, ty, 320, 60)
            pygame.draw.rect(surf, (25, 30, 45, 230), t_rect, border_radius=12)
            pygame.draw.rect(surf, (255, 215, 60), t_rect, 2, border_radius=12)
            pygame.draw.circle(surf, (255, 215, 60), (WIDTH // 2 - 130, ty + 30), 16)
            pygame.draw.circle(surf, (255, 255, 255), (WIDTH // 2 - 130, ty + 30), 16, 2)
            t1 = FONT_SMALL.render(self.achieve_toast["title"], True, (255, 225, 80))
            t2 = FONT_TINY.render(self.achieve_toast["desc"], True, (230, 240, 255))
            surf.blit(t1, (WIDTH // 2 - 105, ty + 10))
            surf.blit(t2, (WIDTH // 2 - 105, ty + 32))

# ----------------- MISSILES & BOSS -----------------
class PlasmaMissile:
    def __init__(self, x, y):
        self.x, self.y, self.vx, self.radius, self.life = x, y, 9.0, 6, 1.5

    def update(self, dt):
        self.x += self.vx; self.life -= dt

    def draw(self, surf):
        glow_s = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (0, 255, 255, 100), (14, 14), 13)
        surf.blit(glow_s, (int(self.x) - 14, int(self.y) - 14))
        pygame.draw.circle(surf, (150, 245, 255), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, (255, 255, 255), (int(self.x), int(self.y)), 3)

class CyberBoss:
    def __init__(self):
        self.active, self.x, self.y = False, WIDTH + 80, 250
        self.max_hp, self.hp, self.phase, self.shoot_timer = 30, 30, 0, 2.0
        self.fireballs, self.wing_cycle = [], 0

    def spawn(self, score):
        self.active, self.x, self.y = True, WIDTH + 60, 220
        self.max_hp = 25 + (score // 10) * 10
        self.hp, self.shoot_timer = self.max_hp, 1.8
        self.fireballs.clear()

    def update(self, dt, bird_y, particles):
        if not self.active: return
        self.wing_cycle += dt * 8; self.phase += dt * 2.2
        self.x += ((WIDTH - 90) - self.x) * 0.05
        self.y = 240 + math.sin(self.phase) * 110

        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1.4, 2.2)
            angle = math.atan2(bird_y - self.y, 70 - self.x)
            self.fireballs.append({"x": self.x - 20, "y": self.y, "vx": math.cos(angle) * 4.5, "vy": math.sin(angle) * 4.5, "rad": 8})
            particles.emit_sparkles(self.x - 20, self.y, (255, 60, 40), 8)

        for fb in self.fireballs:
            fb["x"] += fb["vx"]; fb["y"] += fb["vy"]
        self.fireballs = [fb for fb in self.fireballs if fb["x"] > -30 and 0 < fb["y"] < GROUND_Y]

    def draw(self, surf):
        if not self.active: return
        boss_s = pygame.Surface((80, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(boss_s, (45, 25, 65), (10, 10, 60, 40))
        pygame.draw.ellipse(boss_s, (255, 40, 80), (12, 12, 56, 36), 3)
        wing_y = 15 + int(math.sin(self.wing_cycle) * 10)
        pygame.draw.polygon(boss_s, (180, 30, 70), [(25, 25), (5, wing_y), (35, wing_y + 12)])
        pygame.draw.circle(boss_s, (255, 30, 30), (22, 26), 6)
        pygame.draw.circle(boss_s, (255, 255, 255), (20, 25), 2)
        pygame.draw.polygon(boss_s, (220, 200, 50), [(20, 30), (0, 35), (20, 40)])
        surf.blit(boss_s, (int(self.x) - 40, int(self.y) - 30))

        bar_w, bar_h, bar_x, bar_y = 260, 16, WIDTH // 2 - 130, 48
        pygame.draw.rect(surf, (30, 20, 40), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), border_radius=6)
        fill_w = int((self.hp / self.max_hp) * bar_w)
        pygame.draw.rect(surf, (240, 45, 65), (bar_x, bar_y, fill_w, bar_h), border_radius=4)
        pygame.draw.rect(surf, (255, 215, 60), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), 2, border_radius=6)
        b_txt = FONT_TINY.render("★ MECHA DRAGON BOSS ★", True, (255, 225, 100))
        surf.blit(b_txt, (WIDTH // 2 - b_txt.get_width() // 2, bar_y - 18))

        for fb in self.fireballs:
            glow_s = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (255, 50, 30, 110), (16, 16), 14)
            surf.blit(glow_s, (int(fb["x"]) - 16, int(fb["y"]) - 16))
            pygame.draw.circle(surf, (255, 180, 40), (int(fb["x"]), int(fb["y"])), fb["rad"])
            pygame.draw.circle(surf, (255, 255, 255), (int(fb["x"]), int(fb["y"])), 3)

# ----------------- BIRD WITH HATS & DASH -----------------
class Bird:
    def __init__(self, x=90, y=280):
        self.x, self.y, self.vel, self.angle = x, y, 0, 0
        self.wing_phase, self.squash_x, self.squash_y = 0, 1.0, 1.0
        self.skin_idx = SAVE_DATA.get("selected_skin", 0)
        self.hat_idx = SAVE_DATA.get("selected_hat", 0)
        self.has_shield, self.dash_cooldown, self.is_dashing, self.dash_duration = False, 0.0, False, 0.0
        self.trail_history = []

    def reset(self, y=280):
        self.x, self.y, self.vel, self.angle = 90, y, 0, 0
        self.wing_phase, self.squash_x, self.squash_y = 0, 1.0, 1.0
        self.has_shield, self.is_dashing, self.dash_duration, self.dash_cooldown = False, False, 0, 0
        self.trail_history.clear()

    def jump(self, particles):
        if self.is_dashing: return
        self.vel = -8.8; self.squash_x, self.squash_y = 0.8, 1.25
        audio.play('jump')
        particles.emit_jump_dust(self.x, self.y, SKINS[self.skin_idx]["glow"])

    def trigger_dash(self, particles):
        max_cd = max(2.5, 5.0 - SAVE_DATA.get("dash_lvl", 1) * 0.6)
        if self.dash_cooldown <= 0:
            self.is_dashing, self.dash_duration, self.dash_cooldown, self.vel = True, 0.45, max_cd, 0
            audio.play('dash')
            particles.emit_sparkles(self.x, self.y, (80, 240, 255), 20)
            particles.add_floating_text("SONIC DASH!", self.x, self.y - 25, (80, 240, 255), 1.2)

    def update(self, dt):
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        if self.is_dashing:
            self.dash_duration -= dt; self.vel = 0
            if self.dash_duration <= 0: self.is_dashing = False
        else:
            self.vel += 0.46; self.y += self.vel

        self.wing_phase += 0.4 if self.is_dashing else 0.35
        self.squash_x += (1.0 - self.squash_x) * 0.18
        self.squash_y += (1.0 - self.squash_y) * 0.18
        target_angle = 0 if self.is_dashing else max(-75, min(35, -self.vel * 4.2))
        self.angle += (target_angle - self.angle) * 0.22

        self.trail_history.append((self.x, self.y, self.angle))
        if len(self.trail_history) > (10 if self.is_dashing else 6): self.trail_history.pop(0)

    def draw_hat(self, surf, bx, by):
        hat = HATS[self.hat_idx]["name"]
        if hat == "Crown":
            pts = [(bx - 10, by - 12), (bx - 12, by - 22), (bx - 5, by - 16), (bx, by - 25), (bx + 5, by - 16), (bx + 12, by - 22), (bx + 10, by - 12)]
            pygame.draw.polygon(surf, (255, 215, 0), pts)
            pygame.draw.polygon(surf, (200, 150, 0), pts, 2)
            pygame.draw.circle(surf, (255, 50, 50), (bx, by - 19), 2)
        elif hat == "Viking":
            pygame.draw.ellipse(surf, (150, 150, 160), (bx - 12, by - 18, 24, 10))
            pygame.draw.polygon(surf, (245, 240, 220), [(bx - 10, by - 14), (bx - 20, by - 24), (bx - 7, by - 18)])
            pygame.draw.polygon(surf, (245, 240, 220), [(bx + 10, by - 14), (bx + 20, by - 24), (bx + 7, by - 18)])
        elif hat == "Wizard":
            pygame.draw.polygon(surf, (60, 40, 140), [(bx - 14, by - 12), (bx, by - 32), (bx + 12, by - 12)])
            pygame.draw.ellipse(surf, (90, 60, 180), (bx - 16, by - 14, 32, 8))
            pygame.draw.circle(surf, (255, 220, 60), (bx, by - 32), 3)
        elif hat == "Cyber Visor":
            pygame.draw.rect(surf, (0, 255, 255), (bx + 6, by - 4, 18, 6), border_radius=2)
            pygame.draw.line(surf, (255, 255, 255), (bx + 8, by - 2), (bx + 20, by - 2), 1)

    def draw(self, surf):
        skin = SKINS[self.skin_idx]
        for i, (tx, ty, tang) in enumerate(self.trail_history):
            alpha = int((i / len(self.trail_history)) * (180 if self.is_dashing else 70))
            if alpha > 10:
                t_surf = pygame.Surface((48, 38), pygame.SRCALPHA)
                col = (80, 240, 255) if self.is_dashing else skin["glow"]
                pygame.draw.ellipse(t_surf, (*col, alpha), (6, 6, 32, 24))
                rot_t = pygame.transform.rotate(t_surf, tang)
                surf.blit(rot_t, rot_t.get_rect(center=(tx, ty)).topleft)

        bird_surf = pygame.Surface((48, 38), pygame.SRCALPHA)
        pygame.draw.ellipse(bird_surf, skin["glow"], (6, 5, 34, 26))
        pygame.draw.ellipse(bird_surf, skin["body"], (7, 6, 32, 24))
        pygame.draw.ellipse(bird_surf, skin["outline"], (7, 6, 32, 24), 2)
        pygame.draw.ellipse(bird_surf, (255, 255, 255, 140), (9, 14, 20, 13))

        pygame.draw.circle(bird_surf, (255, 255, 255), (29, 13), 7)
        pygame.draw.circle(bird_surf, (20, 20, 30), (31, 13), 3.5)
        pygame.draw.circle(bird_surf, (255, 255, 255), (32, 11), 1.5)

        pygame.draw.polygon(bird_surf, skin["beak"], [(31, 15), (43, 20), (31, 25)])
        pygame.draw.polygon(bird_surf, (160, 30, 10), [(31, 15), (43, 20), (31, 25)], 1)

        wing_y = 13 + int(math.sin(self.wing_phase) * 5)
        pygame.draw.ellipse(bird_surf, skin["wing"], (4, wing_y, 18, 12))
        pygame.draw.ellipse(bird_surf, skin["outline"], (4, wing_y, 18, 12), 1)

        scaled = pygame.transform.smoothscale(bird_surf, (max(10, int(48 * self.squash_x)), max(10, int(38 * self.squash_y))))
        rotated = pygame.transform.rotate(scaled, self.angle)
        surf.blit(rotated, rotated.get_rect(center=(self.x, self.y)).topleft)
        self.draw_hat(surf, self.x, self.y)

        if self.has_shield:
            shield_surf = pygame.Surface((108, 108), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (80, 220, 255, 60), (54, 54), 50)
            pygame.draw.circle(shield_surf, (150, 245, 255, 180), (54, 54), 50, 3)
            surf.blit(shield_surf, (int(self.x) - 54, int(self.y) - 54))

# ----------------- PIPES -----------------
class PipeManager:
    def __init__(self):
        self.pipes, self.powerups = [], []
        self.pipe_width, self.base_speed, self.gap_size = 62, 2.9, 145

    def reset(self):
        self.pipes.clear(); self.powerups.clear()

    def spawn_pipe(self, score):
        gap = max(120, self.gap_size - min(25, score // 4))
        gap_center = random.randint(140, GROUND_Y - 140)
        is_moving = score > 15 and random.random() < 0.35

        self.pipes.append({
            "x": WIDTH + 20, "gap_y": gap_center, "base_gap_y": gap_center,
            "gap_size": gap, "is_moving": is_moving, "move_phase": random.uniform(0, math.pi*2),
            "move_amp": random.randint(25, 45), "hp": 3, "scored": False, "grazed": False
        })

        if random.random() < 0.45:
            p_type = "gem" if random.random() >= 0.25 else random.choice(["shield", "slow"])
            self.powerups.append({"x": WIDTH + 20 + self.pipe_width // 2, "y": gap_center, "type": p_type, "phase": random.uniform(0, math.pi*2), "collected": False})

    def update(self, dt, score, speed_scale=1.0):
        current_speed = self.base_speed * speed_scale
        if not self.pipes or self.pipes[-1]["x"] < WIDTH - 195:
            self.spawn_pipe(score)

        for p in self.pipes:
            p["x"] -= current_speed
            if p["is_moving"]:
                p["move_phase"] += dt * 2.5
                p["gap_y"] = p["base_gap_y"] + int(math.sin(p["move_phase"]) * p["move_amp"])

        for pu in self.powerups:
            pu["x"] -= current_speed
            pu["phase"] += dt * 3.5

        self.pipes = [p for p in self.pipes if p["x"] > -self.pipe_width - 20 and p["hp"] > 0]
        self.powerups = [pu for pu in self.powerups if pu["x"] > -40 and not pu["collected"]]

    def draw(self, surf):
        for p in self.pipes:
            top_h = p["gap_y"] - (p["gap_size"] // 2)
            bot_y = p["gap_y"] + (p["gap_size"] // 2)
            for (py, ph, is_t) in [(0, top_h, True), (bot_y, GROUND_Y - bot_y, False)]:
                if ph <= 0: continue
                pygame.draw.rect(surf, (70, 185, 45), (p["x"], py, self.pipe_width, ph))
                pygame.draw.rect(surf, (135, 230, 95), (p["x"] + 5, py, 7, ph))
                pygame.draw.rect(surf, (35, 120, 25), (p["x"] + self.pipe_width - 12, py, 9, ph))
                pygame.draw.rect(surf, (15, 60, 12), (p["x"], py, self.pipe_width, ph), 2)
                cap_h, cap_w = 26, self.pipe_width + 12
                cap_x = p["x"] - 6
                cap_y = py + ph - cap_h if is_t else py
                pygame.draw.rect(surf, (70, 185, 45), (cap_x, cap_y, cap_w, cap_h), border_radius=4)
                pygame.draw.rect(surf, (135, 230, 95), (cap_x + 5, cap_y, 7, cap_h))
                pygame.draw.rect(surf, (15, 60, 12), (cap_x, cap_y, cap_w, cap_h), 2, border_radius=4)

        for pu in self.powerups:
            float_y = pu["y"] + math.sin(pu["phase"]) * 6
            px, py = int(pu["x"]), int(float_y)
            if pu["type"] == "gem":
                glow_s = pygame.Surface((36, 36), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (255, 220, 60, 90), (18, 18), 16)
                surf.blit(glow_s, (px - 18, py - 18))
                pts = [(px, py - 12), (px + 9, py), (px, py + 12), (px - 9, py)]
                pygame.draw.polygon(surf, (255, 235, 70), pts)
                pygame.draw.polygon(surf, (255, 170, 20), pts, 2)
                pygame.draw.circle(surf, (255, 255, 255), (px, py), 3)
            elif pu["type"] == "shield":
                glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (60, 220, 255, 100), (20, 20), 18)
                surf.blit(glow_s, (px - 20, py - 20))
                pygame.draw.circle(surf, (40, 180, 255), (px, py), 12)
                pygame.draw.circle(surf, (255, 255, 255), (px, py), 12, 2)
                pygame.draw.polygon(surf, (255, 255, 255), [(px - 5, py - 5), (px + 5, py - 5), (px, py + 6)])
            elif pu["type"] == "slow":
                glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
                pygame.draw.circle(glow_s, (255, 100, 220, 100), (20, 20), 18)
                surf.blit(glow_s, (px - 20, py - 20))
                pygame.draw.circle(surf, (220, 60, 190), (px, py), 12)
                pygame.draw.circle(surf, (255, 255, 255), (px, py), 12, 2)
                pygame.draw.polygon(surf, (255, 255, 255), [(px - 5, py - 6), (px + 5, py - 6), (px - 5, py + 6), (px + 5, py + 6)])

# ----------------- GAME ENGINE -----------------
class TitanFlappyGame:
    def __init__(self):
        self.state = STATE_START
        self.env = Environment()
        self.weather = WeatherEngine()
        self.particles = ParticleSystem()
        self.bird = Bird()
        self.pipe_mgr = PipeManager()
        self.boss = CyberBoss()
        self.missiles = []

        self.score = 0
        self.high_score = SAVE_DATA.get("high_score", 0)
        self.gems_collected = SAVE_DATA.get("total_gems", 0)
        self.session_gems = 0
        self.combo_count = 0
        self.slow_mo_timer = 0.0
        self.screen_shake = 0
        self.flash_alpha = 0
        self.ground_offset = 0

    def check_achievement(self, key, title, desc):
        if key not in SAVE_DATA["achievements"]:
            SAVE_DATA["achievements"].append(key)
            self.particles.show_achievement(title, desc)
            save_data(SAVE_DATA)

    def start_game(self):
        self.state = STATE_PLAYING
        self.score = 0
        self.session_gems = 0
        self.combo_count = 0
        self.slow_mo_timer = 0
        self.missiles.clear()
        self.bird.reset()
        self.pipe_mgr.reset()
        self.boss.active = False
        self.bird.jump(self.particles)
        self.check_achievement("first_flight", "First Flight", "Started a new voyage!")

    def shoot_missile(self):
        if self.state == STATE_PLAYING:
            self.missiles.append(PlasmaMissile(self.bird.x + 20, self.bird.y))
            audio.play('shoot')
            self.particles.emit_sparkles(self.bird.x + 20, self.bird.y, (0, 255, 255), 6)

    def trigger_game_over(self):
        self.state = STATE_GAMEOVER
        self.screen_shake = 16
        self.flash_alpha = 220
        audio.play('explosion')

        if self.score > self.high_score:
            self.high_score = self.score
            self.particles.emit_confetti(50)

        if self.score >= 50: self.check_achievement("pro_flyer", "Sky Ace", "Reached Score 50!")
        if self.gems_collected >= 100: self.check_achievement("gem_king", "Treasure Baron", "Collected 100+ Star Gems!")

        SAVE_DATA["high_score"] = self.high_score
        SAVE_DATA["total_gems"] = self.gems_collected
        save_data(SAVE_DATA)

    def handle_collisions(self, dt):
        bird_box = pygame.Rect(self.bird.x - 13, self.bird.y - 13, 26, 26)
        graze_box = pygame.Rect(self.bird.x - 22, self.bird.y - 22, 44, 44)

        if self.bird.y + 14 >= GROUND_Y:
            self.bird.y = GROUND_Y - 14
            self.trigger_game_over()
            return
        if self.bird.y - 14 <= 0:
            self.bird.y = 14
            self.bird.vel = 0

        if self.boss.active:
            boss_box = pygame.Rect(self.boss.x - 30, self.boss.y - 20, 60, 40)
            if not self.bird.is_dashing and bird_box.colliderect(boss_box):
                self.trigger_game_over()
                return

            for fb in self.boss.fireballs:
                if not self.bird.is_dashing and bird_box.colliderect(pygame.Rect(fb["x"] - 6, fb["y"] - 6, 12, 12)):
                    if self.bird.has_shield:
                        self.bird.has_shield = False
                        audio.play('explosion')
                        self.particles.emit_sparkles(self.bird.x, self.bird.y, (80, 220, 255), 18)
                    else:
                        self.trigger_game_over()
                        return

            for m in self.missiles:
                if boss_box.colliderect(pygame.Rect(m.x - 6, m.y - 6, 12, 12)):
                    m.life = 0
                    dmg = SAVE_DATA.get("plasma_lvl", 1) * 2
                    self.boss.hp -= dmg
                    audio.play('explosion')
                    self.particles.emit_sparkles(m.x, m.y, (255, 80, 30), 12)
                    self.particles.add_floating_text(f"-{dmg}", m.x, m.y - 15, (255, 100, 50), 1.1)

                    if self.boss.hp <= 0:
                        self.boss.active = False
                        self.score += 25
                        self.gems_collected += 15
                        self.session_gems += 15
                        self.check_achievement("boss_slayer", "Titan Slayer", "Defeated the Mecha-Dragon Boss!")
                        self.particles.emit_explosion(self.boss.x, self.boss.y, 40)
                        self.particles.emit_confetti(60)
                        self.particles.add_floating_text("BOSS DEFEATED! +25", WIDTH//2, HEIGHT//3, (255, 215, 0), 1.6)

        for p in self.pipe_mgr.pipes:
            top_h = p["gap_y"] - (p["gap_size"] // 2)
            bot_y = p["gap_y"] + (p["gap_size"] // 2)
            top_rect = pygame.Rect(p["x"], 0, self.pipe_mgr.pipe_width, top_h)
            bot_rect = pygame.Rect(p["x"], bot_y, self.pipe_mgr.pipe_width, GROUND_Y - bot_y)

            for m in self.missiles:
                if top_rect.colliderect(pygame.Rect(m.x, m.y, 10, 10)) or bot_rect.colliderect(pygame.Rect(m.x, m.y, 10, 10)):
                    m.life = 0
                    p["hp"] -= 1
                    audio.play('explosion')
                    self.particles.emit_sparkles(m.x, m.y, (140, 240, 80), 10)
                    if p["hp"] <= 0:
                        self.score += 2
                        self.particles.emit_explosion(p["x"] + 30, p["gap_y"], 20)
                        self.particles.add_floating_text("PIPE DESTROYED!", p["x"] + 30, p["gap_y"], (255, 200, 60), 1.2)

            if not self.bird.is_dashing and (bird_box.colliderect(top_rect) or bird_box.colliderect(bot_rect)):
                if self.bird.has_shield:
                    self.bird.has_shield = False
                    self.screen_shake = 8
                    audio.play('explosion')
                    self.particles.emit_sparkles(self.bird.x, self.bird.y, (80, 220, 255), 20)
                    self.particles.add_floating_text("SHIELD BREAK!", self.bird.x, self.bird.y - 25, (80, 220, 255), 1.2)
                    self.bird.y = p["gap_y"]; self.bird.vel = -3
                else:
                    self.trigger_game_over()
                    return

            elif not p["grazed"] and (graze_box.colliderect(top_rect) or graze_box.colliderect(bot_rect)):
                p["grazed"] = True
                self.combo_count += 1
                graze_pts = 2 * self.combo_count
                self.score += graze_pts
                audio.play('graze')
                self.particles.emit_sparkles(self.bird.x, self.bird.y, (255, 230, 80), 8)
                self.particles.add_floating_text(f"GRAZE! +{graze_pts}", self.bird.x, self.bird.y - 20, (255, 240, 100), 1.1)

            if not p["scored"] and p["x"] + self.pipe_mgr.pipe_width < self.bird.x:
                p["scored"] = True
                self.score += 1
                audio.play('score')
                self.particles.add_floating_text("+1", self.bird.x, self.bird.y - 18, (255, 255, 255), 1.0)
                if self.score in [20, 45, 75] and not self.boss.active:
                    self.boss.spawn(self.score)
                    self.particles.add_floating_text("WARNING: BOSS SPAWN!", WIDTH//2, HEIGHT//3, (255, 50, 50), 1.5)

        magnet_rad = 50 + SAVE_DATA.get("magnet_lvl", 1) * 35
        for pu in self.pipe_mgr.powerups:
            if not pu["collected"]:
                dist = math.hypot(pu["x"] - self.bird.x, pu["y"] - self.bird.y)
                if dist < magnet_rad and pu["type"] == "gem":
                    pu["x"] += (self.bird.x - pu["x"]) * 0.15
                    pu["y"] += (self.bird.y - pu["y"]) * 0.15

                if bird_box.colliderect(pygame.Rect(pu["x"] - 14, pu["y"] - 14, 28, 28)):
                    pu["collected"] = True
                    if pu["type"] == "gem":
                        self.gems_collected += 1; self.session_gems += 1; self.score += 3
                        audio.play('gem')
                        self.particles.emit_sparkles(pu["x"], pu["y"], (255, 235, 70), 14)
                        self.particles.add_floating_text("+3 GEM", pu["x"], pu["y"] - 15, (255, 235, 70), 1.2)
                    elif pu["type"] == "shield":
                        self.bird.has_shield = True
                        audio.play('fanfare')
                        self.particles.emit_sparkles(pu["x"], pu["y"], (80, 220, 255), 16)
                        self.particles.add_floating_text("SHIELD UP!", pu["x"], pu["y"] - 15, (80, 220, 255), 1.3)
                    elif pu["type"] == "slow":
                        self.slow_mo_timer = 5.5
                        audio.play('graze')
                        self.particles.emit_sparkles(pu["x"], pu["y"], (255, 120, 230), 16)
                        self.particles.add_floating_text("SLOW MOTION!", pu["x"], pu["y"] - 15, (255, 120, 230), 1.3)

    def update(self, dt):
        speed_scale = 0.55 if self.slow_mo_timer > 0 else 1.0
        if self.slow_mo_timer > 0: self.slow_mo_timer -= dt

        self.env.update(dt, speed_scale=speed_scale if self.state == STATE_PLAYING else 0.5)
        self.weather.update(dt)
        self.particles.update(dt)

        for m in self.missiles: m.update(dt)
        self.missiles = [m for m in self.missiles if m.life > 0 and m.x < WIDTH + 40]

        if self.state != STATE_GAMEOVER:
            self.ground_offset = (self.ground_offset + 3.0 * speed_scale) % 28

        if self.state == STATE_START:
            self.bird.y = 280 + math.sin(pygame.time.get_ticks() * 0.005) * 10
            self.bird.wing_phase += 0.2
            self.bird.angle = 0
        elif self.state == STATE_PLAYING:
            self.bird.update(dt)
            self.pipe_mgr.update(dt, self.score, speed_scale=speed_scale)
            self.boss.update(dt, self.bird.y, self.particles)
            self.handle_collisions(dt)
        elif self.state == STATE_GAMEOVER:
            if self.bird.y + 14 < GROUND_Y:
                self.bird.vel += 0.55; self.bird.y += self.bird.vel
                self.bird.angle = max(-85, self.bird.angle - 5)
            else:
                self.bird.y = GROUND_Y - 14

    def draw_hud(self, surf):
        def draw_text_outline(text, font, color, out_color, x, y, center=True):
            base, out = font.render(text, True, color), font.render(text, True, out_color)
            rect = base.get_rect(center=(x, y)) if center else base.get_rect(topleft=(x, y))
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]: surf.blit(out, rect.move(dx, dy))
            surf.blit(base, rect)

        if self.state == STATE_START:
            draw_text_outline("FLAPPY BIRD", FONT_TITLE, (255, 230, 50), (150, 70, 0), WIDTH // 2, 110)
            draw_text_outline("TITAN EDITION", FONT_SMALL, (255, 255, 255), (0, 0, 0), WIDTH // 2, 150)

            box = pygame.Rect(WIDTH // 2 - 160, 340, 320, 95)
            pygame.draw.rect(surf, (20, 25, 40, 210), box, border_radius=14)
            pygame.draw.rect(surf, (255, 215, 60), box, 2, border_radius=14)
            skin = SKINS[self.bird.skin_idx]
            hat = HATS[self.bird.hat_idx]
            draw_text_outline(f"Skin: < {skin['name']} >", FONT_MEDIUM, skin["glow"], (0, 0, 0), WIDTH // 2, 365)
            draw_text_outline(f"Hat: < {hat['name']} >", FONT_SMALL, (240, 220, 140), (0, 0, 0), WIDTH // 2, 405)

            draw_text_outline("[SPACE] Fly  |  [F/CLICK] Shoot  |  [SHIFT] Dash", FONT_TINY, (240, 240, 255), (0, 0, 0), WIDTH // 2, 475)
            draw_text_outline("Press [S] to Open UPGRADE SHOP", FONT_SMALL, (80, 240, 255), (0, 0, 0), WIDTH // 2, 515)
            draw_text_outline(f"High Score: {self.high_score}   |   Gems: {self.gems_collected}", FONT_MEDIUM, (255, 235, 140), (40, 30, 0), WIDTH // 2, 565)

        elif self.state == STATE_SHOP:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 18, 30, 240)); surf.blit(overlay, (0, 0))
            draw_text_outline("TITAN UPGRADE SHOP", FONT_LARGE, (255, 215, 60), (100, 60, 0), WIDTH // 2, 70)
            draw_text_outline(f"Your Gems: ★ {self.gems_collected}", FONT_MEDIUM, (255, 235, 80), (0, 0, 0), WIDTH // 2, 115)

            items = [
                ("[1] Sonic Dash CD", f"Lvl {SAVE_DATA.get('dash_lvl', 1)}/5", 20 * SAVE_DATA.get('dash_lvl', 1)),
                ("[2] Plasma Egg Power", f"Lvl {SAVE_DATA.get('plasma_lvl', 1)}/5", 25 * SAVE_DATA.get('plasma_lvl', 1)),
                ("[3] Gem Magnet Field", f"Lvl {SAVE_DATA.get('magnet_lvl', 1)}/5", 15 * SAVE_DATA.get('magnet_lvl', 1)),
                ("[H] Cycle / Equip Hats", f"Current: {HATS[self.bird.hat_idx]['name']}", 0),
            ]
            for i, (name, lvl, cost) in enumerate(items):
                card = pygame.Rect(40, 160 + i * 85, 380, 70)
                pygame.draw.rect(surf, (30, 38, 60), card, border_radius=10)
                pygame.draw.rect(surf, (80, 180, 255), card, 2, border_radius=10)
                draw_text_outline(name, FONT_SMALL, (255, 255, 255), (0, 0, 0), 55, 180 + i * 85, center=False)
                cost_str = f"Cost: ★ {cost}" if cost > 0 else "Free"
                draw_text_outline(f"{lvl}  ({cost_str})", FONT_TINY, (255, 220, 100), (0, 0, 0), 55, 205 + i * 85, center=False)

            draw_text_outline("Press [1, 2, 3, H] to Buy   |   [ESC] Return", FONT_SMALL, (220, 230, 255), (0, 0, 0), WIDTH // 2, 590)

        elif self.state == STATE_PLAYING:
            draw_text_outline(str(self.score), FONT_TITLE, (255, 255, 255), (20, 20, 20), WIDTH // 2, 55)
            draw_text_outline(f"★ {self.session_gems}", FONT_MEDIUM, (255, 235, 70), (40, 30, 0), WIDTH - 60, 30)

            dash_w, dash_h, dash_x, dash_y = 120, 10, 20, 30
            pygame.draw.rect(surf, (40, 40, 50), (dash_x, dash_y, dash_w, dash_h), border_radius=4)
            max_cd = max(2.5, 5.0 - SAVE_DATA.get("dash_lvl", 1) * 0.6)
            fill_pct = 1.0 - max(0.0, min(1.0, self.bird.dash_cooldown / max_cd))
            col = (0, 255, 255) if fill_pct >= 1.0 else (120, 180, 200)
            pygame.draw.rect(surf, col, (dash_x, dash_y, int(dash_w * fill_pct), dash_h), border_radius=4)
            draw_text_outline("DASH [SHIFT]", FONT_TINY, (240, 240, 255), (0, 0, 0), dash_x + dash_w // 2, dash_y - 12)

            if self.slow_mo_timer > 0:
                draw_text_outline(f"SLOW-MO: {self.slow_mo_timer:.1f}s", FONT_SMALL, (255, 120, 230), (50, 0, 40), WIDTH // 2, 105)

        elif self.state == STATE_GAMEOVER:
            card = pygame.Rect(45, 140, 370, 270)
            pygame.draw.rect(surf, (245, 235, 210), card, border_radius=16)
            pygame.draw.rect(surf, (190, 140, 80), card, 5, border_radius=16)
            draw_text_outline("GAME OVER", FONT_LARGE, (235, 55, 55), (100, 10, 10), WIDTH // 2, 95)
            draw_text_outline(f"Score : {self.score}", FONT_MEDIUM, (40, 40, 40), (220, 220, 220), WIDTH // 2 + 10, 185)
            draw_text_outline(f"Best   : {self.high_score}", FONT_MEDIUM, (220, 120, 0), (255, 235, 180), WIDTH // 2 + 10, 230)
            draw_text_outline(f"Gems : +{self.session_gems}", FONT_MEDIUM, (210, 170, 20), (255, 255, 200), WIDTH // 2 + 10, 275)

            draw_text_outline("Press SPACE to Retry   |   [S] Upgrade Shop", FONT_SMALL, (255, 255, 255), (0, 0, 0), WIDTH // 2, 450)
            draw_text_outline("Press [ESC] for Menu", FONT_TINY, (220, 220, 220), (0, 0, 0), WIDTH // 2, 490)

    def render(self):
        render_surf = pygame.Surface((WIDTH, HEIGHT))
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-self.screen_shake, self.screen_shake)
            shake_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen_shake -= 1

        self.env.draw(render_surf)
        self.pipe_mgr.draw(render_surf)
        self.boss.draw(render_surf)

        # Ground
        pygame.draw.rect(render_surf, (215, 180, 110), (0, GROUND_Y, WIDTH, GROUND_HEIGHT))
        pygame.draw.rect(render_surf, (85, 185, 45), (0, GROUND_Y, WIDTH, 18))
        pygame.draw.rect(render_surf, (55, 140, 30), (0, GROUND_Y + 14, WIDTH, 5))
        for i in range(-28, WIDTH + 28, 28):
            sx = i - int(self.ground_offset)
            pygame.draw.polygon(render_surf, (190, 155, 85), [(sx, GROUND_Y + 19), (sx + 14, GROUND_Y + 19), (sx + 6, HEIGHT), (sx - 8, HEIGHT)])

        for m in self.missiles: m.draw(render_surf)
        self.particles.draw(render_surf)
        self.bird.draw(render_surf)
        self.weather.draw(render_surf)

        if self.slow_mo_timer > 0:
            slow_tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            slow_tint.fill((160, 40, 220, 35)); render_surf.blit(slow_tint, (0, 0))

        if self.flash_alpha > 0:
            flash_s = pygame.Surface((WIDTH, HEIGHT))
            flash_s.fill((255, 255, 255)); flash_s.set_alpha(self.flash_alpha)
            render_surf.blit(flash_s, (0, 0))
            self.flash_alpha = max(0, self.flash_alpha - 18)

        self.draw_hud(render_surf)
        screen.fill((0, 0, 0))
        screen.blit(render_surf, (shake_x, shake_y))
        pygame.display.flip()

# ----------------- MAIN ENTRYPOINT -----------------
def main():
    game = TitanFlappyGame()
    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                SAVE_DATA["high_score"] = game.high_score
                SAVE_DATA["total_gems"] = game.gems_collected
                SAVE_DATA["selected_skin"] = game.bird.skin_idx
                SAVE_DATA["selected_hat"] = game.bird.hat_idx
                save_data(SAVE_DATA)
                pygame.quit()
                sys.exit()

            jump_input = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    jump_input = True
                elif event.key in (pygame.K_f, pygame.K_z):
                    game.shoot_missile()
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_x):
                    if game.state == STATE_PLAYING:
                        game.bird.trigger_dash(game.particles)
                elif event.key == pygame.K_s:
                    if game.state in (STATE_START, STATE_GAMEOVER): game.state = STATE_SHOP
                elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                    if game.state == STATE_PLAYING: game.state = STATE_PAUSED
                    elif game.state == STATE_PAUSED: game.state = STATE_PLAYING
                    elif game.state in (STATE_SHOP, STATE_GAMEOVER): game.state = STATE_START
                elif game.state == STATE_START:
                    if event.key == pygame.K_LEFT:
                        game.bird.skin_idx = (game.bird.skin_idx - 1) % len(SKINS)
                        SAVE_DATA["selected_skin"] = game.bird.skin_idx
                    elif event.key == pygame.K_RIGHT:
                        game.bird.skin_idx = (game.bird.skin_idx + 1) % len(SKINS)
                        SAVE_DATA["selected_skin"] = game.bird.skin_idx
                    elif event.key == pygame.K_h:
                        game.bird.hat_idx = (game.bird.hat_idx + 1) % len(HATS)
                        SAVE_DATA["selected_hat"] = game.bird.hat_idx
                elif game.state == STATE_SHOP:
                    if event.key == pygame.K_1:
                        cost = 20 * SAVE_DATA.get("dash_lvl", 1)
                        if game.gems_collected >= cost and SAVE_DATA.get("dash_lvl", 1) < 5:
                            game.gems_collected -= cost; SAVE_DATA["dash_lvl"] = SAVE_DATA.get("dash_lvl", 1) + 1
                            audio.play('fanfare'); save_data(SAVE_DATA)
                    elif event.key == pygame.K_2:
                        cost = 25 * SAVE_DATA.get("plasma_lvl", 1)
                        if game.gems_collected >= cost and SAVE_DATA.get("plasma_lvl", 1) < 5:
                            game.gems_collected -= cost; SAVE_DATA["plasma_lvl"] = SAVE_DATA.get("plasma_lvl", 1) + 1
                            audio.play('fanfare'); save_data(SAVE_DATA)
                    elif event.key == pygame.K_3:
                        cost = 15 * SAVE_DATA.get("magnet_lvl", 1)
                        if game.gems_collected >= cost and SAVE_DATA.get("magnet_lvl", 1) < 5:
                            game.gems_collected -= cost; SAVE_DATA["magnet_lvl"] = SAVE_DATA.get("magnet_lvl", 1) + 1
                            audio.play('fanfare'); save_data(SAVE_DATA)
                    elif event.key == pygame.K_h:
                        game.bird.hat_idx = (game.bird.hat_idx + 1) % len(HATS)
                        SAVE_DATA["selected_hat"] = game.bird.hat_idx

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: jump_input = True
                elif event.button == 3: game.shoot_missile()

            if jump_input:
                if game.state == STATE_START: game.start_game()
                elif game.state == STATE_PLAYING: game.bird.jump(game.particles)
                elif game.state == STATE_GAMEOVER: game.start_game()

        if game.state not in (STATE_PAUSED, STATE_SHOP):
            game.update(dt)
        game.render()

if __name__ == "__main__":
    main()