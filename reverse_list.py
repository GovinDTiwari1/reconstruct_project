with open("list.txt","r",encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]
lines.reverse()
with open("list_correct.txt","w",encoding="utf-8") as f:
    for l in lines:
        f.write(l + "\n")
print("Wrote list_correct.txt")
