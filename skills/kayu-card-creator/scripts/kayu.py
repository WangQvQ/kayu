#!/usr/bin/env python3
"""Portable KAYU authoring tools. Python 3.9+, Pillow; no App checkout required."""
import argparse
import base64
import hashlib
import io
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZE = (1320, 2000)
LIMIT = 40 * 1024 * 1024
ROLES = {'artwork', 'background', 'subject', 'midground', 'effects', 'foreground', 'text', 'back', 'imageA', 'imageB', 'lineart'}
ALPHA_ROLES = {'subject', 'midground', 'effects', 'foreground', 'text'}
MODEL = os.environ.get('ARK_MODEL', '')
ENDPOINT = 'https://ark.cn-beijing.volces.com/api/v3/images/generations'


def load_json(path):
    path = Path(path)
    if path.stat().st_size > 240 * 1024 * 1024:
        raise ValueError('Input JSON exceeds 240 MB')
    return json.loads(path.read_text(encoding='utf-8'),
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite JSON number')))



def image(path):
    if Path(path).stat().st_size > LIMIT:
        raise ValueError('Source image exceeds 40 MB')
    with Image.open(path) as opened:
        if opened.width * opened.height > 36_000_000:
            raise ValueError('Source image exceeds 36 million pixels')
        return ImageOps.exif_transpose(opened).convert('RGBA')


def png(img):
    stream = io.BytesIO()
    img.save(stream, format='PNG', optimize=True)
    return stream.getvalue()


def has_alpha(img):
    low, high = img.getchannel('A').resize((64,96), Image.Resampling.NEAREST).getextrema()
    return low < 250 and high > 8


def fit(img, size=SIZE, fill=False):
    scale = (max if fill else min)(size[0] / img.width, size[1] / img.height)
    resized = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.Resampling.LANCZOS)
    return resized, ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2)


def plate(img):
    output = Image.new('RGBA', SIZE)
    resized, position = fit(img)
    output.alpha_composite(resized, position)
    return output


def background(img):
    output = Image.new('RGBA', SIZE, '#172437')
    cover, position = fit(img, fill=True)
    output.alpha_composite(cover, position)
    complete, position = fit(img)
    output.alpha_composite(complete, position)
    return output.convert('RGB').convert('RGBA')


