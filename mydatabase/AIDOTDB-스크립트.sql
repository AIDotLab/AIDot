USE AIDOTDB;

/*
DELETE FROM aidot_ana_analysis where cod_no in ('1000000005', '1000000009');

INSERT INTO aidot_ana_analysis values ('1000000001', 'c33e8032-e11f-11ee-8c68-b11980472f07', '강아지 YOLOv8 기본 모델', 'YOLOv8 기본 모델을 사용해서 강아지를 탐지합니다.', '1000000008', '1000000006', '1000000005', '2024-03-04 13:10:15', '2024-03-04 13:10:16', 'dog.jpg', 'dog.jpg', 'demo/dog.jpg', 'https://aidot2024.s3.ap-northeast-2.amazonaws.com/demo/dog.jpg', 'demo/dog-a.jpg', 'https://aidot2024.s3.ap-northeast-2.amazonaws.com/demo/dog-a.jpg', 'Y', 'Y', '1', 'Y');
DELETE FROM aidot_ana_analysis where ana_analysis_no in ('1000000005', '1000000006');
*/
update aidot_ana_analysis
   set ana_use_flag = 'Y'
 where ana_analysis_no = '1000000005'
;

update aidot_com_aiserver 
   set ais_status_code = 'PAUSE'
 where ais_no in ('1000000001', '1000000002');
;

SELECT * FROM aidot_com_code;
SELECT * FROM aidot_com_aiserver;
SELECT * FROM aidot_ana_analysis;
SELECT * FROM aidot_ana_analysis_v;

---------------------------------------
-- 신규 분석No 조회
SELECT IFNULL(MAX(ana_analysis_no), 1000000000) + 1 AS NEWNO
  FROM aidot_ana_analysis
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
