# Part 2 of the mod build: the Trichter production chain (goods, need, buildings, area effects, build menu).
#
#   python build_trichter.py <mod-dir> [<vanilla assets.xml>]
#
# New buildings are edited copies of vanilla assets. The vanilla XML of the template assets is cached in
# vanilla_templates.json next to this script, so the game's assets.xml is only needed when the cache is missing
# or the template list changes. Run via build.py after build_base.py.
import sys, os, re, json, bisect
import xml.dom.minidom

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, 'vanilla_templates.json')
OUT = sys.argv[1]
VANILLA = sys.argv[2] if len(sys.argv) > 2 else None

# ---- GUIDs (personal-use range) -------------------------------------------------------------------------------
P_TRICHTER, P_SCHLAUCH = 2001000300, 2001000301
NEED = 2001000310
R_MALT, R_BREW, R_HOSE, R_FUNNEL = 2001000320, 2001000321, 2001000322, 2001000323
C_HOSE, C_FUNNEL = 2001000330, 2001000331
E_HOSE, E_FUNNEL = 2001000340, 2001000341
CHAIN_R, CHAIN_C, CHAIN_E = 2001000350, 2001000351, 2001000352
BUFF_PRESTIGE, EFFECT_PRESTIGE, EFFECT_PRESTIGE_E = 2001000360, 2001000361, 2001000362

# ---- vanilla GUIDs --------------------------------------------------------------------------------------------
WHEAT, MALT, BEER, AMPHORAE, LEATHER, REED, HORNS, OIL_LAMPS = 2069, 2131, 2154, 31700, 2110, 2103, 55954, 151700
V_BEER, V_LEATHER, V_NEED_BEER, V_CHAIN = 2154, 2110, 6431, 55974
V_R_BAKERY, V_R_ROPES, V_R_POTTER = 3174, 3168, 3199
V_C_HORNER, V_E_LAMPS = 55963, 152731
V_BUFF, V_EFFECT = 32350, 99036            # area effect of the Roman potter: Effect -> BuildingBuff
TEMPLATES = [V_BEER, V_LEATHER, V_NEED_BEER, V_CHAIN, V_R_BAKERY, V_R_ROPES, V_R_POTTER, V_C_HORNER, V_E_LAMPS, V_BUFF, V_EFFECT]

# ---- texts ----------------------------------------------------------------------------------------------------
TEXTS = {  # id: (de, en)
    2001000401: ("Trichter", "Beer Funnels"),
    2001000402: ("Schläuche", "Hoses"),
    2001000403: ("Wer trichtert, ist glücklich. Wer zu viel trichtert, vergisst allerdings das eine oder andere.",
                 "Those who funnel are happy. Those who funnel too much tend to forget a thing or two."),
    2001000410: ("Mälzerei", "Malthouse"),
    2001000411: ("Brauerei", "Brewery"),
    2001000412: ("Schlauchmacher", "Hose Maker"),
    2001000413: ("Trichter-Werkstatt", "Funnel Workshop"),
    2001000420: ("Lässt Weizen keimen und darrt ihn zu Malz.", "Sprouts wheat and kilns it into malt."),
    2001000421: ("Braut aus Malz ein Weizenbier, wie es sonst nur die Provinzen kennen.",
                 "Brews a wheat beer from malt, the way only the provinces know it."),
    2001000422: ("Fertigt biegsame Schläuche.", "Makes flexible hoses."),
    2001000423: ("Setzt Trichterkopf, Schlauch und Bier zu einem Trichter zusammen. Hebt das Ansehen der Nachbarschaft.",
                 "Assembles funnel head, hose and beer into a beer funnel. Raises the prestige of the neighbourhood."),
    2001000430: ("Kegel-Produktion", "Bowling Production"),
}

ICON_TRICHTER = 'data/lukas/kegeln/icons/trichter.png'
ICON_SCHLAUCH = 'data/lukas/kegeln/icons/schlauch.png'


