本文档用于整理 NovelCrafter 中 **Developmental Editor** prompt 所体现的故事层面、写作层面的评价准则。

这里讨论的不是 longform writing trajectory 的过程评价，例如 Codex 是否召回、Scene Beat 是否正确、summary 是否准确、上下文是否合理等；而是 <font style="background-color:#FBDE28;">NovelCrafter 作为小说写作辅助工具，在“作品质量 / 故事质量 / 写作质量”层面默认关注哪些指标</font>。

换句话说，本文档回答的问题是：

> 如果我们只看一篇小说文本本身，或者看一个章节/scene 本身，NovelCrafter 的 Developmental Editor 会从哪些文学编辑角度判断它好不好？
>

这些准则可以作为后续长程写作评价框架中的“<font style="background-color:#FBDE28;">故事质量 / 文本质量</font>”部分，但不能直接覆盖完整的 trajectory evaluation。

完整prompt：

```json
You are an award-winning editor in the "{either(input("Genre"), "novel")}" genre.
The author is asking for advice on: "{either(input("Feedback"), "general advice")}".

They have provided you with some information regarding their story, and their story itself. Your task is to give them guidance on improving their story, based on the following guidance:

<generalAdvice>
{#if input("Feedback") is "Developmental"}
  Regardless of the genre you are helping the author with, a strong story foundation should:
   - Ensure their core concept is clear, compelling, and consistently executed throughout
   - Verify their premise creates sufficient conflict to sustain the narrative
   - Check that their story answers its central dramatic question by the conclusion
   - Confirm their theme is explored through plot and character choices
    You can ask the author to clarify these, if not provided.

  The narrative arc should:
   - Verify the story contains a clear beginning (setup), middle (complications), and end (resolution)
   - Ensure the stakes escalate as the story progresses
   - Check that subplots connect meaningfully to the main storyline or theme
   - Confirm the climax resolves the central conflict in a satisfying way
{#endif}
{#if input("Feedback") is "Structural"}
  When doing structural edits:
  <pacingMomentum>
  Pacing and Momentum
  - Verify each scene moves the story forward through plot advancement or character development
  - Ensure action and reflection are appropriately balanced for your genre
  - Check for unnecessary scenes or passages that can be cut to improve momentum
  - Confirm key turning points occur at effective intervals to maintain reader engagement
  </pacingMomentum>
  <scenes>
  Scene Construction
  - Ensure each scene has a clear purpose and creates meaningful change
  - Verify scenes begin as late as possible and end as early as possible
  - Check that transitions between scenes and chapters maintain narrative flow
  - Confirm scenes follow a logical sequence that builds tension toward the climax
  </scenes>
  <pointOfView>
  - Verify POV choices (first-person, third-person, etc.) serve the story effectively
  - Ensure POV remains consistent within scenes or shifts deliberately and clearly
  - Check that multiple POVs (if used) each contribute unique value to the narrative
  - Confirm the narrative distance (close or distant) serves the emotional impact needed
  </pointOfView>
{#endif}
{#if input("Feedback") is "Pacing"}
  - Vary sentence, paragraph, and chapter length to control reading speed—shorter for tension, longer for reflection
  - Alternate between scene (showing action in real-time) and summary (condensing less critical periods) based on emotional importance
  - Ensure each major plot development is given sufficient space for emotional impact before moving to the next
  - Accelerate pacing toward major turning points and the climax by removing obstacles to quick reading
  - Recognize genre expectations for pacing—thrillers demand quicker pacing than literary fiction, but all stories need variation
{#endif}
{#if input("Feedback") is "Dialogue"}
  - Craft speech patterns and word choices that reflect each character's background, education, personality, and emotional state
  - Use dialogue to create conflict, reveal character, advance plot, and deliver information—ideally accomplishing multiple goals simultaneously
  - Balance dialogue with action, reaction, and interior thought to create rhythm and emphasize important moments
  - Cut greetings, small talk, and obvious statements unless they serve character or story purposes
  - Remember that what remains unsaid can be as powerful as what's spoken—use subtext to create depth
{#endif}
{#if input("Feedback") is "Characterization"}
  - Give each character a distinctive combination of desire, fear, and flaw that drives their actions throughout the story
  - Reveal character through specific choices made under pressure rather than through exposition
  - Ensure characters' internal landscapes (thoughts, emotions, beliefs) align with or meaningfully contradict their external actions
  - Allow room for both explicit change and subtle evolution in your character arcs
  - Create secondary characters with their own goals that sometimes complement, sometimes complicate the protagonist's journey
{#endif}
</generalAdvice>

{#if "Romance" in input("role") }
  <romance>
    When specifically editing a Romance Novel, you should also:

    {#if input("Feedback") is "Developmental"}
      Focus on the foundation of the romance: ensure both main characters have distinct personalities with compelling chemistry, establish meaningful obstacles that challenge their relationship, and create a romance arc with clear emotional progression and stakes that matter.
    {#endif}
    {#if input("Feedback") is "Structural"}
      Architect your romance effectively: position the meet-cute early, space relationship milestones appropriately throughout, ensure turning points carry emotional weight, verify the black moment feels earned, and create a resolution that satisfies without feeling rushed or too convenient.
    {#endif}
    {#if input("Feedback") is "Pacing"}
      Ensure that the author crafted a rhythm that mirrors realistic relationship development: allow the romance to unfold at a believable pace, space emotional high points strategically throughout the story, and ensure intimate moments occur when emotionally justified—never rushing key relationship milestones or resolutions.
    {#endif}
    {#if input("Feedback") is "Characterization"}
      Ensure that the author has created protagonists readers will invest in: give each character authentic flaws, emotional wounds that influence their approach to love, clear growth arcs tied to the romance, and interests beyond the relationship itself—while ensuring their vulnerabilities emerge naturally as trust builds.
    {#endif}
    {#if input("Feedback") is "Dialogue"}
      Make conversations reveal character and advance the relationship: develop distinct speaking styles for each protagonist, incorporate meaningful subtext in romantic exchanges, balance what's said against what remains unspoken, and ensure dialogue evolves naturally from casual to intimate as the relationship develops.
    {#endif}
  </romance>
{#endif}

{#if "Fantasy" in input("role")}
  <fantasy>
    When specifically editing a Fantasy Novel, you should also:
    {#if input("Feedback") is "Developmental"}
      - Ensure your magic system has clear rules, limitations, and consequences that remain consistent throughout
      - Verify worldbuilding elements (politics, religions, cultures) have logical internal structures that influence character choices
      - Check that fantasy elements serve the story's themes rather than existing solely for spectacle
      - Balance familiar fantasy tropes with innovative elements that make your work distinctive
      - Confirm your fantasy world has authenticity—even the most magical realms need internal logic and consistency
    {#endif}
    {#if input("Feedback") is "Structural"}
      - Assess the balance between worldbuilding exposition and plot progression, especially in early chapters
      - Ensure quest structures (if used) feature meaningful milestones that build toward the climax
      - Verify that magical elements and revelations escalate in significance throughout the narrative
      - Check that subplots enhance understanding of your fantasy world while supporting the main conflict
      - Confirm your ending resolves both the immediate conflict and addresses wider implications for your fantasy world
    {#endif}
    {#if input("Feedback") is "Pacing"}
      - Balance immersive worldbuilding sequences with plot-advancing action to maintain momentum
      - Allow sufficient time for readers to absorb new fantasy concepts before introducing additional complexities
      - Recognize that fantasy often requires a slower opening to establish the world, but still needs a compelling hook
      - Vary pacing between political intrigue, character development, magical discovery, and action sequences to create rhythm
    {#endif}
    {#if input("Feedback") is "Characterization"}
      - Ensure protagonists have relatable motivations and conflicts despite their fantastic abilities or circumstances
      - Develop antagonists with comprehensible goals beyond generic evil, shaped by the unique aspects of your fantasy world
      - Create characters whose relationship with magic/fantasy elements reveals their values and worldview
      - Balance character archetypes familiar to fantasy readers with surprising depths or subversions
      - Ensure diverse characters reflect the complexity of your fantasy world rather than simply importing real-world stereotypes
    {#endif}
    {#if input("Feedback") is "Dialogue"}
      - Ensure magical terminology, made-up words, and fantasy jargon are introduced organically and used consistently
      - Use dialogue to reveal aspects of your world's customs, beliefs, and magic without obvious exposition
      - Create distinct voices for different fantasy races, cultures, or magical practitioners that reflect their worldviews
    {#endif}
  </fantasy>
{#endif}

{include("Novelcrafter/Chat/DefaultContext")}
{include("Novelcrafter/Chat/DefaultInstructions")}

Read the provided material first before analyzing it based on the criteria provided.
```

