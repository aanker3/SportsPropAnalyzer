
# So last10 is the % that a the player hit.  so if the line is 7.5 over and the player hit it in 9 of his last 10 games.  We care about the 9/10 and 90%.

# I want the last%.  The idea is that sometimes its more important to get the last 17.  like a player could be 16/17 and then 16/20.  So the last% idea is that it finds the best % hit with the best denominator.

#dont count 100% as a valid return unless its > 10 games.  but if its preceeded  by 2 losses in a row, use the 100%.  EX: W W W W L L W L W L should be 4/4.

def last_percent(hits: list[bool]) -> tuple[float, str]:
    # Initialize best values
    max_percent = 0.0
    best_hit_count = 0
    best_total = 0
    start = 0  # window always starts at index 0

    # Expand the window one element at a time
    for end in range(start, len(hits)):
        window = hits[start:end + 1]
        total = end - start + 1
        hit_count = sum(window)
        percent = hit_count / total

        # Handle 100% hit rate exceptions
        is_hundred = percent == 1.0
        if is_hundred and total <= 5:
            # Allow it only if followed by 2 losses
            if not (len(hits) > end + 2 and not hits[end + 1] and not hits[end + 2]):
                continue

        # Update max if current window is better
        if percent >= max_percent:
            max_percent = percent
            best_hit_count = hit_count
            best_total = total

    # Return the best percentage and its fraction string
    return round(max_percent * 100, 2), f"{best_hit_count}/{best_total}"


print(last_percent([True, True, True, True, True, False, True, True, True, True, True, False, False, False, True, True, True, True, True, True]))
print(last_percent(hits= [True, True, True, True, True, False, True, True, True, True, True, False, False, False, True, True, True, True, True, True]))
print(last_percent(hits=[False, False, 0, 1,1, 1,0, 1, 0,0, 1]))
print(last_percent(hits=[0, 1,0 ,1 ,0, 1, 0,1,1,1,0,0,0,0,0,0,1,1]))