# Part 1 of the mod build: modinfo, the emperor's bowling invitation (governor decision) and its timer.
#
#   python build_base.py <mod-dir> [--dev]
#
# --dev adds test hotkeys: Shift+F6 opens the invitation at once, Shift+F7 runs a scratch Lua script.
# Run via build.py, which calls all parts in order.
import sys, os, json, glob
import xml.dom.minidom

OUT = sys.argv[1]
DEV = '--dev' in sys.argv[2:]
VERSION = os.environ.get('KEGELN_VERSION', '0.1.0')
for d in ('data/base/config/export', 'data/base/config/gui', 'lukas') + (('data/script/content/kaiserkegeln',) if DEV else ()):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)


def w(rel, text):
    open(os.path.join(OUT, rel), 'w', encoding='utf-8', newline='\n').write(text)


modinfo = {
    "Anno": 8,
    "ModID": "kegeln-lukas",
    "Version": VERSION,
    "Difficulty": "unchanged",
    "Category": {"English": "Gameplay", "German": "Gameplay"},
    "ModName": {
        "English": "Bowling" + (" (dev build)" if DEV else ""),
        "German": "Kegeln" + (" (Entwicklungsstand)" if DEV else ""),
    },
    "Description": {
        "English": "Adds beer funnels as a new good with its own production chains in Latium, Albion and Aegyptus, a matching need for all residents from tier 2, funnel delivery contracts at the lighthouses, and an emperor who invites you to go bowling now and then.",
        "German": "Bringt Trichter als neue Ware mit eigenen Produktionsketten in Latium, Albion und Aegyptus, ein passendes Beduerfnis fuer alle Bewohner ab Stufe 2, Trichter-Lieferauftraege an den Leuchttuermen und einen Kaiser, der ab und an zum Kegeln einlaedt.",
    },
    "CreatorName": "Lukas",
    "GameSetup": {"RequiresNewGame": False, "SafeToRemove": False, "Multiplayer": True, "Campaign": False},
    "Scripts": {
        "Modules": ["lukas/kaiserkegeln.lua"],
        "Init": "KaiserKegeln = require(\"kaiserkegeln\")",
        "Tick": "KaiserKegeln.Tick()",
    },
}
w('modinfo.json', json.dumps(modinfo, indent=2, ensure_ascii=False) + '\n')

T = {  # id: (de, en)
    2001000201: ("Einladung zum Kegeln", "Invitation to bowl"),
    2001000202: ("Der Kaiser lässt anfragen, ob du Zeit für eine Runde Kegeln hast.",
                 "The emperor asks whether you have time for a round of bowling."),
    2001000203: ("Der Kaiser hat die Kugeln polieren lassen und erwartet dich auf der Bahn. Wer mit dem Kaiser kegelt, dem ist seine Gunst gewiss.",
                 "The emperor has had the balls polished and awaits you at the lane. Whoever bowls with the emperor is sure of his favour."),
    2001000204: ("Ja, lass uns kegeln!", "Yes, time to bowl!"),
    2001000205: ("Keine Zeit.", "No time."),
    2001000206: ("Alle Neune! Der Kaiser ist beeindruckt und zeigt sich großzügig.",
                 "Strike! The emperor is impressed and shows his generosity."),
    2001000207: ("Gut gekegelt.", "Well bowled."),
    2001000208: ("Ein Statthalter hat sich durch Kegeln Respekt beim Kaiser verschafft! (+1 Ansehen)",
                 "A governor has earned the emperor's respect through bowling! (+1 reputation)"),
}
for lang, idx in (('german', 0), ('english', 1)):
    s = '<ModOps>\n  <ModOp Add="/TextExport/Texts[1]">\n'
    for k, v in T.items():
        s += f'    <Text>\n      <LineId>{k}</LineId>\n      <Text>{v[idx]}</Text>\n    </Text>\n'
    s += '  </ModOp>\n</ModOps>\n'
    w(f'data/base/config/gui/texts_{lang}.xml', s)


def key(k, cmd):
    return f'''    <Item>
      <InputTypes>
        <Modern><KeyType>{k}</KeyType></Modern>
        <Legacy><KeyType>{k}</KeyType></Legacy>
      </InputTypes>
      <Command>{cmd}</Command>
      <Active>Session</Active>
      <AvailableOnPlatforms>PC</AvailableOnPlatforms>
    </Item>
'''


