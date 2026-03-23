import re
import logging

def get_court(jfull: str, case_number: str) -> str:
        # 取得法院名稱
        # 目前無法處理：「臺灣○○地方法院」（113年度訴字第369號）、「智慧財產與商業法院」
        first_line = jfull.split('\n')[0].strip()
        court_pattern = r'(臺灣|福建|最高).*?(法院.*?分院|法院)'
        match = re.search(court_pattern, first_line)
        if match:
            court = match.group(0)
        else:
            match = re.search(r"宣[\s\u3000]*示[\s\u3000]*判[\s\u3000]*決[\s\u3000]*筆[\s\u3000]*錄", first_line)
            if match:
                pattern = r"中[\s\u3000]*華[\s\u3000]*民[\s\u3000]*國.*?日([\s\S]{0,100}?)書[\s\u3000]*記[\s\u3000]*官"
                blocks = re.findall(pattern, jfull)
                court = None
                for block in reversed(blocks):
                    if "法院" in block:
                        raw_court_line = block.strip()
                        clean_match = re.search(court_pattern, raw_court_line)
                        court = clean_match.group(0) if clean_match else raw_court_line
                        break  
                if not court:
                    logging.warning(f"宣示判決筆錄找不到法院名稱: {case_number}")
                    court = first_line  
            else:
                logging.warning(f"無法萃取法院名稱: {case_number}")
                court = first_line  
        return court
