# Tiny UI helper for regression tests (retries for TCG slowness).
# ui.py tap-text <text> | tap-class <classSubstr> | wait-class <classSubstr>   (timeout 90s; exit 1 if not found)
import subprocess as sp, sys, re, time
def dump():
    try: x=sp.run(["adb","exec-out","uiautomator","dump","/dev/tty"],capture_output=True,text=True,timeout=60).stdout
    except sp.TimeoutExpired: return []
    return re.findall(r"<node[^>]*>", x)
def find(attr,val):
    for n in dump():
        m=re.search(attr+r'="([^"]*)"',n); b=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',n)
        if m and b and (m.group(1)==val if attr=="text" else val in m.group(1)):
            x1,y1,x2,y2=map(int,b.groups()); return (x1+x2)//2,(y1+y2)//2
cmd,val=sys.argv[1],sys.argv[2]; attr="text" if cmd=="tap-text" else "class"; t=time.time()
while time.time()-t<90:
    p=find(attr,val)
    if p:
        if cmd!="wait-class": sp.run(["adb","shell","input","tap",str(p[0]),str(p[1])])
        sys.exit(0)
    time.sleep(3)
print(f"not found: {val}"); sys.exit(1)
