# 외부접근 허용
create user 'aidotuser'@'%' identified by 'aidot2024';

# database
create database AIDOTDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

grant all privileges on AIDOTDB.* to 'aidotuser'@'%';

---------------------------------------
USE AIDOTDB;

DROP TABLE aidot_com_code;

CREATE TABLE aidot_com_code (
  cod_no INT NOT NULL,
  cod_set VARCHAR(100) NOT NULL,
  cod_key VARCHAR(100) NOT NULL,
  cod_name VARCHAR(300),
  cod_comment VARCHAR(1000),
  cod_order INT,
  cod_use_flag VARCHAR(10),
  CONSTRAINT aidot_com_code_PK PRIMARY KEY(cod_no)
);

SELECT * FROM aidot_com_code;

---------------------------------------
USE AIDOTDB;

DROP TABLE aidot_ana_analysis;

CREATE TABLE aidot_ana_analysis (
  ana_analysis_no INT NOT NULL,
  ana_analysis_id VARCHAR(100) NOT NULL,
  ana_title VARCHAR(300) NOT NULL,
  ana_description VARCHAR(1000),
  ana_aimodel_code INT NOT NULL,
  ana_aiserver_code INT NOT NULL,
  ana_status_code INT NOT NULL,
  ana_request_date DATETIME,
  ana_complete_date DATETIME,
  ana_org_fil_name VARCHAR(100),
  ana_org_mod_name VARCHAR(100),
  ana_org_s3_path VARCHAR(100),
  ana_org_s3_url VARCHAR(300),
  ana_ana_s3_path VARCHAR(100),
  ana_ana_s3_url VARCHAR(300),
  ana_public_flag VARCHAR(10),
  ana_main_flag VARCHAR(10),
  ana_main_order INT,
  ana_use_flag VARCHAR(10),
  CONSTRAINT aidot_ana_analysis_PK PRIMARY KEY(ana_analysis_no)
);

SELECT * FROM aidot_ana_analysis;

---------------------------------------
USE AIDOTDB;

DROP VIEW aidot_ana_analysis_v;

CREATE VIEW aidot_ana_analysis_v
AS
SELECT A.ana_analysis_no
     , A.ana_analysis_id
     , A.ana_title
     , A.ana_description
     , A.ana_aimodel_code
     , B.cod_key AS ana_ai_key
     , B.cod_name AS ana_ai_name
     , B.cod_comment AS ana_ai_comment
     , A.ana_aiserver_code
     , C.cod_key AS ana_aiserver_key
     , C.cod_name AS ana_aiserver_name
     , C.cod_comment AS ana_aiserver_comment
     , A.ana_status_code
     , D.cod_key AS ana_status_key
     , D.cod_name AS ana_status_name
     , D.cod_comment AS ana_status_comment
     , A.ana_request_date
     , A.ana_complete_date
     , A.ana_org_fil_name
     , A.ana_org_mod_name
     , A.ana_org_s3_path
     , A.ana_org_s3_url
     , A.ana_ana_s3_path
     , A.ana_ana_s3_url
     , A.ana_public_flag
     , A.ana_main_flag
     , A.ana_main_order
     , A.ana_use_flag
  FROM aidot_ana_analysis A
 INNER JOIN aidot_com_code B
    ON B.cod_set = 'AIModel'
   AND A.ana_aimodel_code = B.cod_no
 INNER JOIN aidot_com_code C
    ON C.cod_set = 'AIServer'
   AND A.ana_aiserver_code = C.cod_no
 INNER JOIN aidot_com_code D
    ON D.cod_set = 'AnalysisStatus'
   AND A.ana_status_code = D.cod_no
;
