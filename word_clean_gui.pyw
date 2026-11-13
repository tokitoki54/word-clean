from pathlib import Path
from collections import Counter
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading, queue, hashlib, uuid, csv, os, sys
from word_clean_core import load_mapping, process_docx, process_file
from word_clean_history import append_history, read_history

BASE=Path(sys.executable).resolve().parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parent
DEFAULT_PATH=BASE/'默认字表_新旧字形_v6.csv'
DEFAULT_SHA256='05b2cd07ce887d74da0ffe36389dde22a655b120db71c53cb70d18fb7aedd4a4'

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def is_reviewed_default(path):
    try:return Path(path).resolve()==DEFAULT_PATH.resolve() and digest(path)==DEFAULT_SHA256
    except OSError:return False

def mapping_label(path):
    if is_reviewed_default(path):return '新旧字形160条（项目逐项审阅）'
    if Path(path).resolve()==DEFAULT_PATH.resolve() and not Path(path).exists():
        return '默认字表缺失，请点击“选择”指定字表；不会回退历史表。'
    return '历史 / 自选字表（待核对范围）'

class App:
    def __init__(self,root):
        self.root=root; self.files=[]; self.ready=None; self.busy=False; self.events=queue.Queue(); self.last_output=None
        root.title('Word Clean · 新旧字形 · 字形统计版 2026-11-13'); root.geometry(f'{min(900,root.winfo_screenwidth()-60)}x{min(700,root.winfo_screenheight()-100)}'); root.minsize(min(700,root.winfo_screenwidth()-60),min(480,root.winfo_screenheight()-100))
        style=ttk.Style(); style.theme_use('clam'); style.configure('.',font=('Microsoft YaHei UI',10)); style.configure('Title.TLabel',font=('Microsoft YaHei UI',20,'bold'))
        # Reserve the action area before the expandable content, including at high DPI.
        self.buttons=[]
        self.action_bar=ttk.Frame(root,padding=(24,8,24,12));self.action_bar.pack(side='bottom',fill='x')
        actions=ttk.Frame(self.action_bar);actions.pack(fill='x')
        self.preview=self.button(actions,'1  预览替换',lambda:self.run(False));self.preview.pack(side='left')
        self.convert=self.button(actions,'2  转换并另存',lambda:self.run(True));self.convert.pack(side='left',padx=8);self.convert.state(['disabled'])
        self.button(actions,'打开输出文件夹',self.open_output).pack(side='right')
        self.status=tk.StringVar(value='添加文件后，点“1 预览替换”查看替换数量，再转换另存。')
        ttk.Label(self.action_bar,textvariable=self.status,wraplength=650).pack(anchor='w',pady=(8,0))
        box=ttk.Frame(root,padding=(24,16,24,0)); box.pack(fill='both',expand=True)
        ttk.Label(box,text='Word Clean',style='Title.TLabel').pack(anchor='w')
        ttk.Label(box,text='仅执行当前字表。先核对规则、预览，再另存；原文稿保持不变。').pack(anchor='w',pady=(4,18))
        self.map_path=tk.StringVar(value=str(DEFAULT_PATH))
        self.out_path=tk.StringVar(value=str(BASE/'output'))
        for title,var,command in [('字表',self.map_path,self.choose_map),('输出到',self.out_path,self.choose_output)]:
            row=ttk.Frame(box); row.pack(fill='x',pady=4)
            ttk.Label(row,text=title,width=8).pack(side='left'); ttk.Entry(row,textvariable=var,state='readonly').pack(side='left',fill='x',expand=True,padx=8)
            self.button(row,'选择',command).pack(side='left')
        self.map_info=tk.StringVar(); ttk.Label(box,textvariable=self.map_info,wraplength=820).pack(anchor='w',pady=4); self.update_map_info()
        row=ttk.Frame(box); row.pack(fill='x',pady=(16,8))
        self.button(row,'添加 DOCX / TXT',self.add_files).pack(side='left')
        self.button(row,'添加文件夹',self.add_folder).pack(side='left',padx=8)
        self.button(row,'清空',self.clear).pack(side='left')
        self.button(row,'查看 / 编辑字表',self.edit_mapping).pack(side='right')
        self.button(row,'处理记录',self.show_history).pack(side='right',padx=8)
        encoding_row=ttk.Frame(box); encoding_row.pack(fill='x',pady=(0,8))
        ttk.Label(encoding_row,text='TXT 编码').pack(side='left')
        self.encoding=tk.StringVar(value='自动：UTF-8 / BOM')
        self.encoding_box=ttk.Combobox(encoding_row,textvariable=self.encoding,values=['自动：UTF-8 / BOM','GB18030（明确指定）'],state='readonly',width=28)
        self.encoding_box.pack(side='left',padx=8); self.encoding_box.bind('<<ComboboxSelected>>',lambda e:self.invalidate())
        list_box=ttk.Frame(box);list_box.pack(fill='x')
        self.tree=ttk.Treeview(list_box,columns=('file','result'),show='headings',height=3)
        self.tree.heading('file',text='文件'); self.tree.heading('result',text='预览 / 处理结果'); self.tree.column('file',width=520); self.tree.column('result',width=220)
        file_scroll=ttk.Scrollbar(list_box,orient='vertical',command=self.tree.yview);file_scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=file_scroll.set)
        self.tree.pack(fill='x',expand=True)
        ttk.Label(box,text='预览 / 转换结果').pack(anchor='w',pady=(10,4))
        result_box=ttk.Frame(box);result_box.pack(fill='both',expand=True,pady=(0,8))
        self.log=tk.Text(result_box,height=9,wrap='word',font=('Microsoft YaHei UI',10),state='disabled')
        result_scroll=ttk.Scrollbar(result_box,orient='vertical',command=self.log.yview);result_scroll.pack(side='right',fill='y');self.log.configure(yscrollcommand=result_scroll.set);self.log.pack(fill='both',expand=True)
        self.write(mapping_label(self.map_path.get())+'。仅执行当前字表，不额外启用简繁/异体转换引擎。历史或自选表请另行核对规则范围；批注、修订删除文字、图片内文字不处理。')
        root.protocol('WM_DELETE_WINDOW',self.close); self.poll_id=root.after(100,self.poll); root.bind('<Destroy>',self.on_destroy,add='+')
    def on_destroy(self,event):
        if event.widget is self.root:
            try:self.root.after_cancel(self.poll_id)
            except tk.TclError:pass
    def button(self,parent,text,command):
        b=ttk.Button(parent,text=text,command=command); self.buttons.append(b); return b
    def write(self,text):
        self.log.configure(state='normal'); self.log.insert('end',text+'\n'); self.log.see('end'); self.log.configure(state='disabled')
    def update_map_info(self):
        try:
            mapping=load_mapping(self.map_path.get()); same=sum(a==b for a,b in mapping.items()); self.map_info.set(f'{mapping_label(self.map_path.get())}：{Path(self.map_path.get()).name} | {len(mapping)} 条规则，其中 {same} 条原样项')
        except Exception as e:self.map_info.set(mapping_label(self.map_path.get())+' 字表需要检查：'+str(e))
    def invalidate(self):
        self.ready=None; self.convert.state(['disabled'])
    def choose_map(self):
        p=filedialog.askopenfilename(filetypes=[('字表','*.xlsx *.csv')],initialdir=BASE)
        if p: self.map_path.set(p); self.update_map_info(); self.invalidate()
    def choose_output(self):
        p=filedialog.askdirectory(initialdir=BASE)
        if p:self.out_path.set(p)
    def add_files(self):
        self.add(filedialog.askopenfilenames(filetypes=[('Word / 文本','*.docx *.txt')],initialdir=BASE/'input'))
    def add_folder(self):
        p=filedialog.askdirectory(initialdir=BASE/'input')
        if p:self.add(sorted(x for x in Path(p).iterdir() if x.is_file() and x.suffix.lower() in ('.docx','.txt')))
    def add(self,paths):
        for p in paths:
            p=Path(p).resolve()
            if p.suffix.lower() not in ('.docx','.txt'):
                messagebox.showinfo('不支持此格式','仅支持 DOCX 和 TXT。DOC 请先另存为 DOCX；PDF 暂不支持直接替换。');continue
            if p.name.startswith('~$') or p in self.files:continue
            self.files.append(p); self.tree.insert('','end',iid=str(len(self.files)-1),values=(str(p),'尚未预览'))
        self.invalidate(); self.status.set(f'已选择 {len(self.files)} 个文件。')
    def edit_mapping(self):
        try:mapping=load_mapping(self.map_path.get())
        except Exception as e:messagebox.showerror('字表读取失败',str(e));return
        win=tk.Toplevel(self.root);win.title('查看 / 编辑字表副本');win.geometry('560x600');win.transient(self.root);win.grab_set()
        frame=ttk.Frame(win,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='编辑后另存 CSV 副本；不会修改原始 Excel。').pack(anchor='w',pady=8)
        table=ttk.Treeview(frame,columns=('old','new'),show='headings');table.heading('old',text='旧字型');table.heading('new',text='新字形');table.pack(fill='both',expand=True)
        scroll=ttk.Scrollbar(table,orient='vertical',command=table.yview);scroll.pack(side='right',fill='y');table.configure(yscrollcommand=scroll.set)
        # Filtering changes only the view. The full mapping remains authoritative.
        search_row=ttk.Frame(frame);search_row.pack(fill='x',pady=(8,0),before=table)
        ttk.Label(search_row,text='搜索新字或旧字').pack(side='left')
        query=tk.StringVar();a=tk.StringVar();b=tk.StringVar();match_info=tk.StringVar()
        ttk.Entry(search_row,name='mapping_search',textvariable=query,width=16).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(search_row,text='清空搜索',command=lambda:query.set('')).pack(side='left')
        ttk.Label(frame,textvariable=match_info).pack(anchor='w',pady=(4,8),before=table)
        def refresh(*_):
            table.delete(*table.get_children());a.set('');b.set('')
            keyword=query.get().strip()
            shown=0
            for old,new in mapping.items():
                if not keyword or keyword in old or keyword in new:
                    table.insert('','end',values=(old,new));shown+=1
            match_info.set(f'显示 {shown} / 共 {len(mapping)} 条；另存时保存完整字表。')
        query.trace_add('write',refresh)
        refresh();row=ttk.Frame(frame);row.pack(fill='x',pady=12)
        ttk.Label(row,text='旧字').pack(side='left');ttk.Entry(row,name='old_input',textvariable=a,width=8).pack(side='left',padx=8);ttk.Label(row,text='新字').pack(side='left');ttk.Entry(row,name='new_input',textvariable=b,width=8).pack(side='left',padx=8)
        def select(event):
            chosen=table.selection()
            if chosen:
                values=table.item(chosen[0],'values');a.set(values[0]);b.set(values[1])
        table.bind('<<TreeviewSelect>>',select)
        def change():
            old,new=a.get().strip(),b.get().strip()
            if len(old)!=1 or len(new)!=1:messagebox.showerror('单字映射','每格请输入一个字。',parent=win);return
            if old in mapping and mapping[old]!=new and not messagebox.askyesno('修改映射',f'将 {old}→{mapping[old]} 改为 {old}→{new}？',parent=win):return
            mapping[old]=new;refresh()
        ttk.Button(row,text='添加 / 更新',command=change).pack(side='left')
        def remove():
            chosen=table.selection()
            if chosen:
                old=table.item(chosen[0],'values')[0]
                if messagebox.askyesno('移除映射',f'从编辑副本中移除 {old}→{mapping[old]}？',parent=win):del mapping[old];refresh()
        ttk.Button(frame,text='移除选中行',command=remove).pack(anchor='w')
        def save():
            if not mapping:messagebox.showerror('字表为空','至少保留一条映射。',parent=win);return
            path=filedialog.asksaveasfilename(parent=win,initialdir=BASE,initialfile='我的字形表.csv',defaultextension='.csv',filetypes=[('CSV 字表','*.csv')])
            if not path:return
            if Path(path).exists():messagebox.showerror('保留旧版本','请选择一个新的文件名，不覆盖已有字表。',parent=win);return
            try:
                with Path(path).open('x',encoding='utf-8-sig',newline='') as f:
                    writer=csv.writer(f);writer.writerow(['旧字型','新字形']);writer.writerows(mapping.items())
            except Exception as e:messagebox.showerror('保存失败',str(e),parent=win);return
            self.map_path.set(path);self.update_map_info();self.invalidate();self.write('已选择编辑副本：'+path);win.destroy()
        ttk.Button(frame,text='另存副本并使用',command=save).pack(anchor='e',pady=12)
    def show_history(self):
        try:records,invalid=read_history(BASE/'history.jsonl')
        except Exception as e:messagebox.showerror('记录读取失败',str(e));return
        win=tk.Toplevel(self.root);win.title('本地处理记录');win.geometry('760x420');win.transient(self.root)
        frame=ttk.Frame(win,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='只记录成功另存的文件名、时间和替换字对次数；不保存正文或完整路径。',wraplength=700).pack(anchor='w',pady=(0,8))
        note=f'共 {len(records)} 条成功处理记录。失败的转换不会记入。'
        if invalid:note+=f' 另有 {invalid} 条损坏记录已跳过，原记录文件未改动。'
        ttk.Label(frame,text=note,wraplength=700).pack(anchor='w',pady=(0,8))
        detail=tk.Text(frame,height=4,wrap='word',state='disabled');detail.pack(side='bottom',fill='x',pady=(8,0))
        table=ttk.Treeview(frame,columns=('time','name','stats'),show='headings')
        def selected(event):
            selection=table.selection()
            if selection:
                values=table.item(selection[0],'values');detail.configure(state='normal');detail.delete('1.0','end');detail.insert('end',values[2]);detail.configure(state='disabled')
        table.bind('<<TreeviewSelect>>',selected)
        for key,title,width in [('time','处理时间',185),('name','文件名',220),('stats','替换统计',290)]:table.heading(key,text=title);table.column(key,width=width)
        scroll=ttk.Scrollbar(frame,orient='vertical',command=table.yview);scroll.pack(side='right',fill='y');table.configure(yscrollcommand=scroll.set);table.pack(fill='both',expand=True)
        for r in reversed(records):
            summary='；'.join(f"{p['old']}→{p['new']} ×{p['count']}" for p in r['replacements']) or '0 处替换'
            table.insert('','end',values=(r['processed_at'],r['file_name'],summary))

    def clear(self):
        self.files=[]; self.tree.delete(*self.tree.get_children()); self.invalidate()
    def close(self):
        if self.busy:messagebox.showinfo('正在处理','请等待当前任务结束后再关闭。原文稿不会被覆盖。'); return
        self.root.destroy()
    def open_output(self):
        p=self.last_output or Path(self.out_path.get())
        if p.exists():os.startfile(str(p))
        else:messagebox.showinfo('输出文件夹','转换成功后会创建输出文件夹。')
    def run(self,convert):
        self.update_map_info()
        if not self.files:messagebox.showinfo('添加文件','请先添加 .docx 或 .txt 文件。'); return
        if convert and not self.ready:messagebox.showinfo('先预览','请先预览替换。');return
        if convert and not messagebox.askyesno('转换并另存',f'{mapping_label(self.map_path.get())}。仅按当前规则处理；历史或自选表请先核对范围。\n将处理 {len(self.files)} 个文档，在输出位置新建独立批次文件夹。\n不会覆盖原文稿或已有结果。\n\n继续？'):return
        self.busy=True
        for b in self.buttons:b.state(['disabled'])
        self.encoding_box.configure(state='disabled')
        self.status.set('正在处理，请稍候…')
        files=list(self.files); mp=Path(self.map_path.get()); out=Path(self.out_path.get()); ready=self.ready
        encoding_choice='gb18030' if self.encoding.get().startswith('GB18030') else 'auto'
        def worker():
            completed=[]
            try:
                mapping=load_mapping(mp); fingerprint=digest(mp); hashes={str(p):digest(p) for p in files}
                if convert and ready!=(fingerprint,hashes,encoding_choice):raise ValueError('字表或原文件已改变，请重新预览后转换。')
                batch=None
                if convert:
                    batch=out/('WordClean_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]); batch.mkdir(parents=True,exist_ok=False)
                total=Counter(); errors=0; history_errors=0
                for i,p in enumerate(files):
                    try:
                        dest=batch/(f'{i+1:03d}_'+p.stem+'_字形已转换'+p.suffix.lower()) if convert else None
                        counts=process_file(p,mapping,dest,encoding_choice); total.update(counts)
                        if convert:
                            completed.append(i)
                            try:append_history(BASE/'history.jsonl',p,mapping,counts)
                            except Exception:history_errors+=1
                        msg=f'{sum(counts.values())} 处替换'+('，已另存' if convert else '')
                        self.events.put(('row',i,msg))
                    except Exception as e:
                        errors+=1; self.events.put(('row',i,'失败：'+str(e)))
                if batch:
                    with (batch/'字形统计.csv').open('x',encoding='utf-8-sig',newline='') as f:
                        writer=csv.writer(f); writer.writerow(['旧字型','新字形','次数']); writer.writerows((a,mapping[a],n) for a,n in total.most_common())
                summary=f'{"转换完成" if convert else "预览完成"}：{len(files)-errors} 个成功，{errors} 个失败，共 {sum(total.values())} 处。'
                if history_errors:summary+=f' {history_errors} 个文件已另存，但本地处理记录写入失败。'
                detail='；'.join(f'{a}→{mapping[a]} ×{n}' for a,n in total.most_common()) or '未发现需要替换的字形。'
                self.events.put(('done',summary,detail,None if errors else (fingerprint,hashes,encoding_choice),batch,completed))
            except Exception as e:self.events.put(('error',str(e),completed))
        threading.Thread(target=worker,daemon=True).start()
    def remove_completed(self,indices):
        removed=set(indices)
        if not removed:return
        remaining=[(p,self.tree.set(str(i),'result')) for i,p in enumerate(self.files) if i not in removed]
        self.tree.delete(*self.tree.get_children());self.files=[p for p,_ in remaining]
        for i,(p,result) in enumerate(remaining):self.tree.insert('','end',iid=str(i),values=(str(p),result))
        self.invalidate()

    def poll(self):
        while not self.events.empty():
            e=self.events.get()
            if e[0]=='row':self.tree.set(str(e[1]),'result',e[2])
            else:
                self.busy=False; self.encoding_box.configure(state="readonly")
                for b in self.buttons:b.state(['!disabled'])
                if e[0]=='error':self.ready=None; self.write('未完成：'+e[1]); self.status.set('请检查提示后重试。'); messagebox.showerror('无法完成',e[1])
                else:
                    self.ready=e[3]; self.last_output=e[4] or self.last_output; self.status.set(e[1]); self.write(e[1]+'\n'+e[2])
                    if e[4]:self.write('结果保存在：'+str(e[4])+'\n点击“打开输出文件夹”查看另存文稿和字形统计.csv。')
                completed=e[2] if e[0]=='error' else e[5]
                self.remove_completed(completed)
                if completed:self.write(f'已从待处理列表移除 {len(completed)} 个成功另存文件；剩余 {len(self.files)} 个。')
                if not self.ready:self.convert.state(['disabled'])
        self.poll_id=self.root.after(100,self.poll)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--self-test':
        from word_clean_selftest import run_selftest
        run_selftest(sys.modules[__name__],Path(sys.argv[2]))
    else:
        root=tk.Tk(); App(root); root.mainloop()