def load_templates():
    if os.path.exists(CACHE):
        c = json.load(open(CACHE, encoding='utf-8'))
        if all(str(g) in c for g in TEMPLATES):
            return {int(k): v for k, v in c.items()}
    if not VANILLA:
        sys.exit('template cache missing or incomplete: pass the path of the vanilla assets.xml as second argument')
    a = open(VANILLA, encoding='utf-8', errors='replace').read()
    starts = [m.start() for m in re.finditer(r'<Asset>\n<(?:Template|BaseAssetGUID)>', a)]
    out = {}
    for g in TEMPLATES:
        i = a.find('<Standard>' + chr(10) + '<GUID>%d</GUID>' % g)
        k = bisect.bisect_right(starts, i) - 1
        block = a[starts[k]:starts[k + 1] if k + 1 < len(starts) else len(a)]
        out[g] = block[:block.rfind('</Asset>') + len('</Asset>')]
    json.dump({str(k): v for k, v in out.items()}, open(CACHE, 'w', encoding='utf-8'), indent=1)
    return out


TPL = load_templates()


# ---- text edit helpers (work on the flat vanilla XML) ---------------------------------------------------------
def sub1(pattern, repl, s, flags=re.S, required=True):
    new, n = re.subn(pattern, lambda m: repl, s, count=1, flags=flags)
    if required and n != 1:
        raise SystemExit('pattern not found: ' + pattern[:60])
    return new


def base(vanilla_guid, guid, name, text_id=None, icon=None, info_id=None):
    s = TPL[vanilla_guid]
    s = sub1(r'<GUID>\d+</GUID>\n<Name>[^<]*</Name>', f'<GUID>{guid}</GUID>\n<Name>{name}</Name>', s)
    s = re.sub(r'<ValueHash>.*?</ValueHash>\n?', '', s, flags=re.S)
    if icon:
        s = sub1(r'<IconFilename>[^<]*</IconFilename>', f'<IconFilename>{icon}</IconFilename>', s)
    if info_id:
        if '<InfoDescription>' in s:
            s = sub1(r'<InfoDescription>[^<]*</InfoDescription>', f'<InfoDescription>{info_id}</InfoDescription>', s)
        else:
            s = sub1(r'</Name>\n', f'</Name>\n<InfoDescription>{info_id}</InfoDescription>\n', s)
    if text_id:
        s = sub1(r'<Text>\n<OasisId>-?\d+</OasisId>\n</Text>', f'<Text>\n<OasisId>{text_id}</OasisId>\n</Text>', s)
    # always available: the vanilla unlock triggers have already fired in running savegames
    if '<Locked />' in s:
        s = s.replace('<Locked />', '<Locked>\n<DefaultLockedState>0</DefaultLockedState>\n</Locked>', 1)
    return s


def items(tag, entries, with_storage=True):
    out = f'<{tag}>\n'
    for product, amount, storage in entries:
        out += f'<Item>\n<Product>{product}</Product>\n<Amount>{amount}</Amount>\n'
        if with_storage:
            out += f'<StorageAmount>{storage}</StorageAmount>\n'
        out += '</Item>\n'
    return out + f'</{tag}>'


def factory(s, inputs, outputs, cycle=None):
    s = sub1(r'<FactoryInputs>.*?</FactoryInputs>', items('FactoryInputs', inputs), s)
    s = sub1(r'<FactoryOutputs>.*?</FactoryOutputs>', items('FactoryOutputs', outputs), s)
    if cycle is not None:
        if '<CycleTime>' in s:
            s = sub1(r'<CycleTime>\d+</CycleTime>', f'<CycleTime>{cycle}</CycleTime>', s)
        else:
            s = sub1(r'</FactoryOutputs>\n', f'</FactoryOutputs>\n<CycleTime>{cycle}</CycleTime>\n', s)
    return s


def area_attributes(s, attrs):
    """Replace the area attributes a building radiates (FireSafety, Health, Happiness, Prestige)."""
    m = re.search(r'<AttributeProvider>(.*?)</AttributeProvider>', s, re.S)
    if not m:
        raise SystemExit('no AttributeProvider')
    inner = re.sub(r'<Attributes>.*?</Attributes>\n?', '', m.group(1), flags=re.S)
    block = ''
    if attrs:
        block = '\n<Attributes>\n' + ''.join(f'<{k}>\n<Value>{v}</Value>\n</{k}>\n' for k, v in attrs.items()) + '</Attributes>'
    return s[:m.start()] + '<AttributeProvider>' + block + inner + '</AttributeProvider>' + s[m.end():]