---

## 1. Prompt 定位
Developmental Editor 的角色设定是：

```plain
You are an award-winning editor in the "{Genre}" genre.
The author is asking for advice on: "{Feedback}".
```

也就是说，它不是一个正文生成器，也不是一个自动修订器，而是一个 **编辑诊断器 / 写作顾问 / Critic**。

它的输入由两个主要变量控制：

```plain
Genre：作品类型，例如 novel、romance、fantasy、psychological horror 等。
Feedback：用户希望获得哪类反馈，例如 Developmental、Structural、Pacing、Dialogue、Characterization。
```

因此，它的运行逻辑可以抽象为：

```plain
用户提供故事材料
→ 选择 Genre
→ 选择 Feedback 类型
→ Developmental Editor 根据对应准则分析故事
→ 输出修改建议，而不是直接替作者改全文
```

在 NovelCrafter 的产品定位中，Developmental Editor 适合帮助人类作者发现故事问题，然后由作者决定是否以及如何修改。

---

## 2. Prompt 中的 Feedback 类型
Developmental Editor 的评价准则主要分成五类：

```plain
1. Developmental
2. Structural
3. Pacing
4. Dialogue
5. Characterization
```

这五类基本覆盖了传统小说编辑中的主要问题域：

| Feedback 类型 | 关注对象 | 适合评价的文本粒度 |
| --- | --- | --- |
| Developmental | 故事地基、核心概念、主题、整体弧线 | 全书、完整大纲、全局结构 |
| Structural | 场景结构、章节推进、转场、视角 | 章节、scene、章节组 |
| Pacing | 节奏、展开/压缩、阅读速度、情绪分配 | 章节、scene、全文 |
| Dialogue | 对话声音、冲突、信息传递、潜台词 | 对话段落、scene |
| Characterization | 人物动机、缺陷、压力下选择、人物弧光 | 人物线、scene、全文 |