def save_json(path, value, force=False):
    path = Path(path)
    encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
    cap = 240 * 1024 * 1024 if value.get('format') == 'app.shancard.pack' else 60 * 1024 * 1024
    if len(encoded) > cap:
        raise ValueError('Encoded file exceeds the App file limit')
    if path.exists() and not force:
        raise FileExistsError(f'{path} exists; choose another output or use --force')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_bytes(encoded)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def check_card(package):
    if package.get('format') != 'app.shancard.card' or package.get('version') != 1:
        raise ValueError('Unsupported card format')
    card, resources = package['card'], package['resources']
    if not resources or set(resources) != set(card['assets']) or not set(resources) <= ROLES:
        raise ValueError('Asset roles do not match resources')
    if card.get('kind') not in ('holographic', 'lenticular') or card.get('rarity') not in ('自制', 'SR', 'SSR', 'UR'):
        raise ValueError('Invalid kind or rarity')
    lengths = {'id':160, 'title':100, 'subtitle':300, 'creator':100, 'story':10000, 'series':120, 'number':80, 'accent':32}
    for field, maximum in lengths.items():
        if not isinstance(card.get(field), str) or len(card[field]) > maximum:
            raise ValueError('Invalid text field: ' + field)
    if not card['title'].strip() or not card['id'] or len(card.get('tags', [])) > 20 or any(not isinstance(t,str) or len(t)>100 for t in card['tags']):
        raise ValueError('Missing title/id or invalid tags')
    if type(card.get('finish',3)) is not int or not 0 <= card.get('finish',3) <= 10:
        raise ValueError('Invalid surface finish')
    raw, decoded, total = {}, {}, 0
    for role, value in resources.items():
        if not isinstance(value, str) or len(value) > LIMIT * 4 // 3 + 4: raise ValueError('Resource exceeds card limit')
        raw[role] = base64.b64decode(value, validate=True)
        total += len(raw[role])
        if total > LIMIT: raise ValueError('Card image resources exceed 40 MB')
        with Image.open(io.BytesIO(raw[role])) as opened:
            if not 0 < opened.width <= 4096 or not 0 < opened.height <= 4096:
                raise ValueError('Invalid resource dimensions: ' + role)
            decoded[role] = opened.convert('RGBA')
    if sum(map(len,raw.values())) > LIMIT:
        raise ValueError('Card image resources exceed 40 MB')
    if card['kind'] == 'lenticular':
        if not {'imageA','imageB'} <= set(decoded): raise ValueError('Lenticular needs imageA and imageB')
    elif 'artwork' not in decoded and not {'background','subject'} <= set(decoded):
        raise ValueError('Need artwork or background + subject')
    if {'background','subject'} <= set(decoded):
        base = decoded['background']
        if base.getchannel('A').getextrema() != (255,255): raise ValueError('Background must be opaque')
        for role in ALPHA_ROLES | {'lineart'}:
            if role in decoded:
                if decoded[role].size != base.size: raise ValueError('Layer canvas mismatch: ' + role)
                if role != 'lineart' and not has_alpha(decoded[role]): raise ValueError('Layer needs real nonempty alpha: ' + role)
    for value in card.get('parameters',{}).values():
        if isinstance(value,(float,int)) and not isinstance(value,bool) and not math.isfinite(value):
            raise ValueError('Nonfinite rendering parameter')
    return raw