def trig(g, name, action):
    return f'''  <Asset>
    <Template>Trigger</Template>
    <Values>
      <Standard>
        <GUID>{g}</GUID>
        <Name>{name}</Name>
      </Standard>
      <Trigger>
        <TriggerCondition>
          <Template>ConditionAlwaysTrue</Template>
          <Values>
            <Condition />
            <ConditionAlwaysTrue />
          </Values>
        </TriggerCondition>
        <TriggerActions>
          <Item>
            <TriggerAction>
{action}
            </TriggerAction>
          </Item>
        </TriggerActions>
      </Trigger>
      <TriggerSetup>
        <AutoRegisterTrigger>0</AutoRegisterTrigger>
        <UsedBySecondParties>0</UsedBySecondParties>
      </TriggerSetup>
    </Values>
  </Asset>
'''


def start_story(guid):
    # Location filter as used by vanilla reward actions: any area controlled by the processing participant.
    return f'''              <Template>ActionStartStoryline</Template>
              <Values>
                <Action />
                <ActionStartStoryline>
                  <StorylineAsset>{guid}</StorylineAsset>
                </ActionStartStoryline>
                <LocationFilter>
                  <AllowAllLocations>1</AllowAllLocations>
                  <AllowProcessingParticipantControlledAreas>1</AllowProcessingParticipantControlledAreas>
                </LocationFilter>
              </Values>'''


NOTRIG = '''<IsBaseAutoCreateAsset>1</IsBaseAutoCreateAsset>
              <Values>
                <CharacterNotificationTrigger>
                  <Type>None</Type>
                </CharacterNotificationTrigger>
              </Values>'''

SCREEN = '''<BackgroundImage>data/ui/fhd/base/features/images_fullscreen/img_villa_interior_evening.png</BackgroundImage>
          <LeftParticipant>
            <Value>ActiveEmperor</Value>
            <IsVariable>1</IsVariable>
          </LeftParticipant>'''

