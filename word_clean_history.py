"""Local history: successful conversions only; no manuscript text or paths."""
from pathlib import Path
from datetime import datetime
import json, os

def append_history(path, source, mapping, counts):
    record={'file_name':Path(source).name,'processed_at':datetime.now().astimezone().isoformat(timespec='seconds'),
            'replacements':[{'old':old,'new':mapping[old],'count':int(n)} for old,n in counts.items() if n>0]}
    data=(json.dumps(record,ensure_ascii=False)+'\n').encode('utf-8')
    # A single append write preserves previous records; do not rewrite the file.
    fd=os.open(path,os.O_APPEND|os.O_CREAT|os.O_WRONLY,0o600)
    try:
        if os.write(fd,data)!=len(data):raise OSError('处理记录未完整写入')
        os.fsync(fd)
    finally:os.close(fd)

def read_history(path):
    if not Path(path).exists():return [],0
    records=[];invalid=0
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        try:
            r=json.loads(line)
            if set(r)!={'file_name','processed_at','replacements'}:raise ValueError('字段不符')
            if not isinstance(r['file_name'],str) or '/' in r['file_name'] or '\\' in r['file_name']:raise ValueError('无效文件名')
            if not isinstance(r['processed_at'],str) or not isinstance(r['replacements'],list):raise ValueError('字段不符')
            for p in r['replacements']:
                if set(p)!={'old','new','count'} or not isinstance(p['old'],str) or not isinstance(p['new'],str) or len(p['old'])!=1 or len(p['new'])!=1 or type(p['count']) is not int or p['count']<1:raise ValueError('无效统计')
            records.append(r)
        except (ValueError,TypeError,KeyError):invalid+=1
    return records,invalid