def make(config, output, force=False):
    config = Path(config)
    settings = load_json(config)
    assets = {role:image(config.parent / path) for role,path in settings['assets'].items()}
    if set(assets) - (ROLES | {'frame'}): raise ValueError('Unknown source asset role')
    layers = {}
    layered = 'subject' in assets or 'background' in assets
    if layered:
        if not {'subject','background'} <= set(assets): raise ValueError('Spatial card needs both subject and complete background')
        source_size = assets['background'].size
        if assets['background'].getchannel('A').getextrema() != (255,255): raise ValueError('Source background must be opaque')
        layers['background'] = background(assets['background'])
        for role in ALPHA_ROLES | {'lineart', 'frame'}:
            if role not in assets: continue
            if assets[role].size != source_size: raise ValueError('Use same-size registered canvases, or decompose first: '+role)
            if role != 'lineart' and not has_alpha(assets[role]): raise ValueError('Real transparent pixels required: '+role)
            layers[role] = plate(assets[role])
    elif 'imageA' in assets or 'imageB' in assets:
        if not {'imageA','imageB'} <= set(assets): raise ValueError('Lenticular needs two complete faces')
        layers.update({role:background(assets[role]) for role in ('imageA','imageB')})
    elif 'artwork' in assets:
        if settings.get('fit','contain') == 'fill':
            layers['artwork'] = ImageOps.fit(assets['artwork'], SIZE, method=Image.Resampling.LANCZOS)
        else:
            layers['artwork'] = Image.new('RGBA',SIZE,'#172437')
            item, position = fit(assets['artwork']); layers['artwork'].alpha_composite(item,position)
    else: raise ValueError('No usable artwork in config')
    lettering = layers.pop('frame', Image.new('RGBA',SIZE))
    if 'text' in layers: lettering.alpha_composite(layers.pop('text'))
    rarity = settings.get('rarity','自制')
    draw = ImageDraw.Draw(lettering)
    if settings.get('showRarity', rarity != '自制'):
        font = ImageFont.truetype(str(config.parent/settings['font']),100) if settings.get('font') else ImageFont.load_default(size=100)
        draw.text((SIZE[0]*.89,SIZE[1]*.07),rarity,font=font,fill='#EACB91',anchor='ra',stroke_width=1)
    if settings.get('printTitle'):
        if not settings.get('font'): raise ValueError('printTitle requires a font path that supports the title characters')
        draw.text((SIZE[0]/2,SIZE[1]*.91),settings['title'],font=ImageFont.truetype(str(config.parent/settings['font']),72),fill='#F7F0DA',anchor='mm')
    if has_alpha(lettering): layers['text'] = lettering
    if layered:
        artwork = layers['background'].copy()
        for role in ('midground','subject','effects','foreground','text'):
            if role in layers: artwork.alpha_composite(layers[role])
        layers['artwork'] = artwork
    elif 'text' in layers:
        for role in ('artwork','imageA','imageB'):
            if role in layers: layers[role].alpha_composite(lettering)
        layers.pop('text')
    if 'back' in assets:
        layers['back'] = Image.new('RGBA',SIZE,'#172437')
        item,position = fit(assets['back'],fill=settings.get('backFit')=='fill')
        layers['back'].alpha_composite(item,position)
    else:
        layers['back'] = Image.new('RGBA',SIZE,'#172437')
    params = {'foil':0.25,'particles':0,'glow':0,'starsEnabled':False,'glowEnabled':False,
              'backgroundDepth':-0.18,'subjectDepth':0.132,'effectsDepth':0.16,'subjectScale':1}
    # Restrict overrides to the portable fields exposed here; native validation is final authority.
    bounds = {'foil':(0,1.5),'particles':(0,1.5),'glow':(0,1.5),'subjectDepth':(0,0.3),'backgroundDepth':(-0.5,0),'effectsDepth':(0,0.3)}
    for key,value in settings.get('parameters',{}).items():
        if key in ('starsEnabled','glowEnabled') and type(value) is bool: params[key]=value
        elif key in bounds and type(value) in (float,int) and math.isfinite(value) and bounds[key][0]<=value<=bounds[key][1]: params[key]=value
        else: raise ValueError('Unsupported or unsafe parameter: '+key)
    card = {'id':settings.get('id','agent-'+str(uuid.uuid4())), 'title':settings['title'],
            'subtitle':settings.get('subtitle',''), 'creator':settings.get('creator',''), 'story':settings.get('story',''),
            'series':settings.get('series','我的创作'), 'number':settings.get('number',''), 'rarity':rarity,
            'kind':'lenticular' if 'imageA' in layers else 'holographic','accent':settings.get('accent','B6A3FF'),
            'tags':settings.get('tags',['Agent 制卡']), 'assets':{r:'embedded' for r in layers},'parameters':params,
            'finish':settings.get('finish',3),'borderless':True,'containedArtwork':True,
            'layers':{'foreground':{'depth':0.2,'width':6.3,'height':9.45,'offset':[0,0]}}}
    if settings.get('attribution'): card['attribution']=settings['attribution']
    package = {'format':'app.shancard.card','version':1,'card':card,'resources':{r:base64.b64encode(png(img)).decode() for r,img in layers.items()}}
    check_card(package)
    save_json(output,package,force)
    preview = Path(output).with_suffix('.preview.png')
    (layers.get('artwork') or layers.get('imageA')).save(preview)
    return package


def api(body, model):
    key = os.environ.get('ARK_API_KEY','').strip()
    if not key: raise ValueError('Set your own ARK_API_KEY; no credential is included in this skill')
    if not model.strip(): raise ValueError('Supply your compatible model with --model or ARK_MODEL')
    body.update(model=model,response_format='url',watermark=False)
    request = urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=240) as response: value=json.load(response)
    except urllib.error.HTTPError as error:
        raise ValueError('Seedream HTTP '+str(error.code)+'; check model access, quota or input. No automatic paid retry.') from None
    items = value.get('data',[])
    if not items or len(items)>17 or any(not item.get('url') for item in items): raise ValueError('Incomplete API result')
    return value