def no_fuel(s):
    """The building does not burn charcoal."""
    return s.replace('<NeedsFuelInput>1</NeedsFuelInput>' + chr(10), '')


def effects(s, guids):
    """Set the area effects the building radiates (FunctionalEffects -> Effect -> BuildingBuff).
    This is what actually changes the neighbourhood; AttributeProvider/Attributes mirrors it."""
    block = ''
    if guids:
        block = '<FunctionalEffects>' + chr(10) + ''.join(
            f'<Item>{chr(10)}<FunctionalEffect>{g}</FunctionalEffect>{chr(10)}</Item>{chr(10)}' for g in guids) + '</FunctionalEffects>' + chr(10)
    s = re.sub(r'<FunctionalEffects>.*?</FunctionalEffects>' + chr(10), '', s, flags=re.S)
    return sub1(r'</Building>', block + '</Building>', s)


def model(s, cfg):
    return sub1(r'<Variations>.*?</Variations>', f'<Variations>\n<Item>\n<Filename>{cfg}</Filename>\n</Item>\n</Variations>', s)


assets = []

# ---- products -------------------------------------------------------------------------------------------------
ALL_REGIONS = ('<AssociatedRegion>Roman;Celtic;Egyptian</AssociatedRegion>\n<ProductionRegions>\n'
               + ''.join(f'<Item>\n<RegionType>{r}</RegionType>\n</Item>\n' for r in ('Roman', 'Celtic', 'Egyptian'))
               + '</ProductionRegions>')
p = base(V_BEER, P_TRICHTER, 'Good Trichter', 2001000401, ICON_TRICHTER)
p = sub1(r'<AssociatedRegion>.*?</ProductionRegions>', ALL_REGIONS, p)
p = sub1(r'<BasePrice>\d+</BasePrice>', '<BasePrice>100</BasePrice>', p)
assets.append(('Product: Trichter (copy of beer 2154), base price 100', p))
p = base(V_LEATHER, P_SCHLAUCH, 'Good Schlaeuche', 2001000402, ICON_SCHLAUCH)
p = sub1(r'<AssociatedRegion>.*?</ProductionRegions>', ALL_REGIONS, p)
p = sub1(r'<BasePrice>\d+</BasePrice>', '<BasePrice>24</BasePrice>', p)
assets.append(('Product: Schlaeuche (copy of leather 2110), base price 24', p))

# ---- need -----------------------------------------------------------------------------------------------------
n = base(V_NEED_BEER, NEED, 'Need Trichter', 2001000401, ICON_TRICHTER)
n = sub1(r'<NeedProduct>\d+</NeedProduct>', f'<NeedProduct>{P_TRICHTER}</NeedProduct>', n)
n = sub1(r'<NeedAttributes>.*?</NeedAttributes>',
         '<NeedAttributes>\n<Money>\n<Value>1</Value>\n</Money>\n<Happiness>\n<Value>3</Value>\n</Happiness>\n'
         '<Knowledge>\n<Value>-1</Value>\n</Knowledge>\n</NeedAttributes>', n)
n = sub1(r'<NeedDescription>-?\d+</NeedDescription>', '<NeedDescription>2001000403</NeedDescription>', n)
assets.append(('Need: Trichter (copy of Celtic beer need 6431): happiness +3, money +1, knowledge -1', n))

# ---- area effect of the funnel workshop: prestige +1 for the buildings around it ------------------------------
bf = base(V_BUFF, BUFF_PRESTIGE, 'Buff Trichter Building', 2001000413, ICON_TRICHTER)
bf = sub1(r'<AdditionalAttributes>.*?</AdditionalAttributes>',
          '<AdditionalAttributes>' + chr(10) + '<Prestige>' + chr(10) + '<AmountOrPercent>' + chr(10) + '<Value>1</Value>' + chr(10)
          + '<Percental>0</Percental>' + chr(10) + '</AmountOrPercent>' + chr(10) + '</Prestige>' + chr(10) + '</AdditionalAttributes>', bf)