其中，Developmental 和 Structural 是最适合长程写作评价的基础层；Pacing、Dialogue、Characterization 更适合用于正文质量和局部写作质量判断。

---

## 3. Developmental：故事地基层评价
Developmental 反馈关注的是故事是否拥有稳定、清楚、足以支撑全文的底层设计。

### 3.1 核心概念是否清楚、有吸引力，并持续执行
评价问题：

```plain
这个故事的核心概念是否清楚？
它是否足够有吸引力？
故事后续是否持续围绕这个核心概念展开？
```

例如，在《选择室》这种密室心理惊悚中，核心概念是：

```plain
主角被困在选择室中，被迫重新面对过去的道德选择。
```

如果后续文本不断转向外部追逐、动作逃亡、警察调查，而忽视“选择室审判”和“道德选择”，则说明核心概念没有被持续执行。

### 3.2 Premise 是否产生足够冲突
评价问题：

```plain
故事 premise 是否天然包含冲突？
这个冲突是否足以支撑完整篇幅？
主角是否被迫行动，而不是被动旁观？
```

弱 premise 常见问题：

```plain
主角只是观察事件；
规则没有强迫主角做选择；
冲突只靠氛围维持，没有真正的对抗关系；
故事没有足够压力推动后续章节。
```

强 premise 通常会包含：

```plain
明确压力；
明确代价；
明确不可逃避的选择；
主角内在缺陷与外部困境之间的冲突。
```

### 3.3 central dramatic question是否最终被回答
central dramatic question是贯穿全篇的核心问题，例如：

```plain
小帅是否会承认自己在旧案中的真实责任？
选择室的审判到底是惩罚还是救赎？
审判者是谁？
```

评价时要看：

