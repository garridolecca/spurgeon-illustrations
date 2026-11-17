"""Curated topic taxonomy.

The clustering in embed.py names each cluster by its most frequent theme ("divine protection", "refuge" ...).
TAXONOMY puts those automatic clusters under a clear topic name and a category; synonyms are merged.
DROP lists clusters too vague to browse (their illustrations keep their other topics and stay searchable by
meaning). Clusters not listed keep their automatic name and are placed in the nearest category by meaning;
run embed.py and check data/topics.json for new unlisted clusters after each refresh.
"""

TAXONOMY = {
    "God and His Attributes": {
        "The love of God": ["love of god", "divine love", "affection"],
        "The power of God": ["god's power", "divine power", "power"],
        "The faithfulness of God": ["faithfulness", "fidelity"],
        "The mercy of God": ["mercy"],
        "The holiness and glory of God": ["glory"],
        "The goodness of God": ["goodness", "blessing"],
        "The wrath of God": ["divine wrath"],
        "Justice of God": ["justice"],
        "The presence of God": ["divine presence"],
        "God's knowledge": ["divine knowledge"],
        "Creation": ["creation"],
    },
    "Providence": {
        "Providence": ["providence", "divine intervention", "miracles"],
        "The sovereignty of God": ["divine sovereignty", "divine will", "divine purpose", "divine order", "authority"],
        "God's care and provision": ["divine care", "provision", "care"],
        "God's protection": ["divine protection", "protection", "safety", "spiritual safety", "refuge", "preservation", "security"],
        "God's timing": ["divine timing", "waiting"],
        "Guidance": ["divine guidance", "guidance"],
        "God's ownership and stewardship": ["divine ownership", "stewardship"],
        "Deliverance": ["deliverance", "rescue"],
    },
    "Christ: Person and Work": {
        "Christ": ["christ", "divinity"],
        "The sufferings of Christ": ["christ's suffering", "agony"],
        "The cross": ["cross", "crucifixion"],
        "Atonement and substitution": ["atonement", "substitution"],
        "Christ the Mediator": ["mediation", "divine condescension"],
        "The incarnation": ["incarnation", "humanity of christ"],
        "Union with Christ": ["union with christ", "spiritual union"],
        "The Good Shepherd": ["shepherd"],
        "Sacrifice": ["sacrifice"],
    },
    "The Holy Spirit": {
        "The Holy Spirit": ["holy spirit"],
        "Spiritual gifts": ["spiritual gifts"],
        "Revival and awakening": ["spiritual awakening"],
    },
    "Scripture": {
        "The Word of God": ["word of god", "scripture"],
        "Hearing the Word": ["hearing the word", "hearing"],
        "The promises of God": ["promises"],
        "Truth": ["truth", "spiritual truth"],
        "Doctrine and teaching": ["doctrine", "teaching", "education"],
        "The law": ["law"],
    },
    "Sin and the Human Heart": {
        "Sin": ["sin", "sinfulness", "wickedness", "evil"],
        "The consequences of sin": ["consequences of sin", "consequence"],
        "Fighting sin": ["fear of sin"],
        "Depravity and the fall": ["original sin", "depravity", "corruption", "spiritual corruption", "fall", "flesh"],
        "Moral decline": ["moral decay", "decline"],
        "Pride": ["pride"],
        "Envy": ["envy"],
        "Hypocrisy": ["hypocrisy", "false piety", "self-deception", "religion"],
        "Selfishness": ["selfishness"],
        "Deceit and lies": ["deception", "falsehood"],
        "Idolatry": ["idolatry", "false worship"],
        "Hardness of heart": ["hardness of heart", "heart", "spiritual blindness"],
        "Unbelief and doubt": ["unbelief", "doubt", "uncertainty"],
        "Rebellion against God": ["rebellion", "disobedience", "enmity"],
        "Rejecting Christ": ["rejection"],
        "Ignorance": ["ignorance"],
        "Sloth and neglect": ["spiritual neglect", "idleness"],
        "Backsliding and apostasy": ["backsliding", "apostasy"],
        "Betrayal": ["betrayal"],
        "Conviction of sin": ["conviction", "guilt", "shame"],
        "Conscience": ["conscience"],
        "Human nature": ["human nature", "humanity"],
    },
    "Grace and Salvation": {
        "Grace": ["grace", "hidden grace", "divine favor", "acceptance"],
        "Salvation": ["salvation", "soul salvation"],
        "Redemption": ["redemption"],
        "Forgiveness": ["forgiveness"],
        "Justification": ["justification"],
        "Reconciliation": ["reconciliation"],
        "Election": ["election"],
        "The covenant": ["covenant"],
        "New birth": ["regeneration", "new birth", "new life"],
        "Access to God": ["access to god"],
        "Inheritance": ["inheritance"],
        "Freedom from bondage": ["freedom", "spiritual freedom", "bondage", "spiritual bondage"],
        "Spiritual death": ["spiritual death", "deadness"],
    },
    "Faith and Repentance": {
        "Faith": ["faith", "genuine faith", "personal faith", "faith in action", "humble faith"],
        "Trust in God": ["trust", "trust in god", "dependence", "self-reliance", "surrender", "commitment", "resignation"],
        "Repentance": ["repentance", "penitence", "confession"],
        "Conversion": ["conversion", "spiritual transformation", "renewal", "moral change", "change", "restoration"],
        "Childlike faith": ["childhood faith"],
        "Testimony": ["testimony"],
        "Seeking God": ["searching", "longing"],
    },
    "Assurance and Perseverance": {
        "Assurance": ["assurance", "eternal security", "confidence", "permanence", "stability"],
        "Perseverance": ["perseverance", "endurance"],
        "Fear and anxiety": ["fear", "anxiety"],
        "Strength from God": ["spiritual strength", "strength", "sufficiency", "divine support"],
        "Spiritual drift and stability": ["spiritual stability"],
        "Victory": ["victory", "triumph"],
        "Spiritual weakness": ["spiritual weakness", "weakness", "vulnerability", "helplessness"],
    },
    "Prayer": {
        "Prayer": ["prayer"],
        "Intercession": ["intercession"],
        "Communion with God": ["communion", "relationship with god", "spiritual intimacy"],
        "Meditation": ["meditation"],
    },
    "Holiness and Sanctification": {
        "Holiness": ["holiness", "godliness", "holy living", "sanctification", "piety"],
        "Purity": ["purity"],
        "Cleansing": ["cleansing", "purification", "refinement"],
        "Spiritual growth": ["spiritual growth", "growth", "spiritual maturity", "progress", "spiritual formation"],
        "Fruitfulness": ["fruitfulness", "harvest"],
        "Obedience": ["obedience", "submission"],
        "Duty": ["duty", "moral duty", "spiritual duty", "responsibility"],
        "Spiritual disciplines": ["spiritual discipline"],
        "Self-denial": ["self-denial"],
        "Self-control": ["self-control"],
        "Self-examination": ["self-examination", "self-awareness"],
        "Spiritual life": ["spiritual life", "spiritual vitality"],
        "Good works": ["works"],
        "Discipleship": ["discipleship"],
    },
    "Christian Virtues": {
        "Love for others": ["love"],
        "Compassion": ["compassion", "sympathy", "empathy", "tenderness"],
        "Humility": ["humility", "humble service"],
        "Meekness and gentleness": ["meekness", "gentleness", "calmness"],
        "Patience": ["patience"],
        "Contentment": ["contentment", "satisfaction"],
        "Gratitude": ["gratitude", "thanksgiving"],
        "Generosity": ["generosity", "charity"],
        "Zeal": ["zeal", "passion"],
        "Courage": ["courage", "boldness"],
        "Simplicity": ["simplicity"],
        "Hospitality": ["hospitality"],
    },
    "Suffering and Affliction": {
        "Affliction": ["affliction", "trouble", "tribulation", "oppression"],
        "Suffering": ["suffering"],
        "Faith under trial": ["faith in suffering", "trial", "testing"],
        "Spiritual distress": ["spiritual pain", "spiritual crisis", "inner struggle", "spiritual condition"],
        "Despair": ["despair", "desolation"],
        "Loneliness and desertion": ["isolation", "solitude", "abandonment", "desertion"],
        "Grief and sorrow": ["grief", "sorrow", "loss", "regret", "divine sorrow"],
        "Chastening": ["discipline", "chastening"],
        "Persecution": ["persecution", "reproach", "mockery", "humiliation"],
        "Martyrdom": ["martyrdom"],
        "Poverty": ["poverty", "need", "famine", "debt"],
        "Sickness": ["sickness", "health"],
        "Spiritual dryness": ["spiritual dryness", "spiritual barrenness", "spiritual emptiness", "desert"],
    },
    "Comfort and Hope": {
        "Comfort": ["comfort", "consolation", "encouragement"],
        "Hope": ["hope"],
        "Joy": ["joy", "happiness", "blessedness", "pleasure"],
        "Joy in suffering": ["joy in suffering"],
        "Peace and rest": ["peace", "rest", "inner peace", "spiritual rest"],
        "Healing of the soul": ["healing", "spiritual healing", "soul health", "spiritual health"],
        "Spiritual hunger and nourishment": ["spiritual food", "spiritual nourishment", "spiritual hunger", "thirst", "spiritual refreshment"],
        "Spiritual poverty": ["spiritual poverty", "spiritual need", "unworthiness", "need for grace"],
    },
    "Temptation and Spiritual Warfare": {
        "Temptation": ["temptation"],
        "Spiritual warfare": ["spiritual warfare", "spiritual conflict", "spiritual struggle", "war", "resistance", "opposition"],
        "Satan": ["satan"],
        "Spiritual danger": ["spiritual danger", "danger"],
        "False teaching": ["false teaching"],
    },
    "Worldliness and Riches": {
        "Riches": ["wealth", "worldly wealth", "prosperity", "abundance", "materialism"],
        "Covetousness": ["covetousness", "greed", "desire"],
        "Worldliness": ["worldliness", "worldly pleasures", "worldly desires", "carnality", "conformity"],
        "Vanity of the world": ["vanity", "futility"],
    },
    "Death and Eternity": {
        "Death": ["death", "body"],
        "The death of believers": ["death of believers"],
        "The brevity of life": ["fleeting life", "transience"],
        "Human frailty": ["human frailty", "human limitation"],
        "Eternity": ["eternity", "eternal destiny"],
        "Eternal life": ["eternal life", "life after death"],
        "Readiness and watchfulness": ["preparation", "readiness", "spiritual readiness", "watchfulness", "vigilance"],
    },
    "Heaven and Glory": {
        "Heaven": ["heaven", "heavenly vision", "eternal joy", "home"],
        "Heavenly reward": ["heavenly reward", "eternal reward", "spiritual treasure"],
        "Pilgrimage": ["journey", "pilgrimage", "exile"],
    },
    "Judgment and Hell": {
        "Judgment": ["judgment", "condemnation", "accountability", "final judgment"],
        "Hell": ["hell", "destruction"],
        "Warning": ["warning"],
        "The fear of God and of judgment": ["fear of god"],
    },
    "Last Things": {
        "Resurrection": ["resurrection"],
        "The kingdom of God": ["kingdom"],
        "Last things": ["eschatology"],
    },
    "The Church and Fellowship": {
        "The church": ["church life", "church", "body of christ"],
        "Fellowship and unity": ["fellowship", "community", "unity", "diversity"],
        "Baptism": ["baptism"],
        "Church history and reformation": ["reformation"],
    },
    "Preaching and Ministry": {
        "Preaching": ["preaching"],
        "Ministry and pastoral care": ["ministry", "pastoral care", "leadership"],
        "Christian service": ["service", "spiritual labor", "usefulness"],
        "Calling": ["calling", "divine calling"],
    },
    "Evangelism and the Gospel Call": {
        "The gospel": ["gospel", "invitation", "gospel reception"],
        "Evangelism and missions": ["evangelism", "mission", "soul-winning"],
        "The need of salvation": ["need for salvation"],
        "Sinners saved": ["sinners"],
        "Urgency of salvation": ["urgency", "delay"],
    },
    "Worship and Praise": {
        "Worship": ["worship", "devotion", "praise"],
        "Reverence and awe": ["reverence", "awe", "wonder"],
        "The Sabbath": ["sabbath"],
        "Spiritual discernment": ["spiritual discernment", "spiritual insight", "spiritual sensitivity"],
    },
    "Family and Daily Life": {
        "Family and home": ["family", "home life", "daily life"],
        "Marriage": ["marriage"],
        "Parents and children": ["parenting", "fatherhood", "motherhood", "parental love", "childhood"],
        "Youth": ["youth"],
        "Old age": ["aging"],
        "Friendship": ["friendship"],
        "Work and labor": ["work", "labor"],
        "Use of time": ["time"],
    },
    "Wisdom and Character": {
        "Wisdom": ["wisdom", "knowledge", "understanding", "reason"],
        "Character and example": ["character", "virtue", "example", "influence"],
        "Integrity": ["integrity", "honor", "reputation", "sincerity", "consistency", "loyalty"],
        "Diligence": ["diligence", "effort"],
        "Righteousness": ["righteousness"],
        "The soul": ["soul"],
    },
}