x = f'''<ModOps>
  <!-- Kegeln: the emperor's bowling invitation. GUIDs 2001000100-2001000199, texts 2001000201-2001000299 (personal-use range). -->

  <!-- Asset ModOp workaround: use it once before you use asset modops -->
  <ModOp Add="/AssetList/Groups[last()]"><Group><Assets /></Group></ModOp>

  <!-- Trichter production chain (goods, need, buildings, build menu); generated by build_trichter.py -->
  <Include File="trichter.include.xml" />

  <!-- Trichter delivery contracts at NPC lighthouses; generated by build_contracts.py -->
  <Include File="contracts.include.xml" />

  <!-- Storyline: governor request -> decision (yes / no) -> outcome with rewards. Modelled on vanilla decision quest 81384. -->
  <Asset>
    <Template>StoryLine</Template>
    <Values>
      <Standard>
        <GUID>2001000100</GUID>
        <Name>Kegeln Storyline</Name>
      </Standard>
      <StoryLine>
        <System>GovernorDecisions</System>
        <StartConnector>
          <Item>
            <Component>2001000101</Component>
          </Item>
        </StartConnector>
        <StorylineVariables>
          <IsBaseAutoCreateAsset>1</IsBaseAutoCreateAsset>
          <Values>
            <ConditionVariableConfiguration />
          </Values>
        </StorylineVariables>
        <IsRepeatable>1</IsRepeatable>
      </StoryLine>
      <QuestComponent />
      <QuestComponentConnector />
      <PreConditionList>
        <Condition>
          <Template>ConditionAlwaysTrue</Template>
          <Values>
            <Condition />
            <ConditionAlwaysTrue />
          </Values>
        </Condition>
      </PreConditionList>
    </Values>
  </Asset>
  <Asset>
    <Template>DecisionRoot</Template>
    <Values>
      <Standard>
        <GUID>2001000101</GUID>
        <Name>Kegeln DecisionRoot</Name>
      </Standard>
      <DecisionRoot>
        <DecisionRootOutput>
          <Item />
          <Item />
        </DecisionRootOutput>
        <DecisionRootStartComponent>2001000102</DecisionRootStartComponent>
        <DecisionGovernorRequest>
          <IsBaseAutoCreateAsset>1</IsBaseAutoCreateAsset>
          <Values>
            <GovernorRequest>
              <RequestDescription>2001000202</RequestDescription>
              <RequestIcon>68769</RequestIcon>
              <RequestParticipantOrIcon>
                <Value>27075</Value>
              </RequestParticipantOrIcon>
            </GovernorRequest>
          </Values>
        </DecisionGovernorRequest>
      </DecisionRoot>
      <QuestComponent />
    </Values>
  </Asset>
  <Asset>
    <Template>Decision</Template>
    <Values>
      <Standard>
        <GUID>2001000102</GUID>
        <Name>Kegeln Decision</Name>
      </Standard>
      <Decision>
        <DecisionScreenConfig>
          <Headline>2001000201</Headline>
          <Text>
            <Value>2001000203</Value>
          </Text>
          {SCREEN}
        </DecisionScreenConfig>
        <DecisionOptions>
          <Item>
            <VectorElement>
              <InheritedIndex>0</InheritedIndex>
            </VectorElement>
            <OptionText>2001000204</OptionText>
            <CharacterNotificationOnDecisionTaken>
              {NOTRIG}
            </CharacterNotificationOnDecisionTaken>
          </Item>
          <Item>
            <OptionText>2001000205</OptionText>
            <ChallengeData>
              <CheckValue>
                <Template>FloatVariableOrValue</Template>
                <Values>
                  <FloatVariableOrValue />
                </Values>
              </CheckValue>
            </ChallengeData>
            <UnlockRequirement>
              <Conditions>
                <Template>PreConditionList</Template>
                <Values>
                  <PreConditionList />
                </Values>
              </Conditions>
            </UnlockRequirement>
            <CharacterNotificationOnDecisionTaken>
              <Template>CharacterNotificationTrigger</Template>
              <Values>
                <CharacterNotificationTrigger>
                  <Type>None</Type>
                </CharacterNotificationTrigger>
              </Values>
            </CharacterNotificationOnDecisionTaken>
          </Item>
        </DecisionOptions>
      </Decision>
      <QuestComponent />
      <DecisionComponent>
        <DecisionOutputs>
          <Item>
            <VectorElement>
              <InheritedIndex>0</InheritedIndex>
            </VectorElement>
            <SuccessOutput>
              <Item>
                <Component>2001000103</Component>
              </Item>
            </SuccessOutput>
          </Item>
          <Item />
        </DecisionOutputs>
      </DecisionComponent>
    </Values>
  </Asset>
  <!-- Outcome of "yes": 5000 denarii (good 1010017) and +1 emperor reputation, as in vanilla outcome 88515; plus a side notification. -->
  <Asset>
    <Template>Decision</Template>
    <Values>
      <Standard>
        <GUID>2001000103</GUID>
        <Name>Kegeln Outcome Yes</Name>
      </Standard>
      <Decision>
        <DecisionScreenConfig>
          <Headline>2001000201</Headline>
          <Text>
            <Value>2001000206</Value>
          </Text>
          {SCREEN}
        </DecisionScreenConfig>
        <DecisionOptions>
          <Item>
            <VectorElement>
              <InheritedIndex>0</InheritedIndex>
            </VectorElement>
            <OptionText>2001000207</OptionText>
            <CharacterNotificationOnDecisionTaken>
              {NOTRIG}
            </CharacterNotificationOnDecisionTaken>
          </Item>
        </DecisionOptions>
      </Decision>
      <QuestComponent />
      <DecisionComponent>
        <DecisionActions>
          <Item>
            <Action>
              <Template>ActionAddGoodsToItemContainer</Template>
              <Values>
                <Action />
                <ActionAddGoodsToItemContainer>
                  <Goods>
                    <Item>
                      <Good>
                        <Value>1010017</Value>
                      </Good>
                      <Amount>
                        <Value>5000</Value>
                      </Amount>
                    </Item>
                  </Goods>
                  <ItemContainerObjects>
                    <Template>ObjectFilter</Template>
                    <Values>
                      <ObjectFilter />
                    </Values>
                  </ItemContainerObjects>
                </ActionAddGoodsToItemContainer>
                <LocationFilter>
                  <AllowAllLocations>1</AllowAllLocations>
                  <AllowProcessingParticipantControlledAreas>1</AllowProcessingParticipantControlledAreas>
                  <ComponentLocation>
                    <Template>ComponentLocation</Template>
                    <Values>
                      <ComponentLocation />
                    </Values>
                  </ComponentLocation>
                  <ObjectLocations>
                    <ObjectFilter>
                      <Template>EmptyAutoCreateValue</Template>
                      <Values>
                        <EmptyAutoCreateValue />
                      </Values>
                    </ObjectFilter>
                  </ObjectLocations>
                  <AdditionalLocationFilter>
                    <Template>EmptyAutoCreateValue</Template>
                    <Values>
                      <EmptyAutoCreateValue />
                    </Values>
                  </AdditionalLocationFilter>
                </LocationFilter>
              </Values>
            </Action>
          </Item>
          <Item>
            <Action>
              <Template>ActionChangeReputation</Template>
              <Values>
                <Action />
                <ActionChangeReputation>
                  <UseProcessingParticipant>1</UseProcessingParticipant>
                  <Amount>
                    <Value>1</Value>
                  </Amount>
                </ActionChangeReputation>
              </Values>
            </Action>
          </Item>
          <Item>
            <Action>
              <Template>ActionNotification</Template>
              <Values>
                <Action />
                <ActionNotification>
                  <Notification>
                    <Template>SideNotification</Template>
                    <Values>
                      <SideNotification>
                        <IconAsset>68769</IconAsset>
                        <NotificationSideTitle>2001000201</NotificationSideTitle>
                        <HasJumpLocation>0</HasJumpLocation>
                      </SideNotification>
                      <BaseNotification>
                        <NotificationText>2001000208</NotificationText>
                        <NotificationTopic>Quests</NotificationTopic>
                      </BaseNotification>
                      <NotificationSubtitle />
                    </Values>
                  </Notification>
                </ActionNotification>
              </Values>
            </Action>
          </Item>
        </DecisionActions>
      </DecisionComponent>
    </Values>
  </Asset>

  <!-- Start trigger: registered by the Lua timer (lukas/kaiserkegeln.lua) when an invitation is due. -->
''' + trig(2001000110, 'Kegeln StartStoryline', start_story(2001000100))
if DEV:
    x += '''  <!-- DEV: Shift+F7 registers this trigger, which runs the scratch script (re-read on every run, hot-reloadable). -->
''' + trig(2001000111, 'Kegeln Dev RunScript', '''              <Template>ActionExecuteScript</Template>
              <Values>
                <Action />
                <ActionExecuteScript>
                  <ScriptFileName>data/script/content/kaiserkegeln/run.lua</ScriptFileName>
                </ActionExecuteScript>
              </Values>''') + '''
  <!-- DEV hotkeys. Bindings and Lua modules are not hot-reloaded, so they only register triggers (asset data is). -->
  <ModOp GUID="2001271" Add="ShortcutConfig/InputBindings">
''' + key('Shift;F6', 'Conditions:RegisterTriggerForCurrentParticipantNet(2001000110)') \
        + key('Shift;F7', 'Conditions:RegisterTriggerForCurrentParticipantNet(2001000111)') + '''  </ModOp>
'''
x += '</ModOps>\n'
w('data/base/config/export/assets.xml', x)

