# Fills every EditText on each reachable screen with adversarial values, submits, checks app alive.
import subprocess as sp, sys, re, time, xml.etree.ElementTree as ET
PKG, OUT = sys.argv[1], sys.argv[2]
VALS = ["", " ", "-1", "-999999999", "0", "99999999999999999999", "1e308", "NaN", "12/45/2026", "2026-02-30", "00/00/0000",
        "😀🏠💸", "' OR 1=1;--", "<script>x</script>", "%s%n%d", "A"*5000, "١٢٣", "\u202eRTL"]
def adb(*a): return sp.run(["adb",*a],capture_output=True,text=True,timeout=60).stdout
def fields():
    x=adb("exec-out","uiautomator","dump","/dev/tty"); i=x.find("<?xml")
    if i<0: return []
    try: r=ET.fromstring(x[i:x.rfind(">")+1])
    except ET.ParseError: return []
    out=[]
    for n in r.iter("node"):
        if n.get("package")==PKG and "EditText" in n.get("class",""):
            a=list(map(int,re.findall(r"\d+",n.get("bounds")))); out.append(((a[0]+a[2])//2,(a[1]+a[3])//2))
    return out
def typ(v):
    # adb input text can't take raw unicode/specials; use clipboard-free per-char escaping for ASCII, ADB keyboard broadcast fallback otherwise
    if v and all(32<=ord(c)<127 for c in v):
        esc=re.sub(r"([\\'\"`$&|;<>()*?!~#%\s])",r"\\\1",v)
        for i in range(0,len(esc),900): adb("shell","input","text",esc[i:i+900])
    elif v: adb("shell","am","broadcast","-a","ADB_INPUT_TEXT","--es","msg",v)
log=open(f"{OUT}/inputs.txt","w")
fs=fields(); log.write(f"fields on first screen: {len(fs)}\n")
for v in VALS:
    for (x,y) in fields():
        adb("shell","input","tap",str(x),str(y)); adb("shell","input","keyevent","123"); adb("shell","input","keyevent","--longpress","67")
        for _ in range(3): adb("shell","input","keyevent","KEYCODE_MOVE_END","KEYCODE_DEL") if False else None
        typ(v)
    adb("shell","input","keyevent","66"); time.sleep(1)
    alive=bool(adb("shell","pidof",PKG).strip()); log.write(f"{v[:30]!r}: alive={alive}\n")
    if not alive: break