def download(address):
    url=urllib.parse.urlsplit(address)
    if url.scheme!='https' or not url.hostname or url.username or url.password: raise ValueError('Only HTTPS image download URLs are accepted')
    with urllib.request.urlopen(address,timeout=120) as response:
        data=response.read(LIMIT+1)
    if len(data)>LIMIT: raise ValueError('Downloaded image exceeds 40 MB')
    return data


def classify(item):
    if item.get('z_index')==0: return 'background'
    name=(item.get('name') or item.get('description') or '').lower()
    for role,words in [('background',('背景','底图','background','scene')),('frame',('卡框','边框','frame','border','text','文字','标题','徽章')),('subject',('主体','人物','角色','character','subject','person')),('foreground',('前景','foreground'))]:
        if any(word in name for word in words): return role
    return 'effects'


def decompose(manifest, source_dir, output_dir, settings, subject_layer=None):
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=False)
    items=manifest['data']
    ids=[item.get('z_index') for item in items]
    if not 2<=len(items)<=17 or any(type(i) is not int or i<0 for i in ids) or len(set(ids))!=len(ids) or 0 not in ids:
        raise ValueError('Invalid layer count or z_index values')
    raw=[]; total=0
    for index,item in enumerate(items):
        cached=Path(source_dir)/f'layer-{index}.png' if source_dir else None
        if cached is not None and not cached.exists(): raise FileNotFoundError('Missing offline layer cache: '+str(cached))
        data=cached.read_bytes() if cached is not None else download(item['url'])
        total+=len(data)
        if total>LIMIT: raise ValueError('Decomposition sources exceed 40 MB')
        path=output_dir/f'layer-{index}.png';path.write_bytes(data)
        raw.append((item,image(path)))
    base=next(img for meta,img in raw if meta['z_index']==0)
    if base.getchannel('A').getextrema() != (255,255): raise ValueError('Decomposition base must be an opaque complete background')
    groups={}; background_image=base.copy()
    for meta,img in sorted(raw,key=lambda pair:pair[0]['z_index']):
        if meta['z_index']==0:continue
        role='subject' if meta['z_index']==subject_layer else classify(meta)
        box=meta.get('bounding_box',{})
        if 'absolute' in box:
            v=box['absolute']; scale=(base.width,base.height,base.width,base.height)
        else: v=box.get('normalized',[]); scale=(1000,)*4
        if len(v)!=4 or any(type(n) not in (float,int) or not math.isfinite(n) for n in v): raise ValueError('Missing or invalid bounding_box')
        left,top,right,bottom=[n/s for n,s in zip(v,scale)]
        if not (0<=left<right<=1 and 0<=top<bottom<=1):raise ValueError('Out-of-bounds layer')
        if role!='background' and not has_alpha(img):raise ValueError('Layer has no real transparent pixels: '+str(meta.get('name')))
        target=(max(1,round((right-left)*base.width)),max(1,round((bottom-top)*base.height)))
        fitted,position=fit(img,target)
        canvas=background_image if role=='background' else groups.setdefault(role,Image.new('RGBA',base.size))
        canvas.alpha_composite(fitted,(round(left*base.width)+position[0],round(top*base.height)+position[1]))
    if 'subject' not in groups:raise ValueError('No subject recognized. Inspect source layers and retry with --subject-layer Z_INDEX using the cached manifest.')
    groups['background']=background_image.convert('RGB').convert('RGBA')
    paths={}
    for role,img in groups.items():
        path=output_dir/(role+'.png');img.save(path);paths[role]=path.name
    settings.update(assets=paths)
    save_json(output_dir/'card.json',settings)
    result = make(output_dir/'card.json',output_dir/'card.shancard')
    pack([output_dir/'card.shancard'],output_dir/'card.kayu',settings['title'],settings.get('creator') or '卡屿创作者','')
    return result


