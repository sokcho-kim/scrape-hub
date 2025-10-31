#!/usr/bin/env python3
"""
게이트 체인 기반 약제 매칭 정제 스크립트

목적: drug_matching_results_v2.json의 오탐을 제거하고,
     정밀도 최우선으로 하드 레이어(앵커 사전)를 구축

작성일: 2025-10-30
"""

import json
import yaml
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
import unicodedata
from difflib import SequenceMatcher

# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class DrugEntry:
    """약제 항목"""
    en: str
    ko: str
    count: int = 0
    source: str = ""
    reason_codes: List[str] = field(default_factory=list)
    decision: str = "pending"  # active, pending, drop, route_*
    confidence: float = 0.0
    aliases: List[str] = field(default_factory=list)
    context_span: str = ""
    first_seen_source: str = ""

@dataclass
class GateChainStats:
    """게이트 체인 통계"""
    total_input: int = 0
    active: int = 0
    pending: int = 0
    dropped: int = 0
    routed_regimen: int = 0
    routed_biomarker: int = 0
    routed_disease: int = 0
    reason_code_counts: Counter = field(default_factory=Counter)

# =============================================================================
# 메인 클래스
# =============================================================================

class DrugAnchorRefiner:
    """약제 앵커 정제기"""

    def __init__(self, filters_path: str, brand_alias_path: Optional[str] = None, curated_pairs_path: Optional[str] = None):
        """
        초기화

        Args:
            filters_path: filters.yaml 파일 경로
            brand_alias_path: brand_alias.yaml 파일 경로 (선택)
            curated_pairs_path: curated pairs JSON 파일 경로 (선택)
        """
        self.logger = logging.getLogger(__name__)

        # 필터 규칙 로드
        with open(filters_path, 'r', encoding='utf-8') as f:
            self.filters = yaml.safe_load(f)

        # 브랜드명 매핑 로드
        self.brand_to_ingredient = {}
        self.ingredient_to_brands = {}
        if brand_alias_path and Path(brand_alias_path).exists():
            with open(brand_alias_path, 'r', encoding='utf-8') as f:
                brand_data = yaml.safe_load(f)
                self.brand_to_ingredient = brand_data.get('brand_to_ingredient', {})
                self.ingredient_to_brands = brand_data.get('ingredient_to_brands', {})
            self.logger.info(f"Loaded {len(self.brand_to_ingredient)} brand mappings")

        # 큐레이션 화이트리스트 로드 (나중에 normalize_text 사용 필요)
        self.curated_pairs_raw = []  # 원본 데이터 임시 저장
        if curated_pairs_path and Path(curated_pairs_path).exists():
            with open(curated_pairs_path, 'r', encoding='utf-8-sig') as f:
                curated_data = json.load(f)

                # manual_drugs 형식 처리: {"manual_drugs": {"drug_en": ["ko1", "ko2"]}}
                if 'manual_drugs' in curated_data:
                    for en, ko_list in curated_data['manual_drugs'].items():
                        for ko in ko_list:
                            self.curated_pairs_raw.append({
                                'en': en,
                                'ko': ko
                            })

                # 레거시 형식 처리: {"matched_via_english": [...]}
                elif 'matched_via_english' in curated_data:
                    for item in curated_data.get('matched_via_english', []):
                        if item.get('source') == 'manual_curated':
                            self.curated_pairs_raw.append({
                                'en': item.get('english', ''),
                                'ko': item.get('korean', '')
                            })

        # 컨텍스트 시그널 토큰
        self.ctx_tokens = [
            '투여', '용량', 'mg/m²', 'mg/kg', '주사', '정맥', '병용',
            '1일', '2일', '3일', '1회', '2회', '3회',
            '사이클', 'cycle', '주기',
            '임상시험', '유효성', '안전성', '승인',
            '적응증', '허가', '급여'
        ]

        self.stats = GateChainStats()
        self.entries: List[DrugEntry] = []

        # 결과 컨테이너
        self.active_drugs: List[DrugEntry] = []
        self.pending_drugs: List[DrugEntry] = []
        self.dropped_drugs: List[DrugEntry] = []
        self.regimens: List[DrugEntry] = []
        self.biomarkers: List[DrugEntry] = []
        self.diseases: List[DrugEntry] = []

        # 충돌 추적
        self.ko_to_en_map: Dict[str, List[str]] = defaultdict(list)

    # =========================================================================
    # 1. 정규화
    # =========================================================================

    def normalize_text(self, text: str) -> str:
        """
        텍스트 정규화 (NFKC + 따옴표/하이픈/공백 통일)

        Args:
            text: 원본 텍스트

        Returns:
            정규화된 텍스트
        """
        if not text:
            return ""

        # Unicode 정규화
        text = unicodedata.normalize('NFKC', text)

        # 따옴표 통일
        for chars, target in self.filters['normalization']['quote_normalization']:
            for char in chars:
                text = text.replace(char, target)

        # 하이픈 통일
        for chars, target in self.filters['normalization']['hyphen_normalization']:
            for char in chars:
                text = text.replace(char, target)

        # 플러스 통일
        for chars, target in self.filters['normalization']['plus_normalization']:
            for char in chars:
                text = text.replace(char, target)

        # 중복 공백 제거
        if self.filters['normalization']['remove_duplicate_spaces']:
            text = re.sub(r'\s+', ' ', text)

        text = text.strip()

        return text

    def normalize_case(self, text: str, lang: str) -> str:
        """
        대소문자 정규화

        Args:
            text: 텍스트
            lang: 언어 ('en' 또는 'ko')

        Returns:
            정규화된 텍스트
        """
        handling = self.filters['normalization']['case_handling'].get(lang, 'as_is')

        if handling == 'lowercase':
            return text.lower()
        elif handling == 'uppercase':
            return text.upper()
        else:
            return text

    # =========================================================================
    # 2. 브랜드명 해소 및 컨텍스트 분석
    # =========================================================================

    def resolve_brand_name(self, entry: DrugEntry) -> DrugEntry:
        """
        브랜드명을 성분명으로 해소

        Args:
            entry: 약제 항목

        Returns:
            해소된 약제 항목
        """
        en_lower = entry.en.lower()
        ko = entry.ko

        # 영문 브랜드명 체크
        if en_lower in self.brand_to_ingredient:
            ingredient = self.brand_to_ingredient[en_lower]
            self.logger.info(f"Resolved brand: {entry.en} → {ingredient}")
            entry.en = ingredient
            entry.reason_codes.append("BRAND_RESOLVED_EN")

        # 한글 브랜드명 체크
        if ko in self.brand_to_ingredient:
            ingredient = self.brand_to_ingredient[ko]
            self.logger.info(f"Resolved brand: {entry.ko} → {ingredient}")
            # 한글은 브랜드명 그대로 유지하되, 영문만 성분명으로 변경
            if not entry.en or entry.en == ko:
                entry.en = ingredient
            entry.reason_codes.append("BRAND_RESOLVED_KO")

        return entry

    def has_context_signal(self, entry: DrugEntry) -> bool:
        """
        컨텍스트에 임상 시그널이 있는지 확인

        Args:
            entry: 약제 항목

        Returns:
            컨텍스트 시그널 존재 여부
        """
        if not entry.context_span:
            return False

        # 컨텍스트 토큰 검사
        for token in self.ctx_tokens:
            if token in entry.context_span:
                return True

        return False

    # =========================================================================
    # 3. 게이트 1 - 금칙어 필터
    # =========================================================================

    def check_forbidden_forms(self, entry: DrugEntry) -> Tuple[bool, List[str]]:
        """
        금칙어(제형/포장어) 필터

        Args:
            entry: 약제 항목

        Returns:
            (pass, reason_codes)
        """
        reasons = []

        ko = entry.ko

        # 하드 컷 (무조건 제외)
        hard_forms = self.filters['forbidden_forms']['hard']
        if ko in hard_forms:
            reasons.append("FORM_TERM")
            return False, reasons

        # 조건부 컷 (mL, mg 등)
        conditional_forms = self.filters['forbidden_forms']['conditional']
        if ko in conditional_forms:
            # 컨텍스트 확인 (±20자 이내에 성분 단서가 있는지)
            if not self._has_ingredient_hint_in_context(entry):
                reasons.append("CONTEXT_PACKAGING")
                return False, reasons

        return True, reasons

    def _has_ingredient_hint_in_context(self, entry: DrugEntry) -> bool:
        """
        컨텍스트 내에 성분 단서가 있는지 확인

        Args:
            entry: 약제 항목

        Returns:
            성분 단서 존재 여부
        """
        # 현재는 context_span이 비어있으므로 False 반환
        # 실제로는 원본 문서에서 ±20자를 추출해야 함
        if not entry.context_span:
            return False

        ingredient_hints = self.filters['ingredient_hints']
        for hint in ingredient_hints:
            if hint in entry.context_span:
                return True

        return False

    # =========================================================================
    # 3. 게이트 2 - 접미사 정합성
    # =========================================================================

    def check_suffix_consistency(self, entry: DrugEntry) -> Tuple[bool, List[str], bool]:
        """
        접미사 정합성 검사 (EN ↔ KO)

        Args:
            entry: 약제 항목

        Returns:
            (pass, reason_codes, strict_suffix_matched)
        """
        reasons = []
        strict_suffix_matched = False

        en = entry.en.lower()
        ko = entry.ko

        # 접미사 힌트 확인
        for hint in self.filters['en_suffix_to_ko_hint']:
            en_suffix = hint['en']
            ko_suffixes = hint['ko'] if isinstance(hint['ko'], list) else [hint['ko']]
            strict = hint.get('strict', False)

            # EN 접미사 매칭
            if re.search(en_suffix + r'$', en):
                # KO 접미사 매칭 확인
                ko_match = any(re.search(ko_suf + r'$', ko) for ko_suf in ko_suffixes)

                if not ko_match:
                    if strict:
                        # strict 모드에서는 불일치 시 보류
                        reasons.append("SUFFIX_MISMATCH")
                        return False, reasons, False
                    else:
                        # loose 모드에서는 경고만
                        reasons.append("SUFFIX_MISMATCH_WARN")
                else:
                    # 접미사 매칭 성공
                    if strict:
                        strict_suffix_matched = True
                        reasons.append("SUFFIX_MATCH_STRICT")

        return True, reasons, strict_suffix_matched

    # =========================================================================
    # 4. 게이트 3 - 음차/철자 유사도
    # =========================================================================

    def check_phonetic_similarity(self, entry: DrugEntry) -> Tuple[bool, List[str]]:
        """
        음차/철자 유사도 검사

        Args:
            entry: 약제 항목

        Returns:
            (pass, reason_codes)
        """
        reasons = []

        en = entry.en.lower()
        ko = entry.ko

        # 한글 → 로마자 변환 (간단한 음차)
        ko_romanized = self._romanize_korean(ko)

        # 편집 거리 계산
        similarity = SequenceMatcher(None, en, ko_romanized).ratio()

        # 임계값 선택 (고빈도 vs 희귀)
        threshold = (
            self.filters['phonetic_threshold']['strict']
            if entry.count >= self.filters['high_frequency_threshold']
            else self.filters['phonetic_threshold']['loose']
        )

        # 유사도가 임계값보다 낮으면 보류
        if 1 - similarity > threshold:  # distance = 1 - similarity
            reasons.append("PHONETIC_FAIL")
            return False, reasons

        return True, reasons

    def _romanize_korean(self, text: str) -> str:
        """
        한글 → 로마자 변환 (간단한 음차)

        Args:
            text: 한글 텍스트

        Returns:
            로마자 텍스트
        """
        # 간단한 자모 분해 및 로마자 변환
        # 실제로는 jamo, romanize 라이브러리 사용 권장
        # 여기서는 단순화된 버전

        # 초성, 중성, 종성 유니코드 오프셋
        CHOSUNG_BASE = 0x1100
        JUNGSUNG_BASE = 0x1161
        JONGSUNG_BASE = 0x11A8
        HANGUL_BASE = 0xAC00

        CHOSUNG_LIST = ['g', 'kk', 'n', 'd', 'tt', 'r', 'm', 'b', 'pp', 's', 'ss', '', 'j', 'jj', 'ch', 'k', 't', 'p', 'h']
        JUNGSUNG_LIST = ['a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye', 'o', 'wa', 'wae', 'oe', 'yo', 'u', 'weo', 'we', 'wi', 'yu', 'eu', 'ui', 'i']
        JONGSUNG_LIST = ['', 'g', 'kk', 'gs', 'n', 'nj', 'nh', 'd', 'l', 'lg', 'lm', 'lb', 'ls', 'lt', 'lp', 'lh', 'm', 'b', 'bs', 's', 'ss', 'ng', 'j', 'ch', 'k', 't', 'p', 'h']

        result = []
        for char in text:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:  # 한글 음절
                code -= HANGUL_BASE
                cho = code // (21 * 28)
                jung = (code % (21 * 28)) // 28
                jong = code % 28

                result.append(CHOSUNG_LIST[cho])
                result.append(JUNGSUNG_LIST[jung])
                if jong != 0:
                    result.append(JONGSUNG_LIST[jong])
            else:
                result.append(char)

        return ''.join(result)

    def is_curated_pair(self, entry: DrugEntry) -> bool:
        """
        큐레이션 화이트리스트에 있는 쌍인지 확인

        Args:
            entry: 약제 항목

        Returns:
            큐레이션 여부
        """
        pair_key = (entry.en.lower(), entry.ko)
        return pair_key in self.curated_pairs

    # =========================================================================
    # 5. 게이트 4 - ATC/계열 교차검증 (선택)
    # =========================================================================

    def check_atc_consistency(self, entry: DrugEntry) -> Tuple[bool, List[str]]:
        """
        ATC 계열 교차검증 (현재는 스킵)

        Args:
            entry: 약제 항목

        Returns:
            (pass, reason_codes)
        """
        # ATC 데이터가 없으므로 스킵
        return True, []

    # =========================================================================
    # 6. 게이트 5 - 레짐/바이오마커/질환축 분리
    # =========================================================================

    def check_routing(self, entry: DrugEntry) -> Tuple[bool, List[str], Optional[str]]:
        """
        레짐/바이오마커/질환축 분리

        Args:
            entry: 약제 항목

        Returns:
            (is_routed, reason_codes, route_target)
        """
        reasons = []

        en = entry.en.upper()
        ko = entry.ko

        # 레짐 패턴 확인
        for pattern in self.filters['patterns']['regimen']:
            if re.search(pattern, en) or re.search(pattern, ko):
                reasons.append("ROUTE_REGIMEN")
                return True, reasons, "regimen"

        # 바이오마커 패턴 확인
        for pattern in self.filters['patterns']['biomarker']:
            if re.search(pattern, en, re.IGNORECASE) or re.search(pattern, ko):
                reasons.append("ROUTE_BIOMARKER")
                return True, reasons, "biomarker"

        # 질환 패턴 확인
        for pattern in self.filters['patterns']['disease']:
            if re.search(pattern, en, re.IGNORECASE) or re.search(pattern, ko):
                reasons.append("ROUTE_DISEASE")
                return True, reasons, "disease"

        return False, reasons, None

    # =========================================================================
    # 7. 게이트 6 - 충돌 해소
    # =========================================================================

    def check_conflicts(self, entry: DrugEntry) -> Tuple[bool, List[str]]:
        """
        충돌 해소 (동일 ko ↔ 상이 en)

        Args:
            entry: 약제 항목

        Returns:
            (pass, reason_codes)
        """
        reasons = []

        ko = entry.ko
        en = entry.en

        # 현재 ko에 대한 en 목록 확인
        if ko in self.ko_to_en_map:
            existing_ens = self.ko_to_en_map[ko]
            if en not in existing_ens:
                # 충돌 발생
                reasons.append("ALIAS_CONFLICT")
                self.logger.warning(f"Conflict detected: {ko} ↔ {existing_ens} vs {en}")
                return False, reasons

        # 충돌 없으면 등록
        self.ko_to_en_map[ko].append(en)

        return True, reasons

    # =========================================================================
    # 8. 게이트 체인 실행
    # =========================================================================

    def apply_gate_chain(self, entry: DrugEntry) -> DrugEntry:
        """
        게이트 체인 적용

        Args:
            entry: 약제 항목

        Returns:
            처리된 약제 항목
        """
        all_reasons = []

        # 최우선: 큐레이션 화이트리스트 체크 (모든 게이트 우회)
        if self.is_curated_pair(entry):
            self.logger.info(f"Curated pair - bypassing all gates: {entry.en} → {entry.ko}")
            entry.decision = "active"
            entry.reason_codes = ["PASS_ALL", "CURATED_WHITELIST"]
            return entry

        # 전처리: 브랜드명 해소
        entry = self.resolve_brand_name(entry)

        # 게이트 1: 금칙어 필터
        pass_gate1, reasons1 = self.check_forbidden_forms(entry)
        all_reasons.extend(reasons1)
        if not pass_gate1:
            entry.decision = "drop"
            entry.reason_codes = all_reasons
            return entry

        # 게이트 2: 라우팅 (레짐/바이오마커/질환은 조기 분류)
        is_routed, reasons2, route_target = self.check_routing(entry)
        all_reasons.extend(reasons2)
        if is_routed:
            entry.decision = f"route_{route_target}"
            entry.reason_codes = all_reasons
            return entry

        # 게이트 3: 접미사 정합성
        pass_gate3, reasons3, strict_suffix_matched = self.check_suffix_consistency(entry)
        all_reasons.extend(reasons3)
        if not pass_gate3:
            entry.decision = "pending"
            entry.reason_codes = all_reasons
            return entry

        # 게이트 4: 음차/철자 유사도
        # strict suffix가 매칭된 경우, 음차 검사 스킵
        if strict_suffix_matched:
            phonetic_passed = True
        else:
            pass_gate4, reasons4 = self.check_phonetic_similarity(entry)
            all_reasons.extend(reasons4)
            if not pass_gate4:
                phonetic_passed = False
                # 컨텍스트 승격 로직: 음차 실패 + 컨텍스트 시그널
                if self.has_context_signal(entry):
                    self.logger.info(f"Context promotion: {entry.en} → {entry.ko}")
                    all_reasons.append("CTX_PROMOTE")
                    phonetic_passed = True  # 승격
                else:
                    entry.decision = "pending"
                    entry.reason_codes = all_reasons
                    return entry

        # 게이트 5: ATC 교차검증 (스킵)
        pass_gate5, reasons5 = self.check_atc_consistency(entry)
        all_reasons.extend(reasons5)
        if not pass_gate5:
            entry.decision = "pending"
            entry.reason_codes = all_reasons
            return entry

        # 게이트 6: 충돌 해소
        pass_gate6, reasons6 = self.check_conflicts(entry)
        all_reasons.extend(reasons6)
        if not pass_gate6:
            entry.decision = "pending"
            entry.reason_codes = all_reasons
            return entry

        # 모든 게이트 통과
        entry.decision = "active"
        entry.reason_codes = ["PASS_ALL"] + all_reasons

        return entry

    # =========================================================================
    # 9. 처리 파이프라인
    # =========================================================================

    def load_input(self, input_path: str, dry_run_limit: Optional[int] = None) -> List[DrugEntry]:
        """
        입력 파일 로드 (JSON 또는 CSV)

        Args:
            input_path: 입력 파일 경로
            dry_run_limit: 드라이런 시 처리할 항목 수

        Returns:
            약제 항목 리스트
        """
        import csv

        entries = []
        input_file = Path(input_path)

        if input_file.suffix == '.csv':
            # CSV 로드: context에서 괄호쌍을 추출하여 en-ko 매핑 생성
            pair_pattern = r'([가-힣][가-힣\s]+)\s*\(([A-Za-z][A-Za-z\s\-]+)\)|([A-Za-z][A-Za-z\s\-]+)\s*\(([가-힣][가-힣\s]+)\)'

            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                seen_pairs = set()  # 중복 제거

                for row in reader:
                    surface = row.get('surface', '')
                    lang = row.get('lang', '')
                    context = row.get('context', '')

                    # context에서 괄호쌍 찾기
                    for match in re.finditer(pair_pattern, context):
                        if match.group(1) and match.group(2):
                            ko = match.group(1).strip()
                            en = match.group(2).strip()
                        elif match.group(3) and match.group(4):
                            en = match.group(3).strip()
                            ko = match.group(4).strip()
                        else:
                            continue

                        # 중복 제거
                        pair_key = (en.lower(), ko)
                        if pair_key in seen_pairs:
                            continue
                        seen_pairs.add(pair_key)

                        # 정규화
                        en_norm = self.normalize_case(self.normalize_text(en), 'en')
                        ko_norm = self.normalize_case(self.normalize_text(ko), 'ko')

                        entry = DrugEntry(
                            en=en_norm,
                            ko=ko_norm,
                            count=1,
                            source=row.get('src', 'csv'),
                            context_span=context[:200]  # 컨텍스트 200자로 제한
                        )
                        entries.append(entry)

        else:
            # JSON 로드
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)

            # matched_via_english 섹션 처리
            if 'matched_via_english' in data:
                for item in data['matched_via_english']:
                    entry = DrugEntry(
                        en=self.normalize_case(self.normalize_text(item.get('english', '')), 'en'),
                        ko=self.normalize_case(self.normalize_text(item.get('korean', '')), 'ko'),
                        count=item.get('count', 0),
                        source='matched_via_english'
                    )
                    entries.append(entry)

        # 드라이런 제한
        if dry_run_limit:
            entries = entries[:dry_run_limit]

        self.stats.total_input = len(entries)
        self.logger.info(f"Loaded {len(entries)} entries")

        return entries

    def _build_curated_pairs_set(self) -> None:
        """큐레이션 화이트리스트 세트 구축 (정규화 적용)"""
        self.curated_pairs = set()
        for pair in self.curated_pairs_raw:
            en_norm = self.normalize_case(self.normalize_text(pair['en']), 'en')
            ko_norm = self.normalize_case(self.normalize_text(pair['ko']), 'ko')
            self.curated_pairs.add((en_norm, ko_norm))
        self.logger.info(f"Built {len(self.curated_pairs)} normalized curated pairs")

    def process_all(self, entries: List[DrugEntry]) -> None:
        """
        모든 항목 처리

        Args:
            entries: 약제 항목 리스트
        """
        # 큐레이션 화이트리스트 세트 구축 (정규화 적용)
        self._build_curated_pairs_set()

        progress_interval = self.filters['execution']['progress_interval']

        for idx, entry in enumerate(entries, 1):
            # 게이트 체인 적용
            processed = self.apply_gate_chain(entry)

            # 결과 분류
            if processed.decision == "active":
                self.active_drugs.append(processed)
                self.stats.active += 1
            elif processed.decision == "pending":
                self.pending_drugs.append(processed)
                self.stats.pending += 1
            elif processed.decision == "drop":
                self.dropped_drugs.append(processed)
                self.stats.dropped += 1
            elif processed.decision.startswith("route_"):
                route_target = processed.decision.split('_')[1]
                if route_target == "regimen":
                    self.regimens.append(processed)
                    self.stats.routed_regimen += 1
                elif route_target == "biomarker":
                    self.biomarkers.append(processed)
                    self.stats.routed_biomarker += 1
                elif route_target == "disease":
                    self.diseases.append(processed)
                    self.stats.routed_disease += 1

            # reason_codes 통계
            for code in processed.reason_codes:
                self.stats.reason_code_counts[code] += 1

            # 진행 상황 로그
            if idx % progress_interval == 0:
                self.logger.info(f"Processed {idx}/{len(entries)} entries")

        self.logger.info(f"Processing complete: {len(entries)} entries")

    # =========================================================================
    # 10. 출력
    # =========================================================================

    def save_yaml(self, entries: List[DrugEntry], output_path: str, section: str = "active") -> None:
        """
        YAML 파일 저장

        Args:
            entries: 약제 항목 리스트
            output_path: 출력 파일 경로
            section: 섹션명 (active, pending 등)
        """
        output_data = {
            section: [
                {
                    'canonical_en': entry.en,
                    'canonical_ko': entry.ko,
                    'aliases': entry.aliases,
                    'reason_codes': entry.reason_codes,
                    'count': entry.count,
                    'source': entry.source
                }
                for entry in entries
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(output_data, f, allow_unicode=True, sort_keys=False)

        self.logger.info(f"Saved {len(entries)} entries to {output_path}")

    def save_jsonl_log(self, log_path: str) -> None:
        """
        JSONL 로그 저장

        Args:
            log_path: 로그 파일 경로
        """
        all_entries = (
            self.active_drugs + self.pending_drugs + self.dropped_drugs +
            self.regimens + self.biomarkers + self.diseases
        )

        with open(log_path, 'w', encoding='utf-8') as f:
            for entry in all_entries:
                log_entry = {
                    'en': entry.en,
                    'ko': entry.ko,
                    'decision': entry.decision,
                    'reason_codes': entry.reason_codes,
                    'count': entry.count,
                    'source': entry.source
                }
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        self.logger.info(f"Saved log to {log_path}")

    def generate_report(self, report_path: str) -> None:
        """
        Markdown 리포트 생성

        Args:
            report_path: 리포트 파일 경로
        """
        lines = []

        lines.append("# 게이트 체인 약제 매칭 정제 리포트\n")
        lines.append(f"**생성일**: {Path().cwd()}\n")
        lines.append("---\n\n")

        # 통계 요약
        lines.append("## 📊 통계 요약\n")
        lines.append(f"- **총 입력**: {self.stats.total_input}건\n")
        lines.append(f"- **결정 (active)**: {self.stats.active}건 ({self.stats.active/self.stats.total_input*100:.1f}%)\n")
        lines.append(f"- **보류 (pending)**: {self.stats.pending}건 ({self.stats.pending/self.stats.total_input*100:.1f}%)\n")
        lines.append(f"- **제외 (dropped)**: {self.stats.dropped}건 ({self.stats.dropped/self.stats.total_input*100:.1f}%)\n")
        lines.append(f"- **라우팅**: {self.stats.routed_regimen + self.stats.routed_biomarker + self.stats.routed_disease}건\n")
        lines.append(f"  - 레짐: {self.stats.routed_regimen}건\n")
        lines.append(f"  - 바이오마커: {self.stats.routed_biomarker}건\n")
        lines.append(f"  - 질환: {self.stats.routed_disease}건\n\n")

        # Reason codes Top 10
        lines.append("## 🏆 Reason Codes Top 10\n")
        for code, count in self.stats.reason_code_counts.most_common(10):
            lines.append(f"- **{code}**: {count}건\n")
        lines.append("\n")

        # 샘플 케이스
        lines.append("## 📋 샘플 케이스\n")

        # 제외 예시
        lines.append("### 제외 (Dropped)\n")
        for entry in self.dropped_drugs[:3]:
            lines.append(f"- `{entry.en} → {entry.ko}` ({', '.join(entry.reason_codes)})\n")
        lines.append("\n")

        # 보류 예시
        lines.append("### 보류 (Pending)\n")
        for entry in self.pending_drugs[:3]:
            lines.append(f"- `{entry.en} → {entry.ko}` ({', '.join(entry.reason_codes)})\n")
        lines.append("\n")

        # 활성 예시
        lines.append("### 활성 (Active)\n")
        for entry in self.active_drugs[:5]:
            lines.append(f"- `{entry.en} → {entry.ko}` (count: {entry.count})\n")
        lines.append("\n")

        # 수락 기준 검증
        lines.append("## ✅ 수락 기준 검증\n")

        # 제형/포장어 확인
        forms_in_active = []
        hard_forms = self.filters['forbidden_forms']['hard']
        for entry in self.active_drugs:
            if entry.ko in hard_forms:
                forms_in_active.append(entry)

        if forms_in_active:
            lines.append(f"- ❌ **제형/포장어 발견**: {len(forms_in_active)}건\n")
            for entry in forms_in_active:
                lines.append(f"  - `{entry.en} → {entry.ko}`\n")
        else:
            lines.append("- ✅ **제형/포장어 0건** (통과)\n")

        # 테스트 케이스 검증
        lines.append("\n### 테스트 케이스 검증\n")
        test_cases = self.filters['acceptance_criteria']['test_cases']

        for tc in test_cases:
            en_test = tc['input']['en']
            ko_test = tc['input']['ko']
            expected = tc['expected']

            # 해당 항목 찾기
            found = None
            for entry in (self.active_drugs + self.pending_drugs + self.dropped_drugs +
                         self.regimens + self.biomarkers + self.diseases):
                if entry.en == en_test and entry.ko == ko_test:
                    found = entry
                    break

            if found:
                actual = found.decision
                if (expected == "active" and actual == "active") or \
                   (expected == "pending" and actual == "pending") or \
                   (expected == "drop" and actual == "drop"):
                    lines.append(f"- ✅ `{en_test} → {ko_test}`: {expected} (통과)\n")
                else:
                    lines.append(f"- ❌ `{en_test} → {ko_test}`: 예상 {expected}, 실제 {actual} (실패)\n")
            else:
                lines.append(f"- ⚠️ `{en_test} → {ko_test}`: 항목 없음\n")

        # 파일 저장
        with open(report_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        self.logger.info(f"Report generated: {report_path}")

# =============================================================================
# 메인 함수
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='게이트 체인 기반 약제 매칭 정제')
    parser.add_argument('--input', required=True, help='입력 JSON 파일')
    parser.add_argument('--filters', required=True, help='filters.yaml 파일')
    parser.add_argument('--brand-alias', help='brand_alias.yaml 파일 (선택)')
    parser.add_argument('--curated-pairs', help='큐레이션 화이트리스트 JSON 파일 (선택)')
    parser.add_argument('--out-drug', required=True, help='출력 drug.yaml 파일')
    parser.add_argument('--log', required=True, help='로그 JSONL 파일')
    parser.add_argument('--report', required=True, help='리포트 MD 파일')
    parser.add_argument('--dry-run', action='store_true', help='드라이런 모드 (200건만 처리)')

    args = parser.parse_args()

    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 정제기 초기화
    refiner = DrugAnchorRefiner(args.filters, args.brand_alias, args.curated_pairs)

    # 입력 로드
    dry_run_limit = 200 if args.dry_run else None
    entries = refiner.load_input(args.input, dry_run_limit)

    # 처리
    refiner.process_all(entries)

    # 출력
    # drug.yaml (active + pending)
    output_data = {
        'active': [
            {
                'canonical_en': entry.en,
                'canonical_ko': entry.ko,
                'aliases': entry.aliases,
                'reason_codes': entry.reason_codes,
                'count': entry.count
            }
            for entry in refiner.active_drugs
        ],
        'pending': [
            {
                'canonical_en': entry.en,
                'canonical_ko': entry.ko,
                'aliases': entry.aliases,
                'reason_codes': entry.reason_codes,
                'count': entry.count
            }
            for entry in refiner.pending_drugs
        ]
    }

    with open(args.out_drug, 'w', encoding='utf-8') as f:
        yaml.dump(output_data, f, allow_unicode=True, sort_keys=False)

    # 라우팅 파일들
    if refiner.regimens:
        refiner.save_yaml(refiner.regimens, 'dictionary/anchor/regimen.yaml', 'regimen')
    if refiner.biomarkers:
        refiner.save_yaml(refiner.biomarkers, 'dictionary/anchor/biomarker.yaml', 'biomarker')
    if refiner.diseases:
        refiner.save_yaml(refiner.diseases, 'dictionary/anchor/disease_alias.yaml', 'disease')

    # JSONL 로그
    refiner.save_jsonl_log(args.log)

    # 리포트
    refiner.generate_report(args.report)

    print(f"\n[SUCCESS] Processing complete!")
    print(f"   - Active: {refiner.stats.active}")
    print(f"   - Pending: {refiner.stats.pending}")
    print(f"   - Dropped: {refiner.stats.dropped}")
    print(f"   - Routed: {refiner.stats.routed_regimen + refiner.stats.routed_biomarker + refiner.stats.routed_disease}")

if __name__ == '__main__':
    main()