DROP = [
    "nature", "spirituality", "spiritual effort", "spiritual value", "value", "life", "contrast", "action",
    "experience", "order", "identity", "relationship", "spiritual reality", "spiritual experience", "inner life",
    "spiritual depth", "spiritual elevation", "spiritual awareness", "spiritual focus", "spiritual direction",
    "comparison", "accessibility", "mystery", "clarity", "spiritual identity", "spiritual equality",
    "spiritual authenticity", "divine action", "divine response", "foundation", "vision", "light", "darkness",
    "memory", "silence", "misunderstanding", "dignity", "beauty", "separation", "spiritual legacy", "gifts",
    "perfection", "innocence", "revelation", "consecration", "distraction", "failure", "resilience", "self-destruction",
]


def overrides():
    """{merge: {auto: final}, category: {final: category}, drop: [...]}"""
    merge, category = {}, {}
    for cat, topics in TAXONOMY.items():
        for final, autos in topics.items():
            category[final] = cat
            for a in autos:
                assert a not in merge, f"{a} listed twice"
                merge[a] = final
    return dict(merge=merge, category=category, drop=DROP)


# ---- 2026-11-16 round-2 clusters (new data reshuffled the clustering) ----
_NEW_TOPICS = {   # category -> new final topic -> cluster labels
    "Faith and Repentance": {"Longing for God": ["spiritual longing", "soul's longing"]},
    "Comfort and Hope": {"Light in darkness": ["divine light", "light in darkness"]},
    "Sin and the Human Heart": {"Complacency and indifference": ["spiritual complacency", "spiritual apathy",
                                                                 "indifference", "false security", "presumption"]},
    "Christ: Person and Work": {"The preciousness of Christ": ["value of christ"]},
    "God and His Attributes": {"God as Father": ["fatherly love", "heavenly father"]},
    "Wisdom and Character": {"The tongue": ["speech", "slander", "blasphemy"]},
}
_MERGE = {        # cluster label -> existing final topic
    "active faith": "Faith", "practical faith": "Faith", "comfort in suffering": "Comfort",
    "spiritual service": "Christian service", "servanthood": "Christian service", "faith under trial": "Faith under trial",
    "spiritual victory": "Victory", "conquest": "Victory", "rejection of christ": "Rejecting Christ",
    "rejection of truth": "Unbelief and doubt", "spiritual unity": "Fellowship and unity",
    "eternal punishment": "Hell", "punishment": "Judgment", "retribution": "Judgment",
    "fear of judgment": "The fear of God and of judgment",
    "divine control": "The sovereignty of God", "fate": "The sovereignty of God", "destiny": "The sovereignty of God",
    "reversal of fortune": "Providence", "predestination": "Election", "free will": "Human nature",
    "christ's work": "Christ", "free grace": "Grace", "sudden grace": "Grace",
    "spiritual infancy": "Spiritual growth", "spiritual development": "Spiritual growth",
    "image of god": "Human nature", "nature of man": "Human nature", "body and soul": "The soul",
    "soul's condition": "The soul", "soul safety": "Assurance", "doctrinal clarity": "Doctrine and teaching",
    "false doctrine": "False teaching", "marriage to christ": "Union with Christ", "tender care": "God's care and provision",
    "worldly power": "Worldliness", "worldly ambition": "Worldliness", "worldly attachments": "Worldliness",
    "indulgence": "Worldliness", "hidden truth": "Truth", "spiritual birth": "New birth",
    "heart transformation": "Conversion", "witness": "Testimony", "proclamation": "Preaching",
    "prophetic ministry": "Preaching", "perception": "Spiritual discernment", "attention": "Hearing the Word",
    "receptivity": "Hearing the Word", "thoughts": "Meditation", "expectation": "Hope", "opportunity": "Use of time",
    "decision": "Urgency of salvation", "sharing": "Generosity", "learning": "Wisdom", "foolishness": "Wisdom",
    "recovery": "Healing of the soul", "conflict": "Spiritual warfare", "struggle": "Spiritual warfare",
    "burden": "Affliction", "storm": "Affliction", "adversity": "Affliction", "captivity": "Freedom from bondage",
    "companionship": "Friendship", "modesty": "Humility", "self-worth": "Humility",
    "worthlessness": "Spiritual poverty", "degradation": "Moral decline", "cruelty": "Sin", "hidden sin": "Sin",
    "rejoicing": "Joy", "exaltation": "Heavenly reward", "glorification": "Heaven",
    "divine majesty": "The holiness and glory of God", "divine reliability": "The faithfulness of God",
    "living water": "Spiritual hunger and nourishment", "spiritual fulfillment": "Contentment",
    "spiritual connection": "Communion with God", "personal relationship": "Communion with God",
    "god's nearness": "The presence of God", "distress": "Spiritual distress", "despondency": "Despair",
    "discouragement": "Despair", "disappointment": "Despair", "missionary work": "Evangelism and missions",
    "gospel outreach": "Evangelism and missions", "parental responsibility": "Parents and children",
}
DROP += ["familiarity", "possession", "finality", "seasons", "emotions", "beginnings", "remembrance"]
for _c, _d in _NEW_TOPICS.items():
    TAXONOMY[_c].update(_d)