assets.append(('Buff: prestige +1 (copy of the amphorae building buff 32350)', bf))
for guid, pool, label in ((EFFECT_PRESTIGE, 43097, 'Roman and Celtic'), (EFFECT_PRESTIGE_E, 151971, 'Egyptian')):
    ef = base(V_EFFECT, guid, 'Effect Trichter Building ' + label, 2001000413, ICON_TRICHTER)
    ef = sub1(r'<Buffs>.*?</Buffs>', '<Buffs>' + chr(10) + '<Item>' + chr(10) + f'<GUID>{BUFF_PRESTIGE}</GUID>' + chr(10) + '</Item>' + chr(10) + '</Buffs>', ef)
    ef = sub1(r'<Targets>.*?</Targets>', '<Targets>' + chr(10) + '<Item>' + chr(10) + f'<GUID>{pool}</GUID>' + chr(10) + '</Item>' + chr(10) + '</Targets>', ef)
    assets.append((f'Effect: funnel workshop radius effect, {label} attribute buildings (copy of 99036)', ef))

# ---- Latium ---------------------------------------------------------------------------------------------------
b = base(V_R_BAKERY, R_MALT, 'Production Roman Malt', 2001000410, None, 2001000420)
b = no_fuel(factory(b, [(WHEAT, 1, 4)], [(MALT, 1, 3)], 60))
b = effects(area_attributes(b, {}), [])
b = sub1(r'<IconFilename>[^<]*</IconFilename>',
         '<IconFilename>data/ui/fhd/base/icon_content/production_goods/icon_3d_malt_goods.png</IconFilename>', b)
assets.append(('Latium malthouse: wheat -> malt (copy of Roman bakery 3174, bakery model)', b))

b = base(V_R_BAKERY, R_BREW, 'Production Roman Beer', 2001000411, None, 2001000421)
b = factory(b, [(MALT, 1, 4)], [(BEER, 1, 3)], 60)
b = model(b, 'data/base/graphics/roman/buildings/production/food/wine/food_wine.cfg')
b = effects(area_attributes(b, {'FireSafety': -2}), [99016, 98407])   # vanilla beer effects: money +1, fire safety -2
b = sub1(r'<IconFilename>[^<]*</IconFilename>',
         '<IconFilename>data/ui/fhd/base/icon_content/production_goods/icon_3d_beer_goods.png</IconFilename>', b)
assets.append(('Latium brewery: malt -> beer (copy of Roman bakery 3174, vintner model), fire safety -2', b))

b = base(V_R_ROPES, R_HOSE, 'Production Roman Hoses', 2001000412, ICON_SCHLAUCH, 2001000422)
b = no_fuel(factory(b, [(LEATHER, 1, 4)], [(P_SCHLAUCH, 1, 3)], 60))
b = effects(area_attributes(b, {}), [])
assets.append(('Latium hose maker: leather -> hoses (copy of Roman rope maker 3168)', b))

b = base(V_R_POTTER, R_FUNNEL, 'Production Roman Trichter', 2001000413, ICON_TRICHTER, 2001000423)
# one amphora (one minute at the potter) is halved into two funnels; each funnel takes one hose and one beer
# same rule in every region: 60 s cycle, 1 beer + 1 funnel head + 1 hose -> 1 funnel
b = no_fuel(factory(b, [(BEER, 1, 4), (AMPHORAE, 1, 4), (P_SCHLAUCH, 1, 4)], [(P_TRICHTER, 1, 3)], 60))
b = model(b, 'data/base/graphics/roman/buildings/production/household/fine_glass/household_fine_glass.cfg')
b = effects(area_attributes(b, {'Prestige': 1}), [EFFECT_PRESTIGE])
assets.append(('Latium funnel workshop: beer + amphora + hose -> funnel (copy of Roman potter 3199, fine glass model), prestige +1', b))

# ---- Albion ---------------------------------------------------------------------------------------------------
b = base(V_C_HORNER, C_HOSE, 'Production Celtic Hoses', 2001000412, ICON_SCHLAUCH, 2001000422)
b = no_fuel(factory(b, [(REED, 1, 4)], [(P_SCHLAUCH, 1, 3)], 60))
b = model(b, 'data/base/graphics/celtic/buildings/production/fashion/pelt_hats/fashion_pelt_hats.cfg')
b = effects(area_attributes(b, {}), [])
assets.append(('Albion hose maker: reed -> hoses (copy of horn maker 55963, pelt hat workshop model)', b))

