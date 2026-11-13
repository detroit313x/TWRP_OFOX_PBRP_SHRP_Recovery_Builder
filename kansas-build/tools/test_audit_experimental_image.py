#!/usr/bin/env python3
"""Synthetic audit tests, not a recovery image or evidence of device support."""
import json,pathlib,struct,subprocess,tempfile,unittest
HERE=pathlib.Path(__file__).resolve().parent
PAGE=4096
al=lambda x:(x+PAGE-1)//PAGE*PAGE
def cpio(files):
 out=bytearray()
 for name,data in list(files.items())+[('TRAILER!!!',b'')]:
  n=name.encode()+b'\0';fields=[1,0o100755,0,0,1,0,len(data),0,0,0,0,len(n),0]
  out.extend(b'070701'+b''.join(f'{v:08x}'.encode() for v in fields)+n)
  out.extend(b'\0'*((-len(out))%4));out.extend(data);out.extend(b'\0'*((-len(out))%4))
 return bytes(out)
def image(frags):
 h=bytearray(PAGE);h[:8]=b'VNDRBOOT'
 rd=b''.join(data for _,_,data in frags);dtb=b'reference_dtb';table=bytearray();off=0
 struct.pack_into('<II',h,8,4,PAGE);struct.pack_into('<I',h,24,len(rd));struct.pack_into('<II',h,2096,2128,len(dtb));struct.pack_into('<4I',h,2112,len(frags)*108,len(frags),108,0)
 for name,typ,data in frags:
  row=bytearray(108);struct.pack_into('<III',row,0,len(data),off,typ);row[12:12+len(name)]=name.encode();table.extend(row);off+=len(data)
 return bytes(h)+rd+b'\0'*(al(len(rd))-len(rd))+dtb+b'\0'*(al(len(dtb))-len(dtb))+bytes(table)+b'\0'*(al(len(table))-len(table))
class Tests(unittest.TestCase):
 def run_audit(self,variant):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);stock=cpio({'stock.txt':b'preserved'})
   ref=image([('platform',1,stock)]);ref+=b'\0'*(67108864-len(ref));(d/'ref.img').write_bytes(ref)
   elf=bytearray(64);elf[:6]=b'\x7fELF\x02\x01';struct.pack_into('<H',elf,18,183 if variant!='wrong_arch' else 62)
   files={'system/bin/recovery':bytes(elf),'twres/ui.xml':b'<recovery/>','system/etc/recovery.fstab':b'/data f2fs /dev/block/by-name/userdata\n'}
   if variant=='no_ui':del files['twres/ui.xml']
   if variant=='invented_partition':files['system/etc/recovery.fstab']+=b'/cache ext4 /dev/block/by-name/cache\n'
   if variant=='changed_stock':stock=cpio({'stock.txt':b'changed'})
   data=image([('platform',1,stock),('recovery',2,cpio(files))]);(d/'out.img').write_bytes(data)
   r=subprocess.run(['python3',str(HERE/'audit_experimental_image.py'),str(d/'out.img'),'--reference',str(d/'ref.img'),'--output',str(d/'report.json')],capture_output=True,text=True)
   report=json.loads((d/'report.json').read_text());return r.returncode,report
 def test_valid_synthetic(self):self.assertEqual(self.run_audit('valid')[0],0)
 def test_wrong_arch(self):self.assertFalse(self.run_audit('wrong_arch')[1]['checks']['aarch64_recovery'])
 def test_missing_ui(self):self.assertFalse(self.run_audit('no_ui')[1]['checks']['ui_resources_present'])
 def test_changed_stock(self):self.assertFalse(self.run_audit('changed_stock')[1]['checks']['stock_fragments_preserved'])
 def test_invented_partition(self):self.assertFalse(self.run_audit('invented_partition')[1]['checks']['fstab_no_invented_cache_or_recovery'])
if __name__=='__main__':unittest.main(verbosity=2)
