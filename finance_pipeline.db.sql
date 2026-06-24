BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS accounts (
	id INTEGER NOT NULL, 
	account_number VARCHAR(64) NOT NULL, 
	client_id INTEGER NOT NULL, 
	account_type VARCHAR(10), 
	currency VARCHAR(8), 
	is_active BOOLEAN, 
	opened_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (account_number), 
	FOREIGN KEY(client_id) REFERENCES clients (id)
);
CREATE TABLE IF NOT EXISTS client_theme_matches (
	id INTEGER NOT NULL, 
	client_id INTEGER NOT NULL, 
	theme_id INTEGER NOT NULL, 
	matched_at DATETIME, 
	matched_sectors TEXT, 
	exposure_value FLOAT, 
	exposure_pct FLOAT, 
	sentiment VARCHAR(8), 
	confidence FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_client_theme UNIQUE (client_id, theme_id), 
	FOREIGN KEY(client_id) REFERENCES clients (id), 
	FOREIGN KEY(theme_id) REFERENCES themes (id)
);
CREATE TABLE IF NOT EXISTS clients (
	id INTEGER NOT NULL, 
	client_code VARCHAR(32) NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	email VARCHAR(256), 
	phone VARCHAR(32), 
	risk_profile VARCHAR(32), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (client_code)
);
CREATE TABLE IF NOT EXISTS holdings (
	id INTEGER NOT NULL, 
	portfolio_id INTEGER NOT NULL, 
	security_id INTEGER NOT NULL, 
	quantity FLOAT NOT NULL, 
	avg_cost FLOAT, 
	current_value FLOAT, 
	weight_pct FLOAT, 
	as_of_date DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_portfolio_security UNIQUE (portfolio_id, security_id), 
	FOREIGN KEY(portfolio_id) REFERENCES portfolios (id), 
	FOREIGN KEY(security_id) REFERENCES securities (id)
);
CREATE TABLE IF NOT EXISTS market_event_trends (
	id INTEGER NOT NULL, 
	market_event_id INTEGER NOT NULL, 
	trend_id INTEGER NOT NULL, 
	relevance_score FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_event_trend UNIQUE (market_event_id, trend_id), 
	FOREIGN KEY(market_event_id) REFERENCES market_events (id), 
	FOREIGN KEY(trend_id) REFERENCES trends (id)
);
CREATE TABLE IF NOT EXISTS market_events (
	id INTEGER NOT NULL, 
	article_id INTEGER NOT NULL, 
	event_text TEXT NOT NULL, 
	event_type VARCHAR(64), 
	entities TEXT, 
	extracted_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(article_id) REFERENCES news_articles (id)
);
CREATE TABLE IF NOT EXISTS news_articles (
	id INTEGER NOT NULL, 
	guid VARCHAR(512) NOT NULL, 
	source_name VARCHAR(128), 
	title VARCHAR(512) NOT NULL, 
	summary TEXT, 
	full_text TEXT, 
	url VARCHAR(1024), 
	published_at DATETIME, 
	ingested_at DATETIME, 
	raw_file_path VARCHAR(512), 
	is_processed BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (guid)
);
CREATE TABLE IF NOT EXISTS portfolios (
	id INTEGER NOT NULL, 
	portfolio_code VARCHAR(64) NOT NULL, 
	account_id INTEGER NOT NULL, 
	name VARCHAR(256), 
	strategy VARCHAR(128), 
	inception_date DATETIME, 
	total_value FLOAT, 
	last_valued_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (portfolio_code), 
	FOREIGN KEY(account_id) REFERENCES accounts (id)
);
CREATE TABLE IF NOT EXISTS sector_master (
	id INTEGER NOT NULL, 
	name VARCHAR(128) NOT NULL, 
	gics_code VARCHAR(16), 
	description TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE IF NOT EXISTS sector_tags (
	id INTEGER NOT NULL, 
	theme_id INTEGER NOT NULL, 
	sector_name VARCHAR(128) NOT NULL, 
	sentiment VARCHAR(8) NOT NULL, 
	confidence FLOAT, 
	rationale TEXT, 
	tagged_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(theme_id) REFERENCES themes (id)
);
CREATE TABLE IF NOT EXISTS securities (
	id INTEGER NOT NULL, 
	ticker VARCHAR(16) NOT NULL, 
	name VARCHAR(256), 
	isin VARCHAR(12), 
	security_type VARCHAR(32), 
	exchange VARCHAR(32), 
	sector_id INTEGER, 
	currency VARCHAR(8), 
	last_price FLOAT, 
	last_price_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (ticker), 
	FOREIGN KEY(sector_id) REFERENCES sector_master (id)
);
CREATE TABLE IF NOT EXISTS themes (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	description TEXT, 
	created_at DATETIME, 
	last_updated DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE IF NOT EXISTS trend_themes (
	id INTEGER NOT NULL, 
	trend_id INTEGER NOT NULL, 
	theme_id INTEGER NOT NULL, 
	weight FLOAT, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_trend_theme UNIQUE (trend_id, theme_id), 
	FOREIGN KEY(trend_id) REFERENCES trends (id), 
	FOREIGN KEY(theme_id) REFERENCES themes (id)
);
CREATE TABLE IF NOT EXISTS trends (
	id INTEGER NOT NULL, 
	name VARCHAR(256) NOT NULL, 
	description TEXT, 
	direction VARCHAR(8), 
	first_seen_at DATETIME, 
	last_updated DATETIME, 
	PRIMARY KEY (id)
);
INSERT INTO "accounts" ("id","account_number","client_id","account_type","currency","is_active","opened_at") VALUES (1,'ACC-C001-001',1,'INDIVIDUAL','USD',1,'2026-06-07 13:49:25.599273'),
 (2,'ACC-C002-001',2,'INDIVIDUAL','USD',1,'2026-06-11 21:10:18.016388'),
 (3,'ACC-C003-001',3,'INDIVIDUAL','USD',1,'2026-06-11 21:10:18.067909'),
 (4,'ACC-C004-001',4,'INDIVIDUAL','USD',1,'2026-06-11 21:10:18.104902'),
 (5,'ACC-C005-001',5,'INDIVIDUAL','USD',1,'2026-06-11 21:10:18.132896');
INSERT INTO "client_theme_matches" ("id","client_id","theme_id","matched_at","matched_sectors","exposure_value","exposure_pct","sentiment","confidence") VALUES (1,1,3,'2026-06-11 21:12:15.767712','["Semiconductors", "Technology"]',312600.0,62.52,'POSITIVE',0.85),
 (2,1,1,'2026-06-11 21:12:15.770712','["Technology"]',84000.0,16.8,'POSITIVE',0.9),
 (3,1,6,'2026-06-11 21:12:15.772232','["Technology"]',84000.0,16.8,'POSITIVE',0.85),
 (4,1,7,'2026-06-11 21:12:15.774255','["Technology"]',84000.0,16.8,'MIXED',0.6),
 (5,2,4,'2026-06-11 21:12:15.835291','["Financials"]',15600.0,33.9869281045752,'POSITIVE',0.9),
 (6,2,5,'2026-06-11 21:12:15.839243','["Energy"]',13800.0,30.0653594771242,'POSITIVE',0.7),
 (7,3,1,'2026-06-11 21:12:15.878860','["Technology"]',15300.0,48.4177215189873,'POSITIVE',0.9),
 (8,3,3,'2026-06-11 21:12:15.879861','["Technology"]',15300.0,48.4177215189873,'POSITIVE',0.85),
 (9,3,6,'2026-06-11 21:12:15.880862','["Technology"]',15300.0,48.4177215189873,'POSITIVE',0.85),
 (10,3,7,'2026-06-11 21:12:15.882867','["Technology"]',15300.0,48.4177215189873,'MIXED',0.6),
 (11,3,4,'2026-06-11 21:12:15.885863','["Financials"]',11700.0,37.0253164556962,'POSITIVE',0.9),
 (12,3,5,'2026-06-11 21:12:15.890861','["Energy"]',4600.0,14.5569620253165,'POSITIVE',0.7),
 (13,4,3,'2026-06-11 21:12:15.920899','["Semiconductors", "Technology"]',619300.0,100.0,'POSITIVE',0.85),
 (14,4,1,'2026-06-11 21:12:15.922864','["Technology"]',104500.0,16.8738898756661,'POSITIVE',0.9),
 (15,4,6,'2026-06-11 21:12:15.924860','["Technology"]',104500.0,16.8738898756661,'POSITIVE',0.85),
 (16,4,7,'2026-06-11 21:12:15.926866','["Technology"]',104500.0,16.8738898756661,'MIXED',0.6),
 (17,5,1,'2026-06-11 21:12:15.959923','["Technology"]',34400.0,41.8746195982958,'POSITIVE',0.9),
 (18,5,3,'2026-06-11 21:12:15.961923','["Technology"]',34400.0,41.8746195982958,'POSITIVE',0.85),
 (19,5,6,'2026-06-11 21:12:15.962921','["Technology"]',34400.0,41.8746195982958,'POSITIVE',0.85),
 (20,5,7,'2026-06-11 21:12:15.963932','["Technology"]',34400.0,41.8746195982958,'MIXED',0.6),
 (21,1,11,'2026-06-11 21:12:15.785271','["Technology"]',84000.0,16.8,'MIXED',0.75),
 (22,2,9,'2026-06-11 21:12:15.846276','["Financials"]',15600.0,33.9869281045752,'MIXED',0.6),
 (23,2,8,'2026-06-11 21:12:15.846276','["Energy"]',13800.0,30.0653594771242,'POSITIVE',0.9),
 (24,3,11,'2026-06-11 21:12:15.896859','["Technology"]',15300.0,48.4177215189873,'MIXED',0.75),
 (25,3,9,'2026-06-11 21:12:15.896859','["Financials"]',11700.0,37.0253164556962,'MIXED',0.6),
 (26,3,8,'2026-06-11 21:12:15.896859','["Energy"]',4600.0,14.5569620253165,'POSITIVE',0.9),
 (27,4,11,'2026-06-11 21:12:15.932876','["Technology"]',104500.0,16.8738898756661,'MIXED',0.75),
 (28,5,11,'2026-06-11 21:12:15.969901','["Technology"]',34400.0,41.8746195982958,'MIXED',0.75);
INSERT INTO "clients" ("id","client_code","name","email","phone","risk_profile","created_at") VALUES (1,'C001','Arjun Mehta','arjun.mehta@example.com','+91-98200-00001','Aggressive','2026-06-07 13:49:25.596273'),
 (2,'C002','Priya Sharma','c002@demo.com',NULL,'Conservative','2026-06-11 21:10:18.008696'),
 (3,'C003','Rahul Gupta','c003@demo.com',NULL,'Moderate','2026-06-11 21:10:18.061940'),
 (4,'C004','Neha Joshi','c004@demo.com',NULL,'Aggressive','2026-06-11 21:10:18.097897'),
 (5,'C005','Vikram Patel','c005@demo.com',NULL,'Conservative','2026-06-11 21:10:18.126898');
INSERT INTO "holdings" ("id","portfolio_id","security_id","quantity","avg_cost","current_value","weight_pct","as_of_date") VALUES (1,1,1,200.0,85.0,180000.0,36.0,'2026-06-07 13:49:25.609287'),
 (2,1,2,150.0,310.0,64500.0,12.9,'2026-06-07 13:49:25.609287'),
 (3,1,3,100.0,170.0,19500.0,3.9,'2026-06-07 13:49:25.609287'),
 (4,1,10,300.0,95.0,48600.0,9.72,'2026-06-07 13:49:25.609287'),
 (5,1,9,50.0,200.0,5750.0,1.15,'2026-06-07 13:49:25.609287'),
 (6,2,8,100.0,155.0,16500.0,35.9477124183007,'2026-06-11 21:10:18.043406'),
 (7,2,6,80.0,140.0,15600.0,33.9869281045752,'2026-06-11 21:10:18.043406'),
 (8,2,7,120.0,55.0,13800.0,30.0653594771242,'2026-06-11 21:10:18.043406'),
 (9,3,3,50.0,170.0,9750.0,30.8544303797468,'2026-06-11 21:10:18.081939'),
 (10,3,6,60.0,140.0,11700.0,37.0253164556962,'2026-06-11 21:10:18.081939'),
 (11,3,4,30.0,130.0,5550.0,17.5632911392405,'2026-06-11 21:10:18.081939'),
 (12,3,7,40.0,55.0,4600.0,14.5569620253165,'2026-06-11 21:10:18.081939'),
 (13,4,1,500.0,85.0,450000.0,72.6626836751171,'2026-06-11 21:10:18.113901'),
 (14,4,10,400.0,95.0,64800.0,10.4634264492169,'2026-06-11 21:10:18.113901'),
 (15,4,2,200.0,310.0,86000.0,13.8866462134668,'2026-06-11 21:10:18.113901'),
 (16,4,4,100.0,130.0,18500.0,2.98724366219926,'2026-06-11 21:10:18.113901'),
 (17,5,9,200.0,200.0,23000.0,27.9975654290931,'2026-06-11 21:10:18.143935'),
 (18,5,8,150.0,155.0,24750.0,30.1278149726111,'2026-06-11 21:10:18.143935'),
 (19,5,2,80.0,310.0,34400.0,41.8746195982958,'2026-06-11 21:10:18.143935');
INSERT INTO "market_event_trends" ("id","market_event_id","trend_id","relevance_score") VALUES (1,2,1,0.8),
 (2,3,1,0.9),
 (3,4,1,0.7),
 (4,5,1,0.8),
 (5,23,1,0.6),
 (6,6,2,0.9),
 (7,7,2,0.7),
 (8,15,2,0.6),
 (9,17,2,0.7),
 (10,18,2,0.8),
 (11,19,2,0.8),
 (12,20,2,0.9),
 (13,8,3,0.8),
 (14,9,3,0.7),
 (15,10,3,0.9),
 (16,11,4,0.7),
 (17,13,4,0.6),
 (18,14,4,0.5),
 (19,21,4,0.8),
 (20,22,4,0.7),
 (21,24,4,0.8),
 (22,25,4,0.9),
 (23,26,5,1.0),
 (24,27,5,0.8),
 (25,28,5,0.9),
 (26,30,6,0.9),
 (27,31,6,0.8),
 (28,32,6,0.7),
 (29,33,6,0.9),
 (30,34,6,0.8),
 (31,35,7,0.8),
 (32,36,7,0.9),
 (33,37,7,1.0),
 (34,38,7,0.85),
 (35,39,7,0.8),
 (36,42,8,0.7),
 (37,43,8,0.6),
 (38,41,8,0.6),
 (39,45,9,0.8),
 (40,46,9,0.7),
 (41,47,9,0.85),
 (42,48,9,0.9),
 (43,44,10,1.0),
 (44,49,11,0.7),
 (45,50,11,0.6),
 (46,51,12,0.8),
 (47,52,12,0.7),
 (48,72,12,0.8),
 (49,73,12,0.9),
 (50,89,12,0.9),
 (51,53,13,0.9),
 (52,54,13,0.8),
 (53,55,13,0.7),
 (54,56,13,0.9),
 (55,66,14,0.9),
 (56,67,14,0.9),
 (57,68,14,0.8),
 (58,69,14,0.7),
 (59,70,14,0.8),
 (60,71,14,0.6),
 (61,73,15,0.8),
 (62,77,15,0.7),
 (63,78,15,0.9),
 (64,85,15,0.8),
 (65,63,16,0.8),
 (66,64,16,0.6),
 (67,65,16,0.7),
 (68,84,16,0.9),
 (69,89,16,0.9),
 (70,57,17,0.9),
 (71,58,17,0.6),
 (72,59,17,0.7),
 (73,60,17,0.8),
 (74,61,17,0.7),
 (75,62,17,0.6);
INSERT INTO "market_events" ("id","article_id","event_text","event_type","entities","extracted_at") VALUES (1,24,'Nvidia''s market capitalization fell below $5 trillion after a recent pullback.','OTHER','["Nvidia"]','2026-06-08 04:54:27.335063'),
 (2,24,'Alphabet''s stock recently pulled back, causing its market capitalization to fall to $4.45 trillion.','OTHER','["Alphabet"]','2026-06-08 04:54:27.335063'),
 (3,24,'Alphabet''s first-quarter Google Cloud revenue grew 63% year over year to $20 billion.','EARNINGS','["Alphabet"]','2026-06-08 04:54:27.335063'),
 (4,24,'Alphabet''s order backlog nearly doubled in three months to more than $460 billion.','OTHER','["Alphabet"]','2026-06-08 04:54:27.335063'),
 (5,24,'Google search and other advertising revenue grew 19%.','EARNINGS','["Alphabet"]','2026-06-08 04:54:27.335063'),
 (6,25,'GitLab announced a major restructuring plan, cutting about 14% of its workforce, roughly 350 roles, to tighten costs and focus on profitability.','OTHER','["GitLab", "GTLB"]','2026-06-08 04:54:29.396999'),
 (7,25,'GitLab shares fell nearly 15% after announcing the restructuring plan.','OTHER','["GitLab", "GTLB"]','2026-06-08 04:54:29.396999'),
 (8,26,'The Coca-Cola Company is exploring a potential public listing in India of Hindustan Coca-Cola Holdings Pvt. Ltd. in 2027.','REGULATORY','["The Coca-Cola Company", "Hindustan Coca-Cola Holdings Pvt. Ltd."]','2026-06-08 04:54:31.557301'),
 (9,26,'The Coca-Cola Company is assessing the sale of a portion of its shareholding in Hindustan Coca-Cola Holdings Pvt. Ltd. in relation to the listing.','M_AND_A','["The Coca-Cola Company", "Hindustan Coca-Cola Holdings Pvt. Ltd."]','2026-06-08 04:54:31.557301'),
 (10,26,'In July 2025, The Coca-Cola Company wrapped up a transaction that saw Jubilant Bhartia Group acquiring 40% stake in Hindustan Coca-Cola Holdings Pvt. Ltd.','M_AND_A','["The Coca-Cola Company", "Jubilant Bhartia Group", "Hindustan Coca-Cola Holdings Pvt. Ltd."]','2026-06-08 04:54:31.557301'),
 (11,27,'Simeon Gutman from Morgan Stanley reiterated a ''Buy'' rating on Costco with a price objective of $1,130.00.','OTHER','["Costco Wholesale Corporation", "COST", "Morgan Stanley"]','2026-06-08 04:54:33.021320'),
 (12,27,'Costco reported Q3 net sales rose 11.6% to $69.15 billion from $61.96 billion in the last year.','EARNINGS','["Costco Wholesale Corporation", "COST"]','2026-06-08 04:54:33.021320'),
 (13,28,'UBS analyst Steven Fisher lifted Caterpillar''s stock price objective to $900 from $677.','OTHER','["Caterpillar Inc.", "UBS"]','2026-06-08 04:54:34.610319'),
 (14,28,'UBS maintains a ''Neutral'' rating on Caterpillar shares.','OTHER','["Caterpillar Inc.", "UBS"]','2026-06-08 04:54:34.610319'),
 (15,29,'Circle went public in June 2025 at $31 a share.','OTHER','["Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (16,29,'Circle stock reached a closing high of $263.45 on June 23, 2025.','OTHER','["Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (17,29,'Cathie Wood''s ARK funds first bought Circle shares in Q2 2025.','OTHER','["ARK", "Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (18,29,'Cathie Wood''s ARK funds added 42,500 shares of Circle in Q3 2025.','OTHER','["ARK", "Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (19,29,'Cathie Wood''s ARK funds added 1.17 million shares of Circle in Q4 2025.','OTHER','["ARK", "Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (20,29,'Cathie Wood''s ARK funds added another 368,000 shares of Circle in Q1 2026.','OTHER','["ARK", "Circle Internet Group"]','2026-06-08 04:54:36.918939'),
 (21,30,'Wells Fargo lifted its price objective on Intel''s stock to $110 from $85 and maintained an ''Equal Weight'' rating.','OTHER','["INTC", "Wells Fargo"]','2026-06-08 04:54:38.131118'),
 (22,30,'Mizuho lifted its price objective on Intel''s stock to $128 from $124 and kept a ''Neutral'' rating.','OTHER','["INTC", "Mizuho"]','2026-06-08 04:54:38.131118'),
 (23,31,'Piper Sandler analyst Thomas Champion lifted its price objective on Alphabet''s stock to $445 from $425 and kept an ''Overweight'' rating on the shares.','OTHER','["Alphabet Inc.", "GOOGL"]','2026-06-08 04:54:39.175497'),
 (24,32,'TD Cowen lifted its price target on AMD stock to $600 from $500 and maintained a ''Buy'' rating.','OTHER','["Advanced Micro Devices", "NASADAQ:AMD"]','2026-06-08 04:54:40.650670'),
 (25,33,'Morgan Stanley analyst Erik Woodring reiterated an ''Overweight'' rating for Apple with a price objective of $330.','OTHER','["AAPL", "Apple Inc.", "Morgan Stanley"]','2026-06-08 04:54:41.618908'),
 (26,34,'Kalshi''s crypto perpetual futures crossed $1 billion in trading volume within a week of their launch.','PRODUCT','["Kalshi"]','2026-06-11 07:01:24.479134'),
 (27,34,'The Commodity Futures Trading Commission issued an order approving KalshiEX''s BTCPERP contract on May 29.','REGULATORY','["Commodity Futures Trading Commission", "Kalshi"]','2026-06-11 07:01:24.479134'),
 (28,34,'Kalshi aims to launch crypto perpetuals on more than a dozen currencies, pending additional regulatory reviews.','PRODUCT','["Kalshi"]','2026-06-11 07:01:24.479134'),
 (29,34,'Kalshi raised a $1 billion Series F at a $22 billion valuation last month.','OTHER','["Kalshi"]','2026-06-11 07:01:24.479134'),
 (30,37,'RBC Capital analyst Deane Dray raised Honeywell''s price target to $275 from $268.','OTHER','["Honeywell International Inc."]','2026-06-11 07:01:29.613516'),
 (31,37,'Barclays raised its price target on Honeywell to $251 from $243.','OTHER','["Honeywell International Inc."]','2026-06-11 07:01:29.613516'),
 (32,37,'Barclays reiterated an Overweight rating for Honeywell.','OTHER','["Honeywell International Inc."]','2026-06-11 07:01:29.613516'),
 (33,37,'Honeywell''s management is likely to outline a mid-single-digit organic growth framework and a margin expansion story.','OTHER','["Honeywell International Inc."]','2026-06-11 07:01:29.613516'),
 (34,37,'Barclays points to upcoming catalysts including two capital markets days and planned corporate spinoffs for Honeywell.','OTHER','["Honeywell International Inc."]','2026-06-11 07:01:29.613516'),
 (35,38,'IBM''s software revenue hit $7.05 billion in Q1 2026, up 11%.','EARNINGS','["IBM"]','2026-06-11 07:01:32.538184'),
 (36,38,'IBM mainframe revenue surged 51% as enterprises modernized mission-critical workloads.','EARNINGS','["IBM"]','2026-06-11 07:01:32.538184'),
 (37,38,'IBM raised its dividend for the 31st straight year.','EARNINGS','["IBM"]','2026-06-11 07:01:32.538184'),
 (38,38,'IBM''s FY2025 free cash flow was $14.73 billion, a 25% growth.','EARNINGS','["IBM"]','2026-06-11 07:01:32.538184'),
 (39,38,'IBM declared its 31st consecutive annual dividend increase on April 22, 2026.','EARNINGS','["IBM"]','2026-06-11 07:01:32.538184'),
 (40,39,'AECOM secured the top ranking on Defence Construction Canada''s National Architecture & Engineering Source List for a multi-year program valued up to C$270 million.','REGULATORY','["AECOM"]','2026-06-11 07:01:34.863329'),
 (41,39,'Barclays lowered its price target on AECOM to $90 from $110 while maintaining an Equal Weight rating following the company''s fiscal second-quarter results.','EARNINGS','["AECOM", "Barclays"]','2026-06-11 07:01:34.863329'),
 (42,40,'Citi raised its price target on Autodesk, Inc. (NASDAQ:ADSK) to $252 from $246 while maintaining a Neutral rating.','OTHER','["Autodesk, Inc.", "Citi"]','2026-06-11 07:01:37.012557'),
 (43,40,'RBC Capital lowered its price target on Autodesk, Inc. (NASDAQ:ADSK) to $305 from $335 but maintained an Outperform rating.','OTHER','["Autodesk, Inc.", "RBC Capital"]','2026-06-11 07:01:37.012557'),
 (44,40,'Autodesk''s $3.6 billion acquisition of MaintainX, its largest transaction in history.','M_AND_A','["Autodesk, Inc.", "MaintainX"]','2026-06-11 07:01:37.012557'),
 (45,41,'Emerson Electric Co. announced a collaboration with Saudi Arabian Oil Company, Aramco, to co-develop advanced corrosion management solutions.','M_AND_A','["EMR", "Aramco"]','2026-06-11 07:01:39.511561'),
 (46,41,'On May 6, Barclays raised its price target on Emerson Electric Co. to $144 from $140 while maintaining an Equal Weight rating.','OTHER','["EMR", "Barclays"]','2026-06-11 07:01:39.511561'),
 (47,41,'RBC Capital increased its price target for Emerson Electric Co. to $169 from $161 and reiterated an Outperform rating after the company’s second-quarter results.','EARNINGS','["EMR", "RBC Capital"]','2026-06-11 07:01:39.511561'),
 (48,41,'RBC noted that proactive cost management initiatives enabled Emerson to raise the lower end of its fiscal 2026 earnings-per-share guidance.','EARNINGS','["EMR", "RBC Capital"]','2026-06-11 07:01:39.511561'),
 (49,42,'JPMorgan raised its price target on Deere & Company (NYSE:DE) to $590 from $560.','OTHER','["Deere & Company", "JPMorgan"]','2026-06-11 07:01:42.562609'),
 (50,42,'Oppenheimer analyst Kristen Owen lowered the firm’s price target on Deere & Company (NYSE:DE) to $680 from $715.','OTHER','["Deere & Company", "Oppenheimer"]','2026-06-11 07:01:42.563603'),
 (51,43,'The price of Brent oil decreased by $0.79 to $94.27 per barrel from the previous day.','MACRO','["Brent"]','2026-06-11 21:11:32.387892'),
 (52,43,'Brent oil price is roughly $27 higher than it was at the same time last year.','MACRO','["Brent"]','2026-06-11 21:11:32.387892'),
 (53,44,'Oracle is expected to increase its capital spending to a range of $80 billion to $100 billion in the upcoming quarterly report.','EARNINGS','["Oracle", "ORCL"]','2026-06-11 21:11:34.697633'),
 (54,44,'Oracle is working on a project called Project Stargate to build AI infrastructure with OpenAI and SoftBank.','PRODUCT','["Oracle", "OpenAI", "SoftBank"]','2026-06-11 21:11:34.697633'),
 (55,44,'Oracle announces a $20 billion at-the-market (ATM) equity issuance.','OTHER','["Oracle", "ORCL"]','2026-06-11 21:11:34.697633'),
 (56,44,'Oracle is reportedly laying off as many as 30,000 employees.','SUPPLY_CHAIN','["Oracle", "ORCL"]','2026-06-11 21:11:34.697633'),
 (57,45,'Oklo announced the acquisition of ARMEC, a precision manufacturing firm focused on high-tolerance nuclear components.','M_AND_A','["Oklo", "ARMEC"]','2026-06-11 21:11:37.255926'),
 (58,45,'Oklo secured a long-term power deal with Meta Platforms, boosting its stock.','OTHER','["Oklo", "Meta Platforms"]','2026-06-11 21:11:37.255926'),
 (59,45,'Oklo closed its acquisition of ARMEC on June 4, 2026.','M_AND_A','["Oklo", "ARMEC"]','2026-06-11 21:11:37.255926'),
 (60,45,'Oklo stock rose 3.96% on the day of the ARMEC acquisition announcement.','OTHER','["Oklo"]','2026-06-11 21:11:37.255926'),
 (61,45,'Brookfield Asset Management teamed up with The Nuclear Company to roll out Westinghouse AP1000 and AP300 reactors.','M_AND_A','["Brookfield Asset Management", "The Nuclear Company"]','2026-06-11 21:11:37.255926'),
 (62,45,'Blue Energy works with GE Vernova on a hybrid gas and nuclear design.','SUPPLY_CHAIN','["Blue Energy", "GE Vernova"]','2026-06-11 21:11:37.255926'),
 (63,46,'Cisco Systems Inc stock is up 61% since the start of the year.','OTHER','["Cisco Systems Inc", "CSCO"]','2026-06-11 21:11:39.713855'),
 (64,46,'Cisco has raised its payouts for more than a decade, with investors getting $1.68 per share per year.','OTHER','["Cisco Systems Inc", "CSCO"]','2026-06-11 21:11:39.713855'),
 (65,46,'A consensus among 25 analysts rates Cisco stock as a ''Moderate Buy'', with high target prices suggesting as much as ~20.8% upside over the next year.','OTHER','["Cisco Systems Inc", "CSCO"]','2026-06-11 21:11:39.713855'),
 (66,47,'More than 50% of Bitcoin''s circulating supply is now trading below the price it was purchased at.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (67,47,'Bitcoin price fell 28% from a high of around $82,000 to below $60,000 in recent weeks.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (68,47,'Bitcoin''s price decline pushed more than 10 million Bitcoin below its purchase price.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (69,47,'In May of this year, about 30% of Bitcoin''s supply was underwater.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (70,47,'Bitcoin''s latest selloff brought its price back to the 200-week moving average.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (71,47,'Bitcoin price reached an all-time high of $126,000 in October of last year.','MACRO','["CRYPTO: $BTC"]','2026-06-11 21:11:44.014823'),
 (72,49,'Consumer prices shot up 4.2% in May from the previous year, the hottest annual reading since April 2023.','MACRO','["Bureau of Labor Statistics"]','2026-06-11 21:11:46.266717'),
 (73,49,'Inflation climbed as higher energy prices tied to the Iran conflict continued to pressure the U.S. economy.','GEOPOLITICAL','["Iran", "U.S. economy"]','2026-06-11 21:11:46.266717'),
 (74,50,'Bosch is on track to meet its financial targets in 2026 despite challenges.','EARNINGS','["Robert Bosch GmbH"]','2026-06-11 21:11:48.109574'),
 (75,50,'Bosch plans 22,000 job cuts in its core automotive business.','SUPPLY_CHAIN','["Robert Bosch GmbH"]','2026-06-11 21:11:48.109574'),
 (76,50,'Bosch expects a profit margin this year in the range of 4 to 6% and revenue growth of 2 to 5%.','EARNINGS','["Robert Bosch GmbH"]','2026-06-11 21:11:48.109574'),
 (77,50,'Potential supply chain shocks from the Middle East conflict could impact Bosch.','GEOPOLITICAL','["Robert Bosch GmbH"]','2026-06-11 21:11:48.109574'),
 (78,50,'Uncertainty surrounding the war in the Middle East may impact raw material supply for semiconductors, such as helium, affecting Bosch.','SUPPLY_CHAIN','["Robert Bosch GmbH"]','2026-06-11 21:11:48.109574'),
 (79,51,'NDAQ''s adjusted EPS of $0.96 exceeded Wall Street expectations of $0.93 for Q1.','EARNINGS','["NDAQ", "Nasdaq, Inc."]','2026-06-11 21:11:50.877006'),
 (80,51,'NDAQ''s net revenue was $1.41 billion, topping Wall Street forecasts of $1.37 billion for Q1.','EARNINGS','["NDAQ", "Nasdaq, Inc."]','2026-06-11 21:11:50.877006'),
 (81,51,'Shares of NDAQ climbed 2.2% over the past 52 weeks.','OTHER','["NDAQ", "Nasdaq, Inc."]','2026-06-11 21:11:50.877006'),
 (82,51,'NDAQ slipped 14% from its 52-week high of $101.79.','OTHER','["NDAQ", "Nasdaq, Inc."]','2026-06-11 21:11:50.877006'),
 (83,51,'NDAQ shares closed up marginally after reporting its Q1 results on Apr. 23.','EARNINGS','["NDAQ", "Nasdaq, Inc."]','2026-06-11 21:11:50.877006'),
 (84,51,'Intercontinental Exchange, Inc. (ICE) has experienced 12.6% downtick on a YTD basis and 19.6% losses over the past 52 weeks.','OTHER','["ICE", "Intercontinental Exchange, Inc."]','2026-06-11 21:11:50.877006'),
 (85,52,'In early 2026, US equities declined, with the Russell 3000 falling 4% and the S&P posting losses due to the Iran conflict.','GEOPOLITICAL','["Russell 3000", "S&P"]','2026-06-11 21:11:54.358418'),
 (86,52,'Apple Inc. (NASDAQ:AAPL) closed at $290.55 per share on June 9, 2026.','OTHER','["AAPL", "Apple Inc."]','2026-06-11 21:11:54.358418'),
 (87,52,'One-month return of Apple Inc. (NASDAQ:AAPL) was -2.78%, and its shares gained 46.17% over the past 52 weeks.','OTHER','["AAPL", "Apple Inc."]','2026-06-11 21:11:54.358418'),
 (88,52,'Apple Inc. (NASDAQ:AAPL) has a market capitalization of $4.27 trillion.','OTHER','["AAPL", "Apple Inc."]','2026-06-11 21:11:54.358418'),
 (89,52,'Energy sector surged over 35% while Tech sector dropped over 9% in early 2026.','MACRO','[]','2026-06-11 21:11:54.358418'),
 (90,52,'The London Company Income Equity portfolio returned 4.4% this quarter, outperforming the 2.1% rise in the Russell 1000 Value Index.','OTHER','["The London Company Income Equity", "Russell 1000 Value Index"]','2026-06-11 21:11:54.358418'),
 (91,52,'170 hedge fund portfolios held Apple Inc. (NASDAQ:AAPL) at the end of the first quarter of 2026, up from 169 in the previous quarter.','OTHER','["AAPL", "Apple Inc."]','2026-06-11 21:11:54.358418');
INSERT INTO "news_articles" ("id","guid","source_name","title","summary","full_text","url","published_at","ingested_at","raw_file_path","is_processed") VALUES (1,'253e7228d719e6292eb06207832ff7a2b37121f5270590dec596f5f5709b719e','Yahoo Finance','Top Wall Street Strategist: AI ‘Reality Check’ Is Coming as Bond Market Flashes Warning Signs','','Quick Read

QQQ surged 40% and SPY climbed 27% over the past year, but Teeter says AI enthusiasm must now collide with reality.

Teeter warns bonds have been complacent despite Strait of Hormuz disruptions, with rising yields threatening to halt the Fed''s easing path.

IWM''s 19% year-to-date gain signals capital is already rotating from AI mega-caps into small caps, financials, and health care.

Act now: the analyst who called NVIDIA in 2010 just named his top 10 AI stocks — and iShares Russell 2000 ETF didn''t make the cut. Grab the names FREE today.

The market is on its longest winning streak since 1985, AI enthusiasm is running at levels one strategist calls "unbelievable," and the IPO window has cracked open wide. Into that backdrop, Robert Teeter, Chief Investment Strategist at Silvercrest Asset Management, walked onto CNBC on June 5, 2026, with a measured message: a reality check would be the healthiest thing that could happen next.

The AI Enthusiasm and the Question It Raises

Teeter acknowledges the strength of the AI rally. "It''s one of the most fascinating times we''ve had in a while with just absolutely unbelievable enthusiasm around the AI theme and the AI trade," he said. The numbers back the mood. The Invesco QQQ Trust (NASDAQ:QQQ) is up 40.06% over the past year, while the broader SPDR S&P 500 ETF Trust (NYSEARCA:SPY) has climbed 27.04%.

His framing of the next leg is the question every investor should be asking: "The way we map it out over the next few months is how do those expectations collide with reality? Where do we draw the demand from for investors to come in here and boost stocks higher?" After a historic run, the marginal buyer gets harder to find. That is when consolidation in the sector could become the path of least resistance.

The Healthy Rotation Scenario

Teeter''s constructive base case calls for a pause. "We''d expect to see maybe a little bit more of that, some consolidation, a time to digest these big gains, digest the IPOs that are coming up, maybe get some rotation into other areas. That would be the healthiest path forward," he said.

That rotation has already begun. Yesterday''s session saw healthy rotation into health care, financials, and small caps. The iShares Russell 2000 ETF (NYSEARCA:IWM) is up 18.63% year-to-date, a sign that capital is starting to look beyond the AI mega-caps. With a heavy IPO calendar still to absorb, money leaving crowded growth names has somewhere to go.

The Bond Market Is the Real Wild Card

This is where Teeter''s caution sharpens. "I think bonds have actually been reasonably complacent given what''s gone on in the Gulf," he said. "But it seems like the pressure point is building to if we don''t get traffic flowing in the next few weeks, bonds are likely to go through another round of price down yields up, and more expectations for FED potentially having to respond at some point."','https://finance.yahoo.com/markets/stocks/articles/top-wall-street-strategist-ai-115615116.html',NULL,'2026-06-07 13:53:59.143020','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\top_wall_street_strategist_ai_reality_check_is_coming_as_bond_market_flashes_war__253e7228.json',0),
 (2,'a9942e6ecc582301998de6215ecc71e7d0991930919a129436506c575c6caf60','Yahoo Finance','Eli Lilly Leads Medical Stocks To Watch, While Google Finds Support','','No. 1 Rated Drugmaker Lilly Hits Record High, Leads 18 Onto Best Growth Stock Lists

6/05/2026 See which stocks have just been added to – or removed from – IBD''s stock lists, including the IBD 50,...

6/05/2026 See which stocks have just been added to – or...','https://www.investors.com/news/eli-lilly-stocks-to-watch-google/?src=A00220&yptr=yahoo',NULL,'2026-06-07 13:54:01.105887','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\eli_lilly_leads_medical_stocks_to_watch_while_google_finds_support__a9942e6e.json',0),
 (3,'fd97577dbaef8707dd8bce0e3b579ba99b912493717b2bab375bd6654ec3647e','Yahoo Finance','The next NVIDIA? These 3 stocks below $50 are poised to win the next AI boom (and they’re still flying under the radar)','','More recently, Applied Digital said (3) a new 15-year take-or-pay lease brought its total contracted baseline revenue to $31 billion, or $73 billion if all renewal options are exercised. That gives the company a powerful “AI factory” story at a time when hyperscalers are racing to secure more data-center capacity.

Applied Digital also has a direct Nvidia connection. In 2024, the company announced (2) a $160 million private placement involving a group of investors that included Nvidia and Related Companies.

The company designs, builds and operates digital infrastructure for high-performance computing applications — a business that has become increasingly important as AI models demand enormous amounts of computing power and energy.

If Nvidia sells the high-powered engines of the AI race, Applied Digital is trying to build the garages where those engines run.

For investors willing to look beyond the mega-cap names, here are three AI stocks that recently traded below $50 a share — and Wall Street sees big upside in all of them.

The good news? AI is not just about chips. It also requires data centers, voice interfaces, automation tools, defense applications and the digital infrastructure needed to bring the transformative tech into the real world.

But after such a breathtaking run, some investors may be wondering whether the next stage of the AI boom could spread beyond the obvious winner.

Wall Street has rewarded that growth in spectacular fashion. Over the last five years, Nvidia shares have skyrocketed more than 1,100%, turning the company into the most valuable business on Earth, with a market cap of more than $5 trillion.

In its latest quarter, Nvidia reported record revenue of $81.6 billion (1), up 85% from a year earlier, while data-center revenue surged 92% to $75.2 billion.

The IRS usually taxes gold as a collectible — but this little-known strategy lets you hold physical bullion tax-free. Get your free guide from Priority Gold

Dave Ramsey warns nearly 50% of Americans are making 1 big Social Security mistake — here’s how to fix it ASAP

Here’s how to get rich from rising US property values with as little as $100 — and without the stress of angry tenants

The chip giant’s graphics processors are now the beating heart of the AI buildout, powering everything from large language models to cloud data centers. And the numbers have been staggering.

Moneywise and Yahoo Finance LLC may earn commission or revenue through links in the content below.

Story Continues

Applied Digital shares currently trade at $44.70 apiece as of this writing. Craig-Hallum analyst George Sutton has a “Buy” rating on the APLD and recently raised his price target to $75 — about 68% above the current levels (4).

If you’re looking for research on individual stocks, tools like Moby can come in handy. Their team of former hedge fund analysts does the heavy lifting — breaking down the market, flagging quality stocks, and making the research easy to digest.

In fact, across nearly 400 stock picks over the past four years, Moby’s recommendations have beaten the S&P 500 by almost 12% on average. Their research keeps you up-to-the-minute on market shifts, and takes the guesswork out of choosing investments.

Plus, their reports are easy to understand for beginners, so you can become a smarter investor in just five minutes.

Read More: Here’s the average income of Americans by age in 2026. Are you falling behind?

SoundHound AI (NASDAQ:SOUN)

Not every AI winner needs to live inside a data center.

SoundHound AI is focused on voice and conversational artificial intelligence — the kind of technology that can help cars, restaurants, call centers, hotels and other businesses interact with customers through natural language.

That gives SoundHound a simple pitch: As AI moves into everyday life, companies will need software that lets people talk to machines more naturally.

The company has been growing quickly. In the first quarter of 2026, SoundHound reported (5) record revenue of $44.2 million, up 52% from a year earlier. It also reaffirmed its full-year 2026 revenue outlook of $225 million to $260 million.

SoundHound has also been pushing deeper into agentic AI. Its planned acquisition of LivePerson (6) is aimed at combining voice AI with digital messaging, creating an end-to-end omnichannel conversational AI platform for automated customer interactions.

SoundHound shares haven’t been hot commodities lately — they’re down 23% year to date. But Cantor Fitzgerald analyst Thomas Blakey sees a major rebound on the horizon. Blakey has a “Buy” rating on SoundHound and a price target of $15 — 86% above where the stock sits today (7).

BigBear.ai (NYSE:BBAI)

BigBear.ai offers a very different AI angle: national security, defense and critical operations.

The company uses artificial intelligence and data analytics to help organizations make faster decisions in complex environments. That makes it a potential beneficiary as governments and large enterprises look for ways to use AI in defense, logistics, supply chains, border security and other mission-critical areas.

In the first quarter of 2026, BigBear.ai reported (8) revenue of $34.4 million. More importantly for the growth story, the company said backlog increased to $281.9 million, up 14% from the previous quarter. It also highlighted more than $60 million in national-security contracts and reaffirmed its full-year revenue guidance.

Like the other names on this list, BigBear.ai is not without risk. Revenue declined slightly year over year in the latest quarter and the company remains unprofitable. But H.C. Wainwright analyst Scott Buck has a “Buy” rating on BBAI stock and a price target of $6 — implying a potential upside of about 25% (9).

A golden hedge when AI gets frothy

As exciting as the AI boom has been, investors should remember that high-growth stocks can move sharply in both directions.

That is especially true in a market where enthusiasm around AI has helped push valuations to lofty levels. U.S. tech stocks now account for more than 39% of the S&P 500’s market cap — an even higher level of dominance than during the dot-com bubble, according to Reuters (10). Meanwhile, the S&P 500’s Shiller CAPE ratio has recently climbed above 40, a level not seen outside the late 1990s tech mania (11).

That does not mean AI stocks are doomed. But when a narrow group of market leaders drives so much of the action — and valuations are already stretched — investors may want to avoid putting all their eggs in one basket.

That is where gold can come in.

Gold has long been viewed as a go-to safe haven. It can’t be printed out of thin air like fiat money, and because it’s not tied to any single currency or economy, investors often flock to it during periods of economic turmoil, market stress or geopolitical uncertainty, driving up its value.

Ray Dalio, founder of the world’s largest hedge fund, Bridgewater Associates, told CNBC last year that “people don’t have, typically, an adequate amount of gold in their portfolio,” adding that “when bad times come, gold is a very effective diversifier.”

Despite a recent pullback, gold prices have surged by more than 30% over the last 12 months.

One way to invest in gold that can also provide significant tax advantages is to open a gold IRA with the help of Goldco.

Gold IRAs allow investors to hold physical gold or gold-related assets within a retirement account, thereby combining the tax advantages of an IRA with the protective benefits of investing in gold, making it a compelling potential option for those wanting to ensure their retirement funds are diversified during rough economic times.

Goldco offers free shipping and access to a library of retirement resources. Plus, the company will match up to 10% of qualified purchases in free silver.

If you’re curious whether this is the right investment to diversify your portfolio, you can download your free gold and silver information guide today.

You May Also Like

Join 250,000+ readers and get Moneywise’s best stories and exclusive interviews first — clear insights curated and delivered weekly. Subscribe now.

This article was written for informational purposes and is not intended as investment advice. The author does not hold positions in any of the securities mentioned in this article at the time of publication.

Article Sources

We rely only on vetted sources and credible third-party reporting. For details, see our ethics and guidelines.

Nvidia (1); Applied Digital (2), (3); TipRanks (4), (7), (9); SoundHound (5); SoundHound (6); BigBear.ai (8); Reuters (10); Multpl (11)

This article provides information only and should not be construed as advice. It is provided without warranty of any kind.','https://finance.yahoo.com/markets/stocks/articles/next-nvidia-3-stocks-below-120500020.html',NULL,'2026-06-07 13:54:02.547302','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\the_next_nvidia_these_3_stocks_below_50_are_poised_to_win_the_next_ai_boom_and_t__fd97577d.json',0),
 (4,'3facdf03b40299cebfbf3f33698efca3c29e36bfa6fc082172ae8db4b1cd5712','Yahoo Finance','Lawmakers invest in tech, AI, and crypto as new rules for the industries are on their agenda','','As Congress debates new regulations around artificial intelligence and cryptocurrency, lawmakers'' stock portfolios have surged in recent years toward investments in these sectors.

A tracker of the top 50 lawmaker holdings from the financial data platform Unusual Whales shows over $270 million invested directly in top tech stocks, with tens of millions more invested indirectly through market-tracking funds.

It is a level of consolidation that mirrors trends seen in the larger market, with tech far and away the favored sector among lawmakers: 7 of the 8 most popular individual stocks seen in the data are technology companies.

Nvidia (NVDA) is a bipartisan favorite, with about $43 million in lawmakers'' accounts. Other tech giants, including Apple (AAPL), Alphabet (GOOG), and Microsoft (MSFT), also have tens of millions of dollars each in investment.

This represents a significant shift from recent years, when the proportion of tech holdings was much lower and was primarily seen in Democrats'' portfolios.

A view of US Capitol in Washington on June 4. (Kent NISHIMURA / AFP via Getty Images) · KENT NISHIMURA via Getty Images

Cryptocurrency holdings have also grown significantly in recent years, a trend particularly evident among Republicans. Increased investments in bitcoin (BTC-USD) and crypto-adjacent companies reflect heightened interest among Republicans in Trump-friendly areas of the technology sector writ large.

Dan Weiskopf is the co-portfolio manager of two ETFs that mirror Republican and Democratic portfolios. He notes that the Republican side of the aisle as a whole has become markedly more tech-focused and that Bitcoin has been a particular growth area — even requiring a rebalancing of his fund.

"It''s clearly bigger," he said of Republican interest in Bitcoin. "There''s no question about that."

The buying of bigger companies is another trend among lawmakers that has reshaped the fund in recent years.

"I haven''t seen a lot of buying in small caps," he noted.

Issues before Congress in both sectors

The trading trends coincide with ongoing congressional action to regulate both sectors, with cryptocurrency taking center stage this summer.

The crypto industry is pushing a bill that would establish a regulatory framework for digital assets, called the CLARITY Act. It could see a vote later this summer despite colorful opposition from at least some banking leaders.

Congress is also set to debate AI legislation in the coming months, most notably a new bill released this past week that would preempt certain state AI laws and mandate new security risk disclosures for emerging models.

President Trump has waded deep into the tech sector, making millions of dollars worth of trades in "Magnificent Seven" stocks, as well as in companies he has publicly criticized.','https://finance.yahoo.com/sectors/technology/article/lawmakers-invest-in-tech-ai-and-crypto-as-new-rules-for-the-industries-are-on-their-agenda-114556895.html',NULL,'2026-06-07 13:54:04.147134','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\lawmakers_invest_in_tech_ai_and_crypto_as_new_rules_for_the_industries_are_on_th__3facdf03.json',0),
 (5,'05efb2b88f2dd5902a0dbc07f9ae654e3f53e23efe1fae101f08f081319ae624','Yahoo Finance','SpaceX''s IPO dream runs into Wall Street''s oldest test: Chart of the Day','','SpaceX (SPAX.PVT), OpenAI (OPAI.PVT), and Anthropic (ANTH.PVT) have scale and tech appeal. IPO history says those help — but profits are still the cleaner test.

That matters as SpaceX pitches investors on a record $75 billion public offering. The company has rockets, satellites, Starlink, defense demand, and one of the biggest private-market stories on the planet. What it may not have is the one thing Wall Street eventually asks every growth story to show: that the business can make money.

SpaceX''s filing shows the scale, but also the gap. The company generated nearly $19 billion in revenue in 2025 but posted a net loss of nearly $5 billion, according to its IPO paperwork. That gives investors plenty of business to analyze — but not a profitable one yet.

A great company can still be a rough trade on IPO day. After the opening rush, the question shifts from who wants access to what the business can already prove.

That is where the data gets uncomfortable.

Money-losing IPOs jumped more on day one, but profitable IPOs delivered far better three-year returns. · Yahoo Finance analysis of Jay R. Ritter, University of Florida data

According to IPO data from the University of Florida''s Jay Ritter, money-losing companies had the louder opening act, jumping 26.5% on average on their first day. But three years later, their average return was slightly negative. Profitable IPOs did the opposite: fewer first-day fireworks, better staying power.

Read more: SpaceX IPO: How to buy the stock

SpaceX is not a tiny startup, and that matters too. Its IPO filing gave investors a look at a business with real revenue, not just a story stock with a rocket emoji taped to it.

Ritter''s data shows why that helps. IPOs with more than $100 million in pre-debut revenue had smaller opening pops but much stronger returns over the next three years than companies below that line.

IPOs with more revenue had smaller opening pops but stronger returns over the next three years. · Yahoo Finance analysis of Jay R. Ritter, University of Florida data

Tech also helps, which is good news for the whole SpaceX-OpenAI-Anthropic class. But tech is not magic.

That is especially important for the AI names. OpenAI and Anthropic have the kind of growth stories investors want to believe in, but tech labels do not erase the same public-market math: how much revenue is real, how fast losses are narrowing, and whether the IPO price leaves anything for new buyers.

Tech IPOs beat non-tech IPOs after the first close, but the category still needs a real business underneath. · Yahoo Finance analysis of Jay R. Ritter, University of Florida data

The takeaway is simple.

Losses make the IPO pop louder. Sales and tech help. Profits are what matter after the confetti clears.

Jared Blikre is the global markets and data editor for Yahoo Finance. Follow him on X at @SPYJared or email him at jaredblikre@yahooinc.com.

Click here for in-depth analysis of the latest stock market news and events moving stock prices

Read the latest financial and business news from Yahoo Finance','https://finance.yahoo.com/markets/article/spacexs-ipo-dream-runs-into-wall-streets-oldest-test-chart-of-the-day-114542191.html',NULL,'2026-06-07 13:54:05.653374','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\spacexs_ipo_dream_runs_into_wall_streets_oldest_test_chart_of_the_day__05efb2b8.json',0),
 (6,'29702534135f082e1c3b77a9d94cce8245fb1abd3fe26ed5e3bc009eeab96663','Yahoo Finance','Nvidia Wants to Sell AI Factories, Not Chips','','For years, investors viewed Nvidia (NASDAQ: NVDA) as a semiconductor company. The company designed graphics processing units (GPUs), sold them to gamers and data centers, and generated profits from each chip shipped.

That description is becoming increasingly outdated. Today, Nvidia is pursuing a much bigger opportunity. The company no longer wants customers to buy individual chips. Instead, it wants to sell them entire artificial intelligence factories.

Missed Nvidia in 2009? This Rare Signal Is Flashing Again. In 2009, a "Double Down" signal flashed for a little-known chipmaker called Nvidia. For the first time in years, that same "Total Conviction" signal is flashing for a company 1/100th the size of Nvidia. Continue »

This shift may help explain why Nvidia continues to dominate the AI boom and why its long-term opportunity could be larger than many investors realize.

Image source: Getty Images.

From selling components to selling complete systems

Traditionally, technology companies sold individual components. Intel sold CPUs. Cisco sold networking equipment. Nvidia sold GPUs. Customers then assembled those pieces into functioning systems.

But the AI megatrend is changing the formula. Building advanced AI models now requires far more than powerful chips. Companies need to combine networking equipment, software tools, cooling systems, storage infrastructure, and thousands of GPUs into what is essentially one vast machine. That type of coordination is necessary to meet the ever-growing computing power demands of AI applications.

Nvidia recognized this challenge early. Instead of simply selling chips, the company has spent years building a complete ecosystem that includes GPUs, CPUs, networking hardware, software platforms, and integrated systems designed specifically for AI workloads.

As a result, customers are increasingly purchasing entire AI infrastructure solutions rather than individual components. In other words, Nvidia is quietly moving up the value chain.

The rise of the AI factory

Nvidia frequently describes modern AI data centers as "AI factories."

The idea is simple. Traditional factories take raw materials and convert them into physical products. AI factories take data and convert it into intelligence. These facilities train large language models, power AI applications, and generate the outputs that businesses and consumers increasingly rely on.

To build an AI factory, companies need far more than a collection of chips. They need computing systems capable of coordinating thousands of processors, moving enormous amounts of data, and operating efficiently at scale. That plays directly into Nvidia''s strengths.','https://finance.yahoo.com/markets/stocks/articles/nvidia-wants-sell-ai-factories-115700387.html',NULL,'2026-06-07 13:54:07.146716','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\nvidia_wants_to_sell_ai_factories_not_chips__29702534.json',0),
 (7,'933975005b0cae1c414b9e855e0ecaa5b2dd6028a03cfa5e856849c5d53c316c','Yahoo Finance','NYC bar owner used Kalshi to hedge the bar’s bets and provided that extra insurance during the Knicks’ Game 1','','The New York Knicks’ NBA playoff run has fueled a frenzy across the city, sending ticket prices soaring and boosting local business revenue for local businesses. It even prompted one Manhattan bar owner to try something unconventional.

The Jeffrey, a craft beer and cocktail bar on Manhattan’s Upper East Side, recently announced a bold promotion ahead of Game 1 of the NBA Finals. The bar promised that any customer who arrived before tipoff would receive a free tab of up to $100, excluding tax and gratuity if the Knicks won, according to Yahoo. (1)

Must Read

During the Eastern Conference Finals against the Cleveland Cavaliers, owner Andy Freedman offered customers a 1% discount on their tabs for every point the Knicks netted against the spread. When the team won by an unexpectedly large 37 points, the promotion cost the bar roughly $4,000.

He learned from that. Instead of risking another surprise hit, Freedman found a way to offset the loss: He hedged the promotion using a prediction market.

“If the Knicks win, I cover everyone’s tab,” Freedman explained in a video posted to social media before Game 1, adding that Kalshi would pay for his promotion. (2)

The gamble paid off. The Knicks defeated the Spurs 105-95 in Game 1, leaving the bar on the hook for its promotion while giving sports fans another reason to celebrate. And Freedman was covered. If the Knicks had lost, a bar packed wall-to-wall with paying fans would more than make up the difference.

From Wall Street strategy to Main Street businesses

Kalshi is a federally regulated prediction market that allows users to buy and sell contracts tied to real-world events, including elections, economic data releases, weather outcomes and sporting events.

Unlike traditional gambling, the platform positions itself as a financial marketplace where participants can either speculate on outcomes or hedge against risks.

In the Jeffrey’s case, the odds were stacked against New York, with Kalshi giving the Knicks just a 37% chance of winning Game 1. But a $5,000 bet on the underdog would have turned into a $13,514 payout, an $8,514 windfall, enough to cover drinks for the entire bar.

Kalshi representative Jack Such told Fortune that the company approached Freedman after reading about the bar’s earlier promotion. (3)','https://finance.yahoo.com/markets/options/articles/nyc-bar-owner-used-kalshi-114500509.html',NULL,'2026-06-07 13:54:08.614806','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\nyc_bar_owner_used_kalshi_to_hedge_the_bars_bets_and_provided_that_extra_insuran__93397500.json',0),
 (8,'c7ce0a6ef372a37701bdf137627268e5b41203b4d6a3b3f6b69f5c518f8fc11a','Yahoo Finance','Experts say Google''s $84 billion AI gamble could leave investors waiting a decade for a payoff','','“The financing deal shows that both AI technology and AI adoption are still in their infancy, so it will take a lot more cash than the market expected to drive this technology forward,” Galina Fendikevich. the founder of Fendikevich & Company, a consulting and executive AI intelligence firm, told Moneywise. “Alphabet is not going to sit on the sidelines; they’ve historically been drivers of innovation, so the fact that they are still rushing to play catch-up signals their appetite to be strong competitors.”

With investors watching Google cut one of the biggest financing deals in business history, they’re also learning what happens when some of the world’s largest corporations commit tens of billions of dollars to a technology that is still in its early stages.

In a June 2 statement, Alphabet updated and adjusted the pricing of its previously announced registered public offerings of Class A Common Stock, Class C Capital Stock and depositary shares representing interests in mandatory convertible preferred stock. “The gross proceeds of these offerings, together with potential gross proceeds of Alphabet’s previously announced $40 billion at-the-market offering program for the sale of Class A Common Stock and Class C Capital Stock over time, and concurrent $10 billion private placement, represent a total equity raise of $84.75 billion,” the company noted. “The equity capital raise was upsized from the previously announced total equity raise of $80 billion.”

Millionaires under 43 are reshaping investing — just 25% of their portfolios are in stocks. Here’s where their money is going

Prime US real estate was a rich person''s game — then something changed. Now everyday Americans are getting a piece of the action for as little as $100

Robert Kiyosaki says this 1 asset will surge 400% in a year and begs investors not to miss this ‘explosion’

Experts say the Google parent company’s latest funding push underscores just how fiercely Silicon Valley is competing to dominate the next generation of AI-powered products and services, and how much cash they’re willing to lay out for the cause.

Alphabet (NASDAQ: GOOG), owner of all things Google and boasting a $4.33 trillion market cap along with a one-year 111.1% share rate return, is digging deep into its pockets for its massive AI infrastructure efforts. The Mountain View, Calif., technology powerhouse is looking to spend an eye-popping $80 billion on its AI operational needs, a figure that exceeds the annual economic output of countries like Latvia, Cambodia, and Iceland (1).

Story Continues

A ‘growth support’ move by Google

At first glance, Google’s massive AI investment signals internal confidence that artificial intelligence will transform the technology landscape, from internet search and cloud computing to healthcare, finance, and workplace productivity. Yet the $84 billion financing move also raises a big question for consumers and investors alike: Will these enormous bets ultimately generate the profits that justify their cost, or are technology companies entering an expensive arms race where the winners remain far from certain?

“Strong future AI demand is at least 5-10 years away,” Fendikevich noted. “Workforce training, change management, complex integrations all slow the speed of adoption.”

Consequently, companies need major cash infusions to outlast this incredibly slow adoption and buying cycle. “They can’t predict when it will finally break, so I wouldn’t say it’s necessarily a signal of confidence in future AI demand.”

Even more critically, the US energy and infrastructure system is severely lacking to support any strong growth in AI demand. “Most of the cash will most likely go to building energy power plants and data centers,” Fendikevich added. “Then Alphabet will have the ability to build stronger models which will rely on this infrastructure. Either way, they have a reputation, and they are not going to back down from the competition from OpenAI and Anthropic.

Read More: BlackRock warns buying and holding the S&P 500 isn’t enough for retirement anymore — here''s why

A structural shift for Alphabet and for Silicon Valley

Other AI analysts say that the demand for artificial intelligence comes at a time when the technology is increasingly demanding of digital firepower, and that Google is acting accordingly.

“Most of the headlines around AI infrastructure are still about GPUs, but the smart infrastructure people are watching a quieter, more structural shift,” Roger Cummings, CEO of PEAK:AIO, an AI enterprise scaling, security and governance company, told Moneywise. “As AI moves beyond chatbots and toward more agentic systems, the balance of the data center is starting to change.”

It’s doing so quickly, which helps make the case for Google steering more cash into technology development. In a new research note, Dilip Ramachandran (2), senior director of segment marketing, cloud AI business unit at Arm, projects that CPU core demand per gigawatt will quadruple in the agent era, and the chatbot-era ratio of one CPU to four or eight GPUs is collapsing toward one-to-one. “You can see that in the market with Intel and AMD both raising CPU prices last quarter,” Cummings noted.

What gets missed in the headlines and Wall Street noise is that as work spreads across more CPUs and GPUs, every tier is waiting on the same thing: the data feeding it. “Rebalance the compute all you want; if the other layers, particularly storage, can’t feed both systems fast enough, you’ve just created a more expensive version of the same bottleneck,” Cummings said.

What the move means for investors

While Wall Street market mavens gawk at the massive numbers, Main Street investors may wonder if there’s something in the GOOG deal for them. They may not like the answer, at least in the short term.

“Investors can’t expect a return in the mid-term, as AI IS solely a long-term investment, at least 5-10 years,” Fendikevich noted. “Since Alphabet will most likely invest heavily in infrastructure, which is a good backup asset in case the whole LLM thing doesn’t work out for them and those industries will benefit the most, it’s a sound investment no matter where the chips fall down the road.

On the upside, the financing deal could signal yet another shift in the workplace, with demand for AI specialists accelerating every passing year.

“This AI ‘arms race’ just might be the answer to Trump’s call for re-shoring industrials and manufacturing,” Fendikevich said. “The next issue now, though, is that there won’t be enough blue-collar workers to fulfill the demand in materials manufacturing, energy production, and data center construction. Young people want to go into white-collar work or become ‘influencers.’”

Even that otherwise promising scenario has more questions than answers. “So how is Alphabet or the government going to convince them to pick up a hammer instead?” Fendikevich asked.

Shades of the Internet Age

Business gurus say we’re witnessing an AI investment boom similar to past technology buildouts, such as the internet boom of the 1990s and the cloud-computing expansion of the 2010s. The question now: What lessons should investors learn from those periods?

“Yes, and this is crucial: the AI revolution is similar to both of these phenomena but with a much sharper capital burn,” Mark Vena, CEO and principal analyst at SmartTech Research, told Moneywise.

Like the 1990s internet boom, Vena said some spending will look brilliant in hindsight, and some will look reckless, while the 2010s cloud era showed that infrastructure bets can create huge recurring revenue streams. “The lesson for investors is simple: the infrastructure boom creates winners, but not every company writing giant checks earns giant returns,” he noted.

Fendikevich agrees, noting that investors should proceed with caution.

“Yes, this is exactly the same,” she said. “Investors need to keep a cool head and not get swayed by Silicon Valley founders’ grandiose claims of workforce decimation and AGI. They say those things to get investment, and frankly it’s good PR to get AI into the mainstream.”

Yet if investors have learned anything from other technology buildouts, it’s that things are much more complicated than they seem, so AI progress will take time.

“AI is not a rocket ship,” she added. It takes coordination across multiple sectors, including government, energy, manufacturing, software engineering, and enterprises, to get AI off the ground. Rome wasn’t built in a day, and neither will AI.”

You May Also Like

Join 250,000+ readers and get Moneywise’s best stories and exclusive interviews first — clear insights curated and delivered weekly. Subscribe now.

Article Sources

We rely only on vetted sources and credible third-party reporting. For details, see our ethics and guidelines.

Worldometers (1); Arm (2)

This article originally appeared on Moneywise.com under the title: Experts say Google''s $84 billion AI gamble could leave investors waiting a decade for a payoff

This article provides information only and should not be construed as advice. It is provided without warranty of any kind.','https://finance.yahoo.com/sectors/technology/articles/experts-googles-84-billion-ai-124000060.html',NULL,'2026-06-07 13:54:10.295326','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\experts_say_googles_84_billion_ai_gamble_could_leave_investors_waiting_a_decade___c7ce0a6e.json',0),
 (9,'16e92f092b11cd9ec6b967a7de67b7524da11d6cddf7c05d209814b7bab06d8a','Yahoo Finance','''Too big to stop'': Young American men are flocking to prediction markets to take big risks on even bigger rewards','','“Prediction markets are increasingly being framed not simply as gambling, but as a form of intelligence, strategy, forecasting, or participation in internet culture itself,” she told the BBC.

YouTube personality Logan Paul has a partnership with Polymarket and has posted (6) about prediction markets with captions such as “Never heard of this guy but he made me rich.” Elvira Bolat (7), a professor at Bournemouth University, said she is concerned that prediction markets normalize betting and that influencers are downplaying the risks involved.

The risky nature of the platforms tends to draw a predominantly male audience, reflecting the demographics of adjacent communities such as sports betting, cryptocurrency, meme investing, streamer culture and influencer fandom.

Moneywise reached out to George but did not receive a response.

“I haven’t made any money so far. I’m down a couple of grand,” he said.

Cameron George, a 26-year-old content creator and crypto trader, told the BBC (5) he used an AI bot to make bets for him after hearing on social media that it can be an easy way to make money.

The IRS usually taxes gold as a collectible — but this little-known strategy lets you hold physical bullion tax-free. Get your free guide from Priority Gold

Dave Ramsey warns nearly 50% of Americans are making 1 big Social Security mistake — here’s how to fix it ASAP

Here’s how to get rich from rising US property values with as little as $100 — and without the stress of angry tenants

A recent Bloomberg (3) analysis found more than 100,000 accounts lost at least $1,000 on Polymarket, one of the largest prediction market platforms. More important still, the Wall Street Journal (4) reported that 67% of profits on Polymarket go to just 0.1% of accounts. Close to half a billion dollars allegedly went to fewer than 2,000 accounts. What all this means is that most accounts you’ll find on prediction markets are money losers.

Market volumes are estimated to eclipse $1 trillion by 2030 (1), with 71% of prediction market’s current users being men under the age of 45, according to a recent study from analytics firm Morning Consult. In addition, about one in four American men between the ages of 18 and 24 say they have used at least one prediction market or gambling app in the past six months, according to a poll by the American Institute for Boys and Men (2) (AIBM).

Moneywise and Yahoo Finance LLC may earn commission or revenue through links in the content below.

Story Continues

Jonathan Cohen (8), head of sports betting policy at AIBM, described what young men are experiencing as “economic nihilism” — a mindset in which someone with $20,000 may feel they can get rich quickly through speculative markets rather than waiting decades for returns through vehicles such as the S&P 500, he told the BBC.

Read More: Here’s the average income of Americans by age in 2026. Are you falling behind?

The trade-offs

Ben Fielding (9), CEO of AI infrastructure provider Gensyn, told Moneywise that prediction markets give men a place to express their views, with recognition in the form of financial value when they are correct.

“Prediction markets often encourage trading on specific major events in order to drive maximum liquidity for fees,” Fielding told Moneywise. “This one event can then be spread on social media, encouraging more men to make the same trades without necessarily being better-informed — i.e. much closer to gambling than information trading.”

“Information markets, on the other hand, encourage trading on anything by allowing anyone — including those same men — to create their own markets, encouraging them to trade only the things they genuinely care about or have real information about, rather than just buying into the same trades as the influencers they follow in the hopes of getting rich,” he added.

According to Fielding, over time “this open trade of information leads to something a bit like Wikipedia — a huge encyclopedia of live information that is updated by the people with the real information and they make money by doing it.”

Right now, prediction markets are not classified as gambling in the US. If you live in any one of the 50 states, you can place bets. They are regulated as commodity futures trading and platforms earn revenue by charging a small fee on each transaction. But some states are pushing back: Minnesota became the first state to ban prediction markets, according to The New York Times (10).

You May Also Like

Join 250,000+ readers and get Moneywise’s best stories and exclusive interviews first — clear insights curated and delivered weekly. Subscribe now.

Stick to safer bets

While prediction markets have gained a devoted following for their ability to crowdsource forecasts on everything from elections to economic data, they come with a major caveat: Most participants don''t make money.

Roughly 69% of accounts on Polymarket have lost money since 2022. The story isn''t much different on Kalshi, where more than 70% of traders have been unprofitable over the past six months (11).

Prediction markets can be just as unforgiving as any other speculative asset. Market sentiment and unexpected events can quickly turn a seemingly obvious wager into a losing bet. For those looking to build wealth rather than chase outcomes, focusing on relatively low-risk assets might be a better choice.

Opt for precious metals

If your goal is to grow and protect your nest egg, precious metals like gold might be a good option.

Gold has maintained its reputation as a safe-haven asset for generations. When inflation rises, geopolitical tensions flare, or stock markets wobble, investors often flock to the precious metal as a store of value. Because it tends to move independently of stocks and bonds, gold can help smooth out portfolio volatility during turbulent periods.

One way to invest in gold that also provides significant tax advantages is to open a gold IRA with the help of Priority Gold.

You can hold physical gold or gold-related assets within a tax-deferred retirement account through a gold IRA. And if you opt for Priority Gold’s platinum package, you can get free account setup and insured shipping and storage for up to five years. Plus, you can also roll over your existing IRA or 401(k) into a precious metals IRA with Priority Gold — tax and penalty free.

And when you make a qualifying purchase with Priority Gold, you can receive up to $10,000 in precious metals for free. Just keep in mind that gold is often best used as one part of a well-diversified portfolio.

Get into real estate with just $100

Real estate is another classic wealth-building asset. Property values have historically appreciated over time and real estate can generate passive income through rents while providing diversification away from public markets.

The best part? Gaining exposure no longer requires buying an entire property yourself.

Crowdfunding platforms like Arrived allow you to invest in shares of vacation and rental properties across the country with as little as $100.

To get started, simply browse through their selection of vetted properties, each picked for their potential appreciation and income generation.

Arrived distributes any rental income generated by properties to investors monthly, allowing you to potentially set up a passive income stream without the extra work that comes with being a landlord of your own rental property.

The best part? For a limited time, when you open an account and add $1,000 or more, Arrived will credit your account with a 1% match.

Those with more capital on hand can expand their real estate portfolio beyond short-term vacation rentals. Accredited investors can now tap into this opportunity through platforms such as Lightstone DIRECT, which gives accredited investors access to single-asset multifamily and industrial deals.

Lightstone DIRECT’s direct-to-investor model ensures a high degree of alignment between individual investors and a vertically-integrated, institutional owner-operator — a sophisticated and streamlined option for individual investors looking to diversify into private-market real estate.

With Lightstone DIRECT, accredited individuals can access the same multifamily and industrial assets Lightstone pursues with its own capital, with minimum investments starting at $100,000.

A finer alternative

For those willing to think outside the box, fine art has emerged as a surprisingly resilient alternative. The ultra-wealthy have long carved out a slice of their portfolios in an asset class that has low correlation with traditional assets like equities, crypto and gold. Post-war and contemporary art has outperformed the S&P 500 by 15% from 1995 to 2025 while showing near-zero correlation to traditional equities.

Until recently, this world was off-limits for most investors. Now, with Masterworks, you can buy fractional shares in multimillion-dollar works by icons like Banksy, Picasso and Basquiat. While art can be illiquid and typically requires a long-term hold, it offers unique portfolio diversification.

Masterworks has sold 27 artworks so far, yielding net annualized returns like 14.6%, 17.6% and 17.8%.*

Moneywise readers can get priority access to diversify with art: Skip the waitlist here.

*Past performance is not indicative of future returns. Investing involves risk. See important Regulation A disclosures at Masterworks.com/cd

- With files from Amanda Smith.

Article Sources

We rely only on vetted sources and credible third-party reporting. For details, see our ethics and guidelines.

CNBC (1); American Institute of Business Management (2), (8); Bloomberg (3); The Wall Street Journal (4); BBC (5); Instagram (6); Bournemouth University (7); LinkedIn (9); The New York Times (10); CNBC (11)

This article provides information only and should not be construed as advice. It is provided without warranty of any kind.','https://finance.yahoo.com/markets/options/articles/too-big-stop-young-american-111500724.html',NULL,'2026-06-07 13:54:11.936778','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\too_big_to_stop_young_american_men_are_flocking_to_prediction_markets_to_take_bi__16e92f09.json',0),
 (10,'0465d3940d0d828f1fc4ba1b22144817ea75f8dc04555e2b06b8e5fe81372663','Yahoo Finance','I’m 60 and want a long-term care policy before I retire. Is this a good idea, and how can I find the best option?','','Long-term care planning is one of the most important tasks on your to-do list when preparing for retirement. Around 70% of adults (1) who survive until age 65 develop “severe” long-term care needs before they die, and 48% receive at least some paid care over their lifetime according to the Office of the Assistant Secretary for Planning and Evaluation.

Unfortunately, the costs of care can blow through your nest egg, with the annual median cost of an assisted living facility totaling $70,800 per year and the annual median cost of a semi-private room in a nursing home totaling $111,325, according to the Genworth Cost of Care Survey (2).

Must Read

So how exactly should you prepare for long-term care? Let’s pretend that Susan is 60 years old, married, and getting ready to retire soon. She’s considering long-term care coverage but isn’t sure whether it’s a good idea or how to find the best option if it is.

Susan’s husband is older and already retired, the couple has around $600,000 in 401(k) assets, and they have enough money to live reasonably comfortably but not to cover a $111,325 annual bill. So, what should Susan do?

Is buying a long-term care policy before retirement a good idea?

Susan is smart to think about how she’ll cover long-term care costs, because without a plan, she’d probably have to pay out of pocket.

“Many people assume Medicare will cover long-term care expenses, but in reality, Medicare generally only covers short-term skilled nursing or rehabilitation after hospitalization,” Angie Welsh, founder and president of My Annuity Agents (3) in Henderson, NV, told Moneywise.

So does that mean Susan should buy insurance? “Whether buying coverage makes sense usually depends on whether you have sufficient assets to absorb the cost if you do need long-term care,” Welsh said.

With just $600,000 saved, Susan couldn’t cover the costs out of retirement savings without withdrawing too much money too fast and putting her spouse at risk. While her husband could keep a shared home and certain assets, they’d have to spend down most of their wealth on care costs before Medicaid would kick in to pay for a nursing home if Susan needed one.

If Susan wants insurance to avoid this, she should act sooner rather than later. “If you want long-term care insurance, it’s smart to buy it earlier in life so that the costs are absorbed over time,” says Welsh. “Many people wait until they are already retired to consider a long-term care policy. By then, the costs are usually prohibitive.”','https://finance.yahoo.com/sectors/healthcare/articles/m-60-want-long-term-130000089.html',NULL,'2026-06-07 13:54:13.507949','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\im_60_and_want_a_long_term_care_policy_before_i_retire_is_this_a_good_idea_and_h__0465d394.json',0),
 (11,'0c5468b87075247c1000b9b597ae2bca39630a678b9f92e340952ec2eebc0fbe','Yahoo Finance Markets','NVIDIA surpasses $3 trillion market cap on AI chip demand surge','NVIDIA''s market valuation crossed the $3 trillion mark as institutional investors piled into the stock following record data-center revenue guidance.','','https://finance.yahoo.com/news/mock-article-1','2026-06-07 13:54:13.830275','2026-06-07 13:54:14.365464','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\nvidia_surpasses_3_trillion_market_cap_on_ai_chip_demand_surge__0c5468b8.json',0),
 (12,'c961e414aaed2311c90e5096870d0abc4553b30b11207b5dd03eb7ad6228ab63','Yahoo Finance Markets','Federal Reserve holds rates steady, hints at September cut','Fed Chair Powell signaled the central bank is watching inflation data carefully before committing to a rate reduction cycle.','','https://finance.yahoo.com/news/mock-article-2','2026-06-07 11:54:13.830275','2026-06-07 13:54:14.750613','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\federal_reserve_holds_rates_steady_hints_at_september_cut__c961e414.json',0),
 (13,'e976ec59949e6eac43d9ca204d9ffa3ccc511e4210286641b00b4d54054b3f02','Yahoo Finance Markets','Apple unveils AI-powered iPhone 17 lineup at WWDC 2026','Apple''s new iPhone integrates on-device large language models, boosting privacy and reducing cloud dependency for everyday AI tasks.','','https://finance.yahoo.com/news/mock-article-3','2026-06-07 09:54:13.830275','2026-06-07 13:54:15.062167','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\apple_unveils_ai_powered_iphone_17_lineup_at_wwdc_2026__e976ec59.json',0),
 (14,'550d0c26affa8c428380694a0a9bb2809a42baea90aa36663424c9b6a2f2861a','Yahoo Finance Markets','Oil prices drop 4% as OPEC+ agrees to increase output quotas','The cartel''s unexpected decision to raise production targets sent crude futures tumbling, impacting energy sector stocks globally.','','https://finance.yahoo.com/news/mock-article-4','2026-06-07 07:54:13.830275','2026-06-07 13:54:15.352558','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\oil_prices_drop_4_as_opec_agrees_to_increase_output_quotas__550d0c26.json',0),
 (15,'d55375218f34be515ec0ffbf04757604236a261ba19a4844e4e830888d810234','Yahoo Finance Markets','Microsoft Azure cloud revenue up 35% YoY, beating estimates','Strong enterprise AI workload adoption drove Microsoft''s cloud segment well ahead of analyst forecasts, lifting the broader tech sector.','','https://finance.yahoo.com/news/mock-article-5','2026-06-07 05:54:13.830275','2026-06-07 13:54:15.692366','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\microsoft_azure_cloud_revenue_up_35_yoy_beating_estimates__d5537521.json',0),
 (16,'7db4731796b0bbefd90c0e79d345cc5983bd3894be2bd97db18833ed630e93d1','Yahoo Finance Markets','Tesla Q1 deliveries miss expectations amid pricing pressure','The EV maker delivered fewer vehicles than Wall Street projected as competition from Chinese manufacturers and softening demand weighed on results.','','https://finance.yahoo.com/news/mock-article-6','2026-06-07 03:54:13.830275','2026-06-07 13:54:16.103227','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\tesla_q1_deliveries_miss_expectations_amid_pricing_pressure__7db47317.json',0),
 (17,'e0150449b780da51d22a582af6b248995bfcacab919bf87c399ebe951cbe6ae1','Yahoo Finance Markets','Semiconductor shortage eases as TSMC expands Arizona fab capacity','TSMC''s $40 billion Arizona investment begins bearing fruit with advanced node chips rolling off lines, easing supply constraints for key customers.','','https://finance.yahoo.com/news/mock-article-7','2026-06-07 01:54:13.830275','2026-06-07 13:54:16.515496','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\semiconductor_shortage_eases_as_tsmc_expands_arizona_fab_capacity__e0150449.json',0),
 (18,'0ac20b68acae2cda574cea5b184cf793fb0057319db5829ad05d9ec3886f9d94','Yahoo Finance Markets','JPMorgan warns of recession risk as yield curve inverts further','The bank''s chief economist flagged mounting risks in the credit markets and highlighted the sustained inversion of the 2-10 year Treasury spread.','','https://finance.yahoo.com/news/mock-article-8','2026-06-06 23:54:13.830275','2026-06-07 13:54:17.023541','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-06\jpmorgan_warns_of_recession_risk_as_yield_curve_inverts_further__0ac20b68.json',0),
 (19,'6fbdaa0c3d29020724f9164172d737a9cb42438e25a9cb4bbc688e6a6d5acbcf','Yahoo Finance Markets','Amazon acquires AI startup Adept for $1.2 billion','The deal gives Amazon access to enterprise AI agents capable of operating software autonomously, deepening its cloud-AI stack against Microsoft and Google.','','https://finance.yahoo.com/news/mock-article-9','2026-06-06 21:54:13.830275','2026-06-07 13:54:17.444573','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-06\amazon_acquires_ai_startup_adept_for_12_billion__6fbdaa0c.json',0),
 (20,'80d98a0cf37a9cf0d9f85954d618b64c2bfe50bb83ec1c380dde8837b66ddb51','Yahoo Finance Markets','Renewable energy stocks rally on new IRA extension proposals','Solar and wind equities jumped after bipartisan support emerged for extending Inflation Reduction Act clean-energy credits through 2035.','','https://finance.yahoo.com/news/mock-article-10','2026-06-06 19:54:13.830275','2026-06-07 13:54:17.845399','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-06\renewable_energy_stocks_rally_on_new_ira_extension_proposals__80d98a0c.json',0),
 (21,'32c948e29da4701a819bf2658eeb347644f71493374a08ea0ed831c877509611','Yahoo Finance','HIVE Digital Technologies CFO on Bitcoin mining and AI data center growth – ICYMI','','HIVE Digital Technologies Ltd (TSX:HIVE, NASDAQ:HIVE, FRA:YO0, BVC:HIVECO) CFO Darcy Daubaras says the company is entering a new phase of growth after delivering record fiscal year-end results. With Bitcoin mining expansion in Paraguay providing strong cash flow, HIVE is now accelerating its AI infrastructure strategy through Canadian data centers and its Bell partnership.

Proactive: The company has reported fiscal year-end financial results and, as we''ve seen throughout the year, record numbers once again.

Darcy Daubaras: It''s been an incredible growth story over the last year. The fiscal year was defined by our growth in Paraguay, increasing from 6 EH/s to 25 EH/s. We always manage the ups and downs of Bitcoin, but we''ve also been energizing our dual-engine strategy by growing our high-performance computing business to a $20 million annual run rate and continuing to build from there. Looking ahead, we expect significant growth in high-performance computing through Canadian sovereign AI data center facilities. It''s a very exciting time for HIVE.

You mentioned the Bitcoin side of the business. The company increased Bitcoin production by 104% and generated nearly $300 million in revenue. It seems Bitcoin continues to be a strong contributor.

Absolutely. While some industry participants are pivoting away from Bitcoin mining, we''ve continued to embrace it because it powers our expansion into data centers. We have 300MW in Paraguay and one of the industry''s most efficient mining fleets. That gives us stable cash flow to continue investing in both our AI data center initiatives and our core operations.

Let''s talk about the computing side. Revenue was just under $20 million, but much of that appears to be laying the groundwork for future growth.

Exactly. The $20 million annual run rate comes from our historical data center business using NVIDIA A-series cards acquired several years ago. Now we''re leveraging our Bell partnership in Canada. We''ve deployed our first cluster of 500 units in Manitoba. That agreement is worth $30 million over two years and adds approximately $15 million in annual run-rate revenue.

We''ve also secured capacity in Bell''s Merritt, British Columbia facility. We''re evaluating two large clusters there and have secured the space and power. We are also working with prospective customers under memorandums of understanding. Each cluster could contribute between $65 million and $70 million in annual run-rate revenue.

We see a pathway from our current level to approximately $200 million in annual run-rate revenue by the end of the year. Beyond that, we have ambitions to reach $600 million through developments including the AI Gigafactory initiative in the Toronto-Waterloo corridor and our Toronto airport data center facility. We have the land and power in place; now the focus is on customers and GPU deployment.','https://finance.yahoo.com/markets/crypto/articles/hive-digital-technologies-cfo-bitcoin-121300558.html',NULL,'2026-06-07 14:06:24.315252','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\hive_digital_technologies_cfo_on_bitcoin_mining_and_ai_data_center_growth_icymi__32c948e2.json',1),
 (22,'2a84842e22755b13252ceb055a03e21f6742cda9f578c986f11a2c6eb6767d9e','Yahoo Finance','3 Cathie Wood ETFs to Buy Before They (Likely) Invest in SpaceX','','With the highly anticipated SpaceX initial public offering (IPO) expected next week, investors who have had their eyes on the space stock don''t have to wait much longer before they can lift off with Elon Musk''s rocket company.

But those who are excited about the prospect of owning SpaceX stock may also be fearful of the volatility that could follow the IPO. Fortunately, there are several Cathie Wood exchange-traded funds (ETFs) that are highly likely to invest in SpaceX and offer investors a more measured approach.

Will AI create the world''s first trillionaire? Our team just released a report on the one little-known company, called an "Indispensable Monopoly" providing the critical technology Nvidia and Intel both need. Continue »

Image source: Getty Images.

This ETF is committed to disruption

One strong candidate for holding SpaceX stock is the ARK Innovation ETF (NYSEMKT: ARKK), which identifies its investing theme as "disruptive innovation." In addition to the company''s leading launch-services business, which qualifies it as a disruptive company, SpaceX''s commitment to artificial intelligence (AI) further underscores its appeal to the ETF.

Including xAI, Grok, and X, the company''s AI segment is robust, generating $3.2 billion in revenue in 2025. The ARK Innovation ETF has $6.5 billion in net assets and a 0.75% expense ratio.

An ETF option that''s already out of this world

Dedicated to stocks advancing the space economy, the ARK Space & Defense Innovation ETF (NYSEMKT: ARKX) is highly likely to add SpaceX when it goes public. The fund highlights reusable rocket technology as one of its main targets -- Rocket Lab has the ETF''s second-largest weighting -- so SpaceX will be of obvious interest.

Paving the way forward with orbital-class, rapidly reusable rockets, SpaceX achieved this milestone in 2017 with its Falcon 9 rocket and expanded on it with the partly reusable Falcon Heavy rocket. With $893 million in net assets, the Space & Defense Innovation ETF has an expense ratio of 0.75%.

For a new and improved internet, there''s this ETF

Based on its name, the ARK Next Generation Internet ETF (NYSEMKT: ARKW) may not immediately seem like a candidate for SpaceX exposure, but scratch the surface of the company''s business, and it becomes readily apparent that this fund will probably load up on SpaceX stock. It''s not only about providing launch services to others; SpaceX''s interests lie elsewhere.

The company is pioneering internet innovation with Starlink, the space-based broadband service designed to provide low-latency internet connectivity worldwide. Starlink is gaining traction: The number of subscribers grew from 2.3 million in 2023 to 8.9 million in 2025.','https://finance.yahoo.com/markets/stocks/articles/3-cathie-wood-etfs-buy-121500461.html',NULL,'2026-06-07 14:06:54.253494','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\3_cathie_wood_etfs_to_buy_before_they_likely_invest_in_spacex__2a84842e.json',1),
 (23,'df781b74053ea4d09c7fc6a2cf88a6223278fde71dbf556de10f59c9f819f92c','Yahoo Finance','SpaceX, targeting a $1.77 trillion valuation, just got a 100% property tax exemption for a planned factory in Texas','','SpaceX’s looming debut on the Nasdaq marketplace might be center stage right now, but the rocket/AI company is continuing operations as that IPO draws near — and not all of its actions are winning it fans.

SpaceX has worked out a deal with officials in Grimes County, Texas to completely forego paying property taxes on its $55 billion Terafab semiconductor chip manufacturing facility. Instead, the company will pay a $10 million lump sum to the county (1), followed by $20 million for the next 35 years.

Must Read

Commissioners voted four-to-one in approving the deal on June 4, despite complaints from the community that the approval process lacked sufficient transparency and could strain critical infrastructure in the county.

An ambitious goal

Terafab, Elon Musk has said, will eventually create a terawatt of computing power each year. The company is expected to make two kinds of chips — one of which would be used for Tesla vehicles and Optimus robots, while the other was designed to be used in space, as part of Musk’s plans for space-based data centers.

The facility has been met with skepticism, as none of Musk’s companies have semiconductor manufacturing experience. Tesla, at one point, did have a chip design team, but most left the company after Musk killed the Dojo project, which was working on Tesla’s custom-built supercomputer. (And even if they had stayed, chip design is a much different job than chip manufacturing.)

Musk’s own comments about the process have also fueled doubt. In January, he said the semiconductor industry is “getting clean rooms wrong (2),” betting Tesla would build a 2nm fab where he can “eat a cheeseburger and smoke a cigar.”

Intel joined forces with SpaceX in April to help build out the facility.

Read More: BlackRock warns buying and holding the S&P 500 isn’t enough for retirement anymore — here''s why

Environmental concerns

The Terafab facility will be built at the Gibbons Creek Reservoir site, roughly 90 miles northeast of Austin, Texas. The $55 billion price tag (3) is nearly triple the $20 billion Musk said it would cost when he announced the project in March.

Some residents of Grimes County have expressed concerns about the project, particularly the potential strain it will put on the local water and power infrastructure. More than 100 people showed up for a local hearing (4), where some argued that with the company having an expected valuation of $1.75 trillion following its IPO, a 100% waiver on property taxes was inappropriate.','https://finance.yahoo.com/economy/policy/articles/spacex-targeting-1-77-trillion-131000248.html',NULL,'2026-06-07 14:07:26.676664','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-07\spacex_targeting_a_177_trillion_valuation_just_got_a_100_property_tax_exemption___df781b74.json',1),
 (24,'24c43924a301988ee37be8bad02606a8de89ea49e0280856aa366271c56177b7','Yahoo Finance','Nvidia Just Slipped Below $5 Trillion. These Are the Few Companies With a Realistic Shot at Catching It.','','AI chip company Nvidia (NASDAQ: NVDA) became the first company ever worth $5 trillion in late 2025. As of this writing, it sits just below this after a recent pullback. But it''s still the most valuable company in the world by a comfortable margin.

What''s striking is how few companies are even in the conversation to pass it. But I personally think this is a conversation worth having, because I don''t think Nvidia will hold its crown forever.

Will AI create the world''s first trillionaire? Our team just released a report on the one little-known company, called an "Indispensable Monopoly" providing the critical technology Nvidia and Intel both need. Continue »

Of the handful that have crossed into multitrillion-dollar territory, three arguably look like plausible challengers over time: Alphabet (NASDAQ: GOOG)(NASDAQ: GOOGL), Apple (NASDAQ: AAPL), and Microsoft (NASDAQ: MSFT). Each has market capitalizations measured in the trillions, yet each still trails Nvidia -- and closing that gap would require specific things to go right. But I think passing Nvidia''s value is possible for all three -- especially for one of them.

Apple CEO Tim Cook an at an Apple store. Image source: Apple.

Alphabet

Of the three, Google parent Alphabet had closed the most ground until recently. Its stock has climbed sharply over the past year, lifting its market value to about $4.9 trillion -- a little more than half a trillion dollars short of Nvidia. But after a recent pullback, the stock''s market capitalization is now $4.45 trillion -- still within striking distance but behind Apple, which has a market capitalization of $4.51 trillion as of this writing.

So, how does Alphabet become bigger than Nvidia?

The bull case rests on Alphabet controlling every layer of the AI business. From the chips up, Alphabet has its hands in virtually every part of the technology stack that builds AI and delivers it to end users.

Capturing its incredible AI momentum, Alphabet''s first-quarter Google Cloud revenue grew 63% year over year to $20 billion, accelerating from 48% growth in the fourth quarter of 2025, and its order backlog nearly doubled in three months to more than $460 billion.

And "Google search and other advertising revenue," which many investors feared AI would erode, instead grew 19%.

"And the fact that we own frontier models, own the silicon, really helps us stay ahead of the curve," said Alphabet CEO Sundar Pichai during the company''s first-quarter earnings call.

That silicon -- Google''s in-house Tensor Processing Units -- may be the part that matters most, because Alphabet has started selling that hardware to outside customers and will begin delivering it to select customers later this year, putting it in more direct competition with Nvidia.','https://finance.yahoo.com/markets/stocks/articles/nvidia-just-slipped-below-5-174300785.html',NULL,'2026-06-08 04:53:35.193657','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\nvidia_just_slipped_below_5_trillion_these_are_the_few_companies_with_a_realisti__24c43924.json',1),
 (25,'541ce29ba324b06f9a2944b2da3fdda20d9c81f71da49e1923e5e335c99c415b','Yahoo Finance','GitLab Shares Sink After Layoff News. Why Analysts Still See Massive Upside.','','GitLab (GTLB) took a hard hit on Tuesday, with shares falling nearly 15% after the company unveiled a major restructuring plan. The DevOps software maker said it will cut about 14% of its workforce, or roughly 350 roles, as it tries to tighten costs and sharpen its focus on profitability.

The selloff was sharp, but the reaction was not surprising. Software stocks have been pressured for months as enterprise customers slow spending and become more selective with new deals. That has hurt several names across the space, including Atlassian (TEAM) and JFrog (FROG). GitLab, though, has always stood out a bit from the pack thanks to its all-in-one platform and remote-first culture.

More News from Barchart

For investors, the big question is whether this drop is a warning sign or a chance to buy a quality business at a better price.

How Did GTLB Stock Perform?

GitLab’s stock has already been under serious pressure before this latest blow. Shares are down more than 33% over the past year and had already fallen about 18% year-to-date (YTD) in 2026. With the stock now sitting well below both its 50-day and 200-day moving averages, the chart still looks weak. Sellers remain in control for now.

Still, the valuation picture is starting to look more interesting. GitLab currently trades at about 6 times forward sales, while the software sector median is closer to 8 times. Its enterprise value-to-revenue ratio is also just under 5, compared with an industry median around 7. That is not dirt cheap, but it is a noticeable discount. After such a steep reset, the market is clearly pricing in a lot of bad news.

www.barchart.com

AI and Efficiency Are Driving GitLab’s Next Chapter

The restructuring move is designed to help with exactly that. By trimming headcount and streamlining operations, GitLab expects to cut annual expenses by about $60 million. Management wants to redirect more resources toward the areas where customer demand is strongest while also improving its path to profitability. That makes sense on paper, even if the headlines sound harsh.

The company still has a lot going for it beyond the cost cuts. GitLab’s platform is built to handle the entire software development cycle in one place, from planning and coding to security and deployment. That single-application approach is one of its biggest strengths. It makes collaboration easier and gives customers one system instead of a patchwork of tools.','https://finance.yahoo.com/markets/stocks/articles/gitlab-shares-sink-layoff-news-180002809.html',NULL,'2026-06-08 04:53:41.355851','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\gitlab_shares_sink_after_layoff_news_why_analysts_still_see_massive_upside__541ce29b.json',1),
 (26,'7f145a65af0b5ae7cb0b7f162c914b61c2d4103bb29d85aa0bcd882c86b706a1','Yahoo Finance','The Coca-Cola (KO) Explores Potential Listing in India of Hindustan Coca-Cola Holdings Pvt. Ltd.','','The Coca-Cola Company (NYSE:KO) is one of the Best Big Company Stocks to Buy Right Now. On June 1, the company announced that it is exploring a potential public listing in India of Hindustan Coca-Cola Holdings Pvt. Ltd. (HCCH), which is the parent company of Hindustan Coca-Cola Beverages Pvt. Ltd. (HCCB), in 2027. Also, it is assessing the sale of a portion of its shareholding in HCCH in relation to the listing. Notably, the preparations continue for the potential listing on BSE and NSE. However, the listing remains subject to market conditions and applicable regulatory and other approvals.

The Coca-Cola (KO) Explores Potential Listing in India of Hindustan Coca-Cola Holdings Pvt. Ltd.

In July 2025, The Coca-Cola Company (NYSE:KO) wrapped up a transaction that saw Jubilant Bhartia Group acquiring 40% stake in HCCH. Jubilant Bhartia Group is an Indian family-owned conglomerate that has a presence across diverse sectors and robust relationships with several other multinational companies. The listing is expected to be a critical milestone, which will help complete the refranchising of HCCH and position it well to reap the benefits in the broader Indian market.

The Coca-Cola Company (NYSE:KO) is a beverage company, which is engaged in manufacturing and selling various non-alcoholic beverages.

While we acknowledge the potential of KO as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/coca-cola-ko-explores-potential-172531894.html',NULL,'2026-06-08 04:53:47.241980','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\the_coca_cola_ko_explores_potential_listing_in_india_of_hindustan_coca_cola_hold__7f145a65.json',1),
 (27,'3c32c9e26a8984470a2064e871908c4dd49ad7e15d2a29c33964e1dcb3aaa4ae','Yahoo Finance','Morgan Stanley Reiterates Buy Rating on Costco Wholesale (COST) Stock','','Costco Wholesale Corporation (NASDAQ:COST) is one of the Best Big Company Stocks to Buy Right Now. On May 29, Simeon Gutman from Morgan Stanley reiterated a “Buy” rating on the company’s stock with a price objective of $1,130.00. The analyst’s rating is backed by several factors that are associated with Costco Wholesale Corporation (NASDAQ:COST)’s structural strengths and recent performance.

Morgan Stanley Reiterates Buy Rating on Costco Wholesale (COST) Stock

As per the analyst, Costco Wholesale Corporation (NASDAQ:COST) is one of the few US retailers that is well-placed to outperform in the present environment, thanks to its scale, efficient supply chain, and robust value proposition, which are tagged as critical drivers of continued market share gains and durable earnings growth.

Costco Wholesale Corporation (NASDAQ:COST) released its operating results for Q3 (twelve weeks) and the first 36 weeks of FY 2026, ended May 10, 2026. In Q3, net sales rose 11.6% to $69.15 billion from $61.96 billion in the last year.

Costco Wholesale Corporation (NASDAQ:COST) is engaged in the operation of membership warehouses.

While we acknowledge the potential of COST as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/morgan-stanley-reiterates-buy-rating-172516326.html',NULL,'2026-06-08 04:53:52.474752','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\morgan_stanley_reiterates_buy_rating_on_costco_wholesale_cost_stock__3c32c9e2.json',1),
 (28,'52e6529bb58472c7b1dca8641ecca44c024441ff43759c7519bb2b0bea121206','Yahoo Finance','UBS Lifts PT on Caterpillar (CAT) Stock','','Caterpillar Inc. (NYSE:CAT) is one of the Best Big Company Stocks to Buy Right Now. On June 2, UBS analyst Steven Fisher lifted its price objective on the company’s stock to $900 from $677 and maintained a “Neutral” rating on the shares. As per the analyst, Caterpillar Inc. (NYSE:CAT) remains well-placed to benefit from the robust demand in prime power generation, construction, mining, and oil and gas markets. This will help earnings growth through 2027-2029.

UBS Lifts PT on Caterpillar (CAT) Stock

As per the firm, the US prime power generation opportunities are expected to remain strong until either the grid investment accelerates significantly or the large turbine production capacity increases. That being said, the firm opines that, post its Q1 beat, a significantly larger backlog, and sharply higher consensus earnings expectations, most of the upside seems to be already factored into the stock’s valuation. This limits the potential for further significant positive surprises.

Caterpillar Inc. (NYSE:CAT) is engaged in providing construction and mining equipment, off-highway diesel and natural gas engines, industrial gas turbines, and diesel-electric locomotives.

While we acknowledge the potential of CAT as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/ubs-lifts-pt-caterpillar-cat-172522857.html',NULL,'2026-06-08 04:53:53.758839','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\ubs_lifts_pt_on_caterpillar_cat_stock__52e6529b.json',1),
 (29,'36c91df6e00ea717c618bdf659e5df4ccc0862d4a843a12d38b1cbb78266b94f','Yahoo Finance','Cathie Wood''s favorite crypto stock is still down 66% from record highs','','Few names lit up Wall Street in 2025 like one crypto sector''s breakout IPO.

It tore out of the gate last June, minted overnight winners, and quickly became the stock every trader wanted a piece of. For a few heady weeks, it looked unstoppable.

Today, the crypto stock trades at 66% below its all-time high.

One high-profile money manager hasn''t flinched, though. As the share price slid month after month, she kept buying, and the stock now ranks among her largest holdings.

Why Circle stock became a crypto market bellwether

Circle Internet Group isn''t a meme coin or a mining play. It''s the company behind USDC, the world''s second-largest stablecoin.

A stablecoin is a digital dollar. One USDC is always equal to one U.S. dollar, backed by cash and short-term Treasuries.

That makes Circle (CRCL) less of a crypto gamble and more of a plumbing company for digital money.

Circle went public in June 2025 at $31 a share. Within weeks, it reached a closing high of $263.45 on June 23, 2025.

That''s a stunning run for any new listing.

Since then, reality has set in. At the time of writing, CRCL stock trades around $91, valuing the company at a market cap of $22.5 billion.

The digital-asset market is down over 50% from its October 2025 peak, and Circle got swept up in the tide.

When you understand why the stock fell, the next part gets a lot more interesting.

Cathie Wood has kept adding Circle shares even as the stock trades far below its 2025 peakBloomberg/Getty Images

Cathie Wood keeps buying Circle stock during the slump

Here''s the twist. While most investors headed for the exits, Cathie Wood remained bullish.

Her ARK funds first bought Circle in Q2 of 2025, scooping up 2.92 million shares, according to data from Stock Circle.

Q3 2025: Added 42,500 shares at an average closing price of $138.55

Q4 2025: Added 1.17 million shares (a 39.6% jump) at an average of $102.88

Q1 2026: Added another 368,000 shares at an average of $80.20

Add it up, and ARK now holds 4.51 million Circle shares worth about $408 million. That''s 2.72% of the equity portfolio and her 10th-largest position.

Fund manager buys and sells

ARK owns roughly 1.35% of all outstanding Circle stock.

Wood’s estimated cost basis sits near $98.60 a share. With the stock around $90, that''s a paper loss of about 8.1%.

Wood''s playbook rarely tracks short-term sentiment. She buys disruptors when they''re cheap and unloved, betting the long-term story wins out. Circle fits that mold perfectly.

A strong performance in Q1

In its first-quarter report, Circle said:','https://finance.yahoo.com/markets/crypto/articles/cathie-woods-favorite-crypto-stock-174700110.html',NULL,'2026-06-08 04:53:55.441761','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\cathie_woods_favorite_crypto_stock_is_still_down_66_from_record_highs__36c91df6.json',1),
 (30,'34a60fb7259188a19e7afe5a44ec7e1083478978aa1eb76edb4feea347b597d0','Yahoo Finance','Wells Fargo Raises PT on Intel (INTC) Stock','','Intel Corporation (NASDAQ:INTC) is one of the Best Big Company Stocks to Buy Right Now. On June 1, Wells Fargo lifted its price objective on the company’s stock to $110 from $85 and maintained an “Equal Weight” rating on the shares. The firm hosted meetings on the 4th Annual Wells Fargo Silicon Valley Bus Tour, wherein it saw positive demand tone spanning across AI data center build-outs to the proliferation of AI inferencing/Agentic AI leading to strong incremental server CPU demand as well as continued drives of memory expansion. Furthermore, the firm believes that the economies of scale remain a strong competitive advantage.

Wells Fargo Raises PT on Intel (INTC) Stock

In a different update, Mizuho lifted its price objective on Intel Corporation (NASDAQ:INTC)’s stock to $128 from $124 and kept a “Neutral” rating on the shares. The firm lifted its price objectives in the broader semiconductor group, while adding that agentic AI demand remains robust throughout the CPU ecosystem. As per the analyst, the suppliers are supply-constrained into 2027, demonstrating upside in servers.

Intel Corporation (NASDAQ:INTC) is a semiconductor company specializing in computing & related end products and services through its CCG, DCAI, and Intel Foundry segments.

While we acknowledge the potential of INTC as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/wells-fargo-raises-pt-intel-172508626.html',NULL,'2026-06-08 04:54:00.180794','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\wells_fargo_raises_pt_on_intel_intc_stock__34a60fb7.json',1),
 (31,'ca1dc5d6add0a364713ef9b4d51fb5ff9a257af1032fce5e38aa550016c4efb1','Yahoo Finance','Piper Sandler Raises PT on Alphabet (GOOGL) Stock','','Alphabet Inc. (NASDAQ:GOOGL) is one of the Best Big Company Stocks to Buy Right Now. On June 1, Piper Sandler analyst Thomas Champion lifted its price objective on the company’s stock to $445 from $425 and kept an “Overweight” rating on the shares. The firm released its first analysis of citations data throughout searches in Google’s AI Overview and AI Mode. Notably, the AI-assisted search continues to expand rapidly.

Piper Sandler Raises PT on Alphabet (GOOGL) Stock

Alphabet Inc. (NASDAQ:GOOGL) is leading citation share, thanks to the YouTube and Google properties. Furthermore, the step-function growth in citations since early 2025 remains in line with the commentary from the management that AI Mode has been resulting in queries 3 times longer compared to the traditional search. Also, the queries are at an all-time high.

According to the firm, the AI search expansion happens to be the most positive for Alphabet Inc. (NASDAQ:GOOGL), Reddit, and Meta. Only some companies remain dominant content sources in the broader AI-assisted search environment.

Alphabet Inc. (NASDAQ:GOOGL) is a holding company that operates Google services such as search engines, ad platforms, Internet browsers, devices, mapping software, app stores, video streaming, and more. The company also offers cloud infrastructure and platform services, collaboration tools, and other services for enterprise customers, as well as healthcare-related services and internet services.

While we acknowledge the potential of GOOGL as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/piper-sandler-raises-pt-alphabet-172437951.html',NULL,'2026-06-08 04:54:04.870177','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\piper_sandler_raises_pt_on_alphabet_googl_stock__ca1dc5d6.json',1),
 (32,'592ee7c2ccb8f9ddb66b0ed43b252404d99b4e9e7d6d00d45eab24b6c661f2bf','Yahoo Finance','TD Cowen Raises PT on Advanced Micro Devices (AMD) Stock','','Advanced Micro Devices, Inc. (NASDAQ:AMD) is one of the Best Big Company Stocks to Buy Right Now. On June 1, TD Cowen lifted its price target on the company’s stock to $600 from $500 and maintained a “Buy” rating on the shares post meeting with management. As per the analyst, Advanced Micro Devices, Inc. (NASDAQ:AMD) demonstrated a meaningful change over the past couple of months, with the AI productivity and capabilities improving for enterprises to deploy significant capital for AI.

TD Cowen Raises PT on Advanced Micro Devices (AMD) Stock

According to the firm, while the company doubled its total addressable market expectations, the management sees that the $120 billion figure can be conservative. This is because agentic AI continues to push the requirement for efficient, high-performance, low-latency CPUs, which are flexible throughout different workloads.

Against the significant and early AI compute market, the firm opines that Advanced Micro Devices, Inc. (NASDAQ:AMD) has been doing its groundwork to strengthen its position as the de facto merchant alternative to the strong market position of Nvidia.

Advanced Micro Devices Inc. (NASDAQ:AMD) is a leading semiconductor company specializing in high-performance computing and graphics solutions. Its broad product portfolio includes microprocessors, graphics processors, and system-on-chip (SoC) solutions designed for data centers, gaming, and embedded systems.

While we acknowledge the potential of AMD as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/td-cowen-raises-pt-advanced-172502621.html',NULL,'2026-06-08 04:54:09.276701','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\td_cowen_raises_pt_on_advanced_micro_devices_amd_stock__592ee7c2.json',1),
 (33,'b7191c552e71121cfd1eb796a752fff8bf80a5bee5ddb1d96031de7d5ca57840','Yahoo Finance','Here’s Why Apple (AAPL) is One of the Best Big Company Stocks to Buy Right Now','','Apple Inc. (NASDAQ:AAPL) is one of the Best Big Company Stocks to Buy Right Now. On June 1, Morgan Stanley analyst Erik Woodring reiterated an “Overweight” rating and a price objective of $330. The analyst believes that a successful AI strategy can help unlock a higher valuation for the company’s stock.

Here''s Why Apple (AAPL) is One of the Best Big Company Stocks to Buy Right Now

Apple Inc. (NASDAQ:AAPL)’s recent strength was backed by its products and services business instead of AI. That being said, companies tagged as AI winners were often credited with increased valuations over the previous 2 years, and the analyst opines that Apple Inc. (NASDAQ:AAPL) can be seen as one of them soon.

Contrary to its rivals, Apple Inc. (NASDAQ:AAPL) is not shelling out significantly on building AI infrastructure. Instead of doing this, the company could leverage its significant base of iPhone, iPad, and Mac users in a bid to bring new AI features to consumers. The analyst opines that this can help Apple Inc. (NASDAQ:AAPL) in growing the AI offerings without the high costs that are being faced by its competitors.

Apple Inc. (NASDAQ:AAPL) designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and home accessories. The company develops its own operating systems (iOS, macOS) and provides digital services, including iCloud, Apple Pay, and content streaming through the App Store and Apple TV+.

While we acknowledge the potential of AAPL as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 10 Best FMCG Stocks to Invest In According to Analysts and 11 Best Long-Term Tech Stocks to Buy According to Analysts.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/why-apple-aapl-one-best-172454230.html',NULL,'2026-06-08 04:54:14.304120','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-08\heres_why_apple_aapl_is_one_of_the_best_big_company_stocks_to_buy_right_now__b7191c55.json',1),
 (34,'bf9c72eb63b867721a091161d4f0fdcf59ce29e9106cb31749293e70d38f9a13','Yahoo Finance','Kalshi crypto perpetual futures hit $1 billion in trading volume','','Kalshi''s crypto perpetual futures crossed $1 billion in trading volume within a week of their launch, the company shared with CNBC.

The platform officially launched trading on the contracts last week, recording more than $100 million in volume in the first 24 hours. More than 1 million people had joined the queue for access to the product at its peak, a company spokesperson noted, adding that no other offering in Kalshi''s history has grown as quickly.

Perpetual futures, or perps, do not have an expiration date. This lets traders bet on price changes without owning the asset. A funding system keeps the contract price close to the market price. Globally, trading in this asset class is over $90 trillion each year. Before Kalshi, U.S. traders could not use a regulated domestic platform for these contracts.

The Commodity Futures Trading Commission issued an order approving KalshiEX''s BTCPERP contract on May 29, determining that the contract complies with the Commodity Exchange Act and applicable regulations. The commission noted that the perpetual contract design may not be suitable for all asset classes and encouraged market participants to engage with staff before submitting contracts on assets not covered by the order.

"This marks Kalshi''s evolution from prediction market leader to next-gen derivatives exchange," said Kalshi CEO Tarek Mansour. "Onshore, safe, and regulated perps will improve capital allocation and risk management for countless American businesses."

Kalshi said it aims to launch crypto perpetuals on more than a dozen currencies, pending additional regulatory reviews. Perpetual futures on agricultural commodities will not be part of its product offerings, the company said. Funding rates are updated every eight hours.

For comparison, it took Kalshi 40 months to reach $1 billion in volume across its event contracts.

Kalshi''s perpetual futures launch represents the company''s largest product expansion since it first introduced regulated perpetual futures to U.S. investors, a market that had been accessible only through offshore exchanges. The company, which raised a $1 billion Series F at a $22 billion valuation last month, said it accounts for more than 90% of prediction market activity in the U.S.','https://finance.yahoo.com/markets/crypto/articles/kalshi-crypto-perpetual-futures-hit-185641129.html',NULL,'2026-06-11 07:00:20.819973','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\kalshi_crypto_perpetual_futures_hit_1_billion_in_trading_volume__bf9c72eb.json',1),
 (35,'d444dc97af67194bb0fdd83e93d3b497f47063a483f72cf24214f4b1e2a9c486','Yahoo Finance','Is the Dollar Index Preparing for a Significant Break?','','I concluded an April 17, 2026, Barchart article on the U.S. dollar index with the following:

While the dollar index could be heading for lower lows, it is likely to remain within the 89.20-114.78 range over the coming months.

More News from Barchart

The dollar index was trading at 97.78 in April 2026. At near 100 in June 2026, the index was higher, but it remains in a narrow consolidation range.

Consolidation continues

Over the past year, the dollar index has traded in a tight 5.09 point range.

The daily chart shows that the 5.09 range includes a downside extension that took the index to a 95.55 low on January 27, 2026, and an upside extension that pushed it to 100.64 on March 31, 2026. Aside from those extensions, the index has traded in a narrow 4.18 point range over the past year, with the pivot point around 98.50, which is just above the high and low for the past year.

The bullish case for the dollar index

The bullish technical case for the dollar index is evident from its 20-year monthly chart.

The index has made higher lows and higher highs from the March 2008 low of 70.69 to the September 2022 114.78 high. Since 2008, downside corrections have not declined below the previous critical technical support levels.

Fundamentally, the following factors support the U.S. dollar index, which measures the dollar against the other leading world reserve currencies:

The U.S. continues to have the leading world economy.

Elevated U.S. interest rates support the dollar versus other world reserve currencies.

As the world’s reserve currency, the dollar remains the currency that central banks, governments, and monetary authorities hold as a reserve asset.

Turbulent times and economic and geopolitical surprises tend to support the dollar as a safe haven.

The 20-year chart and a host of fundamental factors support the dollar index at the 99 level.

The dollar index’s bearish case

The bearish technical case for the dollar index is evident from its long-term quarterly chart.

The index has made lower highs and lower lows from the 1985 high of 174.72 to the 2008 low of 70.69. While the index has recovered since 2008, the long-term bearish trend remains intact, as it has not traded above the 2022 high of 114.78.

Fundamentally, the following factors weigh on the U.S. dollar index:','https://finance.yahoo.com/markets/currencies/articles/dollar-index-preparing-significant-break-190003951.html',NULL,'2026-06-11 07:00:26.792532','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\is_the_dollar_index_preparing_for_a_significant_break__d444dc97.json',1),
 (36,'5061a105ee0893b3b373d87bb06d3aa393b3c94f7368b55af4a30c789ac19099','Yahoo Finance','Primis Bank review (2026): High-interest bank accounts with free nationwide ATM access','','Summary: Primis Bank is a financial institution that combines the strength of an FDIC-insured bank with the innovation of a fintech company. It offers personal and business deposit accounts, mortgages, loans, and lines of credit. The bank was founded in 2005 and primarily serves customers online. However, it has physical branches in Virginia and Maryland.

Primis Bank product overview

Primis Premium Checking

Primis Bank''s Premium Checking account is a free checking account with a high yield. It pays 3.7% APY and has no minimum balance. The minimum opening deposit for this account is just $1.

In addition, this account has minimal fees, charging no monthly account fees or overdraft fees. You also have free nationwide ATM access, with all non-Primis ATM fees refunded at the end of each billing cycle.

Primis Perks Checking

This account has most of the same benefits as the Premium Checking account. The main difference is that it earns rewards on every debit card purchase instead of interest. You can earn unlimited 1% cash back on all purchases.

Primis Savings

Primis Bank also offers a high-yield savings account with a competitive 3.85% APY. It has many of the same benefits as the bank''s checking accounts, such as no monthly fees or minimum balances. In addition, it has the same $1 minimum opening deposit.

Primis Bank fees

Primis generally keeps fees low; you can learn more about specific account fees in each account''s disclosure documents. The following table highlights common fees that Primis Bank charges for certain services.

FEE FEE AMOUNT Cashier’s check (savings accounts only) $10 Expedited bill payment (when available) $25 Expedited debit card reorder $25 Foreign check collection (other than Canadian) $50, plus collection fees Foreign check collection (Canadian) $20) Garnishments/liens/levies $150 per item Notary services (remote) $15 Reconciliation/research $35 per hour Return deposited item $10 Domestic outgoing wire $5 International outgoing wire $35 Return wire $2.50 Reverse wire $5 Check images with paper statement $3 Copies of statements and/or individual checks $5 Close account early within 90 days or less $25 Withdrawal from non-Primis ATM $3 Balance inquiry from non-Primis ATM $2

Primis Bank pros and cons

Consider these pros and cons before opening an account with Primis Bank:

Pros

Competitive deposit interest rates: Primis Bank''s Premium checking account pays an impressive 3.7% APY, while the savings account pays slightly more at 3.85% APY. These rates are highly competitive for today''s market.

No monthly fees: This bank charges no monthly fees on any of its deposit accounts.

Free nationwide ATM access: You have fee-free access to ATMs nationwide. Any fees you incur are reimbursed at the end of each billing cycle.

Cons

Limited branch access: Primis Bank has several branches in its home state of Virginia, as well as Maryland. However, it does not have a physical presence in other states. This may be a downside for those who prefer in-person service.

No CDs or money market accounts: CDs sometimes pay higher rates than savings accounts, but Primis doesn''t offer them. The same is true for money market accounts, which offer some features of both checking and savings accounts.

Customer service and mobile banking experience

You can get in touch with Primis Bank via phone or email, in addition to a contact form on the bank''s website. It also has a chat feature, which lets you communicate by typing or speaking. The bank says its customer support number is available 24/7.

Primis Bank has apps available on iOS and Android, with average user ratings of 4.7 stars and 4.5 stars, respectively. The app lets you check account balances, see spending patterns, transfer money between accounts, and deposit checks.

Primis Bank address and phone number

The general customer support number for Primis Bank is 833-477-4647.

Primis Bank''s mailing address is:

Primis

P.O. Box 2075

Ashland, VA 23005

Primis Bank FAQs

Is Primis Bank FDIC-insured?

Yes, Primis Bank is FDIC-insured. In fact, it offers extended FDIC coverage, insuring up to $2 million per tax ID.

What is Primis Bank''s routing number?

Primis Bank''s routing number is 051409278.

How large is Primis Bank?

Primis Bank is relatively small, with $4.3 billion in total assets as of March 31, 2026.

How old is Primis Bank?

Primis Bank was founded in 2005.

What was Primis Bank before?

Primis Bank was previously known as Sonabank. The bank announced that it would rebrand to Primis Bank in 2021.','https://finance.yahoo.com/personal-finance/banking/review/primis-bank-review-211322751.html',NULL,'2026-06-11 07:00:29.755092','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\primis_bank_review_2026_high_interest_bank_accounts_with_free_nationwide_atm_acc__5061a105.json',1),
 (37,'dacbef961a38ad47be5aa8bb09dfbe4e1782a9258fb36204bee6ef38e8af3c39','Yahoo Finance','Why Analysts Believe Honeywell’s (HON) Automation Story Is Gaining Strength','','With an upside potential of 14.09%, Honeywell International Inc. (NASDAQ:HON) is among the 7 Best Automation Stocks to Buy for Warehouse Construction.

Honeywell International Inc. (NASDAQ:HON) received a vote of confidence from Wall Street on June 5 when RBC Capital analyst Deane Dray raised the firm’s price target to $275 from $268 while maintaining an Outperform rating. The analyst expects Honeywell’s Investor Day to serve as a positive catalyst, with management likely outlining a mid-single-digit organic growth framework alongside a compelling margin expansion story. RBC believes Industrial Automation is approaching an important inflection point, with EBITA margins potentially reaching 20%, highlighting the strength of Honeywell’s operational improvement initiatives and the long-term earnings power of its automation businesses.

Earlier, on May 27, Barclays raised its price target on Honeywell to $251 from $243 and reiterated an Overweight rating. The firm pointed to several upcoming catalysts that could unlock shareholder value, including two capital markets days and the planned completion of two corporate spinoffs. Barclays believes these strategic actions could help investors better appreciate the value of Honeywell’s individual business segments and estimates that the stock could experience an additional 10% to 15% upside as the separation process unfolds.

Founded in 1885 and headquartered in Charlotte, North Carolina, Honeywell International is a global leader in industrial automation, aerospace technologies, building solutions, and energy systems. The company plays a significant role in warehouse construction and logistics through its robotics platforms, automated storage and retrieval systems, and Momentum Warehouse Execution System software, which helps customers maximize efficiency, storage density, and order fulfillment speed across increasingly automated facilities.

While we acknowledge the potential of HON as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 7 Best Civil Engineering Stocks to Buy for Smart City Projects and Top 10 Stocks That Members of Congress Own.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/why-analysts-believe-honeywell-hon-194006630.html',NULL,'2026-06-11 07:00:34.017864','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\why_analysts_believe_honeywells_hon_automation_story_is_gaining_strength__dacbef96.json',1),
 (38,'1ece7191aa803e793dacd6c8c04983cbb04001fc4159e00e0f71c32855fdc204','Yahoo Finance','Wall Street Is Missing the Bigger Picture: Why This Legacy Tech Stalwart Is a Screaming Buy Right Now','','Quick Read

IBM''s software revenue hit $7.05 billion in Q1 2026, up 11%, while mainframe revenue surged 51% as enterprises modernized mission-critical workloads.

IBM raised its dividend for the 31st straight year, backed by $14.73 billion in free cash flow that grew 25% in FY2025.

IBM''s $12.5 billion generative AI book of business and beta of 0.665 compound steady gains while protecting capital when speculative tech trades unwind.

It sounds nuts, but SoFi is giving new active invest users up to $1,000 in stock for a limited time, and all it takes is a $50 deposit to get started. See for yourself (Sponsor)

International Business Machines (NYSE:IBM) is a stock worth owning for decades because it pairs a 110-year operating history with a recurring-revenue software and infrastructure engine that is now compounding cash at an accelerating pace. IBM is built for retirement portfolios that need durability, income, and survivability across every market cycle, not narrative-driven upside.

Pillar One: A Business Built to Outlast Cycles

IBM has quietly become a software-led company. In Q1 2026, Software revenue reached $7.05 billion, up 11.3%, with Red Hat growing 13%, Data growing 19%, and Automation growing 10%. Infrastructure, often dismissed as legacy, posted 15.3% growth, while IBM Z mainframe revenue surged 51% year over year as enterprises modernized mission-critical workloads. Hybrid cloud architecture and Watsonx integrations are embedded directly into the systems run by financial services firms, healthcare providers, and government agencies, producing the kind of ecosystem lock-in that does not evaporate in a recession. CEO Arvind Krishna told investors, "As clients scale use cases, AI continues to be a tailwind for our global business."

Pillar Two: Income You Can Actually Plan Around

For an investor who needs predictable cash, IBM is one of the most reliable payers in the market. The board declared its 31st consecutive annual dividend increase on April 22, 2026, lifting the quarterly payout to $1.69 per share. The company has paid consecutive quarterly dividends every year since 1916, a streak that survived the Great Depression, the 1970s stagnation, the dot-com bust, the 2008 financial crisis, and the pandemic. The dividend is well covered: FY2025 free cash flow was $14.73 billion, up 25.29%, and management guided to roughly another $1 billion of free cash flow growth in 2026. The current yield of 2.23% is paired with a forward earnings multiple of 23, modest for a company generating 35.8% return on equity.','https://finance.yahoo.com/markets/stocks/articles/wall-street-missing-bigger-picture-185702010.html',NULL,'2026-06-11 07:00:37.970225','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\wall_street_is_missing_the_bigger_picture_why_this_legacy_tech_stalwart_is_a_scr__1ece7191.json',1),
 (39,'6b072aa82a9403f90b22640904d5bf2c5b743442345d8b329f6d96df50f27996','Yahoo Finance','AECOM (ACM): 7 Best Civil Engineering Stocks to Buy for Smart City Projects','','With an upside potential of 49.83%, AECOM (NYSE:ACM) is among the 7 Best Civil Engineering Stocks to Buy for Smart City Projects.

AECOM (NYSE:ACM) strengthened its position in the defense infrastructure market on May 21 after securing the top ranking on Defence Construction Canada’s National Architecture & Engineering Source List. The multi-year program carries a potential value of up to C$270 million and will support the Department of National Defence in delivering critical infrastructure projects across Canada. Under the agreement, AECOM will provide comprehensive planning, engineering, architectural, and construction support services for facilities, including aircraft maintenance buildings, high-security offices, military accommodations, training centers, and other strategically important assets. The award highlights the company’s strong reputation in managing complex public-sector infrastructure programs.

Earlier, on May 19, Barclays lowered its price target on AECOM (NYSE:ACM) to $90 from $110 while maintaining an Equal Weight rating following the company’s fiscal second-quarter results. Although the firm noted a lack of near-term catalysts and an ongoing market re-rating of asset-light businesses, it also acknowledged AECOM’s strong multi-year growth profile and consistent free-cash-flow generation. The analyst described the stock as attractively valued despite the absence of an immediate catalyst for multiple expansion.

AECOM (NYSE:ACM) is a multinational infrastructure consulting firm headquartered in Dallas, Texas, and was founded in 1990. The company provides planning, engineering, architectural design, environmental consulting, construction management, and program management services for public and private-sector clients worldwide.

While we acknowledge the potential of ACM as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 7 Best Automation Stocks to Buy for Warehouse Construction and Top 10 Stocks That Members of Congress Own.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/aecom-acm-7-best-civil-193850459.html',NULL,'2026-06-11 07:00:42.010611','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\aecom_acm_7_best_civil_engineering_stocks_to_buy_for_smart_city_projects__6b072aa8.json',1),
 (40,'f45576abe38d39937c67a73e57fe3f6e301b63a0c851c24d453fb7a8bbc82369','Yahoo Finance','Is Autodesk, Inc. (ADSK) among the Best Automation Stocks to Buy for Warehouse Construction?','','With an upside potential of 28.71%, Autodesk, Inc. (NASDAQ:ADSK) is among the 7 Best Automation Stocks to Buy for Warehouse Construction.

Autodesk, Inc. (NASDAQ:ADSK) received additional analyst support on June 1 when Citi raised its price target on the stock to $252 from $246 while maintaining a Neutral rating. The firm viewed the company’s first-quarter results favorably and noted that the acquisition of MaintainX creates a meaningful new growth opportunity. Although Citi highlighted some concerns regarding the pace of growth in Autodesk’s core business, the overall assessment suggests that the company continues to execute effectively while expanding into adjacent markets.

Previously, on May 29, RBC Capital lowered its price target on Autodesk, Inc. (NASDAQ:ADSK) to $305 from $335 but maintained an Outperform rating. The firm cited a strong quarterly performance that exceeded expectations and highlighted the company’s $3.6 billion acquisition of MaintainX, the largest transaction in Autodesk’s history. While the acquisition has prompted investor questions regarding future growth and margin profiles, RBC believes any dilution can be absorbed within existing operating-margin targets and views Autodesk as well-positioned to help define the next generation of industrial artificial intelligence solutions.

Autodesk, Inc. (NASDAQ:ADSK) is a multinational software company headquartered in San Francisco, California, and was founded in 1982. The company develops industry-leading computer-aided design, engineering, construction, and digital content creation software used by architects, engineers, manufacturers, and construction professionals worldwide.

While we acknowledge the potential of ADSK as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 7 Best Civil Engineering Stocks to Buy for Smart City Projects and Top 10 Stocks That Members of Congress Own.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/autodesk-inc-adsk-among-best-194117033.html',NULL,'2026-06-11 07:00:46.145510','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\is_autodesk_inc_adsk_among_the_best_automation_stocks_to_buy_for_warehouse_const__f45576ab.json',1),
 (41,'901d5924a3c22bb2dc6ed394d09a2523cef01ade85cbe224001927bb2c96c9c2','Yahoo Finance','Emerson (EMR) Teams Up With Aramco On A Technology Initiative With Bigger Implications','','With an upside potential of 17.08%, Emerson Electric Co. (NYSE:EMR) is among the 7 Best Automation Stocks to Buy for Warehouse Construction.

On May 27, Emerson Electric Co. (NYSE:EMR) announced a collaboration with Saudi Arabian Oil Company, Aramco, to co-develop advanced corrosion management solutions aimed at enhancing industrial asset integrity and operational efficiency. Under the research and development agreement, Aramco will contribute its technical expertise and intellectual property, while Emerson will provide its ultrasonic online corrosion monitoring technology, wireless connectivity solutions for corrosion wall-thickness monitoring, and continuous data collection capabilities. The partnership is focused on digitalizing corrosion management processes and developing a customized solution tailored to Aramco’s operational requirements.

On May 6, Barclays raised its price target on Emerson Electric Co. (NYSE:EMR) to $144 from $140 while maintaining an Equal Weight rating on the shares. On the same day, RBC Capital increased its price target to $169 from $161 and reiterated an Outperform rating following the company’s second-quarter results. RBC noted that proactive cost management initiatives enabled Emerson to raise the lower end of its fiscal 2026 earnings-per-share guidance despite factoring in a one-percentage-point impact from continued Middle East disruptions and reducing its organic sales growth outlook from 4% to 3%. The firm highlighted the company’s operational discipline and resilience in navigating a challenging macroeconomic environment.

Founded in 1890 and headquartered in St. Louis, Missouri, Emerson Electric Co. (NYSE:EMR) deals with supplying smart pneumatics, drives, and programmable logic controllers that automate conveyor sorting, packaging lines, and automated storage and retrieval systems (AS/RS) to optimize distribution efficiency.

While we acknowledge the potential of EMR as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 7 Best Civil Engineering Stocks to Buy for Smart City Projects and Top 10 Stocks That Members of Congress Own.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/emerson-emr-teams-aramco-technology-194022773.html',NULL,'2026-06-11 07:00:50.429822','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\emerson_emr_teams_up_with_aramco_on_a_technology_initiative_with_bigger_implicat__901d5924.json',1),
 (42,'a06e300a91133584f2dc464024ed10e21964ecf4e00543a70e7a6025ea218fa5','Yahoo Finance','Deere (DE) Could Benefit As Farm Equipment Demand Begins To Stabilize','','With an upside potential of 10.09%, Deere & Company (NYSE:DE) is among the 7 Best Automation Stocks to Buy for Warehouse Construction.

Deere & Company (NYSE:DE) attracted analyst attention on June 4 when JPMorgan raised its price target on the stock to $590 from $560 while maintaining a Neutral rating. The firm believes agricultural industry fundamentals are improving and could support a moderate recovery in North America next year. JPMorgan now expects single-digit retail volume growth and modest pricing gains in 2027, reflecting a more balanced outlook for the agricultural equipment market despite ongoing tariff considerations and evolving farm economics.

Earlier, on May 27, Oppenheimer analyst Kristen Owen lowered the firm’s price target on Deere & Company (NYSE:DE) to $680 from $715 while maintaining an Outperform rating. Following extensive discussions with management, the firm noted that near-term share performance could remain influenced by weather conditions and commodity-price movements. However, Oppenheimer continues to view Deere favorably over the longer term and expects business conditions to improve gradually by 2027 as agricultural markets stabilize and demand trends strengthen.

Founded in 1837 and headquartered in Moline, Illinois, Deere & Company is a manufacturer of agricultural, construction, and forestry equipment. The company is also heavily involved in warehouse and industrial site development through its portfolio of earth-moving machinery, including excavators and crawler dozers.

While we acknowledge the potential of DE as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.

READ NEXT: 7 Best Civil Engineering Stocks to Buy for Smart City Projects and Top 10 Stocks That Members of Congress Own.

Disclosure: None. Follow Insider Monkey on Google News.','https://finance.yahoo.com/markets/stocks/articles/deere-could-benefit-farm-equipment-193954092.html',NULL,'2026-06-11 07:00:55.650604','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\deere_de_could_benefit_as_farm_equipment_demand_begins_to_stabilize__a06e300a.json',1),
 (43,'333ac858883e211986bd4f30e0570b7f6ad72f3da29c8b27e4e251bf5498dcc1','Yahoo Finance','Current price of oil as of June 10, 2026','','At 9 a.m. Eastern Time on June 10, 2026, the price of oil sits at $94.27 per barrel, using Brent as the benchmark (we’ll explain what that means shortly). That’s a decrease of 79 cents since yesterday morning and roughly $27 more than at this time last year.

oil price per barrel % Change Price of oil yesterday $95.06 -0.83% Price of oil 1 month ago $104.19 -9.52% Price of oil 1 year ago $66.99 +40.72%

Check Out Our Daily Rates Reports

Will oil prices go up?

Nobody can predict the future path of oil prices with certainty. A range of factors influence how oil trades, yet supply and demand remain the main drivers. When fears of economic slowdown, conflict, or similar shocks rise, oil prices can move sharply.

How oil prices translate to gas pump prices

The price you see at the gas pump reflects more than just crude oil. Also built in are the costs of refining, distribution through wholesalers, various taxes, and the margin your neighborhood station charges.

Crude oil is still the largest single driver of the final pump price, typically representing over half of each gallon’s cost. Spikes in oil prices tend to push gas prices higher in short order. But when oil prices decline, gas prices often ease down gradually, a behavior known as “rockets and feathers.”

The role of the U.S. Strategic Petroleum Reserve

In the event of an emergency, the U.S. maintains a stockpile of crude oil known as the Strategic Petroleum Reserve. Its main goal is to safeguard energy security when disasters strike—think sanctions, severe storm damage, or war. It can also do a lot to ease the pain of sudden price jumps when supply gets disrupted.

It’s not a permanent fix, as it’s more meant to provide immediate support for consumers and ensure critical parts of the economy like key industries, emergency services, public transportation, and so on can keep operating.

How oil and natural gas prices are linked

Both oil and natural gas play key roles as major sources of energy. A big change in oil prices can affect natural gas by proxy. If oil prices increase, some industries may swap natural gas for some segments of their operations where possible, increasing the demand for natural gas.','https://finance.yahoo.com/markets/commodities/articles/current-price-oil-june-10-130405234.html',NULL,'2026-06-11 21:11:04.203212','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\current_price_of_oil_as_of_june_10_2026__333ac858.json',1),
 (44,'ea5bc623493f0bf627802e830a491799f5b4b168409fd868cb49ca3dccb14723','Yahoo Finance','Oracle Earnings Could Reveal a Massive $100 Billion Spending Surge. Here Is Why You Should Still Buy ORCL Stock.','','BNP Paribas analyst Stefan Slowinski believes that Oracle (ORCL) will increase its capital spending to a range of $80 billion to $100 billion in the upcoming quarterly report scheduled for today, June 10, after the market close. Just a couple of years ago, this figure was $6.9 billion. This significantly increased forecast is primarily due to the firm working on building the world’s largest AI infrastructure — called Project Stargate — alongside OpenAI and SoftBank (SFTBY). Oracle is helping develop campuses for this project across the U.S. and beyond, fully supported in its endeavors by President Donald Trump and the federal government.

Investors previously had concerns about how Oracle would pay for the massive spending. But with OpenAI raising a whopping $122 billion, Oracle being prepaid by its customers, and Abilene (Stargate’s biggest data center) expected to be completed by the first quarter of 2027, these concerns have somewhat eased. ORCL stock has also fared relatively well in the last three months, although it''s nowhere near its September 2025 highs.

More News from Barchart

Slowinski also hinted toward a potential risk with new CFO Hilary Maxson taking over in the next quarter for the first time, as not knowing what her approach will be adds a bit of uncertainty. Even bigger developments worth noting are Oracle''s layoffs and share issuance. Oracle is reportedly laying off as many as 30,000 employees to improve cash flow for AI data centers. Although Slowinski expects the actual number to be lower, this signals a huge shift in the way the firm is looking to operate moving forward. Additionally, Oracle has announced a $20 billion at-the-market (ATM) equity issuance. Existing shareholders will be keen on knowing when that comes into effect.

About Oracle Stock

Oracle is a U.S. technology company that operates globally, offering database software and cloud computing services. Its key products include the Oracle Database, Oracle ERP, and Oracle Cloud Infrastructure. Serving practically every major industry, the firm is currently focused on building out massive AI infrastructure.

Oracle is working with OpenAI and SoftBank to create data centers across the U.S. and is now expanding internationally as well, with ongoing projects in Norway, the U.K., and the United Arab Emirates (UAE). Founded in 1977, the company is headquartered in Austin, Texas. In September 2025, the firm announced that Clay Magouyrk and Mike Sicilia would become co-CEOs. Meanwhile, Larry Ellison continues to operate as Executive Chairman and Chief Technology Officer.','https://finance.yahoo.com/markets/stocks/articles/oracle-earnings-could-reveal-massive-130002411.html',NULL,'2026-06-11 21:11:05.988479','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\oracle_earnings_could_reveal_a_massive_100_billion_spending_surge_here_is_why_yo__ea5bc623.json',1),
 (45,'8a7e586569bf827f2687185132529bb42c267edb799b878c37a98b5a34edcb0d','Yahoo Finance','Oklo Buys Precision Manufacturing Company ARMEC to Speed Up Reactor Deployment. What This Means for OKLO Stock.','','Cash use tells the same story, with $17.9 million used in operating activities after adjusting for $15.6 million in stock-based compensation, and $359 million flowing into investing, mostly to buy marketable securities. Capital spending came in at $32.8 million as Oklo pushed projects across its main business lines. For 2026, management is guiding to $80 million–$100 million in operating cash burn and $350 million–$450 million in capex, underlining how much they’re still in build mode.

On the balance sheet, Oklo ended the last quarter with $2.5 billion in cash and marketable securities, split between $1.6 billion in cash and $900 million in securities, helped by $1.2 billion raised through an at-the-market equity program. But the company is still losing money as it builds out. Net loss was $33.1 million, driven by a $51.2 million operating loss and $3.2 million in taxes, partly offset by $21.3 million in interest and dividend income.

Oklo is an advanced nuclear company building small, fast reactors and its own fuel supply, to deliver steady, clean power from a vertically integrated setup that covers design, fuel fabrication, and recycling. Over the past 12 months, the stock is up 4.09%, but year-to-date (YTD), it’s down 21.29%.

The market reacted, OKLO rising 3.96% on the day of the announcement. But for a company still burning cash and without commercial revenue, does owning a manufacturing business actually speed up reactor deployment, or is this just another step that sounds good but takes time to pay off?

Oklo (OKLO) has been riding that momentum. Earlier this year, it secured a long-term power deal with Meta Platforms (META), which gave its small modular reactor model a real vote of confidence and pushed the stock higher. Then on June 4, 2026, Oklo said it had closed its acquisition of ARMEC, a precision manufacturing firm focused on high-tolerance nuclear components.

Nuclear stocks are getting attention again, driven by a flurry of announcements around new reactor deals, including Brookfield Asset Management (BAM) teaming up with The Nuclear Company to roll out Westinghouse AP1000 and AP300 reactors, while Blue Energy (BUENF) works with GE Vernova (GEV) on a hybrid gas and nuclear design. At the same time, a recent Gallup poll shows record U.S. support for nuclear power, pointing to a shift where policy support and demand are starting to turn into actual projects, not just talk.

Story Continues

The Growth Case Behind ARMEC

The ARMEC acquisition is a straightforward way for Oklo to pull more of the hard engineering work inside the company. ARMEC is based in Tennessee and brings more than 20 years of experience, a roughly 40-person technical team, and hands-on skills in high-precision machining, prototyping, fabrication, inspection, and engineering.

The key benefit is the tighter loop between design and manufacturing, so Oklo can move from early test hardware to repeatable production. ARMEC is already helping with nozzle manufacturing through better drawings, inspection planning, and supplier troubleshooting, which shows up as real operational progress, not just a long-term promise.

That extra control also ties into Oklo’s fuel plans. The company was picked by the U.S. Department of Energy for advanced talks on a program to turn surplus Cold War-era plutonium into fuel for advanced reactors. If that moves ahead, it gives Oklo another potential domestic fuel source at a time when enrichment capacity is tight, and it fits with its recycling-focused approach. Working with nuclear energy company Newcleo, Oklo is pairing that strategy with plans for up to $2 billion in fuel fabrication investment.

Oklo is also trying to speed up its design cycle by leaning into AI. The company announced a Strategic Partnership Project with Battelle Energy Alliance, which runs Idaho National Laboratory, to use AI tools to accelerate advanced reactor and fuel-system design work. The National Nuclear Security Administration-backed project gives Oklo access to specialized lab expertise and facilities to support conceptual design for one of its reactor systems using AI-enabled engineering workflows, modeling, simulation, and documentation.

Under the partnership, Oklo and INL will link the Prometheus AI platform with Oklo’s own Multiphysics design and analysis stack to streamline engineering work and push forward Pluto, Oklo’s plutonium-fueled reactor that sits inside the DOE’s Reactor Pilot Program.

Analyst Sentiment and Near-Term Outlook

The next earnings release for Oklo is set for August 10, 2026. For the June 2026 quarter, analysts are looking for a loss of $0.19 per share, a touch worse than the $0.18 loss a year ago, which works out to a 5.56% year-over-year (YOY) decline. The September 2026 quarter is pegged at a $0.20 loss, unchanged from last year, while full-year 2026 is modeled at a $0.78 loss versus $0.72 in 2025, an 8.33% drop.

Bank of America analyst Ross Fowler recently restarted coverage with a “Buy” rating and an $80 price target, calling Oklo an “early leader” in advanced nuclear. His case leans on the full-stack model, where Oklo owns, operates, and manages its reactors under long-term contracts instead of just selling equipment. He also highlighted the binding 1.2 GWe agreement with Meta Platforms and more than 14 GWe of additional projects under non-binding letters of intent as signs that demand is building faster than many investors think.

All 22 analysts covering Oklo have it rated at a consensus "Moderate Buy", with an average price target of $85.68. Off the current price levels, that points to 51.7% upside.

www.barchart.com

www.barchart.com

Conclusion

This appears as a meaningful move for the stock, but mostly as a thesis-strengthening step rather than an immediate game changer. ARMEC gives Oklo tighter control over a critical part of reactor manufacturing, which fits neatly with its broader push to own more of the supply chain, secure fuel pathways, and move closer to deployment. That does not remove the core risks around execution, regulation, and cash burn, but it does make the story more credible. My base case is that shares are more likely to stay volatile in the near term, yet trend higher over time if Oklo keeps stacking operational milestones and avoids major delays.

On the date of publication, Ebube Jones did not have (either directly or indirectly) positions in any of the securities mentioned in this article. All information and data in this article is solely for informational purposes. This article was originally published on Barchart.com','https://finance.yahoo.com/markets/stocks/articles/oklo-buys-precision-manufacturing-company-130003203.html',NULL,'2026-06-11 21:11:07.798211','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\oklo_buys_precision_manufacturing_company_armec_to_speed_up_reactor_deployment_w__8a7e5865.json',1),
 (46,'7bbfda74551048e1bbe2f746eb56f4c85a22101e54b9425c41740758996f5340','Yahoo Finance','Cisco Is Up 61% in 2026. It’s One of 3 Dividend Stocks Quietly Riding the AI Boom.','','Great stocks often start by being good stocks first.

When it comes to dividend investing, that can mean finding companies that are already rewarding shareholders, but aren’t yet relying on yield alone to attract attention. The better opportunities may come from businesses that are still growing, still gaining investor confidence, and still showing strong price momentum.

More News from Barchart

That’s why, for this screen, I looked beyond the usual high-yield names and focused on dividend stocks that are up in 2026, have a good analyst following, and are “buy-rated”. Among the results, these are the top three dividend stocks leading the list so far this year.

How I came up with these stocks

Using Barchart’s Stock Screener, I selected the following filters to get my list:

YTD Percent Change: Greater than 1%. I’m only looking for companies that are up since the year started. Then I’ll sort the results by percent change from highest to lowest.

Number of Analysts: 12 or more. A higher number of analysts suggests broader Wall Street coverage.

Current Analyst Rating: 3.5-5. Speaking of ratings, this filter screens only stocks rated “Moderate” to “Strong Buy” by Wall Street.

Dividend Investing Ideas: Best Dividend Stocks.

I ran the screen and got 10 results, and I’ll cover the top three dividend stocks- with the highest year-to-date percent change.

Let’s start with the first company:

Cisco Systems Inc (CSCO)

Cisco Systems helps businesses connect networks, security systems, and digital infrastructure together. As companies prepare for their growing AI needs, Cisco is leveraging the agentic AI era to showcase how its technology supports the future of connected systems.

CSCO stock is up 61% since the start of the year, making it the top-performing dividend stock on this list. In terms of dividends, Cisco has raised its payouts for more than a decade, and investors currently get $1.68 per share, per year, translating to a yield of around 1.3%

Meanwhile, a consensus among 25 analysts rates the stock a “Moderate Buy”, with the high target prices suggesting as much as ~20.8% upside over the next year.','https://finance.yahoo.com/markets/stocks/articles/cisco-61-2026-one-3-130002601.html',NULL,'2026-06-11 21:11:09.604345','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\cisco_is_up_61_in_2026_its_one_of_3_dividend_stocks_quietly_riding_the_ai_boom__7bbfda74.json',1),
 (47,'8be78d6f301ceedbb1c7d956fa6c9ddc16443e43482bf7b8ddd3e8918a91dff4','Yahoo Finance','More Than 50% Of Bitcoin Supply Is Now Underwater','','More than half (50%) of Bitcoin’s (CRYPTO: $BTC) circulating supply is now underwater, which means it’s trading below the price it was purchased at.

News that the majority of BTC is underwater comes after the cryptocurrency saw its price fall 28% from a high of around $82,000 U.S. to below $60,000 U.S. in recent weeks.

Research firm K33 says that the price decline has pushed more than 10 million Bitcoin below its purchase price, putting investors in the red on their holdings.

More From Cryptoprowl:

In May of this year, about 30% of Bitcoin’s supply was underwater. BTC is currently trading just below $62,000 U.S., a level it has been at for several days now.

Some analysts see a silver lining in the current situation with Bitcoin, noting that in the 2011, 2018, and 2022 bear markets, BTC bottomed within one month of seeing more than 50% of its supply trading at a loss,

Analysts also note that Bitcoin’s latest selloff brought its price back to the 200-week moving average, a level that K33 says has marked every major bear market bottom.

Still, some analysts and investors say BTC likely has further to fall as capital rotates out of cryptocurrencies and into technology stocks and other assets.

The price of $60,000 U.S. has been Bitcoin’s low for the year and a level the cryptocurrency previously reached in February.

Bitcoin last reached an all-time high of $126,000 U.S. in October of last year.','https://finance.yahoo.com/markets/crypto/articles/more-50-bitcoin-supply-now-130200402.html',NULL,'2026-06-11 21:11:11.343794','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\more_than_50_of_bitcoin_supply_is_now_underwater__8be78d6f.json',1),
 (48,'c3fc820c1345e328d6fd1605f86cc28f6ef4eb554032847e87f5391a0028916d','Yahoo Finance','Brutally honest guide to not losing money in the market','','*Get our Investment Guide:* https://clickhubspot.com/xg92



Episode 832: Sam Parr ( https://x.com/theSamParr ) and Shaan Puri ( https://x.com/ShaanVP ) talk to legendary fund manager Barry Ritholtz( https://x.com/Ritholtz ) about the behaviors that destroy returns for investors and how to avoid them.

—

Show Notes:

(0:00) Intro

(2:19) christmas tree portfolio

(4:43) the cowboy account

(9:51) day trading

(11:09) Barry yells at Lloyd Blankfein

(13:46) panic selling

(16:45) sam picks a fight

(18:46) direct indexing

(21:43) Great investors

(27:25) 90% of everything is crap

(36:14) Elon''s foray into PE

(44:02) Predicting the housing crisis

(46:01) spending a year as the dumbest guy on wall street

(49:01) Why bubbles are good for the economy



—

Links:

• How Not To Invest - https://www.hownottoinvestbook.com/



—

Check Out Sam''s Stuff:

• Hampton (joinhampton.com): My community for founders. Average member does $25m/year. Many of the guests are members. Get after it...apply: http://joinhampton.com/mfm



—

Check Out Shaan''s Stuff:

• Shaan''s weekly email - https://www.shaanpuri.com

• Visit https://www.somewhere.com/mfm to hire worldwide talent like Shaan and get $500 off for being an MFM listener. Hire developers, assistants, marketing pros, sales teams and more for 80% less than US equivalents.

• Mercury - Need a bank for your company? Go check out Mercury (mercury.com). Shaan uses it for all of his companies!

Mercury is a financial technology company, not an FDIC-insured bank. Banking services provided by Choice Financial Group, Column, N.A., and Evolve Bank & Trust, Members FDIC

• I run all my newsletters on Beehiiv and you should too + we''re giving away $10k to our favorite newsletter, check it out:

beehiiv.com/mfm-challenge



My First Million is a HubSpot Original Podcast // Brought to you by HubSpot Media // Production by Arie Desormeaux // Editing by Ezra Bakker Trupiano /','https://finance.yahoo.com/video/brutally-honest-guide-not-losing-130019958.html',NULL,'2026-06-11 21:11:13.129912','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\brutally_honest_guide_to_not_losing_money_in_the_market__c3fc820c.json',1),
 (49,'0c853b9ee3e84f693485012f69e0829aa3ff7b77b3978ce263f22b2440e2a195','Yahoo Finance','Best hedges against inflation: 6 ways to protect your purchasing power','','Inflation — the increase in the cost of goods and services over time — impacts your purchasing power. As prices rise, your dollars don''t buy as much as they used to.

According to the Bureau of Labor Statistics, consumer prices shot up 4.2% in May from the previous year, the hottest annual reading since April 2023. Inflation climbed as higher energy prices tied to the Iran conflict continued to pressure the U.S. economy.

During periods of high inflation, it''s important to be strategic about where you park your cash. Choosing the right accounts and investments can help protect the value of your money and hedge against rising costs.

What is an inflation hedge?

An inflation hedge is an asset, account, or strategy that protects your money against rising prices by helping retain its value or increase in value over time. The point of an inflation hedge is to provide stability even during periods of economic downturns and market volatility.

6 best hedges against inflation

Inflation hedges are not completely risk-free, but they do offer the chance to protect your purchasing power and maintain the value of your money. Here''s a look at some of the best options.

1. Gold

Gold is often touted as a safe-haven asset because its value tends to rise even in times of uncertainty. It can also provide a hedge against inflation because there is a limited amount of this asset available — unlike the amount of cash in circulation (or government-issued currency), which can be increased if the government decides to print more.

Read more: Gold forecast and tracker: Where prices could land in 2026

2. High-yield bank accounts

Certain accounts, such as high-yield savings accounts (HYSAs) and certificates of deposit (CDs), can help you secure competitive interest rates that outpace inflation. In fact, it''s possible to find both HYSAs and CDs that currently earn as much as 4% APY.

Plus, as long as you choose a bank that''s federally insured, your deposits are protected against loss (up to $250,000 per depositor, per institution, per ownership category) in the event the bank fails.

Read more: How inflation affects savings: Here''s the interest rate you need to beat

3. Treasury Inflation-Protected Securities

Often referred to as "TIPS," these government bonds are tied to the Consumer Price Index (CPI) and are backed by the full faith of the U.S. government. The principal increases with inflation and decreases with deflation, and interest is paid out every six months.

TIPS are offered in terms of five, 10, and 30 years. Investors are guaranteed to receive at least the full principal amount they originally invested when their bond matures, which can provide some form of financial security in the event of an economic downturn.

Read more: What to do when your wages aren''t keeping up with the cost of living

4. Series I bonds

Series I bonds are a type of U.S. savings bond designed specifically to protect your purchasing power from inflation.

Issued by the U.S. Department of the Treasury, I bonds earn a composite interest rate made up of two parts: a fixed rate that stays the same for the life of the bond, and a variable rate that adjusts every six months based on changes in the CPI.

When inflation rises, the variable portion increases, boosting your overall return; when inflation falls, the rate adjusts downward. Because the bond''s value is tied to inflation, it helps preserve the real (inflation-adjusted) value of your savings over time.

Read more: I bond vs. high-yield savings account: Which is better for beating inflation?

5. Real estate

When prices for everyday goods increase, the same often happens with property values and rents. This is why investing in real estate can be a smart way to hedge against inflation.

You don''t have to invest directly in a property, either. You can gain exposure to the real estate market by investing in real estate investment trusts (REITs). These are companies that own, operate, or finance income-producing properties. These trusts can be especially beneficial if housing inventory is low and direct ownership isn''t an option.

6. Commodities

Gold isn''t the only commodity that can serve as an inflation hedge. Oil, gas, agricultural products, and other metals can be worthwhile investments as inflation remains elevated.

Not only do they have intrinsic value because they are physical assets, but also commodities typically increase in value over the long-term because of the role they play in the production and distribution of everyday goods.','https://finance.yahoo.com/personal-finance/banking/article/best-hedges-against-inflation-231136070.html',NULL,'2026-06-11 21:11:14.369027','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\best_hedges_against_inflation_6_ways_to_protect_your_purchasing_power__0c853b9e.json',1),
 (50,'e13351bd7e89cfa7604b515e092bd065cc966f96a42fa327b11d21b45568a729','Yahoo Finance','Bosch on track to meet 2026 targets but wary of Middle East risks, CEO says','','BERLIN, June 10 (Reuters) - The world''s top automotive supplier, Robert Bosch GmbH, is on track to ‌meet its financial targets this year despite new ‌challenges emerging, including possible supply chain shocks resulting from the Middle ​East conflict, CEO Stefan Hartung told Reuters on Wednesday.

Facing a slowdown in German car production and an investment-heavy transition to electric vehicles, Bosch plans 22,000 job cuts in ‌its core automotive business, ⁠with the measures expected to boost results this year after restructuring costs weighed in ⁠2025.

"We''ve set the course to be well positioned for the next phase," Hartung said at a robotics and automation ​event ​in Berlin.

The company continues to ​expect a profit margin ‌this year in the range of 4 to 6%, two to three times higher than last year, and revenue growth of 2 to 5% - making it more optimistic than its competitors Schaeffler and ZF.

But market conditions ‌aren''t getting any less demanding, Hartung ​said. "On the contrary: the environment ​remains challenging."

Uncertainty surrounding ​the war in the Middle East and ‌its potential impact on the ​supply of raw ​materials used in semiconductors, such as helium, have added to the risks for Bosch, according to the ​CEO.

"But fundamentally, ‌we are well-positioned and can achieve our goals under ​the current conditions," he added.

(Reporting by Rachel ​More, Editing by Linda Pasquini)','https://finance.yahoo.com/news/bosch-track-meet-2026-targets-125508199.html',NULL,'2026-06-11 21:11:16.301593','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\bosch_on_track_to_meet_2026_targets_but_wary_of_middle_east_risks_ceo_says__e13351bd.json',1),
 (51,'a2c901e11aa996114d67bbe3e007d80905438cd1f5db2c38c8d762a4cf077dfc','Yahoo Finance','Nasdaq Stock: Is NDAQ Underperforming the Financial Sector?','','New York-based Nasdaq, Inc. (NDAQ) operates as a technology company that serves capital markets and other industries worldwide. Valued at $49.5 billion by market cap, the company provides trading, clearing, exchange technology, regulatory, securities listing, analysis, investing tools and guides, financial, and information services.

Companies worth $10 billion or more are generally described as “large-cap stocks,” and NDAQ perfectly fits that description, with its market cap exceeding this mark, underscoring its size, influence, and dominance within the financial data & stock exchanges industry. Nasdaq''s diversified business model drives robust financial performance, fueled by successful expansions beyond traditional exchange services.

More News from Barchart

Despite its notable strength, NDAQ slipped 14% from its 52-week high of $101.79, achieved on Jan. 16. Over the past three months, NDAQ stock has declined marginally, underperforming the State Street Financial Select Sector SPDR ETF’s (XLF) 4.2% gains during the same time frame.

www.barchart.com

Shares of NDAQ fell 9.9% on a YTD basis but climbed 2.2% over the past 52 weeks, underperforming XLF’s YTD losses of 4.2% and 2.9% returns over the last year.

To confirm the bearish trend, NDAQ has been trading below its 200-day moving average since early February, with slight fluctuations. The stock has been trading below its 50-day moving average recently, with minor fluctuations.

www.barchart.com

On Apr. 23, NDAQ shares closed up marginally after reporting its Q1 results. Its adjusted EPS of $0.96 exceeded Wall Street expectations of $0.93. The company’s net revenue was $1.41 billion, topping Wall Street forecasts of $1.37 billion.

In the competitive arena of financial data & stock exchanges, Intercontinental Exchange, Inc. (ICE) has lagged behind NDAQ, with a 12.6% downtick on a YTD basis and 19.6% losses over the past 52 weeks.

Wall Street analysts are bullish on NDAQ’s prospects. The stock has a consensus “Strong Buy” rating from the 19 analysts covering it, and the mean price target of $109.18 suggests a potential upside of 24.7% from current price levels.

On the date of publication, Neha Panjwani did not have (either directly or indirectly) positions in any of the securities mentioned in this article. All information and data in this article is solely for informational purposes. This article was originally published on Barchart.com','https://finance.yahoo.com/markets/stocks/articles/nasdaq-stock-ndaq-underperforming-financial-130831693.html',NULL,'2026-06-11 21:11:18.110452','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\nasdaq_stock_is_ndaq_underperforming_the_financial_sector__a2c901e1.json',1),
 (52,'73d9c3e515ae808114ab5367ac11e35ab478d8fa9c6d9daa1c811f5d727dc16f','Yahoo Finance','Apple (AAPL) Declined Defies Strong Fundamentals','','The London Company, an investment management company, released its first-quarter 2026 investor letter for its “The London Company Income Equity Strategy”. A copy of the letter is available to download here. In early 2026, US equities declined, with the Russell 3000 falling 4% and the S&P posting losses. The year began positively on a broad rally, but sentiment reversed sharply in March due to the Iran conflict. Market leadership shifted to a narrow, commodity-focused sector benefiting energy, agriculture, and hard assets. Large-cap growth suffered double-digit losses amid weakness in Big Tech and AI-related concerns in software. Sector dispersion was extreme; Energy surged over 35%, while Tech dropped over 9%. The London Company Income Equity portfolio returned 4.4% (4.2% net) this quarter, outperforming the 2.1% rise in the Russell 1000 Value Index, supported by stock selection and sector exposure. In this environment, the portfolio is positioned to participate in market upside, offering diversification and quality. In addition, please check the Strategy’s top five holdings to know its best picks in 2026.

In its first-quarter 2026 investor letter, The London Company Income Equity Strategy highlighted Apple Inc. (NASDAQ:AAPL). Apple Inc. (NASDAQ:AAPL) is a leading multinational technology company that manufactures and markets smartphones, personal computers, tablets, wearables, and accessories. On June 9, 2026, Apple Inc. (NASDAQ:AAPL) closed at $290.55 per share. One-month return of Apple Inc. (NASDAQ:AAPL) was -2.78%, and its shares gained 46.17% over the past 52 weeks. Apple Inc. (NASDAQ:AAPL) has a market capitalization of $4.27 trillion.

The London Company Income Equity Strategy stated the following regarding Apple Inc. (NASDAQ:AAPL) in its Q1 2026 investor letter:

"Apple Inc. (NASDAQ:AAPL) – AAPL was a detractor despite strong results, including record iPhone revenue with demand partially constrained by supply. Investor sentiment focused on rising AI costs, including higher memory costs, overshadowing solid execution. We view this as a disconnect from fundamentals, as AAPL’s ecosystem strength, pricing power, and capital discipline remain intact. Continued iPhone momentum and significant capital return support our long-term thesis."

Is Apple (AAPL) One of the Best Reddit Stocks to Buy According to Billionaires?

Apple Inc. (NASDAQ:AAPL) ranks 10th on our list of 40 Most Popular Stocks Among Hedge Funds Heading Into 2026. According to our database, 170 hedge fund portfolios held Apple Inc. (NASDAQ:AAPL) at the end of the first quarter, up from 169 in the previous quarter. While we acknowledge the potential of Apple Inc. (NASDAQ:AAPL) as an investment, we believe certain AI stocks offer greater upside potential and carry less downside risk. If you''re looking for an extremely undervalued AI stock that also stands to benefit significantly from Trump-era tariffs and the onshoring trend, see our free report on the best short-term AI stock.','https://finance.yahoo.com/markets/stocks/articles/apple-aapl-declined-defies-strong-130804838.html',NULL,'2026-06-11 21:11:20.092907','C:\Users\sadiya rafiq\Documents\agentic AI\Finance_Pipeline\data\articles\2026-06-11\apple_aapl_declined_defies_strong_fundamentals__73d9c3e5.json',1);
INSERT INTO "portfolios" ("id","portfolio_code","account_id","name","strategy","inception_date","total_value","last_valued_at") VALUES (1,'PF-C001-GROWTH',1,'Arjun – US Growth Portfolio','Growth','2023-01-01 00:00:00.000000',500000.0,'2026-06-07 13:49:25.600284'),
 (2,'PF-C002',2,'Priya Sharma – Income','Income','2024-01-01 00:00:00.000000',45900.0,'2026-06-11 21:10:18.018357'),
 (3,'PF-C003',3,'Rahul Gupta – Balanced','Balanced','2024-01-01 00:00:00.000000',31600.0,'2026-06-11 21:10:18.069909'),
 (4,'PF-C004',4,'Neha Joshi – Tech-Heavy','Tech-Heavy','2024-01-01 00:00:00.000000',619300.0,'2026-06-11 21:10:18.107904'),
 (5,'PF-C005',5,'Vikram Patel – ESG','ESG','2024-01-01 00:00:00.000000',82150.0,'2026-06-11 21:10:18.134897');
INSERT INTO "sector_master" ("id","name","gics_code","description") VALUES (1,'Technology','45',NULL),
 (2,'Semiconductors','45301',NULL),
 (3,'Financials','40',NULL),
 (4,'Energy','10',NULL),
 (5,'Healthcare','35',NULL),
 (6,'Consumer Discretionary','25',NULL),
 (7,'Industrials','20',NULL),
 (8,'Utilities','55',NULL),
 (9,'Real Estate','60',NULL),
 (10,'Communication Services','50',NULL),
 (11,'Materials','15',NULL),
 (12,'Renewable Energy','10RE',NULL);
INSERT INTO "sector_tags" ("id","theme_id","sector_name","sentiment","confidence","rationale","tagged_at") VALUES (1,1,'Technology','POSITIVE',0.9,'Strong growth in cloud and advertising, alongside strategic restructurings, signals a robust outlook for technology companies.','2026-06-08 04:54:49.497675'),
 (2,2,'Consumer Staples','NEUTRAL',0.7,'Coca-Cola''s exploration of strategic share movements indicates stability without immediate growth catalysts.','2026-06-08 04:54:49.508679'),
 (3,3,'Semiconductors','POSITIVE',0.8,'Increased price targets for companies like Intel and AMD reflect confidence in semiconductor growth prospects.','2026-06-08 04:54:49.515356'),
 (4,3,'Technology','POSITIVE',0.85,'Apple''s continued positive ratings suggest sustained demand and innovation.','2026-06-08 04:54:49.515356'),
 (5,3,'Industrials','POSITIVE',0.75,'Industrial players like Caterpillar receiving positive sentiment indicate robust industrial demand.','2026-06-08 04:54:49.515356'),
 (6,4,'Financials','POSITIVE',0.9,'The successful launch of new crypto derivatives is driving significant trading volumes and interest.','2026-06-11 07:02:03.557051'),
 (7,5,'Industrials','POSITIVE',0.8,'Strategic growth initiatives and partnerships enhance efficiency and innovation in industrial operations.','2026-06-11 07:02:03.580047'),
 (8,5,'Energy','POSITIVE',0.7,'Collaborations are leading to improvements in energy efficiency and infrastructure resilience.','2026-06-11 07:02:03.580047'),
 (9,6,'Technology','POSITIVE',0.85,'Strong revenue growth and strategic acquisitions are driving long-term leadership and market expansion in the tech sector.','2026-06-11 07:02:03.604038'),
 (10,7,'Technology','MIXED',0.6,'Differing analyst opinions suggest varied potential outcomes for major technology firms.','2026-06-11 07:02:03.615039'),
 (11,7,'Industrials','NEUTRAL',0.5,'Mixed analyst outlooks for firms like Deere reflect uncertainty in industrial market adaptations.','2026-06-11 07:02:03.615039'),
 (12,8,'Energy','POSITIVE',0.9,'Surging energy prices and increased focus on renewable and nuclear energy initiatives boost sector prospects.','2026-06-11 21:12:15.573547'),
 (13,8,'Utilities','POSITIVE',0.8,'The transition to clean energy sources benefits utilities increasing their renewable energy portfolio.','2026-06-11 21:12:15.573547'),
 (14,9,'Cryptocurrencies','NEGATIVE',0.95,'A significant price decline in Bitcoin and broad market turbulence are affecting investor confidence.','2026-06-11 21:12:15.591539'),
 (15,9,'Financials','MIXED',0.6,'Financial institutions with exposure to cryptocurrencies face challenges, though not all are impacted equally.','2026-06-11 21:12:15.591539'),
 (16,10,'Industrials','NEGATIVE',0.7,'Supply chain risks due to geopolitical tensions can affect manufacturing and distribution operations.','2026-06-11 21:12:15.607539'),
 (17,10,'Consumer Goods','NEUTRAL',0.5,'Potential supply chain disruptions could impact product availability, though effects vary across sub-segments.','2026-06-11 21:12:15.607539'),
 (18,11,'Technology','MIXED',0.75,'While AI and infrastructure investments present growth opportunities, restructuring introduces uncertainty and volatility.','2026-06-11 21:12:15.616534'),
 (19,11,'Information Technology Services','MIXED',0.7,'Investments in technology infrastructure benefit select players, while layoffs present risks for others.','2026-06-11 21:12:15.616534');
INSERT INTO "securities" ("id","ticker","name","isin","security_type","exchange","sector_id","currency","last_price","last_price_at") VALUES (1,'NVDA','NVIDIA Corporation',NULL,'EQUITY','NASDAQ',2,'USD',900.0,'2026-06-07 13:49:25.602272'),
 (2,'MSFT','Microsoft Corporation',NULL,'EQUITY','NASDAQ',1,'USD',430.0,'2026-06-07 13:49:25.603277'),
 (3,'AAPL','Apple Inc.',NULL,'EQUITY','NASDAQ',1,'USD',195.0,'2026-06-07 13:49:25.603277'),
 (4,'AMZN','Amazon.com Inc.',NULL,'EQUITY','NASDAQ',1,'USD',185.0,NULL),
 (5,'TSLA','Tesla Inc.',NULL,'EQUITY','NASDAQ',6,'USD',NULL,NULL),
 (6,'JPM','JPMorgan Chase & Co.',NULL,'EQUITY','NYSE',3,'USD',195.0,NULL),
 (7,'XOM','Exxon Mobil Corporation',NULL,'EQUITY','NYSE',4,'USD',115.0,NULL),
 (8,'JNJ','Johnson & Johnson',NULL,'EQUITY','NYSE',5,'USD',165.0,NULL),
 (9,'ENPH','Enphase Energy Inc.',NULL,'EQUITY','NASDAQ',12,'USD',115.0,'2026-06-07 13:49:25.603277'),
 (10,'AMD','Advanced Micro Devices Inc.',NULL,'EQUITY','NASDAQ',2,'USD',162.0,'2026-06-07 13:49:25.603277');
INSERT INTO "themes" ("id","name","description","created_at","last_updated") VALUES (1,'Tech Resurgence','The technology sector is witnessing a revival driven by significant growth in cloud services and advertising revenues, coupled with strategic restructuring efforts. Companies are positioning themselves for future growth through strategic investments and integration into the public markets.','2026-06-08 04:54:49.478676','2026-06-08 04:54:49.478676'),
 (2,'Corporate Strategic Movements','Corporations across sectors are engaging in strategic share movements to optimize market positioning and shareholder returns. This trend includes potential public listings and sales of subsidiary stakes as part of global expansion strategies.','2026-06-08 04:54:49.492682','2026-06-08 04:54:49.492682'),
 (3,'Broad Market Optimism','Positive analyst sentiment and maintained or increased price targets indicate a healthy outlook across various sectors. This uplift is seen in both technology and industrial companies, suggesting overall confidence in continued economic performance.','2026-06-08 04:54:49.507695','2026-06-08 04:54:49.507695'),
 (4,'Crypto Derivatives Expansion','The rapid adoption of Kalshi''s crypto perpetual futures highlights a burgeoning interest in crypto derivatives, with market activity surging as new products gain momentum despite the regulatory landscape.','2026-06-11 07:02:03.534469','2026-06-11 07:02:03.534469'),
 (5,'Industrial and Energy Innovation','Technological advancements and strategic collaborations are propelling growth in the industrial and energy sectors, fostering resilience and efficiency.','2026-06-11 07:02:03.550051','2026-06-11 07:02:03.550051'),
 (6,'Technology Growth and Strategic Expansion','With financial growth and strategic acquisitions, companies like IBM and Autodesk are positioning themselves as leaders in software and operational infrastructure, respectively.','2026-06-11 07:02:03.576047','2026-06-11 07:02:03.576047'),
 (7,'Tech Sector Uncertainty','The technology sector is experiencing mixed signals from analysts, indicating uncertainty and varied expectations for growth and performance across major tech companies.','2026-06-11 07:02:03.603049','2026-06-11 07:02:03.603049'),
 (8,'Energy Market Dynamics','Volatility in oil and energy prices due to geopolitical tensions and inflationary pressures creates both opportunities and challenges. The drive towards nuclear and clean energy reflects a broader trend of transition and sustainability.','2026-06-11 21:12:15.555225','2026-06-11 21:12:15.555225'),
 (9,'Crypto Market Instability','The cryptocurrency market is undergoing significant instability, with major price declines in Bitcoin and other cryptocurrencies impacting investor sentiment and potentially leading to further regulatory scrutiny.','2026-06-11 21:12:15.567974','2026-06-11 21:12:15.567974'),
 (10,'Geopolitical Uncertainty','Geopolitical conflicts, particularly in the Middle East, are contributing to market disruptions, affecting equities and posing risks to supply chains for global companies.','2026-06-11 21:12:15.589539','2026-06-11 21:12:15.589539'),
 (11,'Tech Sector Realignment','The tech sector is experiencing a divergence in performance with some companies thriving due to strategic investments in AI and infrastructure, while others face challenges due to restructuring and layoffs.','2026-06-11 21:12:15.605542','2026-06-11 21:12:15.605542');
INSERT INTO "trend_themes" ("id","trend_id","theme_id","weight") VALUES (1,1,1,1.0),
 (2,2,1,1.0),
 (3,3,2,1.0),
 (4,4,3,1.0),
 (5,5,4,1.0),
 (6,6,5,1.0),
 (7,9,5,1.0),
 (8,7,6,1.0),
 (9,10,6,1.0),
 (10,8,7,1.0),
 (11,11,7,1.0),
 (12,12,8,1.0),
 (13,17,8,1.0),
 (14,14,9,1.0),
 (15,15,10,1.0),
 (16,13,11,1.0),
 (17,16,11,1.0);
INSERT INTO "trends" ("id","name","description","direction","first_seen_at","last_updated") VALUES (1,'Alphabet Growth and Stock Adjustments','Alphabet is experiencing significant growth in its Google Cloud and advertising revenues, while its stock undergoes adjustments due to price target changes and market pullbacks.','BULLISH','2026-06-08 04:54:45.688466','2026-06-08 04:54:45.688466'),
 (2,'Restructuring and Share Movement in Tech','Several technology companies, such as GitLab, are undergoing restructuring efforts, while investment funds actively increase their holdings in newly public companies like Circle.','BULLISH','2026-06-08 04:54:45.706462','2026-06-08 04:54:45.706462'),
 (3,'Coca-Cola Strategic Share Movements','The Coca-Cola Company is exploring strategic share movements through potential public listings and the sale of stakes in its subsidiaries as part of its global strategy.','SIDEWAYS','2026-06-08 04:54:45.732070','2026-06-08 04:54:45.732070'),
 (4,'Positive Analyst Sentiment in Various Sectors','Multiple major companies including Intel, AMD, Apple, and Caterpillar are receiving positive or maintained ratings and increased price targets from financial analysts, indicating a generally optimistic outlook across sectors.','BULLISH','2026-06-08 04:54:45.740070','2026-06-08 04:54:45.740070'),
 (5,'Surge in Crypto Derivatives','The launch of Kalshi''s crypto perpetual futures has seen remarkable market uptake with over $1 billion in trading volume within a week. This momentum is expected to grow as Kalshi plans to expand its offerings pending regulatory approval.','BULLISH','2026-06-11 07:01:56.440691','2026-06-11 07:01:56.440691'),
 (6,'Honeywell''s Strategic Growth Initiatives','Honeywell is positioned for growth through anticipated organic growth and operational efficiencies. Analysts are optimistic, revising price targets upwards and citing upcoming corporate actions as catalysts.','BULLISH','2026-06-11 07:01:56.460692','2026-06-11 07:01:56.461702'),
 (7,'IBM''s Financial Strength','IBM demonstrates solid financial performance with significant revenue growth in software and mainframe services. The company continues to reward shareholders through consistent dividend increases.','BULLISH','2026-06-11 07:01:56.497686','2026-06-11 07:01:56.497686'),
 (8,'Tech Industry Analyst Activity','There''s notable analyst activity affecting major tech firms with mixed signals from price target adjustments. While some ratings are cautiously optimistic, others show tempered adjustments.','SIDEWAYS','2026-06-11 07:01:56.519750','2026-06-11 07:01:56.519750'),
 (9,'Infrastructure and Energy Collaboration','Corporate collaborations solidify technological and operational advancements, highlighted by Emerson''s partnership with Aramco to innovate in corrosion management, signaling a push in infrastructure resilience and energy efficiency.','BULLISH','2026-06-11 07:01:56.559300','2026-06-11 07:01:56.559300'),
 (10,'Autodesk''s Strategic Expansion','Autodesk''s strategic acquisition of MaintainX is a significant move to bolster its operational infrastructure and expand its market leadership, indicative of strong growth ambitions.','BULLISH','2026-06-11 07:01:56.583287','2026-06-11 07:01:56.583287'),
 (11,'Mixed Outlook on Deere & Company','Analyst opinions on Deere & Company remain varied with adjustments in price targets reflecting mixed expectations for the company''s future performance and potential market adaptations.','SIDEWAYS','2026-06-11 07:01:56.592296','2026-06-11 07:01:56.592296'),
 (12,'Oil and Energy Prices Volatility','Fluctuating energy prices are affecting macroeconomic conditions, largely driven by geopolitical tensions and inflationary pressures. The energy sector experienced a notable surge, while Brent prices remain significantly higher than the previous year.','BULLISH','2026-06-11 21:12:06.855373','2026-06-11 21:12:06.855373'),
 (13,'Oracle''s Strategic Investments and Restructuring','Oracle is actively investing in AI infrastructure and expanding its capital expenditures, while also undergoing significant restructuring including equity issuance and large-scale layoffs.','UNKNOWN','2026-06-11 21:12:06.876416','2026-06-11 21:12:06.876416'),
 (14,'Cryptocurrency Market Turbulence','The cryptocurrency market is experiencing instability, with a notable decline in Bitcoin prices leading to a significant portion of the supply being traded below purchase price.','BEARISH','2026-06-11 21:12:06.898362','2026-06-11 21:12:06.898362'),
 (15,'Geopolitical Impacts on Markets','Ongoing conflicts in the Middle East are causing market disruptions, impacting US equities and posing potential supply chain risks for companies like Bosch.','BEARISH','2026-06-11 21:12:06.914390','2026-06-11 21:12:06.914390'),
 (16,'Technology Sector Performance Divergence','The tech sector is experiencing varied performance, with specific companies like Cisco showing strong stock appreciation and others like ICE facing declines. Overall, the sector has seen a downward trend recently.','UNKNOWN','2026-06-11 21:12:06.924367','2026-06-11 21:12:06.924367'),
 (17,'Nuclear and Clean Energy Developments','There is a growing focus on nuclear and clean energy, as evidenced by acquisitions and collaborations among companies like Oklo and Brookfield Asset Management.','BULLISH','2026-06-11 21:12:06.930368','2026-06-11 21:12:06.930368');
COMMIT;
