#!/usr/bin/env python3
"""Static audit of an experimental Kansas vendor_boot. Never proves bootability."""
import argparse, gzip, hashlib, io, json, pathlib, struct, subprocess, zipfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('image');p.add_argument('--reference',required=True);p.add_argument('--output',required=True)
a=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
def inspect(path):
 b=pathlib.Path(path).read_bytes()
 if len(b)<2128 or b[:8]!=b'VNDRBOOT':raise ValueError('Missing vendor_boot v4 header')
 v,pg=struct.unpack_from('<II',b,8)
 if v!=4 or pg!=4096:raise ValueError('Expected v4/4096')
 rs=struct.unpack_from('<I',b,24)[0];hs,ds=struct.unpack_from('<II',b,2096)
 ts,n,es,bs=struct.unpack_from('<4I',b,2112)
 if hs<2128 or es<108 or ts!=n*es:raise ValueError('Invalid header/table')
 al=lambda x:(x+pg-1)//pg*pg
 ro=al(hs);do=ro+al(rs);to=do+al(ds);bo=to+al(ts)
 if bo+al(bs)>len(b):raise ValueError('Truncated image')
 rows=[];ranges=[]
 for k in range(n):
  e=b[to+k*es:to+(k+1)*es];sz,off,typ=struct.unpack_from('<3I',e)
  if off+sz>rs:raise ValueError('Fragment bounds')
  ranges.append((off,off+sz));data=b[ro+off:ro+off+sz]
  rows.append({'name':e[12:44].split(b'\0')[0].decode(errors='replace'),'type':typ,'offset':off,'bytes':sz,'sha256':sha(data),'board_id_hex':e[44:108].hex(),'data':data})
 ranges.sort()
 if ranges and (ranges[0][0]!=0 or ranges[-1][1]!=rs or any(x[1]!=y[0] for x,y in zip(ranges,ranges[1:]))):raise ValueError('Ramdisk gaps/overlaps')
 return {'bytes':len(b),'sha256':sha(b),'version':v,'page_size':pg,'dtb_sha256':sha(b[do:do+ds]),'dtb_bytes':ds,'bootconfig_sha256':sha(b[bo:bo+bs]),'fragments':rows}
def archive(data):
 if data[:2]==b'\x1f\x8b':data=gzip.decompress(data)
 elif data[:4] in (b'\x02\x21\x4c\x18',b'\x04\x22\x4d\x18'):data=subprocess.run(['lz4','-d','-c'],input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout
 out={};i=0;trailer=False
 while i+110<=len(data):
  if data[i:i+6] not in (b'070701',b'070702'):raise ValueError('Bad newc header')
  f=[int(data[i+6+j*8:i+14+j*8],16) for j in range(13)]
  mode,size,ns=f[1],f[6],f[11]
  if ns<1 or i+110+ns>len(data):raise ValueError('Bad filename length')
  raw=data[i+110:i+110+ns]
  if raw[-1:]!=b'\0':raise ValueError('Missing filename terminator')
  name=raw[:-1].decode(errors='replace').removeprefix('./');start=(i+110+ns+3)&~3
  if start+size>len(data):raise ValueError('Truncated member')
  if name=='TRAILER!!!':trailer=True;break
  out[name]={'mode':mode,'data':data[start:start+size]};i=(start+size+3)&~3
 if not trailer:raise ValueError('Missing archive trailer')
 return out
r=inspect(a.image);ref=inspect(a.reference)
checks={'partition_bound':r['bytes']<=ref['bytes']==67108864,'dtb_preserved':r['dtb_sha256']==ref['dtb_sha256'],'bootconfig_preserved':r['bootconfig_sha256']==ref['bootconfig_sha256'],'stock_fragments_preserved':all(any((x['sha256'],x['type'],x['board_id_hex'])==(y['sha256'],y['type'],y['board_id_hex']) for y in r['fragments']) for x in ref['fragments']),'recovery_exists':any(x['type']==2 for x in r['fragments'])}
allfiles={};collisions=[];details=[];recovery={}
for frag in r['fragments']:
 members=archive(frag['data'])
 for name,val in members.items():
  if name in allfiles and val['data']!=allfiles[name]['data']:collisions.append({'name':name,'overwritten_by':frag['name']})
  allfiles[name]=val
 if frag['type']==2:recovery.update(members)
 details.append({**{k:v for k,v in frag.items() if k!='data'},'member_count':len(members)})
binary=next((recovery[n]['data'] for n in ('system/bin/recovery','sbin/recovery') if n in recovery),b'')
elf={}
if binary[:4]==b'\x7fELF' and len(binary)>=64:
 elf={'class':binary[4],'byte_order':binary[5],'machine':struct.unpack_from('<H',binary,18)[0],'bytes':len(binary),'sha256':sha(binary)}
checks['aarch64_recovery']=elf.get('class')==2 and elf.get('machine')==183
ui=[n for n in recovery if n.startswith(('twres/','res/')) and (n.endswith('ui.xml') or n.endswith('ui.zip'))]
checks['ui_resources_present']=bool(ui)
fstabs={n:v['data'].decode(errors='replace') for n,v in recovery.items() if n.endswith('recovery.fstab')}
checks['fstab_present']=bool(fstabs)
checks['fstab_no_invented_cache_or_recovery']=bool(fstabs) and all(not any(line.split() and line.split()[0] in ('/cache','/recovery') for line in text.splitlines() if not line.lstrip().startswith('#')) for text in fstabs.values())
report={k:v for k,v in r.items() if k!='fragments'}
report.update({'checks':checks,'fragments':details,'recovery_elf':elf,'ui_files':ui,'fstabs':fstabs,'collision_count':len(collisions),'collisions':collisions,'limitations':['Static inspection only; no boot, display, touch, mounting or decryption tests.','Owner XT variant and installed firmware are unknown. Reference firmware is XT2513V Tracfone W1VKS36H.9-12-9-8-3.','Bootloader fragment selection and generic init_boot precedence can differ from image table ordering.']})
pathlib.Path(a.output).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':checks,'sha256':r['sha256'],'bytes':r['bytes'],'recovery_elf':elf,'ui_files':ui,'fstabs':fstabs,'collision_count':len(collisions)},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