def check_pack(value):
    if value.get('format') != 'app.shancard.pack' or value.get('version') != 1:
        raise ValueError('Unsupported pack format')
    for key, limit in [('id',160),('title',60),('creator',100),('message',300)]:
        item = value.get(key)
        if not isinstance(item,str) or len(item)>limit or (key!='message' and not item.strip()):
            raise ValueError('Invalid pack metadata: '+key)
    cards, resources = value['cards'], value['resources']
    if not 1<=len(cards)<=60 or len({c['id'] for c in cards})!=len(cards):
        raise ValueError('Pack requires 1–60 unique card IDs')
    if type(value.get('createdAt')) not in (int,float) or not math.isfinite(value['createdAt']):
        raise ValueError('Invalid pack timestamp')
    used, total = set(), 0
    for digest, encoded in resources.items():
        if not isinstance(encoded,str) or len(encoded)>LIMIT*4//3+4:
            raise ValueError('Resource exceeds card limit')
        data=base64.b64decode(encoded,validate=True)
        total+=len(data)
        if total>160*1024*1024: raise ValueError('Pack exceeds 160 MB resources')
        if hashlib.sha256(data).hexdigest()!=digest: raise ValueError('Hash mismatch')
    for card in cards:
        used.update(card['assets'].values())
        check_card({'format':'app.shancard.card','version':1,
                    'card':{**card,'assets':{r:'embedded' for r in card['assets']}},
                    'resources':{r:resources[d] for r,d in card['assets'].items()}})
    if used!=set(resources): raise ValueError('Pack contains unreferenced resources')