for _lab, _fin in _MERGE.items():
    _hit = [d for d in TAXONOMY.values() if _fin in d]
    assert _hit, _fin
    _hit[0][_fin].append(_lab)


# ---- 2026-11-16 round-3 review: fixes to automatic merges + valuable new clusters ----
_NEW_TOPICS3 = {
    "Grace and Salvation": {"Adoption": ["adoption", "sonship"]},
    "Worship and Praise": {"Formalism and ritualism": ["ritualism", "formalism", "superstition", "tradition", "ordinances"]},
    "Sin and the Human Heart": {"Anger and bitterness": ["temper", "bitterness"],
                                "Drunkenness": ["drunkenness"]},
}
_MERGE3 = {
    "self-righteousness": "Pride", "faithful service": "Christian service", "spiritual anxiety": "Fear and anxiety",
    "moral purity": "Purity", "divine greatness": "The holiness and glory of God", "spiritual responsibility": "Duty",
    "spiritual hardness": "Hardness of heart", "spiritual cleansing": "Cleansing", "spiritual peace": "Peace and rest",
    "carelessness": "Sloth and neglect", "resistance to evil": "Fighting sin", "spiritual distance": "Backsliding and apostasy",
    "heavenly dwelling": "Heaven", "spiritual teaching": "Doctrine and teaching", "divine selection": "Election",
    "absence": "Loneliness and desertion", "value of faith": "Faith", "sudden change": "Conversion",
    "tender heart": "Compassion", "kindness": "Love for others", "diversity of grace": "Spiritual gifts",
    "spiritual gain": "Spiritual growth",
    "liberty": "Freedom from bondage", "liberation": "Freedom from bondage", "escape": "Freedom from bondage",
    "slavery": "Freedom from bondage", "prison": "Freedom from bondage", "immortality": "Eternal life",
    "priesthood": "Christ the Mediator", "universal grace": "Grace", "unexpected grace": "Grace", "pardon": "Forgiveness",
    "sudden death": "The brevity of life", "temporality": "The brevity of life", "fragility": "Human frailty",
    "peril": "Spiritual danger", "compromise": "Worldliness", "worldly distractions": "Worldliness",
    "future hope": "Hope", "crown": "Heavenly reward", "reign of christ": "The kingdom of God",
    "christ's supremacy": "Christ", "christ-centeredness": "Christ", "ascension": "Christ",
    "omniscience": "God's knowledge", "omnipotence": "The power of God", "professing faith": "Hypocrisy",
    "professors": "Hypocrisy", "skepticism": "Unbelief and doubt", "infidelity": "Unbelief and doubt", "belief": "Faith",
    "blood of christ": "Atonement and substitution", "damnation": "Hell", "perdition": "Hell", "torment": "Hell",
    "soul loss": "Hell", "curse": "Judgment", "end times": "Last things", "return": "Last things",
    "chastisement": "Chastening", "forsakenness": "Loneliness and desertion", "importunity": "Prayer",
    "earnestness": "Zeal", "daily devotion": "Spiritual disciplines", "study": "Spiritual disciplines",
    "contemplation": "Meditation", "reflection": "Meditation", "public worship": "Worship", "temple": "Worship",
    "heresy": "False teaching", "error": "False teaching", "delusion": "False teaching",
    "false hope": "Complacency and indifference", "fleeing sin": "Fighting sin", "nature of sin": "Sin",
    "iniquity": "Sin", "defilement": "Sin", "murmuring": "Contentment", "sowing": "Fruitfulness",
    "steadfastness": "Perseverance", "faith under pressure": "Faith under trial", "children": "Parents and children",
    "brotherhood": "Fellowship and unity", "division": "Fellowship and unity", "saints": "The church",
    "fall from grace": "Backsliding and apostasy", "wandering": "Backsliding and apostasy",
    "heathenism": "Evangelism and missions", "rebirth": "New birth", "abiding": "Union with Christ",
    "small things": "Humility", "humble beginnings": "Humility", "insignificance": "Humility",
    "fearlessness": "Courage", "brokenness": "Conviction of sin", "restlessness": "Peace and rest",
    "celebration": "Joy", "dryness": "Spiritual dryness", "enemy": "Spiritual warfare",
}
DROP += ["balance", "curiosity", "necessity", "succession", "spiritual expression"]
for _c, _d in _NEW_TOPICS3.items():
    TAXONOMY[_c].update(_d)
