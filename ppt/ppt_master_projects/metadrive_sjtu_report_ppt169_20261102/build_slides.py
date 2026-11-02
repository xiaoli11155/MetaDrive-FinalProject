from pathlib import Path
import argparse
import html

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "svg_output"
OUT.mkdir(exist_ok=True)

W, H = 1280, 720
RED, DARK_RED, GOLD, BLUE = "#C8161D", "#8F1016", "#D4AF37", "#4E79A7"
INK, MUTED, PALE, LINE = "#202124", "#646A73", "#F6F3F0", "#D8D5D0"
FONT = "Microsoft YaHei, Arial"


def esc(s):
    return html.escape(str(s), quote=True)


def text(x, y, s, size=24, fill=INK, weight=400, anchor="start", family=FONT):
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>'


def lines(x, y, items, size=24, fill=INK, gap=34, weight=400, anchor="start"):
    return "".join(text(x, y+i*gap, s, size, fill, weight, anchor) for i, s in enumerate(items))


def rect(x, y, w, h, fill="none", stroke="none", sw=1, rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def image(x, y, w, h, name, fit="xMidYMid meet"):
    return f'<image href="../images/{name}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="{fit}"/>'


def play(cx, cy, r=32):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" fill-opacity="0.92"/><polygon points="{cx-8},{cy-14} {cx-8},{cy+14} {cx+16},{cy}" fill="{RED}"/>'


def chrome(page, title, section="METADRIVE · 强化学习自动驾驶"):
    title_size = 38 if len(title) > 25 else 42
    return (
        '<g id="page-chrome">'
        + rect(0, 0, W, 8, RED)
        + text(64, 38, section, 14, MUTED, 600)
        + text(64, 94, title, title_size, INK, 700)
        + f'<line x1="64" y1="680" x2="1216" y2="680" stroke="{LINE}" stroke-width="1"/>'
        + text(64, 704, "MetaDrive Final Project · 真实实验数据", 14, MUTED)
        + text(1216, 704, f"{page:02d}", 15, RED, 700, "end")
        + '</g>'
    )


def svg(page, role, body, title=None):
    content = rect(0, 0, W, H, "#FFFFFF") + (chrome(page, title) if title else "") + body
    content = f'<g id="page-content" data-pptx-bounds="0 0 1280 720">{content}</g>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 720" width="1280" height="720" data-pptx-page-role="{role}" font-family="{FONT}">{content}</svg>'''


def p01():
    b = '<g id="identity">' + rect(0, 0, W, H, "#FFFFFF") + rect(0, 0, 22, H, RED)
    b += text(72, 82, "METADRIVE · FINAL PROJECT", 18, RED, 700)
    b += lines(72, 198, ["MetaDrive 强化学习", "自动驾驶"], 58, INK, 74, 700)
    b += text(74, 386, "从模仿学习到课程学习，让智能体在复杂交通中完成闭环驾驶", 28, MUTED, 400)
    b += rect(72, 445, 706, 2, RED)
    b += text(72, 495, "Behavior Cloning  ×  PPO  ×  Curriculum Learning", 24, BLUE, 600)
    b += text(72, 630, "项目汇报  |  2026", 18, MUTED)
    b += '</g><g id="route-motif">'
    pts = [(880,560),(880,455),(1010,455),(1010,330),(1140,330),(1140,190)]
    b += '<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="#E6E1DC" stroke-width="48" stroke-linecap="round" stroke-linejoin="round"/>'
    b += '<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="'+RED+'" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    for x,y in [pts[0],pts[2],pts[4],pts[5]]: b += f'<circle cx="{x}" cy="{y}" r="11" fill="{RED}"/>'
    b += '</g>'
    return svg(1, "cover", b)


def p02():
    title="任务是在随机道路与交通中安全到达终点"
    b='<g id="simulation-hero">'+rect(64,126,820,500,"#111111",rx=14)+image(64,126,820,500,"success_seed_1023_last.jpg","xMidYMid slice")+play(474,376,38)+'</g>'
    b+='<g id="task-facts">'+rect(914,126,302,500,PALE,rx=14)
    facts=[("随机地图","每个 episode 生成不同道路"),("连续控制","转向与油门/制动联合输出"),("三类结局","到达、碰撞或驶出道路")]
    for i,(a,c) in enumerate(facts):
        y=180+i*138
        b+=f'<circle cx="956" cy="{y}" r="19" fill="{RED}"/>'+text(956,y+7,str(i+1),18,"#FFFFFF",700,"middle")
        b+=text(990,y+2,a,24,INK,700)+text(956,y+42,c,17,MUTED)
    b+=text(956,581,"点击视频查看一次成功驾驶",17,RED,600)+'</g>'
    return svg(2,"hero",b,title)


def p03():
    title="155 维观测映射为 2 维连续控制"
    b='<g id="observation-stack">'+rect(64,145,350,455,PALE,rx=14)+text(94,190,"观测输入 · 155-D",28,RED,700)
    items=[("导航与车道","目标方向、车道边界"),("车辆状态","速度、转向、横纵向状态"),("环境感知","激光雷达与邻车信息")]
    for i,(a,c) in enumerate(items):
        y=250+i*106;b+=rect(94,y-32,290,78,"#FFFFFF",LINE,1,10)+text(116,y,a,22,INK,700)+text(116,y+28,c,16,MUTED)
    b+='</g><g id="policy-core">'+rect(488,254,300,174,RED,rx=18)+text(638,319,"PPO POLICY",25,"#FFFFFF",700,"middle")+text(638,360,"π(a | s)",34,"#FFFFFF",700,"middle")+text(638,397,"融合观测并输出动作",17,"#FFFFFF",400,"middle")+'</g>'
    b+=f'<g id="signal-flow"><line x1="414" y1="341" x2="488" y2="341" stroke="{RED}" stroke-width="4"/><polygon points="488,341 472,332 472,350" fill="{RED}"/><line x1="788" y1="341" x2="862" y2="341" stroke="{RED}" stroke-width="4"/><polygon points="862,341 846,332 846,350" fill="{RED}"/></g>'
    b+='<g id="action-output">'+rect(862,190,354,302,"#FFFFFF",RED,2,14)+text(892,235,"连续动作 · 2-D",28,RED,700)
    b+=rect(892,274,294,72,PALE,rx=10)+text(916,318,"Steering",23,INK,700)+text(1162,318,"[-1, 1]",18,BLUE,700,"end")
    b+=rect(892,370,294,72,PALE,rx=10)+text(916,414,"Throttle / Brake",23,INK,700)+text(1162,414,"[-1, 1]",18,GOLD,700,"end")+'</g>'
    b+='<g id="termination-note">'+text(64,645,"策略以闭环方式持续决策，直到到达终点、碰撞、驶出道路或达到时限。",19,MUTED)+'</g>'
    return svg(3,"content",b,title)


def p04():
    title="BC 提供驾驶先验，PPO 在逐级交通中继续优化"
    stages=[("IDM 专家","生成示范"),("行为克隆","学习动作先验"),("无交通 PPO","稳定路线跟随"),("低密度 PPO","学习基础避让"),("高密度 PPO","处理路口冲突")]
    b='<g id="curriculum-ladder">'
    xs=[74,302,530,758,986]
    for i,((a,c),x) in enumerate(zip(stages,xs)):
        color=[MUTED,GOLD,BLUE,RED,DARK_RED][i]
        b+=rect(x,232,188,186,"#FFFFFF",color,3,14)+f'<circle cx="{x+94}" cy="{232}" r="25" fill="{color}"/>'+text(x+94,240,str(i+1),20,"#FFFFFF",700,"middle")
        b+=text(x+94,308,a,23,INK,700,"middle")+text(x+94,350,c,17,MUTED,400,"middle")
        if i<4: b+=f'<line x1="{x+188}" y1="325" x2="{x+228}" y2="325" stroke="{LINE}" stroke-width="5"/><polygon points="{x+228},325 {x+212},316 {x+212},334" fill="{LINE}"/>'
    b+='</g><g id="method-takeaway">'+rect(176,494,928,96,PALE,rx=12)+text(640,535,"每一阶段只增加一种新的不确定性",27,RED,700,"middle")+text(640,568,"先学会驾驶，再逐步学习交通交互，避免一次同时解决全部难题。",20,MUTED,400,"middle")+'</g>'
    return svg(4,"process",b,title)


def chart_page(page,title,img,takeaway,source):
    b='<g id="chart-evidence">'+rect(64,126,1152,470,"#FFFFFF",LINE,1,10)+image(76,138,1128,446,img)+'</g>'
    b+='<g id="interpretation-band">'+rect(64,610,1152,50,PALE,rx=8)+text(86,642,takeaway,18,RED,600)+text(1195,642,source,13,MUTED,400,"end")+'</g>'
    return svg(page,"data",b,title)


def p05(): return chart_page(5,"130,005 个专家样本让策略先学会基本驾驶动作","behavior_cloning_training.png","验证集 MSE 最低达到 0.0070；300 条轨迹覆盖 155-D 观测与 2-D 动作。","来源：BC 训练日志")


def p06():
    title="逐级增加交通密度，把驾驶与交互学习拆开"
    cols=[("无交通","路线跟随","先稳定转向、速度与道路内行驶",BLUE),("低密度","基础避让","在少量 NPC 下学习减速、绕行",RED),("高密度","路口决策","处理多方向来车与通行间隙",DARK_RED)]
    b='<g id="difficulty-stages">'
    for i,(a,c,d,color) in enumerate(cols):
        x=64+i*392;b+=rect(x,172,360,350,"#FFFFFF",color,3,16)+text(x+28,222,a,30,color,700)+text(x+28,278,c,25,INK,700)+text(x+28,324,d,19,MUTED)
        for k in range(i+1): b+=f'<circle cx="{x+42+k*38}" cy="{442}" r="12" fill="{color}"/>'
        b+=text(x+28,492,f"交通复杂度  {i+1}/3",16,MUTED,600)
    b+='</g><g id="curriculum-claim">'+rect(160,558,960,82,PALE,rx=12)+text(640,608,"课程学习的目标：保留已学驾驶能力，只新增当前阶段需要的交互能力。",22,RED,700,"middle")+'</g>'
    return svg(6,"comparison",b,title)


def p07(): return chart_page(7,"无交通预训练提高低密度上限，但检查点仍有波动","low_density_training_dynamics.png","真实 50k checkpoint 数据；展示至 700k，不插值、不平滑。","虚线：未经 PPO 的 BC 基线")
def p08(): return chart_page(8,"低密度成功率由 45% 提升至 85%","low_density_curriculum_comparison.png","BC → 无交通 → 低密度路线同时降低碰撞与出界失败。","相同评估协议")
def p09(): return chart_page(9,"高密度前 400k 步中，逐级课程更早达到较高成功率","high_density_training_dynamics.png","直接训练波动更大；课程路线能迁移已获得的道路内驾驶能力。","真实 checkpoint 数据")
def p10(): return chart_page(10,"逐级课程在统一测试中达到 51% 成功率","high_density_curriculum_comparison.png","100 个相同随机种子：成功率由 22% 提升至 51%，主要来自出界率下降。","高密度 · 100 回合")
def p11(): return chart_page(11,"课程学习的主要收益是提升成功并减少出界","combined_low_high_outcome_comparison.png","左侧低密度、右侧高密度；成功率、碰撞率、出界率按相同方式横向比较。","全部数值为 %")


def p12():
    title="路口冲突而非路线跟随成为高密度主要瓶颈"
    vals=[("成功",0.346,BLUE,"能够选择可通行间隙"),("碰撞",0.697,RED,"冲突风险峰值约为成功样本两倍"),("驶出道路",0.332,GOLD,"避让过度仍会破坏道路约束")]
    b='<g id="risk-comparison">'
    for i,(name,v,color,note) in enumerate(vals):
        x=64+i*392;b+=rect(x,168,360,328,"#FFFFFF",color,3,16)+text(x+28,218,name,28,color,700)+text(x+28,300,f"{v:.3f}",28,INK,700,family="Arial")+text(x+28,337,"路口风险峰值（均值）",17,MUTED)
        b+=rect(x+28,372,304,12,"#E7E4E0",rx=6)+rect(x+28,372,304*v/0.75,12,color,rx=6)+text(x+28,430,note,18,MUTED)
    b+='</g><g id="causal-interpretation">'+rect(112,544,1056,92,PALE,rx=12)+text(640,582,"当前策略已经会开车，但还不够会“抢时机”",26,RED,700,"middle")+text(640,615,"下一步应学习主动选择通行间隙，并预测不同方向 NPC 的冲突。",19,MUTED,400,"middle")+'</g>'
    return svg(12,"diagnosis",b,title)


def p13():
    title="成功策略能通过路口，失败集中在冲突与避让过度"
    b='<g id="success-video">'+rect(64,126,724,470,"#111111",rx=12)+image(64,126,724,470,"success_seed_1023_last.jpg","xMidYMid slice")+play(426,361,34)+rect(82,544,204,36,"#FFFFFF",rx=18)+text(184,568,"成功到达 · Seed 1023",16,BLUE,700,"middle")+'</g>'
    b+='<g id="collision-video">'+rect(820,126,396,218,"#111111",rx=12)+image(820,126,396,218,"collision_seed_1000_last.jpg","xMidYMid slice")+play(1018,235,25)+rect(838,292,172,34,"#FFFFFF",rx=17)+text(924,315,"路口碰撞 · Seed 1000",14,RED,700,"middle")+'</g>'
    b+='<g id="departure-video">'+rect(820,378,396,218,"#111111",rx=12)+image(820,378,396,218,"out_of_road_seed_1046_last.jpg","xMidYMid slice")+play(1018,487,25)+rect(838,544,192,34,"#FFFFFF",rx=17)+text(934,567,"避让出界 · Seed 1046",14,GOLD,700,"middle")+'</g>'
    b+='<g id="video-note">'+text(64,642,"播放按钮对应原始 MP4；案例用于把汇总指标连接到可观察的驾驶行为。",17,MUTED)+'</g>'
    return svg(13,"media",b,title)


def p14():
    title="课程学习有效，下一步应专攻高密度路口交互"
    items=[("01","行为克隆建立驾驶先验","30 个 epoch 后验证 MSE 最低 0.0070"),("02","课程学习提升闭环成功","低密度最高 85%，高密度统一测试 51%"),("03","路口碰撞仍是核心瓶颈","高密度碰撞率仍为 24%，需要更主动的间隙决策")]
    b='<g id="conclusions">'
    for i,(n,a,c) in enumerate(items):
        y=154+i*126;b+=text(66,y+28,n,24,RED,700)+rect(116,y,1100,92,"#FFFFFF",LINE,1,12)+text(146,y+36,a,25,INK,700)+text(146,y+69,c,18,MUTED)
    b+='</g><g id="next-step">'+rect(64,550,1152,96,RED,rx=14)+text(92,590,"NEXT",17,"#FFFFFF",700)+text(190,594,"风险感知的交互奖励  ×  主动通行间隙选择  ×  更高密度压力测试",25,"#FFFFFF",700)+'</g>'
    return svg(14,"closing",b,title)


PAGES=[p01,p02,p03,p04,p05,p06,p07,p08,p09,p10,p11,p12,p13,p14]
NAMES=["cover","task","interface","pipeline","behavior_cloning","curriculum","low_training","low_comparison","high_training","high_comparison","combined","failure_diagnosis","video_cases","conclusion"]

if __name__ == "__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--max",type=int,default=14);args=ap.parse_args()
    for i,(fn,name) in enumerate(zip(PAGES,NAMES),1):
        if i>args.max: break
        (OUT/f"{i:02d}_{name}.svg").write_text(fn(),encoding="utf-8")
    print(f"generated {min(args.max,14)} slides in {OUT}")