```plain
故事开头是否提出了足够清晰的中央问题；
中段是否围绕这个问题推进；
结尾是否正面回应这个问题；
是否用含混或逃避的方式结束核心冲突。
```

开放式结尾可以存在，但不能回避中央问题。开放式结尾应该留下余味，而不是留下未完成感。

### 3.4 主题是否通过剧情和人物选择体现
Prompt 中强调主题应通过 plot 和 character choices 探索，而不是靠作者说教。

评价问题：

```plain
故事主题是否通过人物选择体现？
人物是否在压力下做出能揭示主题的选择？
主题是否只是口号，还是转化成了剧情行动？
```

例如，“责任逃避”这个主题不应该只通过旁白说明，而应该体现在：

```plain
小帅如何解释自己的旧选择；
小帅是否继续选择商业逻辑；
小帅是否愿意承认小美事件中的责任；
审判规则如何一层层剥掉他的借口。
```

### 3.5 叙事弧是否有 setup / complication / resolution
Developmental 还关注故事是否有清晰的叙事弧：

```plain
Beginning：建立人物、世界、冲突和问题；
Middle：制造复杂化、升级冲突、揭示更多信息；
End：解决核心冲突，回应中央问题。
```

常见问题：

```plain
开头只有氛围，没有明确问题；
中段只是重复同类事件，没有复杂化；
结尾突然反转，但缺少铺垫；
高潮没有解决主冲突。
```

### 3.6 Stakes 是否逐步升级
评价问题：

```plain
故事的风险、代价、道德压力是否逐章升级？
每一章是否比前一章揭示更多、逼迫更深？
主角是否越来越难维持原有自我辩解？
```

以心理惊悚为例，升级不一定是物理危险升级，也可以是：

```plain
信息更私人；
旧案后果更严重；
主角借口越来越少；
审判者提问越来越直接；
主角自我认知越来越崩塌。
```

### 3.7 支线是否服务主线或主题
Prompt 中提到 subplots 需要 meaningfully connect to main storyline or theme。

评价问题：

```plain
支线是否只是额外信息？
支线是否帮助解释人物选择？
支线是否推动主题？
支线是否在结尾被回收或转化？
```

对于 V0 写作任务，如果暂时不做复杂 subplot，这个维度可以先弱化。但在后续长篇版本中，它会变得非常重要。

### 3.8 高潮是否解决核心冲突
高潮不是“大场面”，而是核心冲突的集中解决。

评价问题：

```plain
高潮是否回应了故事最核心的问题？
主角是否在高潮中做出了关键选择？
高潮是否改变了人物状态或故事关系？
结尾是否只是信息揭露，而缺少人物选择？
```

对于“选择室”类型故事，高潮应当不是单纯揭示“小美发生了什么”，而是小帅是否终于面对自己的责任。

---

## 4. Structural：结构层评价
Structural 反馈关注的是故事如何被组织，scene 与 chapter 是否有效推进，视角和转场是否稳定。

Prompt 中 Structural 分成三个子块：

```plain
Pacing and Momentum
Scene Construction
Point of View
```

---

### 4.1 Pacing and Momentum：推进力与动量
#### 4.1.1 每个 scene 是否推动故事
评价问题：

```plain
这个 scene 是否带来了新的剧情进展？
是否带来了人物状态变化？
是否揭示了新的信息？
如果删除这个 scene，故事是否会受到影响？
```

如果删除一个 scene 后故事基本不变，说明它可能是冗余 scene。

#### 4.1.2 行动与反思是否平衡
不同题材对 action / reflection 的比例要求不同。

心理惊悚可以有较多内心反应，但仍然需要外部推动：

```plain
新证据出现；
倒计时变化；
审判者提问；
旧案录像播放；
主角做出选择。
```

如果只有心理描写，没有事件变化，节奏会停滞。

如果只有事件推进，没有反应和消化，心理惊悚的情绪承载又会不足。

#### 4.1.3 是否存在可删段落
评价问题：

```plain
是否多次重复同一环境描写？
是否反复用同样的词表达压迫感？
是否有大量不增加信息的心理判断？
是否有只服务氛围、不服务剧情的段落？
```

