#!/usr/bin/env python3
"""
Example: How to use the synchronized display system

This shows how easy it is to integrate sync_display with your own code.
"""

from sync_display import SyncDisplay
import time

def example_countdown():
    """Example: Show a countdown on all displays"""
    sync = SyncDisplay(mode='both')  # 'both' mode works on any Pi
    
    # Countdown
    for i in range(5, 0, -1):
        sync.display_text(str(i), font_size=80, color=(255, 255, 255), bg_color=(0, 0, 0))
        time.sleep(1)
    
    sync.display_text("GO!", font_size=60, color=(0, 255, 0), bg_color=(0, 0, 0))
    time.sleep(2)
    
    sync.stop()


def example_color_cycle():
    """Example: Cycle through colors on all displays"""
    sync = SyncDisplay(mode='both')
    
    colors = [
        (255, 0, 0, "RED"),
        (0, 255, 0, "GREEN"),
        (0, 0, 255, "BLUE"),
        (255, 255, 0, "YELLOW"),
        (255, 0, 255, "MAGENTA"),
        (0, 255, 255, "CYAN"),
    ]
    
    for r, g, b, name in colors:
        sync.display_color(r, g, b)
        print(f"Showing {name}")
        time.sleep(1.5)
    
    sync.stop()


def example_with_sensor():
    """Example: Show sensor data on all displays"""
    sync = SyncDisplay(mode='both')
    
    # Simulate some sensor readings
    for i in range(10):
        temp = 20 + i * 0.5
        sync.display_text(f"{temp:.1f}°C", font_size=40, color=(255, 128, 0))
        print(f"Temperature: {temp:.1f}°C")
        time.sleep(1)
    
    sync.stop()


if __name__ == '__main__':
    import sys
    
    print("=" * 50)
    print("  Synchronized Display Examples")
    print("=" * 50)
    print()
    
    if len(sys.argv) < 2:
        print("Choose an example:")
        print("  1 - Countdown")
        print("  2 - Color cycle")
        print("  3 - Sensor simulation")
        print()
        print("Usage: python sync_example.py [1|2|3]")
        sys.exit(1)
    
    example = sys.argv[1]
    
    if example == '1':
        example_countdown()
    elif example == '2':
        example_color_cycle()
    elif example == '3':
        example_with_sensor()
    else:
        print(f"Unknown example: {example}")