_known = {a for d in TAXONOMY.values() for al in d.values() for a in al}
for _lab, _fin in _MERGE3.items():
    if _lab in _known:
        continue
    _hit = [d for d in TAXONOMY.values() if _fin in d]
    assert _hit, _fin
    _hit[0][_fin].append(_lab)
_MERGE4 = {
    "divine nature": "The holiness and glory of God", "divine likeness": "Holiness", "merit": "Justification",
    "prudence": "Wisdom", "restraint": "Self-control", "reunion": "Heaven", "spiritual fire": "Zeal",
    "enthusiasm": "Zeal", "prejudice": "Hardness of heart", "theology": "Doctrine and teaching",
    "motive": "Self-examination", "reform": "Church history and reformation", "legacy": "Character and example",
    "imperfection": "Human frailty", "divine mystery": "God's knowledge", "harmony": "Fellowship and unity",
    "obstacles": "Affliction", "inner conviction": "Conviction of sin", "rootedness": "Spiritual drift and stability",
    "habit": "Spiritual disciplines", "divine encounter": "Communion with God", "divine approval": "Heavenly reward",
}
_known = {a for d in TAXONOMY.values() for al in d.values() for a in al}
for _lab, _fin in _MERGE4.items():
    if _lab not in _known:
        [d for d in TAXONOMY.values() if _fin in d][0][_fin].append(_lab)
_MERGE5 = {
    "return to god": "Repentance", "eternal love": "The love of God", "brotherly love": "Love for others",
    "sudden loss": "The brevity of life", "spiritual outreach": "Evangelism and missions",
    "spiritual wandering": "Backsliding and apostasy", "heavenly food": "Spiritual hunger and nourishment",
    "dedication": "Self-denial", "sorrow for sin": "Repentance", "timing": "God's timing",
    "spiritual movement": "Revival and awakening", "victory over evil": "Victory",
    "spiritual empowerment": "Strength from God", "fullness": "Spiritual life", "access": "Access to God",
    "history": "Church history and reformation", "divine pursuit": "Grace", "fallibility": "Human frailty",
    "eternal rest": "Heaven", "heavenly love": "The love of God",
}
DROP += ["choice", "transition", "excellence"]
_known = {a for d in TAXONOMY.values() for al in d.values() for a in al}
for _lab, _fin in _MERGE5.items():
    if _lab not in _known:
        [d for d in TAXONOMY.values() if _fin in d][0][_fin].append(_lab)
