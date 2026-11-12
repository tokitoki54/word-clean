"""Word Clean: only the user's Excel mapping; standard library only."""
from pathlib import Path
from collections import Counter
import zipfile, xml.etree.ElementTree as ET, re, posixpath, csv, io
from xml.sax.saxutils import escape

S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def load_mapping(path):
    if Path(path).suffix.lower()==".csv":
        with Path(path).open(encoding="utf-8-sig",newline="") as f: return validate_pairs(csv.DictReader(f))
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(t.text or '' for t in si.iter(S+'t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        sheet=wb.find(S+'sheets')[0]
        rid=sheet.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target=next(r.get('Target') for r in rels if r.get('Id')==rid)
        name=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        rows=[]
        for row in ET.fromstring(z.read(name)).iter(S+'row'):
            values={}
            for c in row.findall(S+'c'):
                col=re.match(r'[A-Z]+',c.get('r','')).group()
                v=c.find(S+'v')
                value=v.text if v is not None else ''
                if c.get('t')=='s': value=shared[int(value)]
                elif c.get('t')=='inlineStr': value=''.join(t.text or '' for t in c.iter(S+'t'))
                values[col]=(value or '').strip()
            rows.append(values)
    if not rows: raise ValueError('字表为空。')
    headers=rows[0]
    old=next((k for k,v in headers.items() if v=='旧字型'),None)
    new=next((k for k,v in headers.items() if v=='新字形'),None)
    if not old or not new: raise ValueError('字表第一行必须包含“旧字型”和“新字形”。')
    mapping={}
    for row in rows[1:]:
        a,b=row.get(old,''),row.get(new,'')
        if not a or not b: continue
        if len(a)!=1 or len(b)!=1: raise ValueError('此版本仅支持单字对单字的原始字表，请检查：'+a+' → '+b)
        if a in mapping and mapping[a]!=b: raise ValueError('字表存在冲突，请先确认规则：'+a)
        mapping[a]=b
    if not mapping: raise ValueError('字表没有有效映射。')
    return mapping

def transform_xml(data,mapping):
    # Validate, then replace only text-node payloads. All other XML bytes remain unchanged.
    if b'<!DOCTYPE' in data.upper(): raise ValueError('不支持包含 DTD 的文档。')
    root=ET.fromstring(data)
    text=data.decode('utf-8')
    word_namespaces={W,'http://purl.oclc.org/ooxml/wordprocessingml/main'}
    bindings={}
    # Parse declarations as XML, so legal whitespace/quoting is supported.
    # Conservative rejection avoids applying a prefix outside its actual scope.
    for event,(prefix,uri) in ET.iterparse(io.BytesIO(data),events=('start-ns',)):
        bindings.setdefault(prefix,set()).add(uri)
    if bindings.get('',set()) & word_namespaces:
        raise ValueError('此文档包含默认 Word XML 命名空间，暂不支持；请用 Word 另存后重试。')
    for prefix,uris in bindings.items():
        if uris & word_namespaces and len(uris)>1:
            raise ValueError('此文档重新绑定了 Word XML 前缀，无法安全替换；请用 Word 另存后重试。')
    prefixes={prefix for prefix,uris in bindings.items() if prefix and uris & word_namespaces}
    counts=Counter()
    for prefix in prefixes:
        pattern=re.compile(r'(<'+re.escape(prefix)+r':t(?:\s[^>]*)?>)(.*?)(</'+re.escape(prefix)+r':t\s*>)',re.S)
        def replace(match):
            payload=match.group(2)
            # Normal Word text nodes have character data only; refuse unusual nested markup.
            if '<' in payload: raise ValueError('遇到非标准 Word 文本节点，已停止，原文件不受影响。')
            original=ET.fromstring('<text>'+payload+'</text>').text or ''
            updated=''.join(mapping.get(c,c) for c in original)
            if updated==original: return match.group(0)
            counts.update(c for c in original if c in mapping and mapping[c]!=c)
            return match.group(1)+escape(updated).replace('\r','&#13;')+match.group(3)
        text=pattern.sub(replace,text)
    result=text.encode('utf-8')
    ET.fromstring(result)
    return result,counts

def process_docx(source,mapping,destination=None):
    source=Path(source)
    if source.suffix.lower()!='.docx': raise ValueError('只支持 .docx，请先将 .doc 另存为 .docx。')
    if destination is not None and Path(destination).resolve()==source.resolve(): raise ValueError('输出不能覆盖原文件。')
    changes={}; counts=Counter()
    with zipfile.ZipFile(source) as z:
        if 'word/document.xml' not in z.namelist(): raise ValueError('不是有效的 Word 文档。')
        if len(z.namelist())!=len(set(z.namelist())): raise ValueError('文档包含重复压缩条目，无法安全处理。')
        for info in z.infolist():
            if info.file_size>100*1024*1024: raise ValueError('文档单项过大，无法安全处理。')
            if re.fullmatch(r'word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml',info.filename):
                original=z.read(info)
                updated,stats=transform_xml(original,mapping)
                counts.update(stats)
                if updated!=original: changes[info.filename]=updated
        if destination is not None:
            destination=Path(destination)
            destination.parent.mkdir(parents=True,exist_ok=True)
            created=False
            try:
                with destination.open('xb') as handle:
                    created=True
                    with zipfile.ZipFile(handle,'w') as out:
                        out.comment=z.comment
                        for info in z.infolist(): out.writestr(info,changes.get(info.filename,z.read(info)))
                with zipfile.ZipFile(destination) as check:
                    if check.testzip(): raise ValueError('输出校验失败。')
            except Exception:
                if created: destination.unlink(missing_ok=True)
                raise
    return counts

def validate_pairs(rows):
    mapping={}
    for row in rows:
        if '旧字型' not in row or '新字形' not in row: raise ValueError('字表须包含旧字型、新字形两列。')
        a,b=(row['旧字型'] or '').strip(),(row['新字形'] or '').strip()
        if not a or not b: continue
        if len(a)!=1 or len(b)!=1: raise ValueError('只支持单字对单字映射。')
        if a in mapping and mapping[a]!=b: raise ValueError('同一旧字有冲突映射：'+a)
        mapping[a]=b
    if not mapping: raise ValueError('字表没有有效映射。')
    return mapping

def process_txt(source,mapping,destination=None,encoding_choice="auto"):
    source=Path(source); raw=source.read_bytes()
    encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    if encoding_choice!='auto':encoding=encoding_choice
    try:text=raw.decode(encoding)
    except UnicodeDecodeError:raise ValueError('TXT 不是 UTF-8 或带 BOM 的 UTF-16，请确认编码，并在界面明确选择 GB18030，或用记事本另存为 UTF-8 后重试。')
    counts=Counter(c for c in text if c in mapping and mapping[c]!=c)
    updated=''.join(mapping.get(c,c) for c in text)
    # Preserve original UTF-16 byte order, BOM, line endings and encoding.
    if encoding_choice=='auto' and raw.startswith(b'\xfe\xff'):data=b'\xfe\xff'+updated.encode('utf-16-be')
    elif encoding_choice=='auto' and raw.startswith(b'\xff\xfe'):data=b'\xff\xfe'+updated.encode('utf-16-le')
    else:data=updated.encode(encoding)
    if destination is not None:
        destination=Path(destination)
        if destination.resolve()==source.resolve(): raise ValueError('输出不能覆盖原文件。')
        destination.parent.mkdir(parents=True,exist_ok=True)
        created=False
        try:
            with destination.open('xb') as f:created=True;f.write(data)
        except Exception:
            if created:destination.unlink(missing_ok=True)
            raise
    return counts

def process_file(source,mapping,destination=None,encoding_choice="auto"):
    suffix=Path(source).suffix.lower()
    if suffix=='.docx':return process_docx(source,mapping,destination)
    if suffix=='.txt':return process_txt(source,mapping,destination,encoding_choice)
    raise ValueError('此版本支持 DOCX 和 TXT；PDF 暂不支持直接替换。')



