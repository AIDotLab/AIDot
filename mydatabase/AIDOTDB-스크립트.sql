USE AIDOTDB;

/*
DELETE FROM aidot_com_code where cod_no in ('1000000008', '1000000009');
DELETE FROM aidot_ana_analysis where ana_analysis_no in ('1000000006', '1000000007');

update aidot_ana_analysis
   set ana_aiserver_code = '1000000006'
 where ana_analysis_no = '1000000005'
;
*/

SELECT * FROM aidot_com_code;
SELECT * FROM aidot_ana_analysis;
SELECT * FROM aidot_ana_analysis_v;

---------------------------------------
-- 신규 분석No 조회
SELECT IFNULL(MAX(ana_analysis_no), 1000000000) + 1 AS NEWNO
  FROM aidot_ana_analysis
;

---------------------------------------
-- AI 서버 업데이트
-- 1000000006	AIServer	AI101
-- 1000000007	AIServer	AI102
update aidot_ana_analysis
   set ana_aiserver_code = '1000000006'
 where ana_analysis_no = '1000000005'
;

-- 처리상태 완료로 업데이트
update aidot_ana_analysis
   set ana_status_code = '1000000005'
     , ana_complete_date = SYSDATE()
	 , ana_ana_s3_path
	 , ana_ana_s3_url
 where ana_analysis_no = '1000000005'
;

-- 이미지 AI 분석 재수행
update aidot_ana_analysis
   set ana_aiserver_code = ''
     , ana_status_code = '1000000004'
     , ana_complete_date = ''
	 , ana_ana_s3_path = ''
	 , ana_ana_s3_url = ''
 where ana_analysis_no = '1000000005'
;

-- 이미지 AI 분석 삭제
update aidot_ana_analysis
   set ana_use_flag = 'N'
 where ana_analysis_no = '1000000005'
;
