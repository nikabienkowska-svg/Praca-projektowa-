import json, gzip, random
from collections import defaultdict

CORPUS  = "data/corpus.jsonl.gz"; OUT = "data/users.json"
SEED=42; N_USERS=100; PROFILE=8; GT_CAP=60; MIN_GT=12; MIN_TOPIC=20

LABEL={"cs.LG":"Machine Learning","cs.CV":"Computer Vision","cs.CL":"Language & NLP",
 "cs.NE":"Neural & Evolutionary Computing","cs.AI":"Artificial Intelligence","stat.ML":"Statistics – ML",
 "cond-mat.dis-nn":"Disordered Systems & Neural Nets","cs.RO":"Robotics","eess.SP":"Signal Processing",
 "eess.AS":"Audio & Speech","eess.IV":"Image & Video","cs.HC":"Human-Computer Interaction",
 "q-bio.QM":"Quantitative Methods","q-bio.PE":"Populations & Evolution","q-bio.MN":"Molecular Networks",
 "nlin.AO":"Adaptation & Self-Organising","nlin.CD":"Chaotic Dynamics","physics.bio-ph":"Biological Physics",
 "math.DS":"Dynamical Systems","cs.IT":"Information Theory","cs.SD":"Sound","cs.IR":"Information Retrieval",
 "cs.MA":"Multiagent Systems","physics.data-an":"Data Analysis","stat.AP":"Statistics – Applications",
 "cs.CY":"Computers & Society","math.OC":"Optimization & Control","cs.SY":"Systems & Control",
 "q-bio.TO":"Tissues & Organs","q-bio.CB":"Cell Behavior"}

papers={}; qbio=[]; 
for line in gzip.open(CORPUS, "rt", encoding="utf-8"):
    try: r=json.loads(line)
    except: continue
    papers[r["id"]]=r
    if "q-bio.NC" in r.get("categories","").split():
        qbio.append(r["id"])
qbioset=set(qbio)

# topic = q-bio.NC papers ALSO tagged X (every reader anchored in Neurons & Cognition)
inter=defaultdict(list)
for pid in qbio:
    for c in set(papers[pid]["categories"].split()):
        if c!="q-bio.NC":
            inter[c].append(pid)

cand=sorted([c for c,ids in inter.items() if len(ids)>=MIN_TOPIC], key=lambda c:-len(inter[c]))
random.Random(SEED).shuffle(cand)
users=[]; used=0
for c in cand:
    if len(users)>=N_USERS: break
    ids=list(inter[c]); rng=random.Random(SEED+used); rng.shuffle(ids)
    profile=ids[:PROFILE]; gt=ids[PROFILE:PROFILE+GT_CAP]
    if len(gt)<MIN_GT: continue
    used+=1
    users.append({"user_id":f"u{used:03d}","topic_rule":f"q-bio.NC AND {c}",
                  "topic_label":f"Neurons & Cognition × {LABEL.get(c,c)}",
                  "second_field":c,"n_relevant_total":len(inter[c]),
                  "profile_ids":profile,"ground_truth_ids":gt,"n_ground_truth":len(gt)})

json.dump({"seed":SEED,"profile_size":PROFILE,"gt_cap":GT_CAP,
  "ground_truth_signal":"arXiv category co-membership (q-bio.NC AND a second field); metadata, independent of the title/abstract text both models read",
  "anchor":"every user is a Neurons & Cognition reader, differentiated by a second field",
  "n_users":len(users),"users":users}, open(OUT,"w"), indent=1)

import statistics as st
gts=[u['n_ground_truth'] for u in users]
print(f"users generated: {len(users)}  (all anchored in q-bio.NC)")
print(f"q-bio.NC papers available as anchor: {len(qbio)}")
print(f"ground-truth per user: min={min(gts)} median={int(st.median(gts))} max={max(gts)}")
print("sample topics:")
for u in users[:14]:
    print(f"  {u['user_id']}  {u['topic_label'][:44]:<44} GT={u['n_ground_truth']:>2}  (q-bio.NC∩{u['second_field']} size {u['n_relevant_total']})")
