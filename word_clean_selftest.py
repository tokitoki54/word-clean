"""Explicit hidden smoke test for the frozen application, with synthetic data only."""
from pathlib import Path
import tempfile,time,json,csv,zipfile,sys,traceback

def run_selftest(gui,report_path):
    root=None
    try:
        reviewed=gui.DEFAULT_PATH
        mapping=gui.load_mapping(reviewed)
        assert len(mapping)==122
        with tempfile.TemporaryDirectory(prefix='wordclean_exe_test_') as td:
            gui.BASE=Path(td)
            root=gui.tk.Tk();root.withdraw();app=gui.App(root)
            sample=Path(td)/'synthetic.txt';original=''.join(mapping)+'\r\n晋晉為爲骨髓滑'
            sample.write_bytes(original.encode('utf-8-sig'))
            from word_clean_core import W
            docx=Path(td)/'synthetic.docx'
            with zipfile.ZipFile(docx,'w') as z:z.writestr('word/document.xml',f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>{original}</w:t></w:r></w:p></w:body></w:document>')
            before={p:p.read_bytes() for p in (sample,docx)}
            app.add([sample,docx]);gui.messagebox.askyesno=lambda *a,**kw:True
            def fail_dialog(*a,**kw):raise AssertionError(str(a))
            gui.messagebox.showerror=fail_dialog
            def wait():
                limit=time.monotonic()+30
                while app.busy and time.monotonic()<limit:root.update();time.sleep(.01)
                assert not app.busy
            app.run(False);wait();assert app.ready and len(app.files)==2
            app.run(True);wait();assert app.last_output and not app.files
            files=list(app.last_output.iterdir());assert len(files)==3
            assert {p.name for p in files if p.suffix=='.csv'}=={'字形统计.csv'}
            with (app.last_output/'字形统计.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
            assert len(rows)==122 and all(int(r['次数'])==2 for r in rows)
            assert all(p.read_bytes()==v for p,v in before.items())
            assert len(gui.read_history(Path(td)/'history.jsonl')[0])==2
            expected=''.join(mapping.get(c,c) for c in original)
            assert next(app.last_output.glob('*.txt')).read_bytes()==expected.encode('utf-8-sig')
            root.destroy();root=None
            result={'passed':True,'frozen':bool(getattr(sys,'frozen',False)),'files':2,'pairs':122,'replacements':244,'only_stats_csv':True,'originals_unchanged':True,'successful_items_removed':True,'executable':sys.executable}
    except Exception:
        result={'passed':False,'error':traceback.format_exc()}
    finally:
        if root is not None:root.destroy()
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if not result['passed']:raise SystemExit(1)