def pack(inputs,output,title,creator,message,force=False):
    if Path(output).suffix.lower() != '.kayu':raise ValueError('Use .kayu for a 卡屿卡包 output file')
    if not 1<=len(inputs)<=60: raise ValueError('Pack requires 1–60 cards')
    cards=[]; resources={}; total=0
    for path in inputs:
        package=load_json(path);raw=check_card(package)
        card=dict(package['card']);card['assets']={}
        for role,data in raw.items():
            digest=hashlib.sha256(data).hexdigest()
            if digest not in resources:
                total+=len(data)
                if total>160*1024*1024: raise ValueError('Pack exceeds 160 MB resources')
                resources[digest]=base64.b64encode(data).decode()
            card['assets'][role]=digest
        cards.append(card)
    if not 1<=len(cards)<=60 or len({c['id'] for c in cards})!=len(cards):raise ValueError('Pack requires 1–60 unique card IDs')
    if sum(len(base64.b64decode(v)) for v in resources.values())>160*1024*1024:raise ValueError('Pack exceeds 160 MB resources')
    if not title.strip() or len(title)>60 or not creator.strip() or len(creator)>100 or len(message)>300:raise ValueError('Invalid pack metadata')
    value={'format':'app.shancard.pack','version':1,'id':str(uuid.uuid4()),'title':title,'creator':creator,'message':message,'cards':cards,'resources':resources,'createdAt':time.time()-978307200}
    save_json(output,value,force)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('make');build.add_argument('config');build.add_argument('--out',required=True);build.add_argument('--force',action='store_true')
    validate=sub.add_parser('validate');validate.add_argument('file')
    bundle=sub.add_parser('pack');bundle.add_argument('cards',nargs='+');bundle.add_argument('--out',required=True);bundle.add_argument('--title',required=True);bundle.add_argument('--creator',required=True);bundle.add_argument('--message',default='');bundle.add_argument('--force',action='store_true')
    for name in ('generate','decompose'):
        command=sub.add_parser(name);command.add_argument('--out-dir',required=True);command.add_argument('--title',required=True);command.add_argument('--creator',default='');command.add_argument('--rarity',choices=['自制','SR','SSR','UR'],default='自制');command.add_argument('--model',default=MODEL)
        if name=='generate':
            command.add_argument('--idea',default='星空中的角色');command.add_argument('--style',choices=['original','ssr','mecha'],default='original');command.add_argument('--reference')
        else:
            command.add_argument('--image');command.add_argument('--manifest');command.add_argument('--layers-dir');command.add_argument('--subject-layer',type=int)
    args=parser.parse_args()
    if args.command=='make':make(args.config,args.out,args.force);print('Card validated:',args.out)
    elif args.command=='validate':
        value=load_json(args.file)
        if value.get('format')=='app.shancard.pack':check_pack(value)
        else:
            if Path(args.file).stat().st_size>60*1024*1024: raise ValueError('Card file exceeds 60 MB')
            check_card(value)
        print('Validated:',args.file)
    elif args.command=='pack':pack(args.cards,args.out,args.title,args.creator,args.message,args.force);print('Pack created:',args.out)
    else:
        if not args.title.strip() or len(args.title)>100 or len(args.creator)>100: raise ValueError('Title must be nonempty and at most100 characters; creator at most100')
        out=Path(args.out_dir)
        if out.exists():raise FileExistsError('Use a fresh output directory; generation is not repeated automatically')
        settings={'title':args.title,'creator':args.creator,'rarity':args.rarity,'attribution':'AI assisted · Seedream' if args.command=='generate' or not args.manifest else 'Agent assembled'}
        if args.command=='generate':
            out.mkdir(parents=True)
            treatment={'original':'无框原画，不要边框','ssr':'幻想收藏卡，精致主题卡框','mecha':'机甲档案卡，科技主题卡框'}[args.style]
            body={'size':'1584x2400','prompt':f'竖版66:100二次元收藏卡，单角色，完整头发四肢，主体与场景清楚分开，光线统一，人物与卡框留安全边距。{treatment}。不要任何文字、字母、SSR或编号，文字由应用排版。用户想法：{args.idea[:800]}'}
            if args.reference:
                reference=png(image(args.reference))
                if len(reference)>30*1024*1024: raise ValueError('Reference exceeds 30 MB')
                body['image']='data:image/png;base64,'+base64.b64encode(reference).decode()
            result=api(body,args.model)
            generated=download(result['data'][0]['url']);(out/'generated.png').write_bytes(generated)
            split=api({'size':'2K','image':'data:image/png;base64,'+base64.b64encode(png(image(out/'generated.png'))).decode(),'layer_decomposition':True,'prompt':'完整无人物背景为底图；角色与手持物作为主体；主题卡框、前景、特效分开为透明图层。名称明确使用主体、背景、卡框、前景、特效。不要人物重影，保持原构图。'},args.model)
            save_json(out/'decomposition.json',split)
            decompose(split,None,out/'assembled',settings)
        else:
            if args.manifest:manifest=load_json(args.manifest)
            elif args.image:
                source=png(image(args.image))
                if len(source)>30*1024*1024:raise ValueError('Reference image exceeds 30 MB')
                manifest=api({'size':'2K','image':'data:image/png;base64,'+base64.b64encode(source).decode(),'layer_decomposition':True,'prompt':'将完整无人物背景、主体角色、卡框和前景分别拆分，名称明确用途，保持原构图和原位置。'},args.model)
            else:raise ValueError('decompose needs --image or --manifest')
            decompose(manifest,args.layers_dir,out,settings,args.subject_layer)
        print('Created card, registered layers and preview under:',args.out_dir)

if __name__=='__main__':
    try:main()
    except Exception as error:
        # Do not dump HTTP responses, headers, signed URLs or environment secrets.
        if isinstance(error,(urllib.error.URLError,TimeoutError)):message='Network request failed; existing output is retained. No automatic paid retry.'
        else:message=str(error)
        credential=os.environ.get('ARK_API_KEY','')
        if credential:message=message.replace(credential,'[redacted]')
        raise SystemExit('Error: '+message)