我们在《选择室》第一章评审中看到的问题正属于这一类：白墙、冷光、压迫、冰冷等描写多次重复，但新增信息不足。

#### 4.1.4 关键转折点是否分布合理
评价问题：

```plain
重要信息是否都堆在结尾？
前半部分是否过长铺垫？
章节之间是否有明确转折？
每个转折是否能维持读者继续读下去的动力？
```

长程写作中，turning points 不能只在最后出现，而应该分阶段分布。

---

### 4.2 Scene Construction：场景构造
#### 4.2.1 每个 scene 是否有清晰目的
一个 scene 应该至少承担一个功能：

```plain
推动剧情；
揭示信息；
改变人物关系；
制造选择；
改变人物状态；
加深主题。
```

如果一个 scene 只有“营造氛围”，但没有信息和状态变化，它在长程结构中通常是不够的。

#### 4.2.2 每个 scene 是否产生 meaningful change
Prompt 中强调 scene creates meaningful change。

评价问题：

```plain
scene 结束时，世界状态是否变了？
人物知道的信息是否变了？
人物的心理立场是否变了？
读者对谜团的理解是否变了？
下一章是否因为这个 scene 而不同？
```

可以用一个简单的 delta 表达：

```plain
Before scene：小帅认为自己只是被随机绑架。
After scene：小帅知道这是针对三年前旧案的审判。
```

如果没有 delta，scene 功能不足。

#### 4.2.3 Scene 是否 begin late / end early
这条准则来自传统编辑经验：scene 应尽量从冲突点附近开始，并在完成核心变化后及时结束。

常见问题：

```plain
进入正题太慢；
大量铺垫无关动作；
核心事件完成后继续拖尾；
重复解释已经明确的信息。
```

在自动写作中，模型常常为了“写得像小说”而过度铺陈，这条准则可以帮助控制冗余。

#### 4.2.4 Scene / Chapter transition 是否自然
评价问题：

```plain
章节之间是否自然承接？
后一章是否记得前一章已经发生的事？
是否重复开场或重复规则说明？
是否突然跳到无关场景？
```

这部分和我们后续的 workflow continuity 有交叉，但在故事层面，它仍然是文本结构质量的一部分。

#### 4.2.5 Scenes 是否按逻辑顺序累积 tension
评价问题：

```plain
场景顺序是否因果清楚？
紧张感是否逐步累积？
信息释放是否有先后逻辑？
是否出现可以任意调换顺序的章节？
```

如果章节顺序可以随意调换，说明结构推进不够强。

---

### 4.3 Point of View：视角与叙事距离
#### 4.3.1 POV 是否服务故事
评价问题：

```plain
当前视角是否最适合这个故事？
第一人称 / 第三人称 / 多 POV 是否有明确作用？
视角是否帮助制造信息差和情绪压力？
```

例如心理惊悚常适合贴近主角的限知视角，因为读者需要和主角一起承受未知和不确定。

#### 4.3.2 POV 是否稳定
常见问题：

```plain
一段中突然进入其他角色内心；
本来是限知视角，却泄露了主角不可能知道的信息；
叙事视角在章节内无意义跳动。
```

长程写作中，POV 漂移会破坏沉浸感和信息控制。

#### 4.3.3 多 POV 是否各有独特价值
如果使用多 POV，每个视角都应提供独特价值，而不是重复信息。

评价问题：

```plain
每个 POV 是否有独特信息、情绪或价值立场？
是否只是为了换人称而换？
多个 POV 是否共同推动主线？
```

V0 可以先不做多 POV，但这个准则对后续复杂长篇有价值。

#### 4.3.4 叙事距离是否服务情绪效果
评价问题：

```plain
叙事距离是贴近人物，还是保持冷静观察？
这种距离是否符合当前 scene 的情绪目标？
```

例如“冷静克制的心理惊悚”不一定需要大量直接情绪词，而可以通过动作、环境和选择表现心理压力。

---

## 5. Pacing：节奏层评价
Pacing 关注文本如何控制读者的阅读速度、情绪密度和信息消化。

### 5.1 句长、段长、章节长度是否有变化
Prompt 中提到通过 sentence、paragraph、chapter length 控制阅读速度。

