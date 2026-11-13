#!/usr/bin/env python3
"""Read-only vendor_boot fragment and newc archive inspection, no extraction paths trusted."""
import argparse,gzip,hashlib,json,pathlib,struct,subprocess
p=argparse.ArgumentParser();p.add_argument('image');p.add_argument('--output',required=True);a=p.parse_args()
b=pathlib.Path(a.image).read_bytes();assert b[:8]==b'VNDRBOOT'
v,pg=struct.unpack_from('<II',b,8);assert v==4
hs,ds=struct.unpack_from('<II',b,2096);rs=struct.unpack_from('<I',b,24)[0]
ts,n,es,bs=struct.unpack_from('<4I',b,2112)
align=lambda x:(x+pg-1)//pg*pg
ro=align(hs);to=ro+align(rs)+align(ds)
def cpio(data):
 out=[];i=0
 while i+110<=len(data):
  assert data[i:i+6] in (b'070701',b'070702'), ('bad cpio',i)
  f=[int(data[i+6+j*8:i+14+j*8],16) for j in range(13)]
  mode,size,ns=f[1],f[6],f[11];name=data[i+110:i+110+ns-1].decode(errors='replace');start=(i+110+ns+3)&~3
  if name=='TRAILER!!!':break
  value=data[start:start+size];assert len(value)==size
  row={'name':name,'mode':oct(mode),'bytes':size}
  if value[:4]==b'\x7fELF':row['elf']={'class':value[4],'machine':struct.unpack_from('<H',value,18)[0]}
  if name.endswith('recovery.fstab') or name.endswith('init.recovery.rc'):row['text']=value.decode(errors='replace')
  if name.endswith('ui.xml'):row['sha256']=hashlib.sha256(value).hexdigest()
  out.append(row);i=(start+size+3)&~3
 return out
fr=[]
for k in range(n):
 off=to+k*es;size,offset,kind=struct.unpack_from('<III',b,off);assert offset+size<=rs
 name=b[off+12:off+44].split(b'\0')[0].decode();data=b[ro+offset:ro+offset+size]
 if data[:2]==b'\x1f\x8b':decoded=gzip.decompress(data)
 elif data[:4] in (b'\x02\x21\x4c\x18',b'\x04\x22\x4d\x18'):decoded=subprocess.run(['lz4','-d','-c'],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
 elif data[:6] in (b'070701',b'070702'):decoded=data
 else:raise ValueError('Unknown compression '+data[:8].hex())
 members=cpio(decoded);fr.append({'name':name,'type':kind,'bytes':size,'sha256':hashlib.sha256(data).hexdigest(),'members':members})
r={'image':a.image,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'fragments':fr}
pathlib.Path(a.output).write_text(json.dumps(r,indent=2)+'\n')
for f in fr:
 print(f['name'],f['type'],f['bytes'],'members',len(f['members']))
 for x in f['members']:
  if x.get('elf') or x['name'].endswith(('ui.xml','recovery.fstab','init.recovery.rc')):print(x['name'],x.get('elf'),x['bytes'])