b = base(V_C_HORNER, C_FUNNEL, 'Production Celtic Trichter', 2001000413, ICON_TRICHTER, 2001000423)
b = no_fuel(factory(b, [(BEER, 1, 4), (HORNS, 1, 4), (P_SCHLAUCH, 1, 4)], [(P_TRICHTER, 1, 3)], 60))
b = model(b, 'data/base/graphics/celtic/buildings/production/coast/amber/coast_amber.cfg')
b = effects(area_attributes(b, {'Prestige': 1}), [EFFECT_PRESTIGE])
assets.append(('Albion funnel workshop: beer + drinking horns + hoses -> funnels (copy of horn maker 55963, unused amber workshop model), prestige +1', b))

# ---- Aegyptus -------------------------------------------------------------------------------------------------
b = base(V_E_LAMPS, E_HOSE, 'Production Egyptian Hoses', 2001000412, ICON_SCHLAUCH, 2001000422)
b = no_fuel(factory(b, [(REED, 1, 4)], [(P_SCHLAUCH, 1, 3)], 60))
b = model(b, 'data/dlc03/graphics/roman_egypt/buildings/production/chemical/leather/chemical_leather.cfg')
b = effects(area_attributes(b, {}), [])
assets.append(('Aegyptus hose maker: reed -> hoses (copy of oil lamp workshop 152731, tanner model)', b))

b = base(V_E_LAMPS, E_FUNNEL, 'Production Egyptian Trichter', 2001000413, ICON_TRICHTER, 2001000423)
b = no_fuel(factory(b, [(BEER, 1, 4), (OIL_LAMPS, 1, 4), (P_SCHLAUCH, 1, 4)], [(P_TRICHTER, 1, 3)], 60))
b = model(b, 'data/dlc03/graphics/egypt/buildings/production/heavy/bronze/heavy_bronze.cfg')
b = effects(area_attributes(b, {'Prestige': 1}), [EFFECT_PRESTIGE_E])
assets.append(('Aegyptus funnel workshop: beer + oil lamps + hoses -> funnels (copy of oil lamp workshop 152731, bronze smelter model), prestige +1', b))


# ---- production chains (build menu entries) ---------------------------------------------------------------------
def chain(guid, name, building, tree):
    def tier(nodes, depth):
        if not nodes:
            return ''
        out = f'<Tier{depth}>\n'
        for g, sub in nodes:
            out += f'<Item>\n<Building>{g}</Building>\n' + tier(sub, depth + 1) + '</Item>\n'
        return out + f'</Tier{depth}>\n'
    s = base(V_CHAIN, guid, name, 2001000430, ICON_TRICHTER, 2001000403)
    return sub1(r'<ProductionChain>.*?</ProductionChain>',
                f'<ProductionChain>\n<Building>{building}</Building>\n' + tier(tree, 1) + '</ProductionChain>', s)


assets.append(('Build menu chain, Latium', chain(CHAIN_R, 'Production Chain Roman Trichter', R_FUNNEL, [
    (R_BREW, [(R_MALT, [(2693, [])])]),      # brewery <- malthouse <- wheat farm
    (V_R_POTTER, []),                        # amphorae
    (R_HOSE, [(2994, [])]),                  # hose maker <- tannery
])))
assets.append(('Build menu chain, Albion', chain(CHAIN_C, 'Production Chain Celtic Trichter', C_FUNNEL, [
    (5570, [(5474, [(2799, [])])]),          # brewery <- malthouse <- barley farm
    (V_C_HORNER, []),                        # drinking horns
    (C_HOSE, [(5849, [])]),                  # hose maker <- reed cutter
])))
assets.append(('Build menu chain, Aegyptus', chain(CHAIN_E, 'Production Chain Egyptian Trichter', E_FUNNEL, [
    (152389, [(152352, [(151993, [])])]),    # brewery <- malthouse <- barley farm
    (V_E_LAMPS, []),                         # oil lamps (funnel head)
    (E_HOSE, [(151997, [])]),                # hose maker <- reed cutter
])))

# ---- assemble include file ----------------------------------------------------------------------------------------
x = '<ModOps>\n  <!-- Trichter production chain. Generated by build_trichter.py, do not edit by hand.\n'
x += '       New assets are edited copies of vanilla assets; GUIDs 2001000300-2001000399, texts 2001000401-2001000499. -->\n\n'
for comment, body in assets:
    x += f'  <!-- {comment} -->\n{body}\n\n'


