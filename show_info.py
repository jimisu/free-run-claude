import datetime
import shutil
import os

def main():
    # Current system time
    now = datetime.datetime.now()
    print(f"Current system time: {now}")

    # Disk usage of the root filesystem
    total, used, free = shutil.disk_usage('/')
    # Convert bytes to gigabytes for readability
    gb = 1024 ** 3
    print(f"Disk space (GB): Total = {total / gb:.2f}, Used = {used / gb:.2f}, Free = {free / gb:.2f}")

if __name__ == "__main__":
    main()
