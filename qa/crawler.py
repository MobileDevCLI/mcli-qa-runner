import subprocess as sp, sys, os, re, time, hashlib, html, xml.etree.ElementTree as ET, signal
PKG, OUT, MAX = sys.argv[1], sys.argv[2], int(sys.argv[3])
def adb(*a, **k):
    try: return sp.run(["adb", *a], capture_output=True, text=k.get("text", True), timeout=k.get("t", 90)).stdout
    except sp.TimeoutExpired: return ""  # TCG stalls: treat as empty, keep crawling
def shot(n):
    # host-side capture: device screencap takes ~55s under TCG, this takes 0.3s
    adb("emu","screenrecord","screenshot",os.path.abspath(f"{OUT}/{n}.png")); time.sleep(.3)
def dump():
    for _ in range(3):
        x = adb("exec-out","uiautomator","dump","/dev/tty")
        i = x.find("<?xml")
        if i >= 0:
            try: return ET.fromstring(x[i:x.rfind(">")+1])
            except ET.ParseError: pass
        time.sleep(1)
    return None
def fg(): return PKG in adb("shell","dumpsys","window")[0:10**7].split("mCurrentFocus")[-1][:300]
def nodes(root):
    r=[]
    for n in root.iter("node"):
        if n.get("package")!=PKG: continue
        if n.get("clickable")=="true" or n.get("long-clickable")=="true" or n.get("checkable")=="true":
            m=re.findall(r"\d+", n.get("bounds",""))
            if len(m)<4: continue
            x1,y1,x2,y2=map(int,m)
            if x2-x1<4 or y2-y1<4: continue
            if "EditText" in n.get("class",""):  # text changes as we type; key by id/position so each field is typed once
                r.append((f"field@{n.get('resource-id') or ''}{x1//50},{y1//50}",(x1+x2)//2,(y1+y2)//2,n.get("class",""))); continue
            lab=n.get("text") or n.get("content-desc") or n.get("resource-id") or ""
            if not lab:  # use descendant text
                lab=" ".join(filter(None,(c.get("text") or c.get("content-desc") for c in n.iter("node"))))[:60]
            r.append((lab or n.get("class","").split(".")[-1], (x1+x2)//2,(y1+y2)//2, n.get("class","")))
    return r
def sig(root):
    s="|".join(sorted({("" if "EditText" in n.get("class","") else (n.get("text") or n.get("content-desc") or ""))+n.get("class","") for n in root.iter("node") if n.get("package")==PKG and (n.get("clickable")=="true" or n.get("text"))}))
    return hashlib.md5(s.encode()).hexdigest()[:10]
NAVBACK=re.compile(r"^(back|close|navigate up|cancel|dismiss|done)$",re.I); idle=0; relaunches=[0]
DANGER=re.compile(r"delete|remove|sign out|log ?out|reset|erase all|uninstall",re.I)
adb("logcat","-c")
rec=[]; ri=[0]
def startrec():
    # host-side recording (device screenrecord starves the TCG CPU)
    if rec: adb("emu","screenrecord","stop"); time.sleep(2)
    adb("emu","screenrecord","start","--time-limit","180","--fps","4",os.path.abspath(f"{OUT}/recording_{ri[0]}.webm")); rec.append((None,ri[0],time.time())); ri[0]+=1
adb("shell","am","force-stop",PKG); startrec()
adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1"); time.sleep(int(os.environ.get("LAUNCH_WAIT","4")))
tried={}; steps=[]; fails=[]; path=[]; seen=set(); step=0; t0=time.time()
def check_crash(ctx):
    lg=adb("logcat","-d","-v","brief","AndroidRuntime:E","ActivityManager:E","*:S")
    adb("logcat","-c")
    for blk in re.split(r"(?=E/AndroidRuntime.*FATAL EXCEPTION)|(?=E/ActivityManager.*ANR in)", lg):
        if re.search(r"ANR in "+re.escape(PKG)+r"\b", blk) or ("FATAL EXCEPTION" in blk and re.search(r"Process: "+re.escape(PKG)+r"\b", blk)):
            fails.append({"step":step,"type":"ANR" if "ANR in" in blk else "CRASH","repro":list(path)+[ctx],"log":blk[:4000]})
            return True
    return False
def relaunch():
    path.clear(); adb("shell","am","force-stop",PKG)
    adb("shell","monkey","-p",PKG,"-c","android.intent.category.LAUNCHER","1"); time.sleep(int(os.environ.get("LAUNCH_WAIT","4")))
while step<MAX:
    if rec and time.time()-rec[-1][2]>165: startrec()
    root=dump()
    if root is None: relaunch(); continue
    if not fg():
        # left the app (system dialog/permission/camera/share sheet): record then back
        shot(f"s{step:03d}_outside"); steps.append((step,"(outside app) BACK",f"s{step:03d}_outside.png")); adb("shell","input","keyevent","4"); time.sleep(1.5); step+=1
        if not fg(): relaunch(); relaunches[0]+=1
        if relaunches[0]>8: break
        continue
    s=sig(root); seen.add(s); todo=[n for n in nodes(root) if (s,n[0]) not in tried and not DANGER.search(n[0])]
    todo.sort(key=lambda n: bool(NAVBACK.search(n[0])))  # explore forward first, back/close last
    if not todo:
        if not path or idle>=3: break
        idle+=1; adb("shell","input","keyevent","4"); path.pop(); time.sleep(2); continue
    idle=0
    lab,x,y,cls=todo[0]; tried[(s,lab)]=1
    ctx=f"tap '{lab}' ({cls.split('.')[-1]}) at {x},{y} on screen {s}"
    if "EditText" in cls:
        adb("shell","input","tap",str(x),str(y)); time.sleep(.5); adb("shell","input","text","QA%stest%s123"); adb("shell","input","keyevent","111"); ctx=f"type into '{lab}' on {s}"
    else: adb("shell","input","tap",str(x),str(y))
    time.sleep(1.2); path.append(ctx); n=f"s{step:03d}"; shot(n); steps.append((step,ctx,n+".png"))
    if check_crash(ctx): shot(n+"_crash"); relaunch()
    step+=1
check_crash("end of crawl")
adb("emu","screenrecord","stop"); time.sleep(3)
ok=not fails; dur=int(time.time()-t0)
md=[f"# QA report: {PKG}\n",f"**Result: {'PASS' if ok else 'FAIL'}** | steps {step} | unique screens {len(seen)} | elements tapped {len(tried)} | {dur}s\n"]
for f in fails: md+= [f"## {f['type']} at step {f['step']}\nRepro:\n"]+[f"{i+1}. {r}" for i,r in enumerate(f["repro"])]+["```",f["log"],"```"]
md.append("\n## Steps"); md+= [f"- {a}: {b} ([png]({c}))" for a,b,c in steps]
open(f"{OUT}/report.md","w").write("\n".join(md))
h=[f"<html><body style='font-family:sans-serif'><h1>{PKG} — <span style='color:{'green' if ok else 'red'}'>{'PASS' if ok else 'FAIL'}</span></h1><p>steps {step}, screens {len(seen)}, taps {len(tried)}, {dur}s. Recordings: "+" ".join(f"<a href='recording_{i}.webm'>{i}</a>" for _,i,_ in rec)+"</p>"]
for f in fails: h.append(f"<h2 style='color:red'>{f['type']} step {f['step']}</h2><ol>"+"".join(f"<li>{html.escape(r)}</li>" for r in f["repro"])+f"</ol><pre>{html.escape(f['log'])}</pre>")
h.append("<div style='display:flex;flex-wrap:wrap'>"+"".join(f"<figure style='width:200px'><img src='{c}' width=190><figcaption style='font-size:11px'>{a}: {html.escape(b)}</figcaption></figure>" for a,b,c in steps)+"</div></body></html>")
open(f"{OUT}/report.html","w").write("".join(h))
print("PASS" if ok else f"FAIL ({len(fails)} issues)", OUT); sys.exit(0 if ok else 1)
