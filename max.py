
total_hr = 0
total_min = 2
total_sec = 58

hour = 0
minute = 0
second = 0

while True:
     print(f"{hour: 02d}: {minute: 02d}: {second: 02d}")
     for _ in range(100):
        pass
     second += 1

     if second == 60:
        second = 0
        minute += 1

     if minute == 60:
        minute = 0
        hour += 1

     if total_hr == hour and total_min == minute and total_sec == second:
        print( f" you have reached the maximum {hour:02d}:{minute:02d}:{second:02d}")
        break

