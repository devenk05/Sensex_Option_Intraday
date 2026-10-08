from pathlib import Path
import re, shutil
p=Path(r"D:\Sensex_Option_Intraday\Entry\config.py")
if not p.exists(): raise SystemExit(f"ERROR: {p} not found.")
text=p.read_text(encoding="utf-8-sig")
vals={"PREMIUM_REVERSAL_CONFIRM_POINTS":20.0,
      "PREMIUM_REVERSAL_CONFIRM_PERCENT":10.0,
      "PREMIUM_REVERSAL_LOOKBACK_CANDLES":5}
backup=p.with_suffix(".py.before_premium_reversal_entry.bak")
if not backup.exists(): shutil.copy2(p,backup)
for k,v in vals.items():
    pat=rf"(?m)^{re.escape(k)}\s*=.*$"
    if re.search(pat,text):
        text=re.sub(pat,f"{k} = {v}",text,count=1)
    else:
        anchor="MIN_TARGET_POINTS = 100"
        if anchor not in text: raise SystemExit("ERROR: config anchor not found.")
        block="\n\n# 1-minute option premium reversal entry gate\n"+              "\n".join(f"{kk} = {vv}" for kk,vv in vals.items())
        text=text.replace(anchor,anchor+block,1)
        break
p.write_text(text,encoding="utf-8")
print("UPDATED:",p)
print("BACKUP:",backup)
