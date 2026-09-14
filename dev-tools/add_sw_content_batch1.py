with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),'''

new_content = '''        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),
    "sole_prop_to_llc": (
        "Kenya haina mchakato wa hatua moja wa 'kubadilisha' -- kwa kweli, "
        "ni hatua mbili tofauti: **(1) sitisha jina lako la biashara "
        "lililopo** kwa kujaza **Fomu ya BN6** kwenye eCitizen, na **(2) "
        "sajili kampuni mpya ya kikomo** ukitumia **Fomu za CR1, CR2, CR8** "
        "pamoja na Memorandum/Articles of Association (BRS hutoa violezo "
        "vya kawaida, au unaweza kuvibinafsisha). Kwa kawaida unaweza "
        "kutumia jina lile lile la biashara, sasa likiwa na 'Limited' au "
        "'Ltd'.\\n\\n**Kuhusu PIN ya KRA hasa**: biashara yako ya umiliki "
        "binafsi ilitumia **PIN yako binafsi ya KRA**. Kampuni mpya "
        "inahitaji **PIN yake tofauti**, unaomba kupitia iTax kwa kuchagua "
        "'Non-Individual' kama aina ya mlipa kodi -- na kila mkurugenzi/"
        "mwanahisa lazima awe na PIN yake binafsi ya KRA kabla ya maombi "
        "ya PIN ya kampuni kuendelea.\\n\\n**Kuhusu ada**: tarajia malipo "
        "mawili tofauti ya serikali -- kusitisha jina la biashara, na "
        "usajili wa kampuni ya kikomo (takriban KES 10,650-10,750 kulingana "
        "na ratiba za sasa za BRS, ingawa ningependekeza uthibitishe kiasi "
        "halisi cha sasa moja kwa moja kwenye eCitizen). Kumbuka hakuna "
        "**mtaji wa chini wa hisa unaotakiwa kisheria**, ingawa watu wengi "
        "huchagua kiasi kama KES 100,000 kama mazoea. Mchakato safi wenye "
        "nyaraka zote sahihi kwa kawaida huchukua **siku 5-10 za kazi**."
    ),
    "wef": (
        "**Women Enterprise Fund (WEF)** ni shirika halisi na tofauti la "
        "serikali (lilianzishwa 2007, chini ya Wizara ya Utumishi wa Umma, "
        "Vijana na Mambo ya Jinsia) -- lisichanganywe na YEDF (inayolenga "
        "vijana) au Hustler Fund. **Sifa: mwanamke yeyote wa Kenya mwenye "
        "miaka 18 au zaidi**, akiomba peke yake au kama sehemu ya kikundi "
        "kilichosajiliwa.\\n\\n**Bidhaa kuu**:\\n"
        "- **Mkopo wa Tuinuke Chama** (kupitia Constituency Women "
        "Enterprise Scheme): kwa vikundi vya wanawake vilivyosajiliwa vya "
        "wanachama 10-30 (angalau asilimia 70 wanawake, uongozi wa "
        "asilimia 100 wanawake), vilivyosajiliwa na Huduma za Jamii kwa "
        "angalau miezi 3, vyenye akaunti ya benki/SACCO -- gharama ndogo "
        "yenye ada ndogo ya utawala\\n"
        "- **Ufadhili wa LPO**: kwa biashara za wanawake binafsi "
        "zinazohitaji kutimiza maagizo ya ununuzi au zabuni\\n\\n"
        "Omba kupitia ofisi za kanda za WEF, au mtandaoni kwenye wef.go.ke."
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
    ),'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added 5 Kiswahili canned answers")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
