with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "sharti la usikilizwaji wa haki la Kifungu cha 41 kabla ya "
        "kufukuzwa, lakini uamuzi wowote lazima usiwe wa ubaguzi na uwe na "
        "sababu halali."
    ),'''

new_content_suffix = '''        "sharti la usikilizwaji wa haki la Kifungu cha 41 kabla ya "
        "kufukuzwa, lakini uamuzi wowote lazima usiwe wa ubaguzi na uwe na "
        "sababu halali."
    ),
    "unified_business_permit": (
        "Katika Kaunti ya Nairobi hasa, hii ni **Unified Business Permit "
        "(UBP)** -- leseni moja ya kila mwaka inayounganisha vibali "
        "kadhaa vilivyokuwa tofauti (leseni ya biashara, ukaguzi wa moto, "
        "cheti cha afya/chakula, kibali cha matangazo/alama) katika maombi "
        "moja. Omba kupitia **NairobiPay (nairobiservices.go.ke)**, piga "
        "***647#**, au tembelea City Hall Annex.\\n\\nAda inategemea aina na "
        "ukubwa wa biashara yako (duka dogo huenda likilipa karibu KES "
        "4,000 pamoja na KES 200 ya maombi; shughuli kubwa zaidi hulipa "
        "zaidi) -- thibitisha ada halisi ya aina yako kwenye tovuti. "
        "Inafuata mzunguko wa **Januari-Desemba**; maombi ya kuhuisha "
        "kwa kawaida hufunguliwa Novemba, na malipo yanatarajiwa kabla ya "
        "Machi 31 kuepuka adhabu zinazoongezeka."
    ),
    "pharmacy_license": (
        "Kuendesha duka la dawa au kemisti kunahitaji leseni kutoka "
        "**Pharmacy and Poisons Board (PPB)**, msimamizi wa kitaifa wa "
        "dawa chini ya Sheria ya Dawa na Sumu (Cap 244) -- hii ni pamoja "
        "na, si badala ya, Single Business Permit ya kaunti yako "
        "(takriban KES 5,000-30,000).\\n\\n**Sharti muhimu**: kila mtu "
        "mwenye maslahi ya kifedha katika duka la dawa lazima awe "
        "mfamasia aliyesajiliwa au fundi wa dawa aliyeandikishwa -- kwa "
        "kawaida huwezi kumiliki duka la dawa kama mwekezaji tu asiye "
        "mfamasia. Msimamizi mfamasia aliyeteuliwa pia anahitaji leseni "
        "yake ya kila mwaka ya kufanya kazi kutoka PPB.\\n\\n**Mchakato**: "
        "sajili majengo yako na PPB, kisha pitisha ukaguzi wa majengo "
        "unaoangalia rafu sahihi, mzunguko wa hewa, eneo la kutolea dawa "
        "tofauti na counter ya mauzo, kabati la sumu lenye kufuli, jokofu "
        "kwa bidhaa zinazohitaji baridi, na alama ya Msalaba wa Kijani. "
        "Leseni hutolewa baada ya ukaguzi wenye mafanikio na lazima "
        "zihuishwe kila mwaka (leseni zote za PPB huisha Desemba 31)."
    ),
    "ca_license": (
        "Si kila kampuni ya teknolojia inahitaji hii -- **Communications "
        "Authority of Kenya (CA)** inatoa leseni hasa kwa mawasiliano ya "
        "simu, utangazaji, huduma za intaneti, na waendeshaji wa posta/"
        "kurier, si biashara za kawaida za programu. Ikiwa kampuni yako "
        "inajenga tu programu au tovuti bila kuendesha miundombinu ya "
        "mawasiliano au kutoa huduma za maudhui/mtandao zinazodhibitiwa, "
        "huenda usihitaji leseni ya CA kabisa.\\n\\nIkiwa unaangukia katika "
        "kundi linalodhibitiwa, mfumo wa CA wa Unified Licensing "
        "Framework unahusisha aina tatu kuu: **Network Facilities "
        "Provider**, **Application Service Provider**, na **Content "
        "Service Provider** (pamoja na leseni tofauti za utangazaji, "
        "uidhinishaji wa vifaa, na huduma za posta/kurier). Maombi "
        "yanahitaji barua kwa Mkurugenzi wa Leseni, cheti chako cha "
        "usajili, hati za kampuni (CR12 kwa makampuni), na orodha ya "
        "wakurugenzi."
    ),
    "nssf_registration": (
        "**Kama mwajiri**, jisajili kupitia NSSF Employer Self-Service "
        "portal (selfservice.nssf.or.ke) -- chagua 'Employer "
        "Registration' ikiwa hujawahi kujisajili. Ni vyema kuwa na "
        "**PIN yako ya KRA kwanza**, kwani utaihitaji wakati wa usajili. "
        "Ukisha idhinishwa, unapewa namba ya mwajiri, mara nyingi papo "
        "hapo.\\n\\n**Usajili ni wa lazima** kwa kila mwajiri mwenye "
        "hata mfanyakazi mmoja anayepata KES 1,000 au zaidi kwa mwezi -- "
        "hii inajumuisha wafanyakazi wa muda, wa kandarasi, na wa muda "
        "mfupi, si wafanyakazi wa kudumu pekee. Kutojisajili ni kosa la "
        "kisheria chini ya Sheria ya NSSF ya 2013.\\n\\n**Kwa kila "
        "mfanyakazi**: wanaweza kujisajili wenyewe katika ofisi yoyote ya "
        "NSSF wakiwa na kitambulisho chao cha taifa/pasipoti/Alien Card na "
        "barua ya utambulisho kutoka kwako kama mwajiri wao, baada ya "
        "hapo watapokea namba ya uanachama wa NSSF utakayoihitaji kutuma "
        "michango yao."
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) ni "
        "shirika la serikali (lililoundwa 2019, likiunganisha Export "
        "Promotion Council ya zamani na Brand Kenya Board) linalosaidia "
        "wafanyabiashara wa Kenya kuuza nje na kuendeleza 'Brand "
        "Kenya' kimataifa.\\n\\n**Kile kinachotolewa**: mwongozo wa "
        "taratibu na nyaraka za usafirishaji, taarifa za soko na sharti "
        "za kuingia katika nchi lengwa, ujenzi wa uwezo kupitia mafunzo "
        "ya usafirishaji, ujumbe wa kibiashara na ushiriki katika "
        "maonyesho ya biashara, na msaada wa **maendeleo ya bidhaa na "
        "branding** -- ikiwa ni pamoja na ufungashaji, uwekaji lebo, na "
        "uwekaji nafasi ya chapa kwa wanunuzi wa kimataifa. Wasiliana "
        "kupitia ofisi za KEPROBA au makeitkenya.go.ke."
    ),
    "no_permit_penalty": (
        "Kuendesha biashara bila kibali halali cha kaunti ni kinyume cha "
        "sheria nchini Kenya, chini ya **Sheria ya Serikali za Kaunti ya "
        "2012** pamoja na Sheria ya Fedha na Leseni za Biashara za kaunti "
        "yako.\\n\\n**Madhara yanaweza kujumuisha**:\\n"
        "- **Faini**: mara nyingi kati ya KES 50,000-200,000, ingawa hii "
        "inatofautiana sana kwa kaunti\\n"
        "- **Amri za kufunga**: wakaguzi wa kaunti wanaweza kutoa amri ya "
        "kufunga mara moja, wakifunga biashara yako mpaka utii\\n"
        "- **Kifungo kinachowezekana**: katika hali mbaya au za "
        "kurudia, wakurugenzi/wamiliki wanaweza kukabiliwa na mashtaka ya "
        "jinai binafsi\\n"
        "- **Malipo ya nyuma ya adhabu**: juu ya ada ya kibali chenyewe "
        "ukisha tii\\n\\n"
        "Kaunti nyingi huruhusu muda wa neema (kawaida siku 30-60 baada "
        "ya kuisha) kabla ya adhabu kuanza kwa kibali kilichoisha muda -- "
        "lakini kuendesha bila kibali kabisa tangu mwanzo kunabeba hatari "
        "kamili tangu siku ya kwanza."
    ),
    "sole_prop_vs_limited": (
        "Tofauti kuu ni **dhima na utengano**. **Umiliki binafsi** si "
        "chombo tofauti cha kisheria kutoka kwako -- wewe na biashara ni "
        "kitu kimoja kisheria, ikimaanisha unabeba **dhima kamili "
        "binafsi** kwa madeni ya biashara, na unatumia **PIN yako "
        "binafsi ya KRA**. Ni haraka na nafuu kuanzisha, bila mtaji wa "
        "chini.\\n\\n**Kampuni ya kikomo** ni mtu tofauti wa kisheria "
        "kutoka kwa wamiliki wake -- dhima ya wanahisa kwa kawaida "
        "inakomea kwa kiasi walichowekeza katika hisa, na kampuni "
        "inapata **PIN yake tofauti ya KRA**, akaunti yake ya benki, na "
        "inaweza kuingia mikataba au kushtakiwa kwa jina lake. **Hakuna "
        "mtaji wa chini wa hisa unaotakiwa kisheria**, ingawa inahusisha "
        "makaratasi zaidi (Memorandum/Articles of Association, fomu za "
        "CR1/CR2/CR8) na uzingatiaji unaoendelea (marejesho ya kila "
        "mwaka kwa BRS) kuliko umiliki binafsi."
    ),
    "late_filing_penalty": (
        "Adhabu zinategemea marejesho gani na kama ni kuchelewa "
        "kuwasilisha au kuchelewa kulipa -- zote zinatumika kwa wajibu wa "
        "KRA chini ya **Sheria ya Taratibu za Kodi ya 2015**:\\n\\n"
        "- **Kodi ya mapato binafsi**: KES 2,000 kwa marejesho kwa "
        "kuchelewa kuwasilisha\\n"
        "- **Kodi ya mapato ya kampuni/ubia**: KES 20,000 au 5% ya kodi "
        "inayodaiwa, kikubwa kati ya hivyo, kwa kuchelewa kuwasilisha; "
        "kuchelewa kulipa kunaongeza 5% zaidi pamoja na riba ya 1% kwa "
        "mwezi\\n"
        "- **PAYE**: kuchelewa kuwasilisha ni 25% ya kodi inayodaiwa au "
        "KES 10,000, kikubwa kati ya hivyo\\n"
        "- **VAT**: kuchelewa kuwasilisha ni 5% ya kodi inayodaiwa au "
        "KES 10,000, kikubwa kati ya hivyo\\n\\n"
        "**Hata kama huna mapato au mauzo, lazima uwasilishe marejesho "
        "ya nil** -- kutofanya hivyo kunasababisha adhabu ile ile ya "
        "moja kwa moja."
    ),
    "etims_general": (
        "**eTIMS** (electronic Tax Invoice Management System) ni mfumo "
        "wa KRA wa kutengeneza risiti/ankara za kielektroniki "
        "zinazokubalika kikodi -- unahitajika kwa biashara "
        "zilizosajiliwa VAT, na kwa mtu yeyote anayetaka gharama za "
        "biashara zikubaliwe kikodi, kwani KRA hukubali tu ankara "
        "zilizotengenezwa na eTIMS kama uthibitisho halali wa "
        "ununuzi.\\n\\n**Kwa nini biashara yako inahitaji**: bila ankara "
        "za eTIMS, gharama zako za biashara huenda zisikubaliwe kikodi, "
        "na wateja wanaohitaji kudai VAT yao wenyewe hawawezi kufanya "
        "hivyo kutoka ankara isiyo ya eTIMS. Kwa biashara ndogo, chaguo "
        "la bure la **eTIMS Lite** (kupitia tovuti au USSD *222#) ni "
        "njia rahisi zaidi ya kutii bila kununua vifaa."
    ),
    "sacco_vs_bank": (
        "**SACCOs** kwa kawaida hutoa mikopo nafuu zaidi kuliko benki za "
        "kibiashara -- mara nyingi **10-14% kwa mwaka**, mara nyingi "
        "ikiwekwa na mkutano mkuu wa mwaka wa SACCO badala ya kubadilika "
        "na Kiwango cha Benki Kuu. Mikopo ya **benki** za kibiashara "
        "kwa kawaida ni **13-20%+ kwa mwaka** na hubadilika na mabadiliko "
        "ya CBK.\\n\\n**Ubadilishanaji muhimu**: SACCOs zinahitaji "
        "**kujiunga na kujenga historia ya akiba kwanza** (kawaida "
        "miezi 3-6) kabla ya kukopa, na kiasi cha mkopo mara nyingi "
        "hukomea kama mara 3-5 ya akiba yako. Benki kwa kawaida "
        "hazihitaji uanachama/akiba ya awali na zinaweza kutoa kiasi "
        "kikubwa zaidi, hasa dhidi ya dhamana -- lakini kwa kiwango cha "
        "juu zaidi."
    ),
    "food_business_license": (
        "Biashara ya chakula (mkahawa, cafe, mkate, duka) inahitaji "
        "tabaka kadhaa, juu ya kibali chako cha kawaida cha kaunti "
        "(Single/Unified Business Permit):\\n\\n"
        "- **Cheti cha Afya/Usafi wa Chakula**: kinatolewa na idara ya "
        "afya ya kaunti, kikithibitisha majengo yako yanafikia viwango "
        "vya usafi -- kawaida KES 2,000-5,000, kinahitajika kabla ya "
        "kufungua\\n"
        "- **Cheti cha Afya cha Mshughulikiaji wa Chakula**: kinahitajika "
        "kwa **kila mfanyakazi binafsi** anayeshughulikia chakula, "
        "kinapatikana baada ya uchunguzi wa afya (karibu KES 1,000 kwa "
        "mtu)\\n"
        "- **Cheti cha Usalama wa Moto**: cha lazima kwa biashara zote, "
        "kinahitaji vizima moto na ukaguzi wa idara ya moto ya kaunti\\n"
        "- **Mahususi kwa mikahawa**: usajili na **Tourism Regulatory "
        "Authority (TRA)** chini ya Sheria ya Utalii ya 2011, ikiwa "
        "unaendesha kama mkahawa\\n\\n"
        "Ikiwa unatengeneza au kufunga bidhaa za chakula kwa mauzo, "
        "utahitaji pia uthibitisho wa **KEBS** (Standardization Mark)."
    ),'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content_suffix, 1)
    print("Added 11 Kiswahili canned answers")
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
