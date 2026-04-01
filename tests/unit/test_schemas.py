import pytest
from pydantic import ValidationError
from models.schemas import SearchRequest, SearchResponse, JudgmentResult, JudgmentDetail, CompensationStats, HealthCheckResponse, ErrorResponse


def test_search_request_valid():
    request = SearchRequest(query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", top_k=10, min_similarity=0.0)
    assert request.model_dump() == {
        "query": "配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。",
        "top_k": 10,
        "min_similarity": 0.0
    }


def test_search_request_blank_query():
    with pytest.raises(ValidationError):
        SearchRequest(query="", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query=" ", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="\t", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="\n", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="\r", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="\f", top_k=10, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="\v", top_k=10, min_similarity=0.0)


def test_search_request_too_long_query():
    with pytest.raises(ValidationError):
        SearchRequest(top_k=10, min_similarity=0.0, query="一、原告起訴主張：㈠原告與被告於110年12月20日登記結婚，二人婚後感情和睦，於113年9月2日晚上，被告突然提出要離婚，並聲稱雙方個性不合，原告讓其壓力很大，若不跟他離婚，他會要自殺以擺脫原告云云，此時，原告大感震驚，然在被告提出要離婚後，原告每天以淚洗面，且每天嘗試與被告甲○○溝通，努力挽回被告，惟被告已鐵了心要離婚，多次拒絕與原告溝通，後來原告於9月5日整理房間時，發現有重功小吃店（即八分雲集）之發票，惟查被告之工作地點或日常生活重心地點根本不可能會出現該小吃店（註：9月8日之八分雲集即重功小吃店發票，店家在新北市○○區○○街00號1樓，此地點在第三人錢穎諭開設工作室址：新北市○○區○○街0000號2樓之附近），甚至被告不愛吃甜品的人會有購買甜品之發票，再加上被告自跟原告提出欲離婚後，每天早出晚歸，其種種舉止讓原告心生疑義，始發現被告有追蹤訴外人錢穎諭IG，原告進而發現被告與錢穎諭發生婚外情。㈡被告與錢穎諭於113年9月1日起至9月15日期間，被告多次以名下車牌號碼000-0000號自小客車接送錢穎諭上下班，且被告多次待在錢穎諭之工作室約會，甚至於113年9月14日被告與錢穎諭至艾蔓汽車旅館開房間，二人待至隔日9月15日中午始出來，二人明顯為已有多次性行為，詳細時間、地點、情狀，如附表所示。被告行為已侵害原告婚姻配偶權，而原告原生活重心完全在丈夫與身上，因突遭被告以莫須有罪名提出離婚，內心本是惶恐不安，事後發現原來係被告早已與第三人錢穎諭交往進而始提出離婚，故原告身心受創甚深，至今有憂鬱、失眠及情緒失控等情形，必須持續回診身心科、按時服藥治療，此有藥單等為證，被告於兩造婚姻關係存續中，與錢穎諭發生性行為，且如附表所示，二人之行為逾越朋友交遊等一般社交行為之不正常往來，被告之行為已逾越社會一般通念所能容忍之範圍，被告甚至以此向原告提出離婚，已達破壞婚姻共同生活圓滿安全及幸福之程度。㈣又因被告堅持要離婚，故於113年9月17日，原告無奈約雙方家長見面，本以為被告會主動承認其與錢穎瑜交往，兩造婚姻仍有轉圜餘地，惟被告堅持強調雙方是個性不合，卻完全忽視倘若兩造個性不合，則兩造為何可以交往八年與結婚三年，故當天原告無法再接受被告所謂個性不合始要跟原告離婚一情，並提出如原證5之影片與照片給被告觀看，而被告看完後當時稱：「我去汽車旅館，我有去，我有跟媽媽說，對，我就嫖妓」、「沒有，因為我只是想要發洩一下」、「我真的沒有要跟他談感情，對我來說，就是有點像是花錢找伴遊一樣」，至此，被告始坦承與錢穎瑜發生性行為，惟為了推卸責任，又稱其與錢穎瑜性行為係嫖妓、錢穎瑜是從事伴遊小姐等語，但真如其所述，二人間為性交易行為，則被告會與所謂性交易對象於113年9月1日～9月15日多次見面，並接送伊回住處？由此可見，被告與錢穎瑜確實已在交往，且二人已發生性行為，絕非被告答辯狀所稱被告欲投資錢穎瑜，與伊見面於汽車旅館過夜。㈤是以原告主張被告以此方式侵害原告基於配偶關係身分法益情節重大，且其精神飽受重大痛苦，故依民法第184條第1項及第195條規定提起本件，請求被告賠償其非財產上之損害即精神慰撫金40萬元，並聲明：⑴被告應給付原告40萬元，及自起訴狀繕本送達翌日起至清償日止，按週年利率百分之五計算之利息。⑵願供擔保，請准宣告假執行。二、被告則以：㈠附表編號1至3：原告係以原證1五張發票，自行推論原告與錢穎諭有八方雲集「約會」行為云云，按依據五張發票本身能之證明事項，就是證明被告有於發票所記載時間在八方雲集店內吃飯，不論被告是自己獨自一人在八方雲集用餐，或是有和其他友人在入方雲集吃飯用餐行為均不構成司法判決實務上所認定侵害配偶權類型。㈡附表編號4、5、6、8：原告以偷拍之原證五錄影光碟檔案，指稱被告於113年9月7、8、12日與錢穎諭待在「錢錢美容美睫spa館」內係在「約會」云云，實則，被告係因朋友介紹而認識錢穎諭，錢穎諭向被告表示其有在美容美睫spa館工作，伊有意願自己開店想找人投資，而被告本來就做汽車包膜美容業，對於增加投資項目投資開店有興趣，故被告利用假日到上開美睫工作室參觀硏究以決定是否要投資，「上開在美睫工作室內」行為並非原告所指稱之「約會」，況該工作室內週六日店內人員及顧客眾多，當然不是所謂約會。原告將被告與友人至八方雲集吃飯、到美睫工作室開會研究是否要投資、至商場吃飯等正常行為都主張為作「約會或不正常往來」，主張被告上開吃飯、至美睫工作室討論投實等行為係侵害配偶權云云，並無可採。基上，附表編號4、5、6、8之待在美睫工作坊內開會考察或吃飯等正常行為不構成司法判決實務上漸認定侵審配偶權類型。㈢附表編號7：被告於113年9月14日確實有與錢穎諭至汽車旅館，被告承認上開載錢穎諭至汽車旅館休息過夜行為思慮不周，但並無發生性行為，且更無原告起訴狀中任意指控之所謂明顯多次性行為，就僅此一次至汽車旅館行為原告主張請求損害賠償金額40萬元明顯過高。㈣原告提出原證10之兩造間錄音譯文主張被告有承認與錢穎諭發生性行為云云，完全與事實不符")


def test_search_request_too_short_query():
    with pytest.raises(ValidationError):
        SearchRequest(query="侵權行為", top_k=10, min_similarity=0.0)


def test_search_request_invalid_top_k():
    with pytest.raises(ValidationError):
        SearchRequest(query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", top_k=0, min_similarity=0.0)
    with pytest.raises(ValidationError):
        SearchRequest(query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", top_k=51, min_similarity=0.0)


def test_search_request_invalid_min_similarity():
    with pytest.raises(ValidationError):
        SearchRequest(query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", top_k=10, min_similarity=-0.1)
    with pytest.raises(ValidationError):
        SearchRequest(query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", top_k=10, min_similarity=1.1)


def test_judgment_result_valid():
    result = JudgmentResult(
        id=1, title="侵權行為損害賠償", case_number="112年度南簡字第1424號", court="臺灣臺南地方法院臺南簡易庭", date="20240125", compensation=100000, 
        facts="原告與被告甲○○自民國104年8月6日起至112年4月12日止為夫妻關係，育有2名子女。被告甲○○自111年10月起經常凌晨才返家，原告為確保其人身安全，於系爭車輛安裝定位系統。原告於112年4月4日晚間發現被告甲○○與被告丙○○同住歐美汽車旅館並發生性行為，原告因此受到精神上之痛苦。", 
        reasoning="原告主張其與被告甲○○為夫妻關係，並提供戶籍謄本證明。原告主張被告二人於112年4月4日晚間同住並出入歐美汽車旅館且發生性行為，原告以定位截圖及錄影畫面、現場照片為證。法院認為定位截圖及錄影畫面、現場照片具有證據能力，且被告二人有於112年4月4日同住並出入歐美汽車旅館，但尚難證明其間發生性行為。被告丙○○知悉被告甲○○為已婚身分，原告得依侵權行為之法律關係請求賠償。", 
        evidence_types=["定位截圖", "錄影畫面", "現場照片"], 
        similarity=0.87
    )
    assert result.model_dump() == {
        "id": 1,
        "title": "侵權行為損害賠償",
        "case_number": "112年度南簡字第1424號",
        "court": "臺灣臺南地方法院臺南簡易庭",
        "date": "20240125",
        "compensation": 100000,
        "facts": "原告與被告甲○○自民國104年8月6日起至112年4月12日止為夫妻關係，育有2名子女。被告甲○○自111年10月起經常凌晨才返家，原告為確保其人身安全，於系爭車輛安裝定位系統。原告於112年4月4日晚間發現被告甲○○與被告丙○○同住歐美汽車旅館並發生性行為，原告因此受到精神上之痛苦。",
        "reasoning": "原告主張其與被告甲○○為夫妻關係，並提供戶籍謄本證明。原告主張被告二人於112年4月4日晚間同住並出入歐美汽車旅館且發生性行為，原告以定位截圖及錄影畫面、現場照片為證。法院認為定位截圖及錄影畫面、現場照片具有證據能力，且被告二人有於112年4月4日同住並出入歐美汽車旅館，但尚難證明其間發生性行為。被告丙○○知悉被告甲○○為已婚身分，原告得依侵權行為之法律關係請求賠償。",
        "evidence_types": ["定位截圖", "錄影畫面", "現場照片"],
        "similarity": 0.87
    }


def test_judgment_result_invalid():
    with pytest.raises(ValidationError):
        JudgmentResult(id=None, title="侵權行為損害賠償", case_number="110年度侵字第123號", court="臺灣臺北地方法院", date="20210615", compensation=150000, facts="被告與配偶多次在汽車旅館過夜...", reasoning="依原告提出之監視器影像、信用卡簽單...", evidence_types=["監視器影像", "信用卡簽單", "通訊軟體對話"], similarity=0.87)
    

def test_compensation_stats_valid():
    stats = CompensationStats(total=10, median_compensation=400000, avg_compensation=338000, min_compensation=80000, max_compensation=500000)
    assert stats.model_dump() == {
        "total": 10,
        "median_compensation": 400000,
        "avg_compensation": 338000,
        "min_compensation": 80000,
        "max_compensation": 500000
    }


def test_compensation_stats_invalid():
    with pytest.raises(ValidationError):
        CompensationStats(total=-1, median_compensation=100000, avg_compensation=100000, min_compensation=100000, max_compensation=100000)
    with pytest.raises(ValidationError):
        CompensationStats(total=None, median_compensation=100000, avg_compensation=100000, min_compensation=100000, max_compensation=100000)
    with pytest.raises(ValidationError):
        CompensationStats(total="十", median_compensation=100000, avg_compensation=100000, min_compensation=100000, max_compensation=100000)


def test_search_response_valid():
    response = SearchResponse(
        results=[
            JudgmentResult(id=1, title="侵權行為損害賠償", case_number="112年度南簡字第1424號", court="臺灣臺南地方法院臺南簡易庭", date="20240125", compensation=100000, 
                facts="原告與被告甲○○自民國104年8月6日起至112年4月12日止為夫妻關係，育有2名子女。被告甲○○自111年10月起經常凌晨才返家，原告為確保其人身安全，於系爭車輛安裝定位系統。原告於112年4月4日晚間發現被告甲○○與被告丙○○同住歐美汽車旅館並發生性行為，原告因此受到精神上之痛苦。", 
                reasoning="原告主張其與被告甲○○為夫妻關係，並提供戶籍謄本證明。原告主張被告二人於112年4月4日晚間同住並出入歐美汽車旅館且發生性行為，原告以定位截圖及錄影畫面、現場照片為證。法院認為定位截圖及錄影畫面、現場照片具有證據能力，且被告二人有於112年4月4日同住並出入歐美汽車旅館，但尚難證明其間發生性行為。被告丙○○知悉被告甲○○為已婚身分，原告得依侵權行為之法律關係請求賠償。", 
                evidence_types=["定位截圖", "錄影畫面", "現場照片"], 
                similarity=0.87)
                ],
        stats=CompensationStats(total=1, median_compensation=100000, avg_compensation=100000.0, min_compensation=100000, max_compensation=100000),
        query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。",
        search_time_ms=1000)
    assert response.model_dump() == {
        "results": [
            {
                "id": 1,
                "title": "侵權行為損害賠償",
                "case_number": "112年度南簡字第1424號",
                "court": "臺灣臺南地方法院臺南簡易庭",
                "date": "20240125",
                "compensation": 100000,
                "facts": "原告與被告甲○○自民國104年8月6日起至112年4月12日止為夫妻關係，育有2名子女。被告甲○○自111年10月起經常凌晨才返家，原告為確保其人身安全，於系爭車輛安裝定位系統。原告於112年4月4日晚間發現被告甲○○與被告丙○○同住歐美汽車旅館並發生性行為，原告因此受到精神上之痛苦。",
                "reasoning": "原告主張其與被告甲○○為夫妻關係，並提供戶籍謄本證明。原告主張被告二人於112年4月4日晚間同住並出入歐美汽車旅館且發生性行為，原告以定位截圖及錄影畫面、現場照片為證。法院認為定位截圖及錄影畫面、現場照片具有證據能力，且被告二人有於112年4月4日同住並出入歐美汽車旅館，但尚難證明其間發生性行為。被告丙○○知悉被告甲○○為已婚身分，原告得依侵權行為之法律關係請求賠償。",
                "evidence_types": ["定位截圖", "錄影畫面", "現場照片"],
                "similarity": 0.87
            }
        ],
        "stats": {
            "total": 1,
            "median_compensation": 100000,
            "avg_compensation": 100000,
            "min_compensation": 100000,
            "max_compensation": 100000
        },
        "query": "配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。",
        "search_time_ms": 1000
    }


def test_search_response_invalid():
    with pytest.raises(ValidationError):
        SearchResponse(results=[], stats=CompensationStats(total=10, median_compensation=100000, avg_compensation=100000, min_compensation=100000, max_compensation=100000), query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", search_time_ms=1000)
    with pytest.raises(ValidationError):
        SearchResponse(results=[JudgmentResult(id=1, title="侵權行為損害賠償", case_number="110年度侵字第123號", court="臺灣臺北地方法院", date="20210615", compensation=150000, facts="被告與配偶多次在汽車旅館過夜...", reasoning="依原告提出之監視器影像、信用卡簽單...", evidence_types=["監視器影像", "信用卡簽單", "通訊軟體對話"], similarity=0.87)], stats=CompensationStats(total=10, median_compensation=100000, avg_compensation=100000, min_compensation=100000, max_compensation=100000), query="配偶與第三人外遇交往長達五年以上，期間多次單獨出國同遊，有出入境紀錄與社群軟體的打卡照片為證。", search_time_ms=1000)

def test_judgment_detail_valid():
    detail = JudgmentDetail(
        id=2, title="損害賠償", case_number="112年度鳳簡字第387號", court="臺灣高雄地方法院", date="20240115", compensation=300000, 
        facts="原告李雅萍與被告李旻峰於民國95年3月18日結婚，育有2女。被告引介訴外人張又云至共同經營之長照機構工作，兩人經常同進同出，形同夫妻。被告在工作上指責原告，導致原告離開該機構。111年底，原告的女兒在被告贈與的平板上發現被告與張又云的親密及性行為照片，並於112年2月告知原告。被告與張又云的交往已逾越朋友關係，侵害原告基於配偶關係之身分法益，導致原告精神上受有極大痛苦，故請求賠償。", 
        reasoning="法院認為，故意或過失不法侵害他人權利者應負損害賠償責任。被告與張又云的交往已逾越配偶應守之份際，侵害原告的身分法益，且情節重大。原告提出的證據，包括被告與張又云的出遊及性行為照片、LINE對話內容，均具證據能力。被告否認性行為照片中女性為張又云，但法院認為照片日期在婚姻關係存續期間，已足以認定被告侵害原告的配偶權益。法院酌情考量雙方身分、資力及侵害程度，認為原告請求的30萬元精神慰撫金為合理，故予以准許。",
        decision="主      文被告應給付原告新臺幣參拾萬元。原告其餘之訴駁回。訴訟費用由被告負擔五分之三，餘由原告負擔。本判決第一項得假執行。但被告以新臺幣參拾萬元為原告預供擔保，得免為假執行。", 
        full_text="原告主張：兩造前於民國95年3月18日結婚，育有2女。惟在兩造婚姻關係存續期間，被告引介訴外人張又云至兩造共同經營之長照機構工作後，兩人經常同進同出，在外形同夫妻......", 
        evidence_types=["性行為照片", "出遊照片", "LINE對話內容擷圖"])
    assert detail.model_dump() == {
        "id": 2,
        "title": "損害賠償",
        "case_number": "112年度鳳簡字第387號",
        "court": "臺灣高雄地方法院",
        "date": "20240115",
        "compensation": 300000,
        "facts": "原告李雅萍與被告李旻峰於民國95年3月18日結婚，育有2女。被告引介訴外人張又云至共同經營之長照機構工作，兩人經常同進同出，形同夫妻。被告在工作上指責原告，導致原告離開該機構。111年底，原告的女兒在被告贈與的平板上發現被告與張又云的親密及性行為照片，並於112年2月告知原告。被告與張又云的交往已逾越朋友關係，侵害原告基於配偶關係之身分法益，導致原告精神上受有極大痛苦，故請求賠償。",
        "reasoning": "法院認為，故意或過失不法侵害他人權利者應負損害賠償責任。被告與張又云的交往已逾越配偶應守之份際，侵害原告的身分法益，且情節重大。原告提出的證據，包括被告與張又云的出遊及性行為照片、LINE對話內容，均具證據能力。被告否認性行為照片中女性為張又云，但法院認為照片日期在婚姻關係存續期間，已足以認定被告侵害原告的配偶權益。法院酌情考量雙方身分、資力及侵害程度，認為原告請求的30萬元精神慰撫金為合理，故予以准許。",
        "decision": "主      文被告應給付原告新臺幣參拾萬元。原告其餘之訴駁回。訴訟費用由被告負擔五分之三，餘由原告負擔。本判決第一項得假執行。但被告以新臺幣參拾萬元為原告預供擔保，得免為假執行。",
        "full_text": "原告主張：兩造前於民國95年3月18日結婚，育有2女。惟在兩造婚姻關係存續期間，被告引介訴外人張又云至兩造共同經營之長照機構工作後，兩人經常同進同出，在外形同夫妻......",
        "evidence_types":["性行為照片", "出遊照片", "LINE對話內容擷圖"]}


def test_judgment_detail_invalid():
    with pytest.raises(ValidationError):
        JudgmentDetail()


def test_health_check_response_valid():
    response = HealthCheckResponse(
        status="ok",
        database={
            "total_judgments": 10000,
            "total_compensations": 8000,
            "avg_compensation": 150000,
            "db_size_mb": 120.5,
        },
        vector_cache_status="loaded",
        vector_cache_count=1234,
        redis="ok",
        version="1.0.0",
        timestamp="2026-01-01T12:00:00",
    )
    assert response.model_dump() == {
        "status": "ok",
        "database": {
            "total_judgments": 10000,
            "total_compensations": 8000,
            "avg_compensation": 150000,
            "db_size_mb": 120.5,
        },
        "vector_cache_status": "loaded",
        "vector_cache_count": 1234,
        "redis": "ok",
        "version": "1.0.0",
        "timestamp": "2026-01-01T12:00:00",
    }


def test_health_check_response_invalid():
    with pytest.raises(ValidationError):
        HealthCheckResponse(
            status="ok",
            database={"total_judgments": 10000},
            vector_cache_status="loaded",
            redis="ok",
            version="1.0.0",
            timestamp="2024-01-01T12:00:00",
        )

    with pytest.raises(ValidationError):
        HealthCheckResponse(
            status="ok",
            database={"total_judgments": 10000},
            vector_cache_status="loaded",
            vector_cache_count="not-an-int",
            redis="ok",
            version="1.0.0",
            timestamp="2024-01-01T12:00:00",
        )


def test_error_response_valid():
    response = ErrorResponse(
        error="查詢內容不能為空白",
        detail="請輸入至少 5 個字的案情描述",
    )
    assert response.model_dump() == {
        "error": "查詢內容不能為空白",
        "detail": "請輸入至少 5 個字的案情描述",
    }

    response_with_list_detail = ErrorResponse(
        error="validation error",
        detail=[
            {
                "loc": ["body", "query"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ],
    )
    assert response_with_list_detail.model_dump() == {
        "error": "validation error",
        "detail": [
            {
                "loc": ["body", "query"],
                "msg": "field required",
                "type": "value_error.missing",
            }
        ],
    }


def test_error_response_invalid():
    with pytest.raises(ValidationError):
        ErrorResponse(detail="查詢內容不能為空白")