评价问题：

```plain
紧张段落是否更短、更密？
反思段落是否有足够空间？
全文句式是否单调？
每章长度是否与章节功能匹配？
```

自动生成文本常见问题是句式长度和节奏模式过于均匀，导致“AI 腔”。

### 5.2 Scene 与 Summary 是否合理交替
Prompt 提到要根据 emotional importance 在 scene 和 summary 之间切换。

评价问题：

```plain
关键冲突是否被实时展开？
不重要的过程是否被压缩？
是否把重要情绪节点一笔带过？
是否把无关动作写得过细？
```

这对应小说写作中的 show / summarize balance。

### 5.3 重大剧情点是否有足够情绪空间
评价问题：

```plain
重要真相揭示后，人物是否有反应？
关键选择是否有心理压力？
重大转折是否来得过快？
读者是否有时间理解其意义？
```

如果一个重大反转只用一句话说完，读者很难感到冲击。

### 5.4 越接近高潮是否加速
Prompt 中提到 toward major turning points and climax should accelerate。

评价问题：

```plain
故事后半段是否逐渐收束？
是否越写越散？
临近高潮是否还在引入大量新设定？
结尾是否被拖慢？
```

### 5.5 是否符合类型节奏期待
不同类型节奏不同。

心理惊悚通常需要：

```plain
开头快速建立异常；
中段持续信息揭示；
每次揭示都带来新的心理压力；
结尾集中完成认知反转或道德审判。
```

如果前半段大量铺陈环境，却迟迟不进入道德选择，节奏就会偏慢。

---

## 6. Dialogue：对话层评价
Dialogue 关注人物说话是否有角色性、冲突性和叙事功能。

### 6.1 语言是否符合人物背景、教育、性格和情绪
评价问题：

```plain
不同角色说话是否有区别？
人物语言是否符合职业和性格？
情绪变化是否影响说话方式？
```

例如：

```plain
小帅作为产品经理，可能会使用流程、风险、优先级、成本、结果等词汇。
审判者则应更冷静、准确、像宣读规则。
小美的语言应体现她对用户安全的专业坚持。
```

### 6.2 对话是否同时承担多个功能
有效对话通常不只传递信息，还应同时：

```plain
制造冲突；
揭示人物；
推动剧情；
暴露关系；
制造潜台词。
```

如果对话只是解释设定，它会显得功能单一。

### 6.3 对话与动作、反应、内心是否平衡
评价问题：

```plain
对话是否悬空？
人物说完话后是否有反应？
动作是否强化了对话中的压力？
内心活动是否重复解释已经说出的内容？
```

### 6.4 是否删掉无效寒暄和显而易见的话
Prompt 中明确提到 cut greetings, small talk, obvious statements。

评价问题：

```plain
对话是否有大量“你是谁”“你想干什么”式重复？
寒暄是否服务人物或剧情？
是否把读者已经知道的信息又说了一遍？
```

### 6.5 是否有潜台词
好的对话不总是把意思说透。

评价问题：

```plain
角色是否有不愿明说的东西？
对话表层和真实意图是否存在张力？
沉默、回避、转移话题是否服务人物？
```

例如小帅在旧案中不断强调“我只是按流程”，潜台词可能是“不想承认我其实在自保”。

---

## 7. Characterization：人物层评价
Characterization 关注人物是否成立、是否有驱动力、是否通过选择而不是说明来展现。

### 7.1 人物是否有 desire / fear / flaw
Prompt 中强调角色应有 desire、fear 和 flaw。

评价问题：

```plain
人物想要什么？
人物害怕什么？
人物的缺陷是什么？
这些是否驱动了人物行动？
```

例如小帅：

```plain
Desire：证明自己的选择是理性的、正确的。
Fear：承认自己并非无辜旁观者。
Flaw：习惯用逻辑和流程合理化自保。
```

这三者共同驱动他的行为。

### 7.2 是否通过压力下的选择展现人物
Prompt 强调通过 choices made under pressure 而不是 exposition 揭示人物。

评价问题：

```plain
人物是否在关键压力下做选择？
这些选择是否揭示了人物真实价值观？
人物是否只是被旁白描述成某种人？
```