def add_list(guid, path, tag, values, comment):
    out = f'  <!-- {comment} -->\n  <ModOp GUID="{guid}" Add="{path}">\n'
    for v in values:
        out += f'    <Item>\n      <{tag}>{v}</{tag}>\n    </Item>\n'
    return out + '  </ModOp>\n'


x += '  <!-- Malt and beer become producible in the Roman region as well. -->\n'
for g in (MALT, BEER):
    x += f'  <ModOp GUID="{g}" Add="Product/ProductionRegions">\n    <Item>\n      <RegionType>Roman</RegionType>\n    </Item>\n  </ModOp>\n'
x += f'  <ModOp GUID="{MALT}" Replace="Product/AssociatedRegion">\n    <AssociatedRegion>Roman;Celtic;Egyptian</AssociatedRegion>\n  </ModOp>\n\n'

x += '  <!-- Optional need "Trichter" for all residents from tier 2 on, in every region. -->\n'
RESIDENCES = {3141: 'Roman 02 Plebeians', 3142: 'Roman 03 Equites', 3145: 'Roman 04 Patricians',
              6471: 'Celtic 02 Smiths', 6472: 'Celtic 03 Aldermen', 6475: 'Roman-Celtic 02 Merchants', 6514: 'Roman-Celtic 03 Nobles',
              150584: 'Egyptian 02 Potters', 150585: 'Egyptian 03 Priests', 150586: 'Greco-Roman 02 Scribes', 150587: 'Greco-Roman 03 Gymnasiarchs'}
for g, name in RESIDENCES.items():
    x += f'  <ModOp GUID="{g}" Add="Residence7/NeedsList"> <!-- {name} -->\n    <Item>\n      <Need>{NEED}</Need>\n      <NeedConsumptionRate>0.008</NeedConsumptionRate>\n    </Item>\n  </ModOp>\n'
x += '\n'

x += add_list(41363, 'ConstructionCategory/BuildingList', 'Building', [CHAIN_R], 'Build menu: Roman tier 2 (Plebeians)')
x += add_list(41330, 'ConstructionCategory/BuildingList', 'Building', [CHAIN_C], 'Build menu: Celtic tier 2 (Smiths)')
x += add_list(152078, 'ConstructionCategory/BuildingList', 'Building', [CHAIN_E], 'Build menu: Egyptian tier 2 (Potters)')
x += '\n'
for g, name in ((28750, 'Meta'), (3409, 'Roman'), (8497, 'Celtic'), (152695, 'Egyptian')):
    x += add_list(g, 'ProductList/List', 'Product', [P_TRICHTER, P_SCHLAUCH], f'Product list {name}: all goods')
for g, name in ((37670, 'Meta'), (28752, 'Roman'), (29326, 'Celtic'), (152696, 'Egyptian')):
    x += add_list(g, 'ProductList/List', 'Product', [P_TRICHTER], f'Product list {name}: needs')
x += '</ModOps>\n'

dst = os.path.join(OUT, 'data/base/config/export/trichter.include.xml')
open(dst, 'w', encoding='utf-8', newline='\n').write(x)
xml.dom.minidom.parse(dst)

# texts: append to the files written by build_kaiser_kegeln.py
for lang, idx in (('german', 0), ('english', 1)):
    f = os.path.join(OUT, f'data/base/config/gui/texts_{lang}.xml')
    s = open(f, encoding='utf-8').read()
    add = ''.join(f'    <Text>\n      <LineId>{k}</LineId>\n      <Text>{v[idx]}</Text>\n    </Text>\n' for k, v in TEXTS.items())
    s = s.replace('  </ModOp>\n</ModOps>', add + '  </ModOp>\n</ModOps>')
    open(f, 'w', encoding='utf-8', newline='\n').write(s)
    xml.dom.minidom.parse(f)

# icons (drawn by assets/icons/make_icons.py and make_schlauch.py)
import shutil
icon_dir = os.path.join(OUT, 'data/lukas/kegeln/icons')
os.makedirs(icon_dir, exist_ok=True)
for name in ('trichter.png', 'schlauch.png'):
    shutil.copyfile(os.path.join(HERE, '..', 'assets', 'icons', name), os.path.join(icon_dir, name))

print('trichter include written:', len(assets), 'assets')
