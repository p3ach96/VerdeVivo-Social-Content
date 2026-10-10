#!/usr/bin/env python3
"""Isolated, deterministic Higgsfield -> Social Content import; never modifies Engine."""
import datetime, hashlib, io, json, pathlib, re, struct, time, urllib.request, zlib
from collections import Counter
from zoneinfo import ZoneInfo
from PIL import Image, __version__ as pillow_version

ROOT=pathlib.Path.cwd()
CONFIG=json.loads((ROOT/'.editorial-bridge-20261010/config.json').read_text())
previous=CONFIG['expectedBaseIndex']
index_file=ROOT/'content/index.json'
assert json.loads(index_file.read_text())==previous, 'STOP: index changed from approved baseline'
assert len(CONFIG['items'])==8 and len(set(x['id'] for x in CONFIG['items']))==8
expected_delivery={
'2026-10-20-roots-need-space-too':'d8af26cf0d85093726452ffe6e116028483d91c98dcfef11fa265bd337c6c0d2',
'2026-10-23-light-changes-everything':'3f1b83850e89405c299a99572fb2eaa98d6d7d169add005b005bbf34b9189540',
'2026-10-27-healthy-plants-are-rarely-perfect':'ddd998a4acdf35f4399865f9c1a8537d5f2d18f2349e8f5c2a4380dcc15726a5',
'2026-10-30-new-leaves-tell-a-story':'d0c9373d0d9f58a20635b1eba3b4e5845c468fc93055015247d4b3749251547e',
'2026-11-03-repotting-is-a-reset-not-a-setback':'548d3f495ecbbfde902aea1b0c18f617f9718e2c8ecf9f2255343e3aa3543f9d',
'2026-11-06-small-pests-early-signs-big-difference':'d2e1d9eaa9f51101ac7c49890521575920af55321f060add810b23e862d9158f',
'2026-11-10-consistency-beats-intensity':'916fdc54307dee392a379bc449351f0588c2ffcde045be8cc593e310a6063c81',
'2026-11-13-a-happy-plant-fits-its-space':'244ff1f75ed4cd0c9568348038d2b7f549353481686e0769ec7954d28cb44cfe',
}
def sha(data): return hashlib.sha256(data).hexdigest()
def chunks(data):
    assert data.startswith(b'\x89PNG\r\n\x1a\n')
    pos=8; out=[]
    while pos<len(data):
        n=struct.unpack('>I', data[pos:pos+4])[0]
        tag=data[pos+4:pos+8]; payload=data[pos+8:pos+8+n]
        assert pos+12+n<=len(data)
        out.append((tag,payload))
        pos+=12+n
        if tag==b'IEND': break
    assert pos==len(data)
    return out
def serialize(parts):
    out=bytearray(b'\x89PNG\r\n\x1a\n')
    for typ,payload in parts:
        out.extend(struct.pack('>I',len(payload))+typ+payload+struct.pack('>I',zlib.crc32(typ+payload)&0xffffffff))
    return bytes(out)
def lossless(data):
    src=chunks(data)
    inp=Image.open(io.BytesIO(data))
    buf=io.BytesIO()
    inp.save(buf,format='PNG',optimize=True,compress_level=9)
    compressed=b''.join(p for typ,p in chunks(buf.getvalue()) if typ==b'IDAT')
    result=[]; inserted=False
    for typ,p in src:
        if typ==b'IDAT':
            if not inserted:
                result.append((b'IDAT',compressed)); inserted=True
        else:
            result.append((typ,p))
    delivery=serialize(result)
    assert Image.open(io.BytesIO(delivery)).tobytes()==inp.tobytes()
    assert [(typ,p) for typ,p in src if typ!=b'IDAT']==[(typ,p) for typ,p in chunks(delivery) if typ!=b'IDAT']
    return delivery
def download(url):
    assert url.startswith('https://d2ol7oe51mr4n9.cloudfront.net/user_3IKUgIPJVJaS3AlVNLw6EYWWGJC/') and url.endswith('.png')
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'VerdeVivo-Editorial-Import/1.0'})
            with urllib.request.urlopen(request,timeout=35) as resp:
                assert resp.status==200
                source=resp.read(12_000_001)
                assert 0<len(source)<=12_000_000
                return source
        except Exception:
            if attempt==2: raise
            time.sleep(2*(attempt+1))

records=[]; weekly=Counter(); ids=[]
for item in CONFIG['items']:
    post_id=item['id']; m=item['manifest']; dest=ROOT/'content'/post_id
    assert re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}',post_id)
    assert post_id==m['id'] and not dest.exists(), 'Duplicate or inconsistent post ID'
    assert m['status']=='approved' and m['version']==1 and m['language']=='en' and m['image']=='social.png'
    assert m['channels']==['bluesky','mastodon','youtube','instagram']
    assert len(m['caption']+' '+' '.join('#'+h for h in m['hashtags']))<300
    local=datetime.datetime.fromisoformat(m['publishAt']).astimezone(ZoneInfo('Europe/Rome'))
    assert local.strftime('%Y-%m-%d')==post_id[:10] and local.weekday() in (1,4) and (local.hour,local.minute)==(18,0)
    assert datetime.datetime.fromisoformat(m['publishAt'])==local
    weekly[local.strftime('%G-W%V')]+=1
    original=download(item['sourceUrl'])
    assert sha(original)==item['originalSha256'], 'Higgsfield source SHA mismatch'
    image=Image.open(io.BytesIO(original))
    assert image.format=='PNG' and image.size==(1254,1254) and image.mode=='RGB'
    if item['resize']:
        n=item['resize']
        assert n in (1150,1180,1200)
        buf=io.BytesIO()
        image.resize((n,n),Image.Resampling.LANCZOS).save(buf,format='PNG',optimize=True,compress_level=9)
        delivery=buf.getvalue()
        method='resize_lanczos_approved'
    else:
        delivery=lossless(original)
        method='lossless_recompress'
    delivered=Image.open(io.BytesIO(delivery))
    assert delivered.size==(item['resize'] or 1254,)*2
    assert 0<len(delivery)<=2_000_000, f'{post_id}: PNG over Bluesky limit'
    expected_hash=expected_delivery[post_id]
    got_hash=sha(delivery)
    # The pinned Pillow release should match local prepared art byte-for-byte. Fail closed otherwise.
    assert got_hash==expected_hash, f'{post_id}: approved artwork byte mismatch {got_hash}'
    dest.mkdir(parents=True)
    (dest/'social.png').write_bytes(delivery)
    (dest/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    ids.append(post_id)
    records.append({'id':post_id,'publishAt':m['publishAt'],'bytes':len(delivery),'sha256':got_hash,'width':delivered.width,'height':delivered.height,'method':method})
    print('VERIFIED',post_id,len(delivery),got_hash,flush=True)
assert weekly=={'2026-W43':2,'2026-W44':2,'2026-W45':2,'2026-W46':2}, weekly
index_file.write_text(json.dumps(previous+ids,indent=2)+'\n')
ops=ROOT/'ops/editorial-validation-20261010.json'
assert not ops.exists()
ops.write_text(json.dumps({'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':'Higgsfield-uploaded approved artwork','pillowVersion':pillow_version,'imageHashesMatchLocalPreparedPack':True,'resizedDeliveryApprovedByUser':True,'scheduledPosts':8,'weeks':dict(weekly),'channels':['bluesky','mastodon','youtube','instagram'],'posts':records},indent=2)+'\n')
print('EDITORIAL_STAGE_VERIFIED posts=8 png=8 index=16 two_per_week=True',flush=True)
