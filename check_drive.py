import re

file_path = r"C:\Users\Chen Qianyu\.gemini\antigravity\brain\2a62d9a5-7974-472a-b5d8-edcfacf823c4\.system_generated\steps\643\content.md"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Pattern: ssk='5:[^:]*:([a-zA-Z0-9_-]{25,})-[0-9]+-[0-9]+'
# or let's search specifically per video
for i in range(1, 21):
    name = f"video{i:02d}.mp4"
    pos = text.find(f'aria-label="{name}')
    if pos != -1:
        chunk = text[pos:pos+400]
        m = re.search(r'ssk=[\'"][0-9]+:[^:]*:([a-zA-Z0-9_-]+)-', chunk)
        if m:
            print(f"{name} => https://drive.google.com/file/d/{m.group(1)}/view (ID: {m.group(1)})")
        else:
            print(f"{name} => (no ssk match, chunk: {chunk[:100]})")
    else:
        print(f"{name} => not found")
