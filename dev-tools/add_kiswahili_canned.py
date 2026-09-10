"""Add Kiswahili translations for all canned answers, and re-enable
Swahili detection to serve them -- verified-answer layer only,
generative path stays English-only as decided."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

sw_dict = '''CANNED_ANSWERS_SW = {
    "nssf": (
        "**Michango ya NSSF** imegawanywa sawa kati ya pande mbili:\\n\\n"
        "- **Mfanyakazi**: 6% ya mshahara unaostahili\\n"
        "- **Mwajiri**: 6% (kiasi sawa)\\n\\n"
        "Hii inatumika kwa Tier I (hadi KES 9,000 ya mshahara unaostahili) na Tier II "
        "(sehemu hadi KES 108,000). Michango hulipwa kila mwezi."
    ),
    "leave": (
        "**Likizo ya kila mwaka kisheria nchini Kenya** (Sheria ya Ajira 2007):\\n\\n"
        "- Angalau **siku 21 za kazi** za likizo yenye malipo kwa kila miezi 12 ya "
        "utumishi endelevu\\n"
        "- Hukusanywa mwaka mzima; baadhi ya waajiri huruhusu kuhamisha siku chache "
        "zilizobaki kwenda mwaka unaofuata\\n\\n"
        "Angalia mkataba wako wa ajira kwa likizo yoyote ya ziada zaidi ya kiwango "
        "cha chini kisheria."
    ),
    "capital": (
        "**Mtaji wa chini wa hisa kwa kampuni binafsi ya dhima ndogo nchini Kenya**:\\n\\n"
        "- **Hakuna** mtaji wa chini wa hisa unaotakiwa kisheria\\n"
        "- Kampuni nyingi husajiliwa na mtaji wa kawaida (mara nyingi KES 100,000, "
        "ingawa hii ni desturi tu, si kiwango cha kisheria)\\n"
        "- Ushuru wa stempu hutozwa kwa **1% ya mtaji wa hisa wa kawaida**"
    ),
    "yedf": (
        "**Mfuko wa Maendeleo ya Wafanyabiashara Vijana (YEDF)**:\\n\\n"
        "- **Sifa**: umri wa miaka 18-34\\n"
        "- **Mkopo wa Rausha**: KES 100,000 (ufadhili wa kuanzisha kikundi)\\n"
        "- **Mkopo wa Inua**: KES 200,000-1,000,000 (upanuzi wa biashara)\\n"
        "- **Mkopo wa Vuka**: hadi KES 5,000,000 kwa asilimia 8 kwa mwaka\\n\\n"
        "Omba kupitia youthfund.go.ke, Fomu 1A, ukiwa na maelezo ya kaunti/jimbo lako."
    ),
    "loan": (
        "**Chaguo za mikopo ya kuanzisha biashara nchini Kenya**:\\n\\n"
        "1. **YEDF** -- omba kupitia youthfund.go.ke (Fomu 1A); bidhaa ni pamoja na "
        "Vuka, Talanta, Agribizz, Vijana Bahari, na ufadhili wa LPO\\n"
        "2. **Hustler Fund** -- omba kupitia USSD *254# au programu ya Hustler Fund; "
        "hakuna dhamana inayohitajika, hujenga kiwango cha juu cha mikopo kupitia akiba\\n"
        "3. **SACCOs** -- zinahitaji uanachama na historia ya akiba kwanza\\n"
        "4. **Benki za kibiashara** -- zinahitaji biashara iliyosajiliwa, kumbukumbu "
        "za kifedha, na dhamana kwa kiasi kikubwa zaidi"
    ),
    "registration": (
        "**Kusajili jina la biashara nchini Kenya**:\\n\\n"
        "1. Tafuta upatikanaji wa jina kupitia tovuti ya eCitizen (ecitizen.go.ke) "
        "au Huduma ya Usajili wa Biashara (brs.go.ke)\\n"
        "2. Wasilisha usajili wako ukiwa na kitambulisho chako cha taifa na namba "
        "ya PIN ya KRA\\n"
        "3. Baada ya kuidhinishwa, utapokea cheti cha usajili wa biashara"
    ),
    "kra_pin": (
        "**Kupata namba ya PIN ya KRA**:\\n\\n"
        "1. Nenda iTax kwenye itax.kra.go.ke\\n"
        "2. Ingia / jisajili kwa kutumia kitambulisho chako cha taifa\\n"
        "3. Bofya \\"Register\\" -- PIN yako hutolewa mara tu unapomaliza usajili\\n\\n"
        "Utahitaji PIN hii kabla ya kusajili kwa VAT, PAYE, au wajibu mwingine "
        "wowote wa kodi."
    ),
    "vat": (
        "**Kiwango cha lazima cha kusajili VAT nchini Kenya**:\\n\\n"
        "- Ni lazima pindi mauzo yako ya mwaka yanayotozwa kodi yanapozidi "
        "**KES 5,000,000**\\n"
        "- Jisajili kupitia iTax (itax.kra.go.ke)"
    ),
    "termination": (
        "**Kumfukuza mfanyakazi kihalali nchini Kenya** (Sheria ya Ajira 2007):\\n\\n"
        "1. Kuwa na **sababu halali na ya haki** (mfano, utovu wa nidhamu, "
        "utendaji duni, kupunguzwa kwa wafanyakazi)\\n"
        "2. Toa **taarifa** ifaayo (kulingana na mkataba, au kiwango cha chini "
        "kisheria)\\n"
        "3. Eleza sababu kwa maandishi na mpe mfanyakazi nafasi halisi ya "
        "kujibu/kusikilizwa kabla uamuzi haujawa wa mwisho\\n\\n"
        "Kuruka hatua ya taarifa au usikilizaji -- hata kwa sababu halali -- "
        "kunaweza kufanya ufukuzaji kuwa si wa haki. Kupunguzwa kwa wafanyakazi "
        "kuna sheria za ziada (taarifa kwa ofisi ya kazi, vigezo vya uchaguzi, "
        "malipo ya kiinua mgongo)."
    ),
    "license": (
        "**Leseni za biashara/kibiashara nchini Kenya** zinasimamiwa katika "
        "**ngazi ya kaunti**, si kitaifa -- aina na ada halisi hutofautiana kwa "
        "kaunti.\\n\\n"
        "Mchakato wa jumla:\\n"
        "1. Sajili jina la biashara yako kwanza (eCitizen/BRS)\\n"
        "2. Omba kibali kimoja cha biashara kupitia ofisi ya leseni za biashara "
        "ya kaunti yako mahususi\\n\\n"
        "Thibitisha aina na ada halisi na kaunti yako mahususi, kwa kuwa "
        "hutofautiana kikweli."
    ),
    "turnover_tax": (
        "**Kodi ya Mauzo (Turnover Tax - TOT)** inahusu watu na makampuni "
        "yanayoishi nchini Kenya ambao mauzo yao ya jumla ni **zaidi ya "
        "KES 1,000,000** lakini **hayazidi KES 25,000,000** katika mwaka wa "
        "mapato. Inatozwa chini ya Kifungu cha 12(C) cha Sheria ya Kodi ya "
        "Mapato (CAP 470).\\n\\n"
        "- **Kiwango**: 1.5% ya mauzo ya jumla, kuanzia tarehe 1 Julai 2023 "
        "kulingana na Sheria ya Fedha 2023\\n"
        "- **Kodi ya mwisho**: TOT hutozwa kwa mauzo ya jumla bila **makato "
        "yoyote ya gharama kuruhusiwa**\\n"
        "- **Chini ya KES 1,000,000**: hakuna TOT (lakini wajibu mwingine wa "
        "kodi unaweza kuendelea kutumika)\\n"
        "- **Zaidi ya KES 25,000,000**: lazima ujisajili kwa mfumo wa kawaida "
        "wa Kodi ya Mapato badala yake\\n"
        "- **Haitumiki kwa**: mapato ya kupanga nyumba, ada za "
        "usimamizi/kitaalamu/mafunzo, mapato yanayotozwa tayari kodi ya mwisho "
        "ya makato (mfano, gawio linalostahili au riba), na walipa kodi wasio "
        "wakazi\\n"
        "- Ikiwa mauzo yako yanafikia **KES 5,000,000** na unashughulika na "
        "bidhaa zinazotozwa VAT, lazima pia ujisajili kwa VAT\\n"
        "- Unaweza kuchagua, kwa taarifa iliyoandikwa kwa Kamishna, "
        "kutojumuishwa katika TOT na kubaki chini ya mfumo wa kawaida wa Kodi "
        "ya Mapato badala yake\\n\\n"
        "Thibitisha msimamo wako mahususi kupitia iTax (itax.kra.go.ke), kwa "
        "kuwa hali za kibinafsi zinaweza kuathiri ustahiki."
    ),
}


'''

marker = "TOPIC_KEYWORDS = {"
if marker not in content:
    print("ERROR: could not find TOPIC_KEYWORDS marker. No changes made.")
else:
    content = content.replace(marker, sw_dict + marker, 1)
    print("CANNED_ANSWERS_SW dict inserted.")

old_detect = '    query_is_swahili = False  # Swahili translation disabled for now -- see is_swahili() for the detection logic if re-enabling'
new_detect = '    query_is_swahili = is_swahili(query)  # re-enabled: routes to CANNED_ANSWERS_SW for verified-answer topics only'
if old_detect not in content:
    print("ERROR: could not find query_is_swahili line. No changes made there.")
else:
    content = content.replace(old_detect, new_detect)
    print("query_is_swahili detection re-enabled.")

old_canned_block = '''    canned_topic = get_canned_topic(query)
    if canned_topic:
        print(f"[CANNED] Query: {query[:80]!r} -- matched topic {canned_topic!r}, returning verified answer directly (no LLM call)")
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": CANNED_ANSWERS[canned_topic]}}]
        })'''

new_canned_block = '''    canned_topic = get_canned_topic(query)
    if canned_topic:
        use_sw = query_is_swahili and canned_topic in CANNED_ANSWERS_SW
        answer_text = CANNED_ANSWERS_SW[canned_topic] if use_sw else CANNED_ANSWERS[canned_topic]
        lang_tag = "sw" if use_sw else "en"
        print(f"[CANNED] Query: {query[:80]!r} -- matched topic {canned_topic!r} ({lang_tag}), returning verified answer directly (no LLM call)")
        return jsonify({
            "choices": [{"message": {"role": "assistant", "content": answer_text}}]
        })'''

if old_canned_block not in content:
    print("ERROR: could not find the canned_topic block. No changes made there.")
else:
    content = content.replace(old_canned_block, new_canned_block)
    print("canned_topic block updated to select language.")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("\nSYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"\nSYNTAX CHECK: FAILED -- {e}")
    print("Do NOT restart the server until this is fixed.")
