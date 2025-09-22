import time
import math
import datetime
import digitalio
import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_rgb_display.st7789 as st7789


#Wiring matches from screen_test.py
cs_pin = digitalio.DigitalInOut(board.D5)     
dc_pin = digitalio.DigitalInOut(board.D25)    
reset_pin = None
BAUDRATE = 64_000_000
spi = board.SPI()
disp = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

#blank rotated canvas
HEIGHT = disp.width
WIDTH  = disp.height
image = Image.new("RGB", (WIDTH, HEIGHT))
rotation = 90
draw = ImageDraw.Draw(image)

#to toggle with button to keep backlight pin
backlight = digitalio.DigitalInOut(board.D22)  # GPIO22
backlight.switch_to_output(value=True)

#font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
except Exception:
    font = ImageFont.load_default()

#guidelines for star button
buttonA = digitalio.DigitalInOut(board.D23)
#comet tail button
buttonB = digitalio.DigitalInOut(board.D24)    
buttonA.switch_to_input(pull=digitalio.Pull.UP)  
buttonB.switch_to_input(pull=digitalio.Pull.UP)

#track last state
prevA = True
prevB = True

show_guides = True
comet_tail = False
time_mode = "linear"

#to store comet trail positions
SEC_TRAIL_LEN = 24
sec_trail = []

#colors
NIGHT = (9, 22, 60)
GLOW  = (30, 60, 110)
MOON  = (245, 240, 180)
STAR1 = (200, 210, 255) #hour star
STAR2 = (220, 220, 160) #minute star
STAR3 = (255, 230, 120) #second star
TRAIL = (180, 200, 240)

def star_points(cx, cy, r, spikes=5, inset=0.5):
    pts = []
    ang = -math.pi / 2
    step = math.pi / spikes
    for i in range(spikes * 2):
        rad = r if i % 2 == 0 else r * inset
        x = cx + math.cos(ang) * rad
        y = cy + math.sin(ang) * rad
        pts.append((x, y))
        ang += step
    return pts

def lerp_x(t):
    #map x coord across screen for the star
    return int(10 + t * (WIDTH - 20))

def draw_background():
    #night sky
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=NIGHT)
    #crescent moon
    mx, my, mr = 38, 32, 22
    draw.ellipse((mx - mr, my - mr, mx + mr, my + mr), fill=MOON)
    draw.ellipse((mx - mr + 8, my - mr, mx + mr + 8, my + mr), fill=NIGHT)
    #smaller stars
    for x, y, r in [(110, 18, 2), (86, 40, 2), (200, 28, 1), (155, 12, 1), (210, 50, 1)]:
        draw.polygon(star_points(x, y, r), fill=(240, 240, 200))

def draw_guides(y_hour, y_min, y_sec):
    #guidelines across the screen for the stars
    draw.line((10, y_hour, WIDTH - 10, y_hour), fill=GLOW)
    draw.line((10, y_min,  WIDTH - 10, y_min),  fill=GLOW)
    draw.line((10, y_sec,  WIDTH - 10, y_sec),  fill=GLOW)

def draw_time_stars(now):
    y_hour = 18
    y_min  = HEIGHT // 2 + 2
    y_sec  = HEIGHT - 24

    #convert current time into x positions for the stars
    t_sec  = (now.second + now.microsecond / 1_000_000) / 60.0
    t_min  = (now.minute + now.second / 60.0) / 60.0
    hour12 = (now.hour % 12) + now.minute / 60.0
    t_hour = hour12 / 12.0

    x_sec  = lerp_x(t_sec)
    x_min  = lerp_x(t_min)
    x_hour = lerp_x(t_hour)

    if show_guides:
        draw_guides(y_hour, y_min, y_sec)

    #comet trail if turned on
    if comet_tail:
        sec_trail.append((x_sec, y_sec))
        if len(sec_trail) > SEC_TRAIL_LEN:
            sec_trail.pop(0)
        for i, (tx, ty) in enumerate(sec_trail):
            r = max(1, 4 - (SEC_TRAIL_LEN - i)//8)
            draw.ellipse((tx - r, ty - r, tx + r, ty + r), fill=TRAIL)
    else:
        sec_trail.clear()

    #stars in the corner
    draw.polygon(star_points(x_hour, y_hour, 10), fill=STAR1)
    draw.polygon(star_points(x_min,  y_min,   8), fill=STAR2)
    draw.polygon(star_points(x_sec,  y_sec,   7), fill=STAR3)

    #digital time
    label_time = now.strftime("%I:%M:%S %p").lstrip("0")
    w_time = draw.textlength(label_time, font=font)
    draw.text((WIDTH - w_time - 6, 2), label_time, font=font, fill=(230, 235, 255))

def read_button_edges():
    global prevA, prevB
    a = buttonA.value   
    b = buttonB.value
    evA = (prevA and not a)
    evB = (prevB and not b)
    prevA, prevB = a, b
    #if both buttons held together
    return evA, evB, (not a) and (not b)  

###Run clock###
while True:
    evA, evB, both_pressed = read_button_edges()

    #if both pressed at once
    if both_pressed:
        backlight.value = False
    else:
        backlight.value = True

    #if either A or B is pressed
    if evA and not both_pressed:
        show_guides = not show_guides
    if evB and not both_pressed:
        comet_tail = not comet_tail

    draw_background()
    now = datetime.datetime.now()
    draw_time_stars(now)
    disp.image(image, rotation)

    time.sleep(0.05) 