这是心理惊悚和道德困境故事的核心。

### 7.3 内心世界与外部行动是否一致或有意义地矛盾
评价问题：

```plain
人物内心想法和行动是否有逻辑关系？
如果人物口头说 A、行动做 B，这种矛盾是否有意义？
人物是否为了剧情需要突然改变立场？
```

例如小帅口头坚持“我是为了大局”，但行动上始终选择保护自己的职业风险，这种矛盾是有意义的。

### 7.4 人物是否有变化空间
Prompt 提到 explicit change 和 subtle evolution。

评价问题：

```plain
人物是否从开头到结尾发生变化？
变化是否有阶段？
变化是否由剧情压力推动？
变化是否过快或过突然？
```

常见弱点：

```plain
主角前几章一直辩解，最后突然忏悔；
没有足够中间过程；
人物弧光像作者安排，而不是被剧情逼出来。
```

### 7.5 配角是否有自身目标
Prompt 也强调 secondary characters 应有 own goals。

评价问题：

```plain
配角是否只是工具人？
配角是否有自己的目标、立场和行动？
配角目标是否会支持或阻碍主角？
```

例如小美不能只是“旧案受害者”，她应该有自己的专业判断和价值立场：她坚持用户安全，不只是为了服务小帅的愧疚。

---

## 8. Genre-specific 插件思路
Developmental Editor 对 Romance 和 Fantasy 额外加入了类型专属评价准则。这说明一个成熟评价框架不应该只有通用维度，还应该有：

```plain
Base Rubric + Genre Rubric
```

### 8.1 Romance 插件启发
Romance 分支关注：

```plain
人物化学反应；
关系障碍；
情感推进；
关键关系节点；
black moment；
情感解决是否自然；
对话是否推动关系发展。
```

这说明对于特定类型，评价应关注该类型最核心的读者期待。

### 8.2 Fantasy 插件启发
Fantasy 分支关注：

```plain
魔法系统规则、限制和后果；
世界观内部逻辑；
幻想元素是否服务主题；
世界真实性；
世界构建与剧情推进的平衡；
专有术语是否自然引入。
```

这说明类型插件需要覆盖该类型的特殊结构问题。

### 8.3 对心理惊悚 / 密室审判题材的插件建议
基于我们当前的小说类型，可以设计一个 Psychological Thriller / Locked-room Moral Trial 插件：

```plain
1. 密室规则是否清楚且自洽；
2. 审判机制是否持续有效；
3. 每次选择是否具有真实道德张力；
4. 惊悚感是否来自心理压力和信息揭示，而不是单纯血腥；
5. 信息释放是否逐步推进；
6. 最终反转是否有前文铺垫；
7. 主角自我辩解是否逐步瓦解；
8. 操控者/审判者是否保持稳定逻辑。
```

这个插件不属于 NovelCrafter 原始 prompt，但符合它的 genre-specific 设计思路。

---

## 9. 可转化为评价框架的维度
基于 Developmental Editor，可以提炼出以下故事/写作层面评价维度：

### 9.1 Story Foundation
关注：

```plain
核心概念；
premise 冲突；
central dramatic question；
主题表达；
结尾回应。
```

评分问题：

> 故事是否有一个清楚、有吸引力、可持续执行的核心？
>

### 9.2 Narrative Arc
关注：

```plain
setup / complications / resolution；
风险升级；
支线连接；
高潮解决核心冲突。
```

评分问题：

> 故事是否有清楚的起承转合和逐步升级的叙事弧？
>

### 9.3 Structural Progression
关注：

```plain
scene purpose；
meaningful change；
transition；
logical sequence；
tension buildup。
```

评分问题：

> 每个章节/场景是否推动了剧情或人物变化？
>

### 9.4 Pacing
关注：

```plain
阅读速度；
展开与压缩；
重大节点的情绪空间；
类型节奏期待。
```

评分问题：

> 节奏是否服务故事，而不是拖沓、重复或过快跳转？
>

### 9.5 Characterization
关注：

```plain
desire / fear / flaw；
压力下选择；
内外一致或有意义矛盾；
人物变化；
配角独立性。
```

