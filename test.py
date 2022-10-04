import winsound
duration = 1000  # milliseconds
freq = 440  # Hz


if __name__ == "__main__":
    winsound.Beep(freq, duration)
    winsound.MessageBeep()