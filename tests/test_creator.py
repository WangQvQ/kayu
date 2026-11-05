import sys,tempfile,importlib.util,json,copy,base64,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parents[1]/'skills/kayu-card-creator/scripts/kayu.py'
spec=importlib.util.spec_from_file_location('kayu',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
with tempfile.TemporaryDirectory() as d:
 root=Path(d)
 Image.new('RGB',(320,480),'#172437').save(root/'background.png')
 im=Image.new('RGBA',(320,480));ImageDraw.Draw(im).ellipse((100,60,220,430),fill='#dbe8ff');im.save(root/'subject.png')
 for mode,assets in [('spatial',{'background':'background.png','subject':'subject.png'}),('flat',{'artwork':'background.png'}),('lenticular',{'imageA':'background.png','imageB':'background.png'})]:
  cfg=root/(mode+'.json');cfg.write_text(json.dumps({'title':'Moonlit Letters','creator':'QA','assets':assets}))
  m.make(cfg,root/(mode+'.shancard'))
  checks.append(mode+' card builds and validates')
 m.pack([root/'spatial.shancard',root/'flat.shancard',root/'lenticular.shancard'],root/'set.kayu','A little universe','QA','')
 pack=m.load_json(root/'set.kayu');m.check_pack(pack);checks.append('multi-card pack builds and validates')
 for desc,mutate in [
  ('duplicate ID',lambda v:v['cards'].append(v['cards'][0])),
  ('hash mismatch',lambda v:v['resources'].__setitem__(next(iter(v['resources'])),base64.b64encode(b'broken').decode())),
  ('unreferenced resource',lambda v:v['resources'].__setitem__(hashlib.sha256(b'extra').hexdigest(),base64.b64encode(b'extra').decode())),
  ('message too long',lambda v:v.__setitem__('message','x'*301)),
  ('unsupported pack version',lambda v:v.__setitem__('version',2))]:
  bad=copy.deepcopy(pack);mutate(bad)
  try:m.check_pack(bad)
  except (ValueError,KeyError): checks.append('rejects '+desc)
  else:raise AssertionError('Accepted '+desc)
 try:m.pack([root/'flat.shancard']*2,root/'bad.kayu','x','QA','')
 except ValueError:checks.append('pack command rejects duplicate works')
 else:raise AssertionError('Accepted duplicate works')
 try:m.make(root/'spatial.json',root/'spatial.shancard')
 except FileExistsError:checks.append('preserves existing output')
 else:raise AssertionError('Overwrote output')
print(json.dumps({'passed':len(checks),'checks':checks},indent=2))