评分问题：

> 人物是否通过选择和行动成立，而不是只靠介绍成立？
>

### 9.6 Dialogue
关注：

```plain
角色声音；
冲突；
剧情推进；
信息传递；
潜台词；
无效寒暄控制。
```

评分问题：

> 对话是否同时服务人物、冲突和剧情？
>

### 9.7 POV / Narrative Distance
关注：

```plain
视角选择；
视角稳定性；
多 POV 价值；
叙事距离。
```

评分问题：

> 叙事视角是否稳定，并服务当前故事的情绪效果？
>

### 9.8 Genre Fulfillment
关注：

```plain
类型核心期待是否满足；
类型特有机制是否自洽；
类型元素是否服务主题。
```

评分问题：

> 作品是否完成了该类型小说承诺给读者的核心体验？
>

---

## 10. 与轨迹层评价的边界
本文档只覆盖故事层面和写作层面评价，不覆盖完整的 longform writing trajectory。

也就是说，它评价：

> 故事是否成立；  
章节是否推进；  
人物是否成立；  
节奏是否合理；  
对话是否有效；  
类型体验是否完成。
>

它不评价，或只间接涉及：

> Codex 是否正确召回；  
Scene Beat 是否符合 schema；  
Beat 是否被忠实扩写；  
summary_after 是否准确；  
上下文拼接是否合理；  
轨迹是否适合 SFT；  
模型是否按 workflow 执行。
>

因此，Developmental Editor-derived rubric 应被放在整体评价框架的一个子模块中：

```plain
Longform Writing Evaluation
├── Workflow / Trajectory Evaluation
├── Memory / Consistency Evaluation
└── Story / Writing Quality Evaluation  ← 本文档覆盖
```

---

## 11. V0 故事质量 Rubric 草案
可以先用 1-5 分制。

| 维度 | 1 分 | 3 分 | 5 分 |
| --- | --- | --- | --- |
| Story Foundation | 核心概念模糊，冲突不足 | 核心概念清楚但执行不稳定 | 核心概念清楚、有冲突，并贯穿全文 |
| Narrative Arc | 没有明显起承转合 | 有基本结构但风险升级弱 | setup、complication、resolution 清楚，风险逐步升级 |
| Structural Progression | 场景可删，缺少变化 | 部分场景推动故事，部分重复 | 每个主要场景都有目的和 meaningful change |
| Pacing | 拖沓、重复或跳转过快 | 基本可读，但节奏变化有限 | 展开/压缩合理，重大节点有足够情绪空间 |
| Characterization | 人物扁平，动机不清 | 主要人物基本成立，但变化不够自然 | 人物 desire/fear/flaw 清楚，通过压力下选择展现 |
| Dialogue | 对话只解释信息或寒暄 | 有一定人物声音和剧情功能 | 对话同时推动冲突、人物和信息，并有潜台词 |
| POV / Distance | 视角混乱或无意义跳动 | 视角基本稳定 | 视角和叙事距离稳定服务情绪效果 |
| Genre Fulfillment | 类型体验缺失或跑偏 | 部分满足类型期待 | 类型核心体验稳定且服务主题 |


这个 rubric 可以作为后续 evaluator 的故事/文本质量部分。

---

## 12. 当前结论
NovelCrafter 的 Developmental Editor prompt 提供了一套相对成熟的小说编辑评价框架。它的价值主要在于：

```plain
1. 把故事质量拆成 Developmental、Structural、Pacing、Dialogue、Characterization 等维度；
2. 每个维度下都有可操作的编辑检查点；
3. 支持根据 genre 添加类型专属准则；
4. 适合作为我们后续 Story / Writing Quality Evaluator 的基础。
```

但它不能直接成为完整的长程写作评价框架，因为它没有覆盖 workflow、Codex、Scene Beats、上下文管理和写后记忆等轨迹层问题。

因此，推荐做法是：

```plain
Developmental Editor-derived rubric
→ 作为故事/写作质量评价子模块

NovelCrafter workflow reverse engineering
→ 作为流程/轨迹质量评价子模块
```

两者结合，才能形成完整的 longform writing evaluation framework。
