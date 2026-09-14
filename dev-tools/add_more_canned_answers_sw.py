with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

sw_anchor = '''        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),
}


TOPIC_KEYWORDS = {'''

sw_new = '''        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),
    "class_r_permit": (
        "Nenda kwenye tovuti ya **Kenya eFNS** kupitia eCitizen na uombe "
        "**Class R Permit** -- kibali maalum kwa raia wa Jumuiya ya Afrika "
        "Mashariki (Burundi, DR Congo, Rwanda, Sudan Kusini, Tanzania, "
        "Uganda), kinachoruhusu kuishi, kufanya kazi, kufanya biashara, au "
        "kuendesha kampuni nchini Kenya. Kibali chenyewe ni **bure** (KES 0), "
        "kilichowekwa kisheria chini ya Kenya Citizenship and Immigration "
        "Amendment Regulations 2024. Utahitaji pia **Foreigner Certificate "
        "(Alien Card)**, ambayo inagharimu **KES 5,000 kwa mwaka**.\\n\\n"
        "Hati zinazohitajika kwa kawaida: pasipoti halali, barua ya maombi, "
        "PIN ya KRA endapo unafanya biashara, na cheti cha uthibitisho wa "
        "polisi (kwa wafanyabiashara wadogo). Omba mtandaoni, kisha "
        "chapisha fomu na uwasilishe kwa mkono katika ofisi za Uhamiaji "
        "(Nyayo House, Nairobi)."
    ),
    "tcc_application": (
        "Ingia kwenye **itax.kra.go.ke** ukitumia PIN ya KRA ya biashara "
        "(si PIN binafsi ya mkurugenzi), nenda kwenye menyu ya "
        "**'Certificates'**, kisha chagua **'Apply for Tax Compliance "
        "Certificate (TCC)'**. Kagua taarifa zilizojazwa kiotomatiki, chagua "
        "sababu ya kuomba, kisha bofya Submit.\\n\\nIkiwa marejesho na malipo "
        "yako yako sawa, mara nyingi huidhinishwa ndani ya siku moja au "
        "mbili na kutumwa kwa barua pepe. Ikiwa kuna jambo lililobaki "
        "(marejesho ambayo hayajawasilishwa, malipo yaliyobaki, au "
        "kutokamilisha eTIMS), mfumo utakuonyesha ili ulishughulikie kabla "
        "ya kuomba tena. Ni **bure**, na ikitolewa ni halali kwa **miezi "
        "12**."
    ),
    "probation_period": (
        "Kwa mujibu wa **Kifungu cha 42 cha Sheria ya Ajira ya 2007**, "
        "kipindi cha majaribio (probation) hakiwezi kuzidi **miezi 6** "
        "mwanzoni, lakini kinaweza kuongezwa kwa kipindi kingine cha **si "
        "zaidi ya miezi 6** kwa ridhaa ya maandishi ya mfanyakazi -- hivyo "
        "muda wa juu unaowezekana ni **miezi 12** kwa jumla, si mwaka "
        "mmoja moja kwa moja tangu mwanzo.\\n\\nWaajiri wengi hutumia "
        "kipindi kifupi zaidi (kawaida miezi 3), wakihifadhi kipindi kizima "
        "cha miezi 6 (au kilichoongezwa) kwa nafasi za juu zaidi au za "
        "kitaalamu. Wafanyakazi walio kwenye majaribio hawapo chini ya "
        "sharti la usikilizwaji wa haki la Kifungu cha 41 kabla ya "
        "kufukuzwa, lakini uamuzi wowote lazima usiwe wa ubaguzi na uwe na "
        "sababu halali."
    ),
    "agpo": (
        "**AGPO** (Access to Government Procurement Opportunities) "
        "inatenga **asilimia 30 ya manunuzi yote ya serikali** kwa "
        "makampuni yanayomilikiwa na vijana (miaka 18-35), wanawake, na "
        "watu wenye ulemavu, kila kundi likihitajika kuwa na **umiliki wa "
        "asilimia 70 angalau** na **uongozi wa asilimia 100** kutoka kwa "
        "kundi hilo.\\n\\nKujiandikisha: hakikisha biashara yako imesajiliwa "
        "kisheria (umiliki binafsi, ubia, au kampuni), kusanya cheti cha "
        "usajili, PIN/cheti cha VAT cha KRA, Tax Compliance Certificate, na "
        "(kwa makampuni) CR12 au (kwa ubia) hati ya ubia, kisha jisajili "
        "moja kwa moja kwenye **agpo.go.ke**. Ukisha idhinishwa, hadhi yako "
        "inatumika katika taasisi zote za manunuzi -- wizara za kitaifa, "
        "kaunti, na mashirika ya umma."
    ),
    "hustler_fund_business": (
        "Kiwango cha msingi cha **Personal Loan** (KES 500 hadi KES "
        "50,000, riba ya asilimia 8 kwa mwaka, kurejeshwa ndani ya siku "
        "14) kinaweza kutumika kwa biashara au mahitaji binafsi, "
        "kinapatikana kupitia *254#.\\n\\nKwa biashara hasa, Hustler Fund "
        "pia inatoa mikopo ya **Biashara/Enterprise** kwa vikundi (chama, "
        "ushirika, au vikundi vilivyosajiliwa) na mikopo ya kiwango cha "
        "juu zaidi kwa **biashara zilizosajiliwa zenye PIN ya KRA**, zote "
        "kwa riba ile ile ya asilimia 8 kwa mwaka lakini kwa kiasi kikubwa "
        "zaidi na muda mrefu zaidi wa kurejesha kuliko kiwango cha "
        "binafsi. Kiwango chako cha mkopo na uwezo wa kufikia viwango vya "
        "juu zaidi hukua kwa historia thabiti ya kurejesha kwa wakati."
    ),
}


TOPIC_KEYWORDS = {'''

if sw_anchor not in content:
    print("ERROR: could not find Kiswahili anchor. No changes made.")
else:
    content = content.replace(sw_anchor, sw_new, 1)
    print("Kiswahili CANNED_ANSWERS_SW: added 5 new topics")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