if DEV:
    w('data/script/content/kaiserkegeln/run.lua', '''-- Scratch script for the dev build (Shift+F7). Output: game log, prefix [K].
local function say(t) system.logInfo("[K] " .. tostring(t)) end
say("==== run.lua: status ====")
say("current participant: " .. tostring(Participants.GetCurrentParticipantGUID))
say("active emperor: " .. tostring(Participants.ActiveEmperor))
say("==== run.lua end ====")
''')

w('lukas/kaiserkegeln.lua', '''-- Kegeln mit dem Kaiser: timer that makes the emperor invite the player now and then.
-- Tick() is called by the mod loader. When the interval has passed, the start trigger is registered for the
-- current participant, which opens the invitation as a governor request. The wait is random (30 to 90 minutes
-- of real time). Nothing is stored in the savegame; the timer restarts whenever the game is started.
local M = {}

local START_TRIGGER = 2001000110
local MIN_INTERVAL = 30 * 60  -- seconds; each invitation comes at a random time between these two bounds
local MAX_INTERVAL = 90 * 60

local function say(t) system.logInfo("[K] " .. tostring(t)) end

local function now()
    local ok, t = pcall(function() return os.time() end)
    if ok and type(t) == "number" then return t end
    return nil
end

local seeded = false
local function randomInterval()
    if not seeded then
        seeded = true
        pcall(function() math.randomseed(os.time()) end)
    end
    local ok, r = pcall(function() return math.random(MIN_INTERVAL, MAX_INTERVAL) end)
    if ok and type(r) == "number" then return r end
    return (MIN_INTERVAL + MAX_INTERVAL) / 2
end

local ticks = 0
local started = nil
local nextAt = nil
local reported = false

function M.Tick()
    ticks = ticks + 1
    local t = now()
    if t == nil then
        if not reported then reported = true; say("os.time() is not available, timer disabled") end
        return
    end
    if started == nil then
        started = t
        local d = randomInterval()
        nextAt = t + d
        say("timer started, first invitation in " .. d .. " s")
        return
    end
    if not reported and t - started >= 10 then
        reported = true
        say("tick rate: " .. ticks .. " ticks in " .. (t - started) .. " s")
    end
    if t >= nextAt then
        local d = randomInterval()
        nextAt = t + d
        local ok, err = pcall(function() Conditions:RegisterTriggerForCurrentParticipantNet(START_TRIGGER) end)
        say("invitation due -> register trigger " .. START_TRIGGER .. ": " .. tostring(ok) .. " " .. tostring(err) .. ", next in " .. d .. " s")
    end
end

say("kaiserkegeln module loaded")
return M
''')

for f in glob.glob(os.path.join(OUT, 'data/base/config/**/*.xml'), recursive=True):
    xml.dom.minidom.parse(f)
json.load(open(os.path.join(OUT, 'modinfo.json'), encoding='utf-8'))
print('base written' + (' (dev)' if DEV else ''))
