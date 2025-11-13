// ============================================================
// 법령 조문 Neo4j 샘플 쿼리
// ============================================================

// 1. 특정 법령의 모든 조(depth=0) 조회
// ------------------------------------------------------------
MATCH (l:Law {law_name: '의료급여법'})-[:HAS_ARTICLE]->(a:Article)
WHERE a.depth = 0
RETURN a.article_number, a.article_title,
       substring(a.full_text, 0, 100) + '...' AS preview
ORDER BY a.article_number_normalized
LIMIT 10;

// 2. 조문의 전체 계층 구조 (제3조의 모든 항/호/목)
// ------------------------------------------------------------
MATCH path = (a:Article {
    law_name: '의료급여법',
    article_number: '제3조',
    depth: 0
})-[:HAS_CHILD*]->(child)
RETURN path
LIMIT 50;

// 3. 특정 조문을 참조하는 모든 조문 찾기
// ------------------------------------------------------------
MATCH (source:Article)-[r:REFERS_TO]->(target:Article {
    law_name: '의료급여법',
    article_number: '제11조'
})
RETURN
    source.article_number,
    source.article_title,
    r.reference_type,
    r.reference_text,
    substring(r.context, 0, 50) + '...' AS context
LIMIT 20;

// 4. 준용 관계 분석
// ------------------------------------------------------------
MATCH (source:Article)-[r:REFERS_TO {reference_type: '준용'}]->(target:Article)
RETURN
    source.law_name,
    source.article_number,
    source.article_title,
    target.article_number,
    target.article_title,
    r.reference_text
LIMIT 10;

// 5. 법령 계층 구조 (시행령 → 법률)
// ------------------------------------------------------------
MATCH (child:Law)-[r:DERIVED_FROM]->(parent:Law)
RETURN
    child.law_name,
    r.relationship_type,
    parent.law_name
ORDER BY parent.law_name, r.relationship_type;

// 6. 가장 많이 참조되는 조문 TOP 10
// ------------------------------------------------------------
MATCH (target:Article)<-[r:REFERS_TO]-(source:Article)
WITH target, count(r) AS reference_count
RETURN
    target.law_name,
    target.article_number,
    target.article_title,
    reference_count
ORDER BY reference_count DESC
LIMIT 10;

// 7. 위임 관계가 있는 조문 (상세 정보)
// ------------------------------------------------------------
MATCH (source:Article)-[r:REFERS_TO {reference_type: '위임'}]->(target:Article)
RETURN
    source.law_name,
    source.article_number + ' ' + source.article_title AS source_article,
    r.reference_text,
    target.article_number + ' ' + target.article_title AS target_article,
    substring(source.full_text, 0, 100) + '...' AS source_text
LIMIT 10;

// 8. 특정 법령의 조문 구조 통계
// ------------------------------------------------------------
MATCH (l:Law {law_name: '의료급여법'})-[:HAS_ARTICLE]->(a:Article)
WITH a.depth AS depth, count(a) AS article_count
RETURN
    CASE depth
        WHEN 0 THEN '조'
        WHEN 1 THEN '항'
        WHEN 2 THEN '호'
        WHEN 3 THEN '목'
    END AS level,
    article_count
ORDER BY depth;

// 9. 참조 유형별 통계
// ------------------------------------------------------------
MATCH ()-[r:REFERS_TO]->()
RETURN
    r.reference_type AS reference_type,
    count(r) AS count
ORDER BY count DESC;

// 10. 복잡한 참조 체인 (3단계 이상 참조)
// ------------------------------------------------------------
MATCH path = (a1:Article)-[:REFERS_TO*2..3]->(a2:Article)
WHERE a1.law_name = '의료급여법'
RETURN
    a1.article_number AS start,
    [node IN nodes(path) | node.article_number] AS reference_chain,
    a2.article_number AS end
LIMIT 10;

// 11. 법령별 참조 네트워크 밀도
// ------------------------------------------------------------
MATCH (l:Law)-[:HAS_ARTICLE]->(a:Article)
WITH l, count(a) AS total_articles
MATCH (a1:Article {law_id: l.law_id})-[r:REFERS_TO]->(a2:Article {law_id: l.law_id})
WITH l, total_articles, count(r) AS total_references
RETURN
    l.law_name,
    total_articles,
    total_references,
    round(total_references * 1.0 / total_articles, 2) AS avg_references_per_article
ORDER BY avg_references_per_article DESC;

// 12. RAG용: 특정 키워드가 포함된 조문 검색
// ------------------------------------------------------------
MATCH (a:Article)
WHERE a.full_text CONTAINS '의료급여' AND a.full_text CONTAINS '수급권자'
RETURN
    a.law_name,
    a.article_number,
    a.article_title,
    substring(a.full_text, 0, 150) + '...' AS text_preview
LIMIT 10;

// 13. 조문 참조 그래프 시각화 (제11조 중심)
// ------------------------------------------------------------
MATCH path = (a1:Article)-[:REFERS_TO*..2]-(a2:Article)
WHERE a1.article_number = '제11조' AND a1.law_name = '의료급여법'
RETURN path
LIMIT 50;

// 14. 법령 계층별 조문 수
// ------------------------------------------------------------
MATCH (l:Law)-[:HAS_ARTICLE]->(a:Article)
WITH l, a.depth AS depth, count(a) AS count
RETURN
    l.law_name,
    l.law_type,
    collect({depth: depth, count: count}) AS structure
ORDER BY l.law_type, l.law_name;

// 15. 개정 근거 추적 (예외 조항 찾기)
// ------------------------------------------------------------
MATCH (source:Article)-[r:REFERS_TO {reference_type: '예외'}]->(target:Article)
RETURN
    source.law_name,
    source.article_number + ' ' + source.article_title AS exception_article,
    target.article_number + ' ' + target.article_title AS base_article,
    r.context
LIMIT 